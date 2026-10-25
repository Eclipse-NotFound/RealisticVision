"""Sequential exact query effects against D44; no widened diagnostic query."""
from pathlib import Path
import importlib.util,argparse,json,re,shutil,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/classic-inputs-output';sys.path.insert(0,str(HERE))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
d=load('d50perf',HERE/'perf.py');r=d.r;BASE=d.BASE;CAND=OUT/'candidates/raw/src'
def local(name):
 folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D50 查询像素',purpose=name,run_dir=folder,evidence=folder/'checks.json',wait=900) as rec:
  src=folder/'src';r.public(CAND,src)
  (src/'BaselineVision.as').write_text(re.sub(r'\bprivate\b','public',(BASE/'RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision'),encoding='utf-8')
  test=(MOD/'build/native-performance-output/checks-final/src/LazyClassicChecks.as').read_text(encoding='utf-8')
  test=test.replace('private var passed:int=0,failed:int=0;','private var ready:int=0,passed:int=0,failed:int=0;')
  test=test.replace('frame<12','frame<24').replace('200+frame*43','200+int(frame/3)*43')
  test=test.replace('     step(a);step(b);','''     if(frame==14){a.m.cfgDim=b.m.cfgDim=.35;}
     if(frame==17){a.m.cfgDim=b.m.cfgDim=.6;}
     if(frame==20){a.m.resetOff();b.m.resetOff();}
     step(a);step(b);''')
  old='''     b.m.classicLogicRegion(new Rectangle(0,0,b.loc.spaceX,b.loc.spaceY));
     check(sameCanonical(a.m.fogCache,b.m.fogCache,new Rectangle(4,4,b.loc.spaceX*8,b.loc.spaceY*8),label),"all queryable canonical pixels "+label);'''
  assert test.count(old)==1
  test=test.replace(old,'''     check(same(a.m.fogCache,b.m.fogCache),"entire published field identical "+label);
     check(String(a.m.classicLogicTiles)==String(b.m.classicLogicTiles),"same published tile flags "+label);
     if(b.m.classicLogicInterpolated)ready++;''')
  needle='      a.m.clearMask(ar.u);b.m.clearMask(br.u);'
  test=test.replace(needle,'''      check(same(a.m.fogCache,b.m.fogCache),"exact published extent after each query "+label+" @"+pos);
      check(same(a.m.fogBmp,b.m.fogBmp),"query retains fog display "+label+" @"+pos);
'''+needle)
  test=test.replace('   trace("PASS "+passed+', '   check(ready>0,"private small-room interpolation actually used");trace("READY "+ready);\n   trace("PASS "+passed+')
  (src/'LazyClassicChecks.as').write_text(test,encoding='utf-8')
  r.runner.compile(src/'LazyClassicChecks.as',folder/'LazyClassicChecks.swf',[src,MOD/'build/motion-tests',MOD/'build/stubs'])
  r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file()}})
  code,log=r.air(folder,'LazyClassicChecks.swf',rec,240);(folder/'checks.log').write_text(log,encoding='utf-8');print(log[-2600:],flush=True)
  ok=code==0 and 'failed=0' in log and 'FAIL ' not in log
  r.save(folder/'checks.json',{'pass':ok,'exit':code,'summary':[x for x in log.splitlines() if 'COMPLETE' in x or x.startswith('READY ')]});assert ok
  rec.outcome='passed'
def native(name,build=False):
 v=load('d50_native',MOD/'build/fog-setters/validate.py');v.OUT=OUT;v.CAND=CAND;v.BASE=BASE;v.r=r;v.d=d
 original=r.runner.compile
 def compile_local(entry,out,sources,**kwargs):
  if entry.name=='RecoveryFrameProbeMod.as':
   text=entry.read_text().replace('fog-setters-output','classic-inputs-output')
   text=text.replace('private var result:Object={cases:[],checks:[]};','private var result:Object={cases:[],checks:[],ready:0};')
   text=text.replace('result.checks.push({caseIndex:', 'if(b.classicLogicInterpolated)result.ready++;result.checks.push({caseIndex:')
   text=text.replace('trace("FRAME COMPLETE");NativeApplication', 'if(result.ready==0)throw new Error("private cache not exercised");trace("PRIVATE READY "+result.ready);trace("FRAME COMPLETE");NativeApplication')
   entry.write_text(text,encoding='utf-8')
   kwargs['definitions']=[x.replace('CONFIG::largeScene,true','CONFIG::largeScene,false') for x in kwargs['definitions']]
  return original(entry,out,sources,**kwargs)
 r.runner.compile=compile_local
 try:
  if build:v.native_build(name,True)
  else:v.native_run(name)
 finally:r.runner.compile=original
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--candidate',default='raw');x=p.parse_args();CAND=OUT/'candidates'/x.candidate/'src';{'local':lambda:local(x.name),'native-build':lambda:native(x.name,True),'native-run':lambda:native(x.name)}[x.action]()
