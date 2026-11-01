from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys,os
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/performance-survey-output'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('solo_runtime',MOD/'build/motion-performance/run.py')
media=module('solo_media',MOD/'build/candidate-comparison/runtime.py');media.bind(r)
from test_resources import snapshot,comparison_environment
from air_test_process import HiddenProcess
from instrument import instrument as census_main, helper as census_helper
from cpu_sampler import OwnedCpuSampler
OwnedCpuSampler.INTERVAL_SECONDS=0.1
class Recorded(HiddenProcess):
 def __init__(self,*a,**kw):
  run=Path(kw['cwd']);descriptor=(run/'test.xml').read_text();appid=re.search(r'<id>(.*?)</id>',descriptor)[1]
  if '--large-screen' in sys.argv:
   descriptor=descriptor.replace('<width>1280</width>','<width>1936</width>').replace('<height>720</height>','<height>1119</height>')
   (run/'test.xml').write_text(descriptor,encoding='utf-8')
  if '--native-screen' in sys.argv:
   descriptor=descriptor.replace('<width>1280</width>','<width>2576</width>').replace('<height>720</height>','<height>1560</height>')
   (run/'test.xml').write_text(descriptor,encoding='utf-8')
  if '--private-visible' in sys.argv:
   descriptor=descriptor.replace('<visible>false</visible>','<visible>true</visible>');(run/'test.xml').write_text(descriptor,encoding='utf-8')
  assert appid.startswith('pfe-modsettings-rv-motion-') and appid!='pfe'
  target=Path(os.environ['APPDATA'])/appid/'Local Store';assert not target.exists();target.mkdir(parents=True)
  for p in SEED.rglob('*'):
   if p.is_file() and p.name!='manifest.json':
    out=target/p.relative_to(SEED);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
  super().__init__(*a,**kw)
  if '--no-cpu' not in sys.argv:
   self.cpu_output=run/'cpu-samples.json';self.cpu_sampler=OwnedCpuSampler(self._process,self.pid);self.cpu_sampler.start()
  r.save(Path(kw['cwd'])/'resource-policy.json',self.resource_policy)
 def close(self):
  if hasattr(self,'cpu_sampler'):
   r.save(self.cpu_output,self.cpu_sampler.stop())
   del self.cpu_sampler
  super().close()
