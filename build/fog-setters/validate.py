"""D49 local equivalence + native whole fog, no timing claims from capture."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/fog-setters-output'
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sys.path.insert(0,str(HERE));d=load('d49_perf',HERE/'perf.py');r=d.r;BASE=d.BASE;CAND=OUT/'candidates/guard/src'
def local(name):
 folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D49 局部画面',purpose=name,run_dir=folder,evidence=folder/'checks.json',wait=900) as rec:
  src=folder/'src';r.public(CAND,src)
  (src/'BaselineVision.as').write_text(re.sub(r'\bprivate\b','public',(BASE/'RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision'),encoding='utf-8')
  (src/'BaselineWallSurface.as').write_text(re.sub(r'\bprivate\b','public',(BASE/'RVWallSurface.as').read_text()).replace('RVWallSurface','BaselineWallSurface'),encoding='utf-8')
  world=(MOD/'build/stubs/fe/World.as').read_text();world=world.replace('public var black:Boolean;','public var cam:*;public var black:Boolean;')
  (src/'fe').mkdir();(src/'fe/World.as').write_text(world,encoding='utf-8')
  # Reuse the moving, broken terrain, alpha and interrupted-scan fixture exactly.
  helper=load('d49_helper',MOD/'build/long-frame/helper.py');helper.OUT=OUT;helper.r=r
  original=helper.r.public
  def public_for_helper(source,dest,*args,**kwargs):
   if source==OUT/'candidate-00/src':source=BASE
   return original(source,dest,*args,**kwargs)
  # The frozen generated helper already contains D39's complete scenario loop.
  old=MOD/'build/long-frame-output/helper-final/src/EquivalenceChecks.as'
  assert old.exists();shutil.copyfile(old,src/'EquivalenceChecks.as')
  shutil.copyfile(HERE/'FogChecks.as',src/'FogChecks.as')
  results=[]
  for test in ['FogChecks','EquivalenceChecks']:
   r.runner.compile(src/(test+'.as'),folder/(test+'.swf'),[src,MOD/'build/motion-tests',MOD/'build/stubs'])
   code,log=r.air(folder,test+'.swf',rec,180);(folder/(test+'.log')).write_text(log,encoding='utf-8')
   assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log,log[-2000:]
   results.append({'test':test,'summary':log.splitlines()[-1],'exit':code});print(results[-1],flush=True)
  r.save(folder/'checks.json',results);r.save(folder/'sources.json',{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*.as')});rec.outcome='passed'
def native_build(name,wide=False):
 folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D49 原生雾构建',purpose=name,run_dir=folder,evidence=folder/'build.json',resource='offline') as rec:
  r.runtime(folder)
  old=MOD/'build/long-frame-output'/('wide-final-parent' if wide else 'exact-final-parent')/'RecoveryFrameProbeMod.as'
  s=old.read_text(encoding='utf-8').replace('long-frame-output','fog-setters-output')
  # Querying the whole classic field before capture changes the display itself.
  query='if(b.cfgMode=="classic"){a.classicLogicRegion(new Rectangle(0,0,a.spaceX,a.spaceY));b.classicLogicRegion(new Rectangle(0,0,b.spaceX,b.spaceY));}'
  assert s.count(query)==1;s=s.replace(query,'')
  # Inputs and oracle are both D44: compare every original field without widening it.
  s=s.replace('!(b.cfgMode=="classic"&&field=="fogBmp")&&','').replace('!sameField(a,b,field)','!equal(a[field],b[field])')
  s=s.replace('var order:Array=(frame&1)?[1,0]:[0,1];','w.pers.infravis=int((frame+30)/30)%2;var order:Array=(frame&1)?[1,0]:[0,1];')
  s=s.replace('var start:int=getTimer();m.frameCount++;m.onFrameInner();', '''if(m.fogVis && frame%15==1){m.fogVis.visible=false;m.fogShadow.transform.colorTransform=new ColorTransform(.7,.6,.5,.8,1,2,3,4);m.fogShadow.blendMode="add";m.fogShadow.scrollRect=new Rectangle(3,5,117,119);m.fogShadow.x=9;m.fogShadow.y=11;}
            var start:int=getTimer();m.frameCount++;m.onFrameInner();''')
  entry=folder/'RecoveryFrameProbeMod.as';entry.write_text(s,encoding='utf-8')
  r.runner.compile(entry,folder/'mods/RecoveryFrameProbe/release/RecoveryFrameProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,true','-define=CONFIG::verifyPixels,true','-define=CONFIG::liveFrames,false'])
  catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
  (catalog/'supported-mods.txt').write_text((d.GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nRecoveryFrameProbe|RecoveryFrameProbeMod|1|0|0\n',encoding='utf-8')
  shutil.copytree(d.GAME/'mods/ContinuousScene/release',folder/'mods/ContinuousScene/release')
  selection=subprocess.run([str(d.GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only','ContinuousSceneMod,RecoveryFrameProbeMod','--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8',timeout=60)
  (folder/'selection.log').write_text(selection.stdout+selection.stderr,encoding='utf-8');assert selection.returncode==0
  for label,source in [('baseline',BASE),('candidate',CAND)]:
   src=folder/(label+'-src');r.public(source,src);r.runner.compile(src/'RealisticVisionMod.as',folder/(label+'.swf'),[src],stubs=True)
  r.save(folder/'build.json',{'wide':wide,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.swf','.xml','.txt')}});rec.outcome='passed'
def native_run(name):
 folder=OUT/name;assert not(folder/'last-run.json').exists()
 build=json.loads((folder/'build.json').read_text());assert all(r.sha(folder/p)==h for p,h in build['files'].items())
 with r.Registration(owner='RealisticVision / D49 原生整雾画面',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
  env=r.environment();r.save(folder/'environment.json',env);assert not env['processes'] and env['available_bytes']>5*1024**3,env
  code,log=r.air(folder,'pfe.swf',rec,600)
  r.save(folder/'validation.json',{'exit':code,'checks':len(re.findall(r'^PASS exact native frame ',log,re.M)),'pass':code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log});print(log[-1600:],flush=True)
  assert code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log;rec.outcome='passed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--wide',action='store_true');x=p.parse_args()
 {'local':lambda:local(x.name),'native-build':lambda:native_build(x.name,x.wide),'native-run':lambda:native_run(x.name)}[x.action]()
