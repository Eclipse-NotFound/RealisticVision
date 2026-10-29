from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys,os
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/enemy-combat-output'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('solo_runtime',MOD/'build/motion-performance/run.py')
media=module('solo_media',MOD/'build/candidate-comparison/runtime.py');media.bind(r)
from test_resources import snapshot,comparison_environment
from air_test_process import HiddenProcess
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
  super().__init__(*a,**kw);r.save(Path(kw['cwd'])/'resource-policy.json',self.resource_policy)
r.HiddenProcess=Recorded
name=sys.argv[1];full='--full' in sys.argv;split='--split' in sys.argv;candidate='--candidate' in sys.argv;plain='--plain' in sys.argv;folder=OUT/name
reuse=next((v.split('=',1)[1] for v in sys.argv if v.startswith('--reuse-from=')),None)
if reuse:assert '/' not in reuse and '\\' not in reuse and (OUT/reuse/'build.json').is_file()
bursts='--bursts' in sys.argv
BASE=OUT/'baseline/src'
SEED=MOD/'build/sustained-fire-output/player-seed';assert (SEED/'manifest.json').exists()
for rel,h in json.loads((SEED/'manifest.json').read_text()).items():assert r.sha(SEED/rel)==h
assert not folder.exists(),'Use new evidence directory'
with r.Registration(owner='RealisticVision / D57 存档轻机枪',purpose=name,run_dir=folder,evidence=folder/'analysis.json',wait=900) as rec:
 r.runtime(folder)
 s=(HERE/'SavedFireProbe.as').read_text()
 if '--native-timing' in sys.argv:
  checked=json.loads((OUT/'native-source/checked.json').read_text());assert r.sha(GAME/'pfe.swf')==checked['host']
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
 if '--short' in sys.argv:s=s.replace('SAMPLE_COUNT=180','SAMPLE_COUNT=120').replace('WARMUP_COUNT=90','WARMUP_COUNT=45')
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
 if '--sweep' in sys.argv:s=s.replace('SWEEP=false','SWEEP=true')
 if '--solo' in sys.argv:s=s.replace('SOLO=false','SOLO=true')
 if '--private-visible' in sys.argv:s=s.replace('SHOW_WINDOW=false','SHOW_WINDOW=true')
 if '--visual' in sys.argv:
  s=s.replace('VISUAL=false','VISUAL=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal']")
 if split:s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal','nomouse','nodraw','noeffects','noeffects','nodraw','nomouse','normal']")
 if candidate:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['off','normal','candidate','candidate','normal','off']")
  if '--reverse' in sys.argv:s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','candidate','normal','normal','candidate','off']")
 if '--diagnostic' in sys.argv:
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['off','normal','enemy-nodraw','effect-nodraw','effect-nodraw','enemy-nodraw','normal','off']")
 if '--both' in sys.argv:s=s.replace("for each(var variant:String in", "for each(var mode:String in ['current','classic'])for each(var variant:String in").replace("mode:'current',variant:variant", "mode:mode,variant:variant")
 if bursts:
  assert not candidate and not split
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal-burst','off-burst','off-burst','normal-burst']").replace('SAMPLE_COUNT=180','SAMPLE_COUNT=360').replace('WARMUP_COUNT=90','WARMUP_COUNT=0')
  if '--reverse' in sys.argv:s=s.replace("['normal-burst','off-burst','off-burst','normal-burst']","['off-burst','normal-burst','normal-burst','off-burst']")
 (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')
 r.runner.compile(folder/'CombatRenderProbeMod.as',folder/'mods/CombatRenderProbe/release/CombatRenderProbeMod.swf',[folder])
 sources=[('rv',BASE)]
 if candidate:sources.append(('candidate',OUT/'candidates'/('raster-crop-opaque' if '--opaque' in sys.argv else 'raster-crop' if '--raster-crop' in sys.argv else 'dark-native' if '--dark-native' in sys.argv else 'dark-child' if '--dark-child' in sys.argv else 'local-guard' if '--guard' in sys.argv else 'local')/'src'))
 chosen=next((v.split('=',1)[1] for v in sys.argv if v.startswith('--source=')),None)
 if chosen:
  assert candidate and chosen.isidentifier() and (OUT/'candidates'/chosen/'src').is_dir()
  sources[-1]=('candidate',OUT/'candidates'/chosen/'src')
 for variant,source in sources:
  src=folder/(variant+'-src');r.public(source,src)
  p=src/'RealisticVisionMod.as';s=p.read_text();pos=s.index('{',s.index('public class'))+1
  s=s[:pos]+'\n public var d53SkipEffects:Boolean=false;public var trailingHits:int=0;public var alphaHits:int=0;\n'+s[pos:]
  s=s.replace('// D56_LOCAL','trailingHits++;')
  s=s.replace('// D57_CLIP','trailingHits++; // D57_CLIP')
  s=s.replace('// D57_ALPHA_CLIP','alphaHits++; // D57_ALPHA_CLIP')
  s=s.replace('// D47_IDENTITY_HIT','trailingHits++;').replace('// D56_DARK_CHILD','trailingHits++;').replace('// D54_TRAILING','trailingHits++;')
  s=s.replace('// D56_REFRESH:','trailingHits++; // D56_REFRESH:').replace('// D56_OFFSCREEN:','trailingHits++; // D56_OFFSCREEN:')
  s=s.replace('public function applyWorldVisuals(w:World,loc:Location):void\n      {','public function applyWorldVisuals(w:World,loc:Location):void\n      {\nif(d53SkipEffects)return;')
  if plain:
   pos=s.index('{',s.index('public class'))+1;s=s[:pos]+'\npublic var profile:Object={},calls:Object={};\n'+s[pos:]
  else:s=r.fp.instrument(s,['prepareOcclusion','computeFov','applyVision','updateWallSurface','hideEnemies','applyMask','applyWeaponVisual','enemyState','refreshMask','fillFogCache','refreshWallField','applyWorldVisuals','applyWorldVisual'])
  if '--memory' in sys.argv:
   s=module('d57_memory',HERE/'memory_probe.py').instrument(s)
  p.write_text(s,encoding='utf-8')
  if reuse:
   frozen=OUT/reuse;prior=frozen/(variant+'-src')
   assert {q.relative_to(src).as_posix():r.sha(q) for q in src.rglob('*.as')}=={q.relative_to(prior).as_posix():r.sha(q) for q in prior.rglob('*.as')}
   shutil.copyfile(frozen/(variant+'.swf'),folder/(variant+'.swf'))
  else:r.runner.compile(p,folder/(variant+'.swf'),[src],stubs=True)
 selected=['CombatRenderProbeMod']
 if full:
  for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
   c=line.split('|')
   if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1]!='RealisticVisionMod':
    selected.append(c[1]);shutil.copytree((OUT/reuse if reuse else GAME)/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)
 if reuse:
  assert set(selected)==set(json.loads((OUT/reuse/'build.json').read_text())['selected'])
  assert r.sha(folder/'pfe.swf')==r.sha(OUT/reuse/'pfe.swf')
 catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
 (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nCombatRenderProbe|CombatRenderProbeMod|1|0|0\n',encoding='utf-8')
 a=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8');assert a.returncode==0,a.stdout+a.stderr
 r.save(folder/'build.json',{'full':full,'selected':selected,'installed':r.sha(MOD/'release/RealisticVisionMod.swf'),'profile':not plain,'candidate':candidate,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.swf','.xml','.txt')}})
 before=snapshot();r.save(folder/'before.json',before)
 code,log=r.air(folder,'pfe.swf',rec,timeout=650)
 after=snapshot();r.save(folder/'after.json',after)
 eligibility=comparison_environment('benchmark',before,after,json.loads((folder/'resource-policy.json').read_text()));r.save(folder/'environment.json',eligibility)
 print(log[-3000:]);assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==set(selected)
 data=json.loads((folder/'evidence/result.json').read_text());assert data['weapon']=='lmg' and data['audioVolume']==0
 groups={}
 for c in data['cases']:
  if 'idle' not in c['variant']:assert c['attacks']>10 and c['maxProjectiles']>0, (c['variant'],c['attacks'],c['maxProjectiles'])
  fs=[f for f in c['frames'] if 'nextInterval' in f];groups.setdefault(c['mode']+'/'+c['variant'],[]).extend(fs)
  assert c['enemyShots']>10,(c['variant'],c['enemyShots'])
  assert c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots']>50,c['variant']
  assert c['samplePlayerShotsLowerBound']>20,c['variant']
  print(c['variant'],'enemyShots',c['enemyShots'],'shots',c['attacks'],'bullets',c['maxProjectiles'],'profile',c.get('profile'))
 def stats(v):
  v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
 metrics=['nextInterval','rv']+(['nativeNext','otherHandlersNext','afterProbe','probeMs'] if '--native-timing' in sys.argv else [])
 result={'environment':eligibility,'groups':{k:{f:stats([x[f] for x in a]) for f in metrics} for k,a in groups.items()}}
 r.save(folder/'analysis.json',result);print(json.dumps(result));rec.outcome='passed';rec.note='LMG原生射击和计时完成；插桩归因不作最终发布收益'
