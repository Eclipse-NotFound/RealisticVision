import json,re,statistics,argparse,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('d43_review_package',Path(__file__).with_name('package.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
r=p.run;OUT=p.OUT
def read(path):return json.loads((OUT/path).read_text(encoding='utf-8-sig'))
def normal(s):return re.sub(r'\bprivate\b','public',s).replace(p.VERSION,'v0.33.8-effect-visibility').replace('\n public var profile:Object={},calls:Object={};\n','')
def stats(a):
 a=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':a[int(.95*(len(a)-1))],'max':max(a),'over100':sum(x>100 for x in a)}
def native(trials):
 perf=[]
 for trial in trials:
  env=read(trial+'/environment.json')
  assert env and min(x['available_bytes'] for x in env)>=3*1024**3,('low memory during timing',trial)
  trace=read(trial+'/evidence/result.json');assert len(trace['cases'])==12
  for c in trace['cases']:
   assert c.get('sampleFrames',240) in [120,240] and len(c['frames'])==c.get('sampleFrames',240) and c['attackStarts']>0 and c['maxProjectiles']>0 and c['denseMercenaries']==6
   for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart']
  for mode in ['current','classic']:
   for variant in ['off','baseline','candidate']:
    rows=[x for c in trace['cases'] if c['mode']==mode and c['variant']==variant for x in c['frames'] if 'nextInterval' in x]
    perf.append({'trial':trial,'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'update':stats([x['rv'] for x in rows])})
 return perf
def main(trials,perf_only=False):
 perf=native(trials);r.save(OUT/'performance.json',perf)
 for x in perf:print(x['trial'],x['mode'],x['variant'],'interval',x['interval'],'update',x['update'])
 if perf_only:return
 manifest=read('production-final/manifest.json');assert manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 runtime=['functional-03','safe-02-parent']+trials;bench=['candidate-03','edges-01']
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==digest
  text=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  for name in runtime:assert text==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(rel,name)
  for name in bench:assert text==normal((OUT/name/'src'/rel).read_text(encoding='utf-8-sig')),(rel,name)
  if rel!='RealisticVisionMod.as':assert text==normal((OUT/'baseline/src'/rel).read_text(encoding='utf-8-sig'))
 checks=read('functional-03/evidence/result.json')['checks'];assert len(checks)==311 and all(c['pass'] for c in checks)
 for name in bench:
  log=(OUT/name/'result.txt').read_text(encoding='utf-8');assert 'LOAD COMPLETE passed=360' in log and 'FAIL ' not in log
  assert read(name+'/last-run.json')['exit']==0
 settings=read('production-final/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 checks=read('safe-02-parent/evidence/result.json')['checks'];assert len(checks)==64 and all(x['exact'] for x in checks)
 parent=(OUT/'safe-02-parent/RecoveryFrameProbeMod.as').read_text(encoding='utf-8')
 assert 'parentCapture(ca,a,w);parentCapture(cb,b,w);' in parent
 for name in runtime:
  assert read(name+'/last-run.json')['exit']==0,(name,'process exit')
  log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig');req=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log));assert req and req==ok and 'FAIL ' not in log
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
 dependencies={}
 for trial in trials:
  extra=read(trial+'/supplemental-inputs.json')
  for rel,digest in extra['files'].items():
   if trial==trials[-1]:assert r.sha(p.GAME/rel)==digest,('latest supplemental dependency drift',rel)
   assert r.sha(OUT/trial/rel)==digest,('isolated supplemental mismatch',rel)
  dependencies[trial]={}
  for rel,digest in read(trial+'/build.json')['files'].items():
   rel=rel.replace('\\','/')
   if rel.startswith('mods/') and '/release/' in rel and rel.endswith(('.swf','.txt','.json')) and 'RecoveryFrameProbe' not in rel:
    assert r.sha(OUT/trial/rel)==digest,('frozen dependency mismatch',trial,rel)
    dependencies[trial][rel]=digest
    if trial==trials[-1]:assert r.sha(p.GAME/rel)==digest,('latest dependency drift',rel)
 latest=dependencies[trials[-1]]
 changes={}
 for trial,files in dependencies.items():
  assert set(files)==set(latest)
  delta={k:{'before':v,'after':latest[k]} for k,v in files.items() if v!=latest[k]}
  if delta:
   allowed={'mods/rconnect/release/rconnectmod.swf':'78c052aea963f1689b705ae1e14d274916ae1a1f7e81933390caf8d1a88f4699',
            'mods/modloader/release/modloadermod.swf':'2050e023205e87fdfdf7fba4b54b9bad7769868e51767d0bfbe1742cdc7542e2'}
   assert all(k.lower() in allowed and v['after']==allowed[k.lower()] for k,v in delta.items()),delta
   changes[trial]=delta
 r.save(OUT/'dependency-transition.json',{'latest':trials[-1],'earlier_changes':changes,'reason':'RConnect roomfix5 and ModLoader2050 independently deployed between rounds; each round compares both RV variants within the same frozen process. No cross-round absolute timing attribution.'})
 evidence={}
 for name in runtime+bench+['production-final']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png','.as']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 for name in ['inputs.json','performance.json','dependency-transition.json']:evidence[name]=r.sha(OUT/name)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':1131,'native_windows':12*len(trials)})
 print('D43 REVIEW PASS; assess performance separately before deployment')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--perf-only',action='store_true');a.add_argument('trials',nargs='+');x=a.parse_args();main(x.trials,x.perf_only)
