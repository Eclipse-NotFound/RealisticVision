"""Per-frame event, RV-stage, cache, and memory attribution on the unpatched host."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil,subprocess
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/long-frame-output';GAME=MOD.parents[1]
spec=importlib.util.spec_from_file_location('d39tools',MOD/'build/followup-performance/measure.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.inv.r;r.OUT=OUT;m.inv.OUT=OUT
RV=['prepareOcclusion','computeFov','applyVision','applyVisionClassic','updateWallSurface','hideEnemies']
HELP=['update','updateContour','rebuildFaces','rebuildSamples','rebuildSupport','buildContourClip']
def source_probe(short=False):
 s=(MOD/'build/followup-performance-output/native-final/RecoveryFrameProbeMod.as').read_text(encoding='utf-8-sig')
 s=s.replace('followup-performance-output','long-frame-output')
 s=s.replace('private var anchorX:Number=0,','private var traceEnter:int=0,traceExit:int=0,lastTrace:Object=null;\n      private var scenario:String="";\n      private var anchorX:Number=0,')
 s=s.replace('host.stage.addEventListener(Event.ENTER_FRAME,liveStep,false,-10000);','host.stage.addEventListener(Event.ENTER_FRAME,earlyFrame,false,1000000);host.stage.addEventListener(Event.EXIT_FRAME,exitFrame,false,-1000000);host.stage.addEventListener(Event.ENTER_FRAME,liveStep,false,-10000);')
 s=s.replace('liveMod.cfgMode=liveIndex<6?"current":"classic"','liveMod.cfgMode=liveIndex<6?"current":"classic"')
 s=s.replace('liveAge=0;liveLast=0;liveRow=', 'scenario=["still","still","sweep","sweep","battle","battle"][liveIndex%6];liveAge=0;liveLast=0;lastTrace=null;liveRow=')
 s=s.replace('drivenFire:true,','drivenFire:true,scenario:scenario,frames:[],')
 s=s.replace('private var liveOrder:Array=["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]','private var liveOrder:Array=["off","candidate","off","candidate","off","candidate","off","candidate","off","candidate","off","candidate"]')
 s=s.replace('      private function liveStep(e:Event):void{','''      private function earlyFrame(e:Event):void{
         var now:int=getTimer();if(lastTrace){lastTrace.nextInterval=now-traceEnter;lastTrace.tail=traceExit?now-traceExit:0;}
         traceEnter=now;traceExit=0;
      }
      private function exitFrame(e:Event):void{traceExit=getTimer();if(lastTrace)lastTrace.toExit=traceExit-traceEnter;}
      private function counters(o:Object):Object{var result:Object={};for(var key:String in o)result[key]=o[key];return result;}
      private function liveStep(e:Event):void{''')
 old='w.ctr.clearAll();w.gg.ggControl=false;w.gg.setPos(Math.max(80,Math.min(w.loc.limX-80,anchorX+Math.abs((liveAge%40)-20)*12-120)),anchorY);w.gg.setVisPos();w.cam.calc(w.gg);'
 new='''var hostMs:int=getTimer()-traceEnter;
            w.ctr.clearAll();w.gg.ggControl=false;
            var px:Number=scenario=="still"?anchorX-120:scenario=="sweep"?240+Math.abs((liveAge%200)-100)*18:anchorX+Math.abs((liveAge%40)-20)*12-120;
            w.gg.setPos(Math.max(80,Math.min(w.loc.limX-80,px)),anchorY);w.gg.setVisPos();w.cam.calc(w.gg);
            liveMod.profile={};liveMod.calls={};liveMod.wallSurface.profile={};liveMod.wallSurface.calls={};
            var memBefore:Number=System.totalMemory;'''
 assert old in s;s=s.replace(old,new)
 s=s.replace('var start:int=getTimer();liveMod.frameCount++;liveMod.onFrameInner();if(liveAge>=30)liveRow.updates.push(getTimer()-start);','''var start:int=getTimer();liveMod.frameCount++;liveMod.onFrameInner();var rvMs:int=getTimer()-start;if(liveAge>=30)liveRow.updates.push(rvMs);
            var view:Rectangle=liveMod.wallViewBounds;
            lastTrace={age:liveAge,host:hostMs,rv:rvMs,position:[w.gg.X,w.gg.Y,w.cam.vx,w.cam.vy],memoryBefore:memBefore,memoryAfter:System.totalMemory,rvStages:counters(liveMod.profile),helper:counters(liveMod.wallSurface.profile),helperCalls:counters(liveMod.wallSurface.calls),fovVersion:liveMod.fovVersion,view:view?[view.x,view.y,view.width,view.height]:null,units:w.loc.units.length,attack:armedEnemy.currentWeapon.t_attack,ammo:armedEnemy.currentWeapon.hold};
            if(liveAge>=30)liveRow.frames.push(lastTrace);''')
 s=s.replace('if(liveAge%6==0)armedEnemy.currentWeapon.attack();','if(scenario=="battle" && liveAge%6==0)armedEnemy.currentWeapon.attack();')
 s=s.replace('if(++liveAge<150)return;','lastTrace.objects=count;lastTrace.projectiles=projectiles;\n            if(++liveAge<330)return;')
 s=s.replace('if(liveRow.attackStarts<1 || liveRow.maxProjectiles<1)','if(scenario=="battle" && (liveRow.attackStarts<1 || liveRow.maxProjectiles<1))')
 # V2 measures consecutive calls of the SAME listener. EXIT_FRAME is a
 # broadcast event and the old row assignment was not a verified phase boundary.
 s=s.replace('lastTrace:Object=null;', 'lastTrace:Object=null,traceSerial:int=0,events:Array=[];')
 s=s.replace('scenario=["still","still","sweep","sweep","battle","battle"][liveIndex%6]', 'scenario="sweep"')
 s=s.replace('["off","candidate","off","candidate","off","candidate","off","candidate","off","candidate","off","candidate"]', '["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]')
 a=s.index('         var now:int=getTimer();if(lastTrace)');b=s.index('\n      private function counters',a)
 s=s[:a]+'''         traceEnter=getTimer();traceSerial++;if(events.length<24)events.push(["early",traceSerial,traceEnter]);
      }
      private function exitFrame(e:Event):void{traceExit=getTimer();if(events.length<24)events.push(["exit",traceSerial,traceExit]);}
'''+s[b:]
 s=s.replace('var hostMs:int=getTimer()-traceEnter;', '''var liveStart:int=getTimer();
            if(events.length<24)events.push(["live",traceSerial,liveStart]);
            if(lastTrace){lastTrace.nextInterval=liveStart-lastTrace.liveStart;lastTrace.outsideRV=lastTrace.nextInterval-lastTrace.rv;}
            var hostMs:int=liveStart-traceEnter;''')
 s=s.replace('lastTrace={age:liveAge,', 'lastTrace={liveStart:liveStart,earlyTime:traceEnter,serial:traceSerial,rvStart:start,rvEnd:start+rvMs,age:liveAge,')
 s=s.replace('var start:int=getTimer();liveMod.frameCount++;', 'var previousView:Rectangle=liveMod.wallViewBounds;var start:int=getTimer();liveMod.frameCount++;')
 s=s.replace('lastTrace={liveStart:', 'lastTrace={viewChanged:view==null?previousView!=null:previousView==null||!view.equals(previousView),liveStart:')
 s=s.replace('scenario:scenario,frames:[],', 'scenario:scenario,eventSequence:events,frames:[],')
 if short:
  s=s.replace('private var liveOrder:Array=["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]','private var liveOrder:Array=["candidate"]')
  s=s.replace('if(++liveAge<330)', 'if(++liveAge<60)')
 # Last frame has no following interval when switching fixtures; exclude it in analysis.
 return s
def build(name,full=False,candidate='candidate-00',short=False,unprofile=False):
 folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D39 长帧诊断构建',purpose=name,run_dir=folder,evidence=folder/'build.json') as rec:
  r.runtime(folder)
  entry=folder/'RecoveryFrameProbeMod.as';entry.write_text(source_probe(short),encoding='utf-8',newline='\n')
  r.runner.compile(entry,folder/'mods/RecoveryFrameProbe/release/RecoveryFrameProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,true','-define=CONFIG::verifyPixels,false','-define=CONFIG::liveFrames,true'])
  catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
  (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nRecoveryFrameProbe|RecoveryFrameProbeMod|1|0|0\n',encoding='utf-8')
  selected=['ContinuousSceneMod','RecoveryFrameProbeMod']
  if full:
   for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
    cols=line.split('|')
    if len(cols)>=3 and cols[2]=='1' and cols[1] not in ['RealisticVisionMod','ContinuousSceneMod'] and not line.startswith('#'):
     selected.append(cols[1]);shutil.copytree(GAME/'mods'/cols[0]/'release',folder/'mods'/cols[0]/'release',dirs_exist_ok=True)
  shutil.copytree(GAME/'mods/ContinuousScene/release',folder/'mods/ContinuousScene/release')
  res=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8',timeout=45)
  (folder/'selection.log').write_text(res.stdout+res.stderr,encoding='utf-8');assert res.returncode==0
  for variant in ['baseline','candidate']:
   src=folder/(variant+'-src');r.public(OUT/('candidate-00' if variant=='baseline' else candidate)/'src',src)
   for filename,methods in [('RealisticVisionMod.as',RV),('RVWallSurface.as',HELP)]:
    path=src/filename;code=path.read_text(encoding='utf-8')
    if unprofile:
     marker='public class '+filename[:-3];a=code.index('{',code.index(marker))+1
     code=code[:a]+'\n public var profile:Object={},calls:Object={};\n'+code[a:]
    else:code=r.fp.instrument(code,methods)
    path.write_text(code,encoding='utf-8',newline='\n')
   r.runner.compile(src/'RealisticVisionMod.as',folder/(variant+'.swf'),[src],stubs=True)
  r.save(folder/'build.json',{'traceVersion':2,'short':short,'candidate':candidate,'profile':not unprofile,'full':full,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ['.swf','.as','.xml','.txt']}});rec.outcome='passed'
def run(name):
 # 12x330 native frames can exceed the old five-minute watchdog.
 original=r.air
 def longer(folder,entry,rec,timeout=300,seed_store=None):return original(folder,entry,rec,600,seed_store)
 r.air=longer;r.run(name)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run']);a.add_argument('name');a.add_argument('--full',action='store_true');a.add_argument('--short',action='store_true');a.add_argument('--unprofile',action='store_true');a.add_argument('--candidate',default='candidate-00');x=a.parse_args()
 build(x.name,x.full,x.candidate,x.short,x.unprofile) if x.action=='build' else run(x.name)
