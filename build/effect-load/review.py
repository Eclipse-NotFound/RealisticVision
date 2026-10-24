import json,re,statistics
import package as p
r=p.run;OUT=p.OUT
def read(path):return json.loads((OUT/path).read_text(encoding='utf-8-sig'))
def normal(s):return re.sub(r'\bprivate\b','public',s).replace(p.VERSION,'v0.33.8-effect-visibility').replace('\n public var profile:Object={},calls:Object={};\n','')
def stats(a):
 a=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':a[int(.95*(len(a)-1))],'max':max(a),'over100':sum(x>100 for x in a)}
def main():
 manifest=read('production-final/manifest.json');assert manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==digest
  text=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  for name in ['functional-01','native-02','native-03','parent-01']:
   assert text==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(rel,name)
  for name in ['candidate-01','edges-01']:
   assert text==normal((OUT/name/'src'/rel).read_text(encoding='utf-8-sig')),(rel,name)
  if rel!='RealisticVisionMod.as':assert text==normal((OUT/'baseline/src'/rel).read_text(encoding='utf-8-sig'))
 checks=read('functional-01/evidence/result.json')['checks'];assert len(checks)==311 and all(c['pass'] for c in checks)
 for name in ['candidate-01','edges-01']:
  log=(OUT/name/'result.txt').read_text(encoding='utf-8');assert 'LOAD COMPLETE passed=360' in log and 'FAIL ' not in log
 settings=read('production-final/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 checks=read('parent-01/evidence/result.json')['checks'];assert len(checks)==64 and all(x['exact'] for x in checks)
 perf=[]
 for trial in ['native-02','native-03']:
  trace=read(trial+'/evidence/result.json');assert len(trace['cases'])==12
  for c in trace['cases']:
   assert len(c['frames'])==240 and c['attackStarts']>0 and c['maxProjectiles']>0 and c['denseMercenaries']==6
   for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart']
  for mode in ['current','classic']:
   for variant in ['off','baseline','candidate']:
    rows=[x for c in trace['cases'] if c['mode']==mode and c['variant']==variant for x in c['frames'] if 'nextInterval' in x]
    perf.append({'trial':trial,'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'update':stats([x['rv'] for x in rows])})
 r.save(OUT/'performance.json',perf)
 for name in ['functional-01','native-02','native-03','parent-01']:
  log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig');req=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log));assert req and req==ok and 'FAIL ' not in log
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
 for rel,digest in read('native-02/build.json')['files'].items():
  if rel.startswith('mods/') and rel.endswith('.swf') and 'RecoveryFrameProbe' not in rel:assert r.sha(p.GAME/rel)==digest,('dependency drift',rel)
 evidence={}
 for name in ['functional-01','candidate-01','edges-01','native-02','native-03','parent-01','production-final']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png','.as']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 for name in ['inputs.json','performance.json']:evidence[name]=r.sha(OUT/name)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':1131,'native_windows':24})
 print(json.dumps(perf,ensure_ascii=False,indent=2));print('D43 REVIEW PASS; assess performance before deployment')
if __name__=='__main__':main()
