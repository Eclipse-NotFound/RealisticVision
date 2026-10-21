"""D33 isolated performance experiments. Never deploys or alters frozen D32."""
from pathlib import Path
import argparse, ctypes, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, threading, time, uuid
import psutil

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
GAME=MOD.parents[1]
OUT=MOD/'build/motion-performance-output'
BASE=MOD/'build/stair-shadow-output/merged-v0323/candidate'
OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeB83d4caf5c46b7'.lower()
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registration
from air_test_process import HiddenProcess
sys.path.insert(0,str(MOD/'build/wall-surface'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fp=load('d31_helpers',MOD/'build/frame-performance/run.py')
runner=fp.runner
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def freeze():
    assert sha(MOD/'release/RealisticVisionMod.swf')==sha(BASE/'RealisticVisionMod.swf')==OLD
    OUT.mkdir(exist_ok=True)
    for name in ['baseline','candidate']:
        dest=OUT/name/'src'
        if not dest.exists():shutil.copytree(BASE/'src',dest)
    pins=json.loads((BASE.parent/'merge-inputs.json').read_text())['candidate']
    assert all(sha(BASE/'src'/p)==h for p,h in pins.items())
    if not (OUT/'inputs.json').exists():save(OUT/'inputs.json',{'installed':OLD,'source':pins})

def runtime(folder):
    folder.mkdir(parents=True,exist_ok=True);(folder/'evidence').mkdir(exist_ok=True)
    for p in GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):shutil.copy2(p,folder/p.name)
    shutil.copytree(GAME/'Rooms',folder/'Rooms',dirs_exist_ok=True)
    desc=(GAME/'application.xml').read_text(encoding='utf-8-sig')
    desc=re.sub(r'<id>.*?</id>','<id>pfe-rv-motion-template-'+uuid.uuid4().hex+'</id>',desc)
    (folder/'application.xml').write_text(desc,encoding='utf-8')

def public(source,dest,profile=False):
    for p in source.rglob('*.as'):
        q=dest/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True)
        s=re.sub(r'\bprivate\b','public',p.read_text(encoding='utf-8-sig'))
        if profile and p.name=='RealisticVisionMod.as':
            s=fp.instrument(s,['prepareOcclusion','computeFov','applyVision','applyVisionClassic','joinClassicWalls','updateWallSurface','hideEnemies','applyMask','enemyState','fillFogCache','refreshWallField'])
            at=s.index('public function profiled_applyMask(');end=s.index('public function clearMask(',at)
            part=s[at:end];brace=part.index('{')+1
            part=part[:brace]+'\nvar sliceTime:int=getTimer();\n'+part[brace:]
            for marker,key in [('         // 子格级判定','maskSetup'),('         // 按模式模糊','maskRead'),('         rec.maskValid = false;','maskCompare'),('         // 位图填充绘制','maskBlur'),('         rec.maskBounds = sig;','maskGraphics')]:
                assert part.count(marker)==1,marker
                part=part.replace(marker,'profile["'+key+'"] = Number(profile["'+key+'"]||0)+getTimer()-sliceTime;sliceTime=getTimer();\n'+marker)
            s=s[:at]+part+s[end:]
        if profile and p.name=='RVWallSurface.as':s=fp.instrument(s,['updateContour','buildContourClip','rebuildFaces','rebuildSamples','rebuildSupport'])
        q.write_text(s,encoding='utf-8')