r.HiddenProcess=Recorded
name=sys.argv[1];full='--full' in sys.argv;split='--split' in sys.argv;candidate='--candidate' in sys.argv;plain='--plain' in sys.argv;folder=OUT/name
reuse=next((v.split('=',1)[1] for v in sys.argv if v.startswith('--reuse-from=')),None)
if reuse:assert '/' not in reuse and '\\' not in reuse and (OUT/reuse/'build.json').is_file()
bursts='--bursts' in sys.argv
BASE=OUT/'baseline/src'
if '--v4-only' in sys.argv:BASE=OUT/'candidate/src'
SEED=MOD/'build/sustained-fire-output/player-seed';assert (SEED/'manifest.json').exists()
for rel,h in json.loads((SEED/'manifest.json').read_text()).items():assert r.sha(SEED/rel)==h
assert not folder.exists(),'Use new evidence directory'
with r.Registration(owner='RealisticVision / 性能切口普查',resource='game',purpose=name,run_dir=folder,evidence=folder/'analysis.json',wait=900) as rec:
 r.runtime(folder)
 shutil.copyfile(OUT/'frozen/pfe.swf',folder/'pfe.swf')
 if reuse:
  # Continue the same comparison even if another chat deploys the host while
  # this run waits. Replace only this new private copy, never the installation.
  shutil.copyfile(OUT/reuse/'pfe.swf',folder/'pfe.swf')
 s=(HERE/'SavedFireProbe.as').read_text()
 if '--maximize' in sys.argv:s=s.replace('MAXIMIZE=false','MAXIMIZE=true')
 if '--try-candidate' in sys.argv:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off','normal','normal','off']", "['off','normal','candidate','candidate','normal','off']")
  if '--reverse' in sys.argv:s=s.replace("['off','normal','candidate','candidate','normal','off']", "['off','candidate','normal','normal','candidate','off']")
  if '--compact-pair' in sys.argv:
   s=s.replace("['off','normal','candidate','candidate','normal','off']", "['normal','candidate','candidate','normal']")
   s=s.replace("['off','candidate','normal','normal','candidate','off']", "['candidate','normal','normal','candidate']")
 if '--pixel-checks' in sys.argv:
  checkFile='PalettePixels.as' if '--palette' in sys.argv else 'MergedPixels.as' if '--merged' in sys.argv else 'PixelChecks.as'
  s=s.replace('  private function undo():void {',(HERE/checkFile).read_text(encoding='utf-8')+'\n  private function undo():void {')
  s=s.replace('row.treeEnd=displaySnapshot(w);', 'row.treeEnd=displaySnapshot(w);if(rv.fogVis)row.pixelChecks=checkPixels(w);')

 if '--layers-pair' in sys.argv:
  s=s.replace("['off','normal','skip-hide','hide-fog','both','both','hide-fog','skip-hide','normal','off']", "['off','normal','no-floor','no-wall','no-floorwall','no-floorwall','no-wall','no-floor','normal','off']")
  s=s.replace('rv.resetRoom(w,w.loc);', "rv.resetRoom(w,w.loc);rv.d60HideFloor=p.variant=='no-floor'||p.variant=='no-floorwall';rv.d60HideWall=p.variant=='no-wall'||p.variant=='no-floorwall';")
 if '--clip-pair' in sys.argv:
  s=s.replace("['off','normal','skip-hide','hide-fog','both','both','hide-fog','skip-hide','normal','off']", "['normal','no-base-clip','no-air','no-contour','no-contour','no-air','no-base-clip','normal']")
  s=s.replace('rv.resetRoom(w,w.loc);', "rv.resetRoom(w,w.loc);rv.wallSurface.d60SkipBase=p.variant=='no-base-clip'||p.variant=='no-contour';rv.wallSurface.d60HideAir=p.variant=='no-air'||p.variant=='no-contour';")
 if '--cache-pair' in sys.argv:
  s=s.replace("['off','normal','skip-hide','hide-fog','both','both','hide-fog','skip-hide','normal','off']", "['off','normal','fog-cache','fog-cache','normal','off']")
  s=s.replace('rv.onFrameInner();var ms:', "rv.onFrameInner();if(age==0&&row.variant=='fog-cache')rv.fogShadow.cacheAsBitmap=true;var ms:")
  s=s.replace('  private function undo():void {',(HERE/'CachePixels.as').read_text(encoding='utf-8')+'\n  private function undo():void {')
  s=s.replace('row.treeEnd=displaySnapshot(w);', 'row.treeEnd=displaySnapshot(w);if(rv.fogShadow)row.cachePixels=cachePixels(w);')
 if '--native-timing' in sys.argv:
  checked=json.loads((OUT/'native-source/checked.json').read_text());assert r.sha(folder/'pfe.swf')==checked['host']
  shutil.copytree(MOD/'build/frame-attribution/fe',folder/'fe')
  s=s.replace('package {','package {\n import fe.NativeTimingAccess;')
  s=s.replace('private var host:*','private var nativeStep:Function,nativeStart:int=0,nativeEnd:int=0,nativeSerial:int=0,lastNativeSerial:int=0;\n  private var host:*')
  s=s.replace('sceneLoc=w.loc;gunHp=', '''nativeStep=w.mm.mainStep as Function;if(nativeStep==null)throw new Error('native mainStep unavailable');
     host.stage.removeEventListener(Event.ENTER_FRAME,nativeStep);host.stage.addEventListener(Event.ENTER_FRAME,nativeFrame,false,1);
     result.nativeTiming={method:'MainMenu.mainStep',priority:1,originalPriority:0,checkedSource:true};
     sceneLoc=w.loc;gunHp=''')
  s=s.replace('  private function inputFrame(','''  private function nativeFrame(e:Event):void {nativeStart=getTimer();nativeSerial++;try{nativeStep(e);}finally{nativeEnd=getTimer();}}
  private function inputFrame(''')
  s=s.replace('var now:int=getTimer();if(previousFrame)previousFrame.nextInterval=now-last;', '''var now:int=getTimer();
    if(nativeSerial!=lastNativeSerial+1||nativeStart>nativeEnd||nativeEnd>now)throw new Error('native order');lastNativeSerial=nativeSerial;
    if(previousFrame){
     previousFrame.nextInterval=now-last;previousFrame.nativeNext=nativeEnd-nativeStart;previousFrame.otherHandlersNext=now-nativeEnd;
     previousFrame.afterProbe=nativeStart-previousFrame.probeEnd;previousFrame.probeMs=previousFrame.probeEnd-previousFrame.start;
     previousFrame.worldStepsNext=NativeTimingAccess.tick(w)-previousFrame.nativeTick;
     if(previousFrame.worldStepsNext!=1||previousFrame.afterProbe<0||previousFrame.nativeNext+previousFrame.otherHandlersNext+previousFrame.afterProbe+previousFrame.probeMs!=previousFrame.nextInterval)throw new Error('native partition');
    }''')
  s=s.replace('previousFrame={nativeEnemyShotLowerBound:', 'previousFrame={start:now,nativeTick:NativeTimingAccess.tick(w),nativeEnemyShotLowerBound:')
  s=s.replace('if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;','previousFrame.probeEnd=getTimer();if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;')
 if '--short' in sys.argv:s=s.replace('SAMPLE_COUNT=360','SAMPLE_COUNT=120').replace('WARMUP_COUNT=90','WARMUP_COUNT=45')
 if '--memory' in sys.argv:
  assert '--native-timing' in sys.argv and plain and not candidate
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']", "['off','normal','normal','off']")
  s=s.replace('private var nativeStep:Function', 'private var nativeMemBefore:Number=0,nativeMemAfter:Number=0;\nprivate var nativeStep:Function')
  s=s.replace('nativeStart=getTimer();nativeSerial++;', 'nativeStart=getTimer();nativeMemBefore=System.totalMemory;nativeSerial++;')
  s=s.replace('finally{nativeEnd=getTimer();}', 'finally{nativeMemAfter=System.totalMemory;nativeEnd=getTimer();}')
  s=s.replace('previousFrame.nativeNext=nativeEnd-nativeStart;', 'previousFrame.nativeNext=nativeEnd-nativeStart;previousFrame.nativeMemoryDeltaNext=nativeMemAfter-nativeMemBefore;')
  s=s.replace('rv.profile={};rv.calls={};', 'rv.profile={};rv.calls={};rv.memoryProfile={};')
  s=s.replace('var t:int=getTimer();rv.frameCount++;', 'if(age==WARMUP_COUNT)rv.memoryProfile={};\nvar t:int=getTimer();rv.frameCount++;')
  s=s.replace('var ms:int=getTimer()-t;', 'var ms:int=getTimer()-t;var memoryAfterRV:Number=System.totalMemory;')
  s=s.replace('previousFrame={start:now,', 'previousFrame={memoryAfterRV:memoryAfterRV,start:now,')
  s=s.replace('row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);', 'row.memoryProfile=rv.memoryProfile;row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);')
 if '--render-phases' in sys.argv:
  assert '--native-timing' in sys.argv
  s=s.replace('sceneLoc=w.loc;gunHp=', '''host.stage.addEventListener(Event.EXIT_FRAME,function(e:Event):void{if(previousFrame)previousFrame.exitAt=getTimer();},false,-10000);
     host.stage.addEventListener(Event.RENDER,function(e:Event):void{if(previousFrame)previousFrame.renderAt=getTimer();},false,-10000);
     sceneLoc=w.loc;gunHp=''')
  s=s.replace('previousFrame.worldStepsNext=NativeTimingAccess.tick(w)-previousFrame.nativeTick;', '''previousFrame.worldStepsNext=NativeTimingAccess.tick(w)-previousFrame.nativeTick;
     if(previousFrame.renderAt!==undefined && previousFrame.renderAt>=previousFrame.probeEnd && previousFrame.renderAt<=nativeStart){
      previousFrame.toRender=previousFrame.renderAt-previousFrame.probeEnd;previousFrame.afterRender=nativeStart-previousFrame.renderAt;
     }''')
  s=s.replace('previousFrame.probeEnd=getTimer();if(++age', 'host.stage.invalidate();previousFrame.probeEnd=getTimer();if(++age')
 if '--moving' in sys.argv:s=s.replace('w.gg.setPos(low+80,floor);','w.gg.setPos(low+80+120*Math.sin(age/25),floor);')
 if '--sweep' in sys.argv:s=s.replace('SWEEP=false','SWEEP=true')
 if '--solo' in sys.argv:s=s.replace('SOLO=false','SOLO=true')
 if '--private-visible' in sys.argv:s=s.replace('SHOW_WINDOW=false','SHOW_WINDOW=true')
 if '--visual' in sys.argv:
  s=s.replace('VISUAL=false','VISUAL=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal']")
 if split:s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal','nomouse','nodraw','noeffects','noeffects','nodraw','nomouse','normal']")
 if candidate:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['off','normal','candidate','vector','vector','candidate','normal','off']")
  if '--reverse' in sys.argv:s=s.replace("['off','normal','candidate','vector','vector','candidate','normal','off']","['off','vector','candidate','normal','normal','candidate','vector','off']")
 if '--diagnostic' in sys.argv:
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['off','normal','enemy-nodraw','effect-nodraw','effect-nodraw','enemy-nodraw','normal','off']")
 if '--both' in sys.argv:s=s.replace("for each(var variant:String in", "for each(var mode:String in ['current','classic'])for each(var variant:String in").replace("mode:'current',variant:variant", "mode:mode,variant:variant")
 if '--pair' in sys.argv:
  s=s.replace("['off','normal','candidate','vector','vector','candidate','normal','off']", "['off','normal','candidate','candidate','normal','off']")
  s=s.replace("['off','vector','candidate','normal','normal','candidate','vector','off']", "['off','candidate','normal','normal','candidate','off']")
 if '--rate-calibration' in sys.argv:
  assert candidate and plain and '--native-timing' in sys.argv
  s=s.replace("['off','normal','candidate','vector','vector','candidate','normal','off']", "['off30','normal30','off60','normal60','normal60','off60','normal30','off30']")
  s=s.replace('var p:Object=plan[index];', 'var p:Object=plan[index];host.stage.frameRate=p.variant.indexOf("60")>=0?60:30;')
  s=s.replace('row={crowd:p.n,', 'row={actualStageRate:host.stage.frameRate,windowActive:host.stage.nativeWindow.active,windowDisplayState:host.stage.nativeWindow.displayState,stageDisplayState:host.stage.displayState,crowd:p.n,')
 if bursts:
  assert not candidate and not split
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal-burst','off-burst','off-burst','normal-burst']").replace('SAMPLE_COUNT=180','SAMPLE_COUNT=360').replace('WARMUP_COUNT=90','WARMUP_COUNT=0')
  if '--reverse' in sys.argv:s=s.replace("['normal-burst','off-burst','off-burst','normal-burst']","['off-burst','normal-burst','normal-burst','off-burst']")
 if '--zero-enemies' in sys.argv:s=s.replace('n:6,mode:', 'n:0,mode:')
 if '--idle-pair' in sys.argv:
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']", "['off-idle','normal-idle','off','normal','normal','off','normal-idle','off-idle']")
 if '--noeffects-pair' in sys.argv:
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']", "['off','normal','noeffects','noeffects','normal','off']")
 if '--fog-diagnostic' in sys.argv:
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']", "['off','normal','fog-hidden','fog-hidden','normal','off']")
  s=s.replace("kind:String=row.variant;", "kind:String=row.variant;if(kind=='fog-hidden'&&rv.fogVis)rv.fogVis.visible=false;")
 if '--audit-checks' in sys.argv:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true')
  s=s.replace('  private function undo():void {',(HERE/'AuditChecks.as').read_text(encoding='utf-8')+'\n  private function undo():void {')
  s=s.replace("undo();host.stage.removeEventListener(Event.ENTER_FRAME,inputFrame)","auditChecks(w);undo();host.stage.removeEventListener(Event.ENTER_FRAME,inputFrame)")
 if '--audit-only' in sys.argv:
  assert '--audit-checks' in sys.argv
  s=s.replace('sceneLoc=w.loc;gunHp=',"timer.stop();auditChecks(w);trace('D58 COMPLETE');NativeApplication.nativeApplication.exit(0);return;sceneLoc=w.loc;gunHp=")
 s=s.replace("var w:*=wc['w'];w.ctr.clearAll();", "if(!host.stage.nativeWindow.active)host.stage.nativeWindow.activate();var w:*=wc['w'];w.ctr.clearAll();")
 assert 'row={windowDisplayState:' in s
 s=s.replace('row={windowDisplayState:','row={windowActive:host.stage.nativeWindow.active,activeSamples:0,windowDisplayState:')
 s=s.replace('var now:int=getTimer();','if(age>=WARMUP_COUNT&&host.stage.nativeWindow.active)row.activeSamples++;var now:int=getTimer();')
 (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')
 r.runner.compile(folder/'CombatRenderProbeMod.as',folder/'mods/CombatRenderProbe/release/CombatRenderProbeMod.swf',[folder])
 sources=[('rv',BASE)]
 for variant,source in sources:
  src=folder/(variant+'-src');r.public(source,src)
  if '--palette' in sys.argv:
   helper=src/'RVWallSurface.as';h=helper.read_text();pos=h.index('{',h.index('public class'))+1
   h=h[:pos]+'\n public var d61PaletteUploads:int=0,d61PaletteSkipped:int=0;\n'+h[pos:]
   h=h.replace('contourFog.paletteMap(floorField,','d61PaletteUploads++;contourFog.paletteMap(floorField,')
   h=h.replace('if(contourFogVersion!=fieldUpdates){','if(contourFogVersion==fieldUpdates)d61PaletteSkipped++;\n         if(contourFogVersion!=fieldUpdates){')
   helper.write_text(h,encoding='utf-8')
  if '--clip-pair' in sys.argv:
   helper=src/'RVWallSurface.as';h=helper.read_text();pos=h.index('{',h.index('public class'))+1
   h=h[:pos]+'\n public var d60SkipBase:Boolean=false,d60HideAir:Boolean=false;\n'+h[pos:]
   assert 'airPixels.visible=wallPixels.visible;' in h and '}else base.mask=baseClip;' in h
   h=h.replace('airPixels.visible=wallPixels.visible;', 'airPixels.visible=wallPixels.visible&&!d60HideAir;')
   h=h.replace('}else base.mask=baseClip;', '}else {base.mask=d60SkipBase?null:baseClip;baseClip.visible=!d60SkipBase;}')
   helper.write_text(h,encoding='utf-8')
  p=src/'RealisticVisionMod.as';s=p.read_text();pos=s.index('{',s.index('public class'))+1
  s=s[:pos]+'\n public var d53SkipEffects:Boolean=false;public var d60SkipHide:Boolean=false;public var d60HideFog:Boolean=false;public var trailingHits:int=0;public var alphaHits:int=0;public var auxHits:int=0;public var vectorHits:int=0;public var fractionHits:int=0;\n'+s[pos:]
  s=s.replace('/* D58_FRACTIONAL_CROP */','if(screenMatrix.tx!=Math.floor(screenMatrix.tx)||screenMatrix.ty!=Math.floor(screenMatrix.ty))fractionHits++;')
  s=s.replace('// D56_LOCAL','trailingHits++;')
  s=s.replace('// D58_CLIP','trailingHits++; // D58_CLIP')
  s=s.replace('/* D57_AUX_OMITTED */','auxHits++;').replace('/* D57_VECTOR_SKIPPED */','vectorHits++;')
  s=s.replace('// D58_ALPHA_CLIP','alphaHits++; // D58_ALPHA_CLIP')
  s=s.replace('// D47_IDENTITY_HIT','trailingHits++;').replace('// D56_DARK_CHILD','trailingHits++;').replace('// D54_TRAILING','trailingHits++;')
  s=s.replace('// D56_REFRESH:','trailingHits++; // D56_REFRESH:').replace('// D56_OFFSCREEN:','trailingHits++; // D56_OFFSCREEN:')
  s=s.replace('public function applyWorldVisuals(w:World,loc:Location):void\n      {','public function applyWorldVisuals(w:World,loc:Location):void\n      {\nif(d53SkipEffects)return;')
  s=s.replace('this.hideEnemies(w,loc,needFov);','if(!d60SkipHide)this.hideEnemies(w,loc,needFov);').replace('this.fogVis.visible = true;','this.fogVis.visible = !d60HideFog;')
  if '--layers-pair' in sys.argv:
   s=s.replace('public var d60SkipHide:Boolean=false;', 'public var d60HideFloor:Boolean=false,d60HideWall:Boolean=false;public var d60SkipHide:Boolean=false;')
   s=s.replace('this.fogVis.visible = !d60HideFog;', 'this.fogVis.visible = !d60HideFog;this.fogBitmap.visible=!d60HideFloor;this.wallLayer.visible=!d60HideWall;')
  s=census_main(s)
  if plain:
   pos=s.index('{',s.index('public class'))+1;s=s[:pos]+'\npublic var profile:Object={},calls:Object={};\n'+s[pos:]
  else:s=r.fp.instrument(s,['prepareOcclusion','computeFov','applyVision','updateWallSurface','hideEnemies','applyMask','applyWeaponVisual','enemyState','refreshMask','fillFogCache','refreshWallField','applyWorldVisuals','applyWorldVisual'])
  if '--memory' in sys.argv:
   s=module('d57_memory',HERE/'memory_probe.py').instrument(s)
  p.write_text(s,encoding='utf-8')
  helper=src/'RVWallSurface.as';helper.write_text(census_helper(helper.read_text()),encoding='utf-8')
  if reuse:
   frozen=OUT/reuse;prior=frozen/(variant+'-src')
   assert {q.relative_to(src).as_posix():r.sha(q) for q in src.rglob('*.as')}=={q.relative_to(prior).as_posix():r.sha(q) for q in prior.rglob('*.as')}
   shutil.copyfile(frozen/(variant+'.swf'),folder/(variant+'.swf'))
  else:r.runner.compile(p,folder/(variant+'.swf'),[src],stubs=True)
 selected=['CombatRenderProbeMod']
 if full:
  for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
   c=line.split('|')
   if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):
    selected.append(c[1]);shutil.copytree((OUT/reuse if reuse else OUT/'frozen')/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)
 if reuse:
  assert set(selected)==set(json.loads((OUT/reuse/'build.json').read_text())['selected'])
  assert r.sha(folder/'pfe.swf')==r.sha(OUT/reuse/'pfe.swf')
 catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
 (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nCombatRenderProbe|CombatRenderProbeMod|1|0|0\n',encoding='utf-8')
 a=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8');assert a.returncode==0,a.stdout+a.stderr
 r.save(folder/'build.json',{'args':sys.argv[1:],'full':full,'selected':selected,'installed':r.sha(MOD/'release/RealisticVisionMod.swf'),'profile':not plain,'candidate':candidate or '--try-candidate' in sys.argv,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.swf','.xml','.txt')}})
 before=snapshot();r.save(folder/'before.json',before)
 code,log=r.air(folder,'pfe.swf',rec,timeout=650)
 after=snapshot();r.save(folder/'after.json',after)
 eligibility=comparison_environment('benchmark',before,after,json.loads((folder/'resource-policy.json').read_text()));r.save(folder/'environment.json',eligibility)
 print(log[-500:]);assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==set(selected)
 data=json.loads((folder/'evidence/result.json').read_text());assert data['weapon']=='lmg' and data['audioVolume']==0
 groups={}
 for c in data['cases']:
  if 'idle' not in c['variant']:assert c['attacks']>10 and c['maxProjectiles']>0, (c['variant'],c['attacks'],c['maxProjectiles'])
  fs=[f for f in c['frames'] if 'nextInterval' in f];groups.setdefault(c['mode']+'/'+c['variant'],[]).extend(fs)
  if '--zero-enemies' not in sys.argv:
   assert c['enemyShots']>10,(c['variant'],c['enemyShots'])
   assert c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots']>50,c['variant']
  if 'idle' not in c['variant']:assert c['samplePlayerShotsLowerBound']>20,c['variant']
  print(c['mode'],c['variant'],'sampleShots',c['samplePlayerShotsLowerBound'],'enemies',c['sampleNativeEnemyShotsLowerBound'])
 def stats(v):
  v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
 metrics=['nextInterval','rv']+(['nativeNext','otherHandlersNext','afterProbe','probeMs'] if '--native-timing' in sys.argv else [])
 result={'environment':eligibility,'groups':{k:{f:stats([x[f] for x in a]) for f in metrics} for k,a in groups.items()}}
 r.save(folder/'analysis.json',result);print(json.dumps(result));rec.outcome='passed';rec.note='两模式固定/受控移动计数完成；含诊断开销，不作性能收益验收'
