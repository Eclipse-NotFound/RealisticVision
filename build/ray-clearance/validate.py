"""D51 functional checks only; retained play windows preclude timing acceptance."""
from pathlib import Path
import argparse, importlib.util, json, re, shutil, sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/ray-clearance-output'
sys.path.insert(0,str(MOD/'build/classic-inputs'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
d=load('d51_runtime',MOD/'build/classic-inputs/perf.py');r=d.r
BASE=d.BASE;CAND=OUT/'candidate-v2/src'

def instrument(s,candidate):
 marker='      public var rayOpac:Vector.<Number>;';assert s.count(marker)==1
 s=s.replace(marker,marker+'\n      public var d51Fast:int=0;public var d51Steps:Number=0;')
 marker='            if(++guard > 400)';assert s.count(marker)==1
 s=s.replace(marker,'            this.d51Steps++;\n'+marker)
 if candidate:
  marker='==0)\n               return 1;';assert s.count(marker)==1
  s=s.replace(marker,'==0){this.d51Fast++;return 1;}')
 return s

def public(source,dest,*args,**kwargs):
 original_public(source,dest,*args,**kwargs)
 p=dest/'RealisticVisionMod.as'
 p.write_text(instrument(p.read_text(encoding='utf-8'),source==CAND),encoding='utf-8',newline='\n')
original_public=r.public

def local(name):
 folder=OUT/name;assert not folder.exists()
 with r.Registration(owner='RealisticVision / D51 射线功能',purpose=name+' 仅结果与步数，不计时',run_dir=folder,evidence=folder/'checks.json',wait=900) as rec:
  src=folder/'src';public(CAND,src)
  s=re.sub(r'\bprivate\b','public',(BASE/'RealisticVisionMod.as').read_text(encoding='utf-8'))
  (src/'BaselineVision.as').write_text(instrument(s,False).replace('RealisticVisionMod','BaselineVision'),encoding='utf-8')
  for name2 in ['RayClearanceChecks.as','RayTestLocation.as']:shutil.copyfile(HERE/name2,src/name2)
  p=src/'fe/loc/Location.as';p.parent.mkdir(parents=True)
  s=(MOD/'build/stubs/fe/loc/Location.as').read_text(encoding='utf-8').replace('public var id:String;','public var space:Array;public var id:String;')
  p.write_text(s,encoding='utf-8')
  r.runner.compile(src/'RayClearanceChecks.as',folder/'RayClearanceChecks.swf',[src,MOD/'build/stubs'])
  r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file()},'performance_evidence':False})
  r.save(folder/'environment.json',r.environment())
  code,log=r.air(folder,'RayClearanceChecks.swf',rec,300)
  lines=[x for x in log.splitlines() if x.startswith(('SIZE ','RAY COMPLETE','FAIL '))]
  matches=re.findall(r'^RAY COMPLETE (.+)$',log,re.M);result=json.loads(matches[-1]) if matches else {}
  result.update({'exit':code,'pass':code==0 and result.get('failed')==0 and 'FAIL ' not in log})
  r.save(folder/'checks.json',result);print('\n'.join(lines),flush=True);assert result['pass']
  rec.outcome='passed';rec.note='射线结果及异常/失效行为一致；步数不是性能验收'

def native_build(name,large):
 v=load('d51_native',MOD/'build/fog-setters/validate.py');v.OUT=OUT;v.CAND=CAND;v.BASE=BASE;v.r=r;v.d=d
 compile_original=r.runner.compile
 def compile_probe(entry,out,sources,**kwargs):
  if entry.name=='RecoveryFrameProbeMod.as':
   s=entry.read_text(encoding='utf-8').replace('fog-setters-output','ray-clearance-output')
   marker='result.checks.push({caseIndex:';assert s.count(marker)==1
   s=s.replace(marker,'''result.clearHitsTotal=Number(result.clearHitsTotal||0)+b.d51Fast;b.d51Fast=0;
               result.oldSteps=Number(result.oldSteps||0)+a.d51Steps;a.d51Steps=0;
               result.newSteps=Number(result.newSteps||0)+b.d51Steps;b.d51Steps=0;
               '''+marker)
   marker='trace("FRAME COMPLETE");NativeApplication';assert s.count(marker)==1
   s=s.replace(marker,'if(!(result.clearHitsTotal>0))throw new Error("shortcut not exercised");trace("CLEAR HITS "+result.clearHitsTotal+" steps="+result.oldSteps+"/"+result.newSteps);'+marker)
   entry.write_text(s,encoding='utf-8')
   if not large:kwargs['definitions']=[x.replace('CONFIG::largeScene,true','CONFIG::largeScene,false') for x in kwargs['definitions']]
  return compile_original(entry,out,sources,**kwargs)
 r.runner.compile=compile_probe;r.public=public
 try:
  with r.Registration(owner='RealisticVision / D51 原生构建',purpose=name+' 功能候选，无计时',run_dir=OUT/name,evidence=OUT/name/'build.json',wait=900) as rec:
   original_registration=r.Registration
   import contextlib
   r.Registration=lambda **kw:contextlib.nullcontext(rec)
   try:v.native_build(name,True)
   finally:r.Registration=original_registration
 finally:r.runner.compile=compile_original;r.public=original_public

def native_run(name):
 folder=OUT/name;assert not (folder/'last-run.json').exists()
 build=json.loads((folder/'build.json').read_text());assert all(r.sha(folder/p)==h for p,h in build['files'].items())
 with r.Registration(owner='RealisticVision / D51 原生画面',purpose=name+' 用户保留试玩；仅功能，不计时',run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
  env=r.environment();r.save(folder/'environment.json',env);assert env['available_bytes']>5*1024**3
  code,log=r.air(folder,'pfe.swf',rec,600)
  count=len(re.findall(r'^PASS exact native frame ',log,re.M))
  selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
  loaded=set(re.findall(r'ModLoader\[ok_(\w+)\]',log));requested=set(re.findall(r'ModLoader\[requested_(\w+)\]',log))
  data=json.loads((folder/'evidence/result.json').read_text())
  ok=code==0 and count==64 and 'FRAME COMPLETE' in log and data.get('clearHitsTotal',0)>0 and 'FAIL ' not in log and 'ModLoader[err_' not in log and selected==requested==loaded
  r.save(folder/'validation.json',{'exit':code,'checks':count,'pass':ok,'selected':sorted(selected),'clearHits':data.get('clearHitsTotal'),
   'oldSteps':data.get('oldSteps'),'newSteps':data.get('newSteps'),'performance_evidence':False})
  print(log[-1800:],flush=True);assert ok
  assert all(r.sha(folder/p)==h for p,h in build['files'].items())
  rec.outcome='passed';rec.note='64项严格原生画面；计数仅证使用路径，不作性能用途'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['local','native-build','native-run']);p.add_argument('name');p.add_argument('--large',action='store_true');a=p.parse_args()
 {'local':lambda:local(a.name),'native-build':lambda:native_build(a.name,a.large),'native-run':lambda:native_run(a.name)}[a.action]()