def build(name,profile=False,verify=False,large=False,live=False):
    folder=OUT/name;assert not folder.exists(),'Use a new experiment name'
    with Registration(owner='RealisticVision / D33 编译',purpose=name+' 编译，无游戏',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
        runtime(folder)
        probe=(MOD/'build/frame-performance/FrameProbe.as').read_text(encoding='utf-8-sig')
        probe=probe.replace('/RealisticVision/build/frame-performance-output/','/RealisticVision/build/motion-performance-output/')
        probe=probe.replace('private var caseIndex:int=0,','private var measuredStart:Number=0;\n      private var caseIndex:int=0,')
        probe=probe.replace('var now:int=getTimer();if(frame>=0', 'if(frame==0)measuredStart=new Date().time;\n         var now:int=getTimer();if(frame>=0')
        probe=probe.replace('entry:Object={spec:c,','entry:Object={measuredStart:measuredStart,measuredEnd:new Date().time,spec:c,')
        if live:
            # Native findCel deliberately excludes invulnerable players.
            # God mode prevents death without suppressing enemy targeting.
            probe=probe.replace('w.gg.invulner=true;','w.gg.invulner=false;')
            probe=probe.replace('["baseline","candidate","candidate","baseline","off"]','["baseline","candidate","candidate","baseline","baseline","candidate","candidate","baseline"]')
            probe=probe.replace('private var liveOrder:Array=', 'private var anchorX:Number=0,anchorY:Number=0,armedEnemy:*,attackTimers:Dictionary=new Dictionary(true);\n      private var liveOrder:Array=')
            probe=probe.replace('liveMod.cfgMode="current";', 'liveMod.cfgMode=liveIndex<4?"current":"classic";')
            probe=probe.replace('stageFps:host.stage.frameRate,','mode:liveMod.cfgMode,attackStarts:0,targetFrames:0,maxObjects:0,maxProjectiles:0,drivenFire:true,stageFps:host.stage.frameRate,')
            probe=probe.replace('trace("LIVE START "+liveIndex+" "+name);','''if(anchorX==0){
               // Spawn a native raider, not a stationary UnitDamager trap.
               // Random scene populations need not contain an armed combatant.
               var raiderClass:Class=host.loaderInfo.applicationDomain.getDefinition("fe.unit.UnitRaider") as Class;
               armedEnemy=new raiderClass("1",10,null,{weap:"smg10"});
               anchorX=Math.min(w.loc.limX-200,w.gg.X+240);anchorY=w.gg.Y;
               armedEnemy.putLoc(w.loc,anchorX,anchorY);armedEnemy.invulner=true;
               w.loc.addObj(armedEnemy);w.loc.units.push(armedEnemy);armedEnemy.step();
               if(!armedEnemy.currentWeapon||armedEnemy.currentWeapon.tip<=1)throw new Error("native ranged weapon missing");
            }
            armedEnemy.invulner=true;
            liveRow.enemyStart={hp:armedEnemy.hp,sost:armedEnemy.sost,weapon:armedEnemy.currentWeapon.id};
            trace("LIVE START "+liveIndex+" "+name+" "+liveMod.cfgMode+" anchor="+anchorX+","+anchorY+" enemy="+armedEnemy.id+" weapon="+armedEnemy.currentWeapon.id+" tip="+armedEnemy.currentWeapon.tip);''')
            probe=probe.replace('w.gg.setPos(360+(liveAge%120)*4,640);','w.gg.setPos(Math.max(80,Math.min(w.loc.limX-80,anchorX+Math.abs((liveAge%40)-20)*12-120)),anchorY);')
            probe=probe.replace('if(++liveAge<210)return;','''// Controlled native firing: only the isolated fixture invokes attack.
            // Weapon physics, projectiles, damage and the native world keep running.
            // Non-automatic weapons reset t_auto while the trigger is held.
            // Leave six native steps between presses so their latch releases.
            armedEnemy.setCel(w.gg);if(liveAge%6==0)armedEnemy.currentWeapon.attack();
            for each(var actor:* in w.loc.units){
               if(actor.celUnit===w.gg)liveRow.targetFrames++;
               var weapon:*=actor.currentWeapon;
               if(weapon){if(weapon.t_attack>int(attackTimers[weapon]))liveRow.attackStarts++;attackTimers[weapon]=weapon.t_attack;}
            }
            var obj:*=w.loc.firstObj;var count:int=0,projectiles:int=0;while(obj&&count<5000){count++;if(getQualifiedClassName(obj).indexOf("Bullet")>=0)projectiles++;obj=obj.nobj;}liveRow.maxObjects=Math.max(liveRow.maxObjects,count);liveRow.maxProjectiles=Math.max(liveRow.maxProjectiles,projectiles);
            if(++liveAge<150)return;''')
            probe=probe.replace('liveRow.unitsEnd=w.loc.units.length;', '''liveRow.enemyEnd={hp:armedEnemy.hp,sost:armedEnemy.sost,attack:armedEnemy.currentWeapon.t_attack,reload:armedEnemy.currentWeapon.t_reload,ammo:armedEnemy.currentWeapon.hold};
            if(liveRow.attackStarts<1 || liveRow.maxProjectiles<1)throw new Error("combat fixture did not sustain native fire: "+JSON.stringify(liveRow.enemyEnd));
            liveRow.unitsEnd=w.loc.units.length;''')
        probe=probe.replace('FrameProbe','MotionFrameProbeMod')
        (folder/'MotionFrameProbeMod.as').write_text(probe,encoding='utf-8')
        runner.compile(folder/'MotionFrameProbeMod.as',folder/'mods/MotionFrameProbe/release/MotionFrameProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,'+str(large).lower(),'-define=CONFIG::verifyPixels,'+str(verify).lower(),'-define=CONFIG::liveFrames,'+str(live).lower()])
        selected=['MotionFrameProbeMod']
        catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
        (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
        if large:
            target=folder/'mods/ContinuousScene/release';target.mkdir(parents=True)
            for p in (GAME/'mods/ContinuousScene/release').iterdir():
                if p.is_file():shutil.copy2(p,target/p.name)
            selected.insert(0,'ContinuousSceneMod')
        result=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8',timeout=45)
        (folder/'selection.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stdout+result.stderr
        for variant in ['baseline','candidate']:
            src=folder/(variant+'-src');public(OUT/variant/'src',src,profile)
            runner.compile(src/'RealisticVisionMod.as',folder/(variant+'.swf'),[src],stubs=True)
        save(folder/'build.json',{'profile':profile,'verify':verify,'large':large,'live':live,'files':{str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix in ['.swf','.as','.xml','.txt']}})
        rec.outcome='passed';rec.note='候选及驱动编译通过；功能与性能另测'

def environment():
    return {'time':time.time(),'available_bytes':psutil.virtual_memory().available,'processes':[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower() in ['adl.exe','adl64.exe','java.exe','javaw.exe']]}

def air(folder,entry,rec,timeout=300,seed_store=None):
    appid='pfe-modsettings-rv-motion-'+uuid.uuid4().hex
    if seed_store:
        target=Path(os.environ['APPDATA'])/appid/'Local Store'
        target.mkdir(parents=True,exist_ok=False)
        shutil.copyfile(seed_store/'RealisticVision_config.txt',target/'RealisticVision_config.txt')
    desc=folder/'test.xml'; process=None
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+'</id><versionNumber>1.0</versionNumber><filename>RVMotion</filename><initialWindow><content>'+entry+'</content><visible>false</visible><width>1280</width><height>720</height><renderMode>'+('direct' if entry=='pfe.swf' else 'cpu')+'</renderMode></initialWindow></application>',encoding='utf-8')
    try:
        rec.before_launch(appid+' / '+str(desc))
        with (folder/'air-output.log').open('w',encoding='utf-8') as log:
            process=HiddenProcess([GAME/'adl64.exe','-runtime',GAME/'runtimes/air/win64',desc,'-nodebug'],cwd=folder,stdout=log,stderr=log)
            rec.child(process.pid)
            save(folder/'running.json',{'app_id':appid,'pid':process.pid,'desktop':process.desktop})
            try:code=process.wait(timeout)
            except subprocess.TimeoutExpired:process.kill();process.wait();code=124
        store=Path(os.environ['APPDATA'])/appid/'Local Store'
        if store.exists():shutil.copytree(store,folder/'storage',dirs_exist_ok=True)
        save(folder/'last-run.json',{'app_id':appid,'pid':process.pid,'exit':code})
        return code,(folder/'air-output.log').read_text(encoding='utf-8',errors='replace')
    finally:
        if process:
            if process.poll() is None:process.kill();process.wait(15)
            process.close()
        rec.child_stopped();desc.unlink(missing_ok=True)

def run(name):
    folder=OUT/name;assert not (folder/'last-run.json').exists(),'Evidence is immutable; use a new run folder'
    build=json.loads((folder/'build.json').read_text())
    for rel,digest in build['files'].items():assert sha(folder/rel)==digest,rel
    with Registration(owner='RealisticVision / D33 运动与战斗性能',purpose=name,run_dir=folder,evidence=folder/'evidence/result.json',wait=300) as rec:
        env=environment();save(folder/'launch-state.json',env)
        assert env['available_bytes']>=6*1024**3,'Less than 6 GiB physical memory available; no AIR started'
        assert not env['processes'],'Other AIR/Java active; no timing run started'
        stop=threading.Event();samples=[]
        def observe():
            while not stop.is_set():samples.append(environment());stop.wait(1)
        thread=threading.Thread(target=observe,daemon=True);thread.start()
        try:code,log=air(folder,'pfe.swf',rec)
        finally:stop.set();thread.join(2);save(folder/'environment.json',samples)
        print('\n'.join(log.splitlines()[-12:]),flush=True)
        assert code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log
        rec.outcome='passed';rec.note='驱动完成、无断言失败；耗时与像素结论见报告'
        data=json.loads((folder/'evidence/result.json').read_text())
        for c in data['cases']:
            if 'spec' in c:print(json.dumps({'spec':c['spec'],'meanUpdates':[round(sum(x)/len(x),2) for x in c['updates']],'stages':c.get('stages'),'helper':c.get('helper')}),flush=True)
            else:print(json.dumps({'mode':c['mode'],'variant':c['variant'],'frames':len(c['updates']),'attacks':c['attackStarts']}),flush=True)

def repeat(source,name):
    folder=OUT/name;assert not folder.exists()
    shutil.copytree(OUT/source,folder,ignore=shutil.ignore_patterns('evidence','storage','*.log','last-run.json','running.json','launch-state.json','environment.json','analysis.json','test.xml'))
    (folder/'evidence').mkdir()
    save(folder/'repeat-of.json',{'source':source,'build':sha(folder/'build.json')})

def checks(name,build_only):
    folder=OUT/name;src=folder/'src'
    entries=[MOD/'build/frame-performance/ViewportChecks.as',MOD/'build/wall-performance/EquivalenceChecks.as',MOD/'build/frame-performance/MaskChecks.as']
    with Registration(owner='RealisticVision / D33 像素回归',purpose=name+(' 编译' if build_only else ' AIR 位图对照'),run_dir=folder,evidence=folder/'checks.json',wait=300) as rec:
        if build_only:
            assert not folder.exists();public(OUT/'candidate/src',src)
            for filename in ['RealisticVisionMod','RVWallSurface']:
                text=(OUT/'baseline/src'/(filename+'.as')).read_text(encoding='utf-8-sig')
                text=re.sub(r'\bprivate\b','public',text).replace('RealisticVisionMod','BaselineVision').replace('RVWallSurface','BaselineWallSurface')
                (src/('BaselineVision.as' if filename=='RealisticVisionMod' else 'BaselineWallSurface.as')).write_text(text,encoding='utf-8')
            for entry in entries:runner.compile(entry,folder/(entry.stem+'.swf'),[src,entry.parent,MOD/'build/motion-tests',MOD/'build/stubs'])
            rec.outcome='passed';rec.note='三项像素夹具编译通过，尚未运行';return
        env=environment();save(folder/'launch-state.json',env);assert env['available_bytes']>=6*1024**3
        results=[]
        for entry in entries:
            code,log=air(folder,entry.stem+'.swf',rec,150)
            (folder/(entry.stem+'.txt')).write_text(log,encoding='utf-8')
            result=json.loads((folder/'last-run.json').read_text());result.update(name=entry.stem,passed=len(re.findall(r'^PASS ',log,re.M)))
            results.append(result);save(folder/'checks.json',results)
            print('\n'.join(log.splitlines()[-5:]),flush=True)
            assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
        rec.outcome='passed';rec.note='原生AIR位图、视野逻辑、移动/材质变化回归通过'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build','run','checks-build','checks-run','repeat']);p.add_argument('--name',default='profile-01');p.add_argument('--source');p.add_argument('--profile',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--large',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='build':build(a.name,a.profile,a.verify,a.large,a.live)
    elif a.action.startswith('checks-'):checks(a.name,a.action=='checks-build')
    elif a.action=='repeat':repeat(a.source,a.name)
    else:run(a.name)
