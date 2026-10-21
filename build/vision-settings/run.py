from pathlib import Path
import argparse, importlib.util, json, os, re, shutil, subprocess, sys, uuid
import prepare as p
MOD,OUT=p.MOD,p.OUT
GAME=MOD.parents[1]
sys.path.insert(0,str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('rv_compiler',MOD/'build/wall-surface/run.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from air_test_process import HiddenProcess
from test_registry import Registration
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def public(src,dest,baseline=False):
    for f in src.rglob('*.as'):
        rel=f.relative_to(src)
        if baseline and str(rel) not in ['RealisticVisionMod.as']:continue
        text=re.sub(r'\bprivate\b','public',f.read_text(encoding='utf-8-sig'))
        if baseline:text=text.replace('RealisticVisionMod','BaselineVision');rel=Path('BaselineVision.as')
        q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text,encoding='utf-8')
def build():
    assert not (OUT/'frozen.json').exists()
    src=OUT/'candidate/src'
    for rel,fn in [('RealisticVisionMod.as',p.main_source),('modlocales/vision/RVLocaleMessages.as',p.locale_source)]:
        (src/rel).write_text(fn((OUT/'baseline/src'/rel).read_text(encoding='utf-8-sig')),encoding='utf-8')
    compiler.compile(src/'RealisticVisionMod.as',OUT/'candidate/RealisticVisionMod.swf',[src],stubs=True)
    test=OUT/'checks/src';public(src,test);public(OUT/'baseline/src',test,True)
    for name in ['SettingsChecks','SoftHarness','SharedExplorationHarness']:
        if name=='SettingsChecks':entry=Path(__file__).parent/(name+'.as')
        else:
            text=(MOD/'build/motion-tests'/(name+'.as')).read_text(encoding='utf-8-sig')
            text=text.replace('p.m.curBlur.blurX=p.m.curBlur.blurY=6','p.m.cfgSoftCurrent=30')
            entry=test/(name+'.as');entry.write_text(text,encoding='utf-8')
        compiler.compile(entry,OUT/'checks'/(name+'.swf'),[test,Path(__file__).parent,MOD/'build/motion-tests',MOD/'build/stubs'])
    save(OUT/'build.json',{'swf':p.sha(OUT/'candidate/RealisticVisionMod.swf'),'sources':{q.relative_to(src).as_posix():p.sha(q) for q in src.rglob('*.as')}})
def air(folder,entry,record,timeout=75,appid=None):
    appid=appid or 'pfe-modsettings-rv-settings-'+uuid.uuid4().hex
    stamp=uuid.uuid4().hex[:8];desc=folder/('test-'+stamp+'.xml')
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+'</id><versionNumber>1.0</versionNumber><filename>RVSettings</filename><initialWindow><content>'+entry+'</content><visible>false</visible><width>1280</width><height>720</height><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
    log=folder/(Path(entry).stem+'-'+stamp+'.txt');proc=None
    try:
        record.before_launch(appid+' / '+str(desc))
        with log.open('wb') as stream:
            proc=HiddenProcess([GAME/'adl64.exe','-runtime',GAME/'runtimes/air/win64',desc,'-nodebug'],cwd=folder,stdout=stream,stderr=stream)
            record.child(proc.pid)
            try:code=proc.wait(timeout)
            except subprocess.TimeoutExpired:proc.kill();proc.wait();code=124
        text=log.read_text(encoding='utf-8',errors='replace')
        result={'appid':appid,'pid':proc.pid,'exit':code,'log':str(log.relative_to(MOD)),'passed':len(re.findall(r'^PASS ',text,re.M))}
        save(log.with_suffix('.json'),result)
        print(entry,code,result['passed'],flush=True)
        assert code==0 and 'COMPLETE' in text and 'FAIL ' not in text,text[-9000:]
        return result
    finally:
        if proc:
            if proc.poll() is None:proc.kill();proc.wait()
            proc.close()
        desc.unlink(missing_ok=True);record.child_stopped()
def checks():
    folder=OUT/'checks'
    with Registration(owner='RealisticVision / 视野设置',purpose='默认画面等价、显示与逻辑隔离、配置及距离边界',run_dir=folder,evidence=folder/'result.json',wait=300) as record:
        results=[]
        for name in ['SettingsChecks','SoftHarness','SharedExplorationHarness']:
            results.append(air(folder,name+'.swf',record));save(folder/'result.json',results)
        record.outcome='passed';record.note='组件断言通过；原生游戏验证另登记'
def build_native():
    folder=OUT/'native-final';folder.mkdir(exist_ok=True);(folder/'evidence').mkdir(exist_ok=True)
    if not (folder/'application.xml').exists():shutil.copyfile(GAME/'application.xml',folder/'application.xml')
    for path in GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',path.name):
            if not (folder/path.name).exists():shutil.copyfile(path,folder/path.name)
    if not (folder/'Rooms').exists():shutil.copytree(GAME/'Rooms',folder/'Rooms')
    source=(MOD/'build/stair-shadow/WallSurfaceProbe.as').read_text(encoding='utf-8-sig')
    source=source[:source.index('      private function capture(w:*):Boolean')]
    source=source.replace('WallSurfaceProbe','SettingsNativeProbeMod').replace('CONFIG::rockFixture','false').replace('CONFIG::wallBench','false')
    source=source.replace('!(BENCH?bench(w):capture(w))','!capture(w)').replace('/RealisticVision/build/stair-shadow-output/','/RealisticVision/build/vision-settings-output/')
    source+=(Path(__file__).parent/'NativeCases.as.txt').read_text(encoding='utf-8')
    probe=OUT/'SettingsNativeProbeMod.as';probe.write_text(source,encoding='utf-8')
    target=folder/'mods/SettingsNativeProbeMod/release/SettingsNativeProbeMod.swf'
    compiler.compile(probe,target,[OUT])
    for variant in ['baseline','candidate']:
        src=folder/(variant+'-src');public(OUT/variant/'src',src)
        compiler.compile(src/'RealisticVisionMod.as',folder/(variant+'.swf'),[src],stubs=True)
    launcher=GAME/'mods/ModLoader/RemainsModLauncher.exe'
    catalog=folder/'mods/ModLoader/supported-mods.txt';catalog.parent.mkdir(exist_ok=True)
    catalog.write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nSettingsNativeProbeMod|SettingsNativeProbeMod|1|0|0\n',encoding='utf-8')
    selection=folder/('selection-'+uuid.uuid4().hex[:8]+'.json')
    selected=subprocess.run([str(launcher),'--root',str(folder),'--only','SettingsNativeProbeMod','--no-ui','--report',str(selection)],capture_output=True,timeout=30)
    assert selected.returncode==0,ascii(selected.stderr.decode('utf-8',errors='replace'))
    manifest=(folder/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig')
    assert 'SettingsNativeProbeMod|SettingsNativeProbeMod|1' in manifest,manifest
    save(folder/'inputs.json',{'host':p.sha(folder/'pfe.swf'),'probe':p.sha(target),'candidate':p.sha(folder/'candidate.swf')})
def native():
    folder=OUT/'native-final'
    assert (folder/'inputs.json').exists() and 'SettingsNativeProbeMod|SettingsNativeProbeMod|1' in (folder/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig')
    with Registration(owner='RealisticVision / 视野设置',purpose='原生阶梯场景默认画面对照与亮度、柔化、视距设置',run_dir=folder,evidence=folder/'result.json',wait=300) as record:
        result=air(folder,'pfe.swf',record,220);save(folder/'result.json',result)
        record.outcome='passed';record.note='原生场景显示与逻辑检查通过，见result.json及PNG'
def build_options():
    folder=OUT/'options-final';folder.mkdir(exist_ok=True)
    shutil.copyfile(OUT/'candidate/RealisticVisionMod.swf',folder/'candidate.swf')
    text=(MOD/'build/stair-shadow/CandidateOptionsProbe.as').read_text(encoding='utf-8-sig')
    text=text.replace('pages.realisticvision.length == 8','pages.realisticvision.length == 11').replace('eight controls','eleven controls')
    text=text.replace('          tested = true;', '''          for each(var key:String in ["dim","viewscale","soft_current","soft_classic"]) {
            var setting:Object=row("realisticvision",key);
            var original:Number=key=="dim"?.35:key=="viewscale"?1:key=="soft_current"?20:0;
            var custom:Number=key=="dim"?.75:key=="viewscale"?2.5:key=="soft_current"?35:15;
            check(setting.get()==(restoring?custom:original),key+" loaded expected persisted/default value");
            setting.set(restoring?original:custom);
            check(setting.get()==(restoring?original:custom)&&readConfig().indexOf(key+"="+(restoring?original:custom))>=0,key+" responds and saves immediately");
          }
          tested = true;''')
    entry=folder/'CandidateOptionsProbe.as';entry.write_text(text,encoding='utf-8')
    compiler.compile(entry,folder/'CandidateOptionsProbe.swf',[folder],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
def options():
    folder=OUT/'options-final';appid='pfe-modsettings-rv-settings-options-'+uuid.uuid4().hex
    with Registration(owner='RealisticVision / 视野设置',purpose='准确生产SWF两进程设置与快捷键保存恢复',run_dir=folder,evidence=folder/'result.json',wait=300) as record:
        results=[]
        for i in range(2):results.append(air(folder,'CandidateOptionsProbe.swf',record,60,appid))
        save(folder/'result.json',{'swf':p.sha(folder/'candidate.swf'),'runs':results})
        record.outcome='passed';record.note='准确SWF两进程设置、快捷键与心跳通过'
def final_validation():
    assert not (OUT/'verified.json').exists(), 'Final evidence already exists; use a new run directory'
    with Registration(owner='RealisticVision / D34 设置终验',purpose='最终生产字节、原生场景与设置持久化',run_dir=OUT,evidence=OUT/'verified.json',wait=300) as record:
        build_native();build_options()
        native_result=air(OUT/'native-final','pfe.swf',record,220)
        appid='pfe-modsettings-rv-settings-final-'+uuid.uuid4().hex
        options_result=[air(OUT/'options-final','CandidateOptionsProbe.swf',record,60,appid) for i in range(2)]
        ffdec=GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'
        r=subprocess.run([str(compiler.JAVA),'-jar',str(ffdec),'-dumpAS3',str(OUT/'candidate/RealisticVisionMod.swf')],capture_output=True,timeout=60)
        (OUT/'classes.txt').write_bytes(r.stdout);(OUT/'classes-stderr.txt').write_bytes(r.stderr)
        assert r.returncode==0
        classes=r.stdout.decode('utf-8',errors='replace')
        assert 'RVAuthorityView' not in classes and 'fe.' not in classes and 'Probe' not in classes,classes
        checks=json.loads((OUT/'checks/result.json').read_text(encoding='utf-8'))
        save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':p.sha(OUT/'candidate/RealisticVisionMod.swf'),'checks':checks,'native':native_result,'options':options_result,'classes':p.sha(OUT/'classes.txt'),'count':sum(r['passed'] for r in checks+[native_result]+options_result)})
        record.outcome='passed';record.note='最终准确包、原生场景及两进程设置通过'
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['build','checks','build_native','native','build_options','options','final_validation']);args=a.parse_args()
    globals()[args.action]()
