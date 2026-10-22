"""Pin D38's tested source, strict pixels, native combat, and deployable bytes."""
import json,re,statistics
import package as p
from logic_blocks import transform as logic_transform
from support_runs import transform as support_transform
r=p.run;OUT=p.OUT
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def stats(a):
 s=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(a),'over50':sum(x>50 for x in a)}
def normalized(s):return re.sub(r'\bprivate\b','public',s.replace(p.VERSION,'v0.33.4-native-performance'))
def main():
 manifest=read('production/manifest.json');assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 selected=read('selected.json');assert selected['candidate']=='candidate-04'
 baseline=p.MOD/'build/native-performance-output/production/src'
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==r.sha(OUT/'production-input/src'/rel)==digest
  prod=normalized((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  assert prod==normalized((OUT/'candidate-04/src'/rel).read_text(encoding='utf-8-sig'))
  expected=(baseline/rel).read_text(encoding='utf-8-sig')
  assert r.sha(baseline/rel)==read('inputs.json')['sources'][rel]
  if rel=='RealisticVisionMod.as':expected=logic_transform(expected)
  elif rel=='RVWallSurface.as':expected=support_transform(expected)
  assert prod==normalized(expected),('unplanned source change',rel)
  for name in ['wide-final-parent','exact-final-parent','timing-final-visible','native-final','weapon-final']:
   tested=(OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig');assert prod==tested,(name,rel)
  assert prod==(OUT/'checks-final/src'/rel).read_text(encoding='utf-8-sig')
 checks=read('checks-final/result.json');assert len(checks)==4 and all(x['exit']==0 for x in checks)
 extra=read('checks-final/extra.json');assert len(extra)==2 and all(x['exit']==0 for x in extra)
 for name,count in [('LazyClassicChecks',1536),('SettingsChecks',90),('EquivalenceChecks',68),('DirtyClassicChecks',3072)]:
  log=(OUT/'checks-final'/(name+'.txt')).read_text(encoding='utf-8-sig');assert 'passed='+str(count) in log and 'FAIL ' not in log
 for name,count in [('SoftHarness',16),('SharedExplorationHarness',21)]:
  log=(OUT/'checks-final'/(name+'.txt')).read_text(encoding='utf-8-sig');assert len(re.findall(r'^PASS ',log,re.M))==count and 'FAIL ' not in log
 for name,count in [('wide-final-parent',64),('exact-final-parent',32)]:
  result=read(name+'/evidence/result.json');assert len(result['checks'])==count and all(c['exact'] for c in result['checks'])
  probe=(OUT/name/'RecoveryFrameProbeMod.as').read_text(encoding='utf-8-sig')
  assert 'parentCapture(ca,a,w);parentCapture(cb,b,w);' in probe and 'finally {if(original)original.addChildAt(node,index)' in probe
 weapon=read('weapon-final/evidence/result.json');assert len(weapon['checks'])==52 and all(x['pass'] for x in weapon['checks'])
 assert all(x['pixels']==0 for x in weapon['rows'] if x['variant']=='candidate')
 settings=read('production/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 perf=read('timing-final-visible/evidence/result.json');assert len(perf['cases'])==4
 rows=[]
 for c in perf['cases']:
  assert all(len(x)==120 for x in c['updates']+c['draws'])
  rows.append({'case':c['spec'],'update':[stats(x) for x in c['updates']],'total':[stats([u+d for u,d in zip(c['updates'][i],c['draws'][i])]) for i in range(2)]})
 combat=read('native-final/evidence/result.json');assert len(combat['cases'])==12
 for c in combat['cases']:assert c['attackStarts']>0 and c['maxProjectiles']>0 and len(c['updates'])==120
 environments={}
 for name in ['wide-final-parent','exact-final-parent','timing-final-visible','native-final']:
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
  assert r.sha(OUT/name/'mods/ContinuousScene/release/ContinuousSceneMod.swf')==r.sha(p.GAME/'mods/ContinuousScene/release/ContinuousSceneMod.swf')
  pid=read(name+'/last-run.json')['pid'];samples=read(name+'/environment.json')
  assert not [(s['time'],x) for s in samples for x in s['processes'] if x['pid']!=pid],name
  environments[name]={'min_available_gib':round(min(s['available_bytes'] for s in samples)/1024**3,3),'samples':len(samples),'pid':pid}
  if name in ['timing-final-visible','native-final']:assert min(s['available_bytes'] for s in samples)>=3*1024**3
 evidence={}
 for name in ['checks-final','wide-final-parent','exact-final-parent','timing-final-visible','native-final','weapon-final','production']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 performance={'paired':rows,'environment':environments,'combat':[{'variant':c['variant'],'mode':c['mode'],'update':stats(c['updates']),'interval':stats(c['intervals']),'attacks':c['attackStarts'],'maxProjectiles':c['maxProjectiles']} for c in combat['cases']], 'combat_pooled':[{'mode':mode,'variant':variant,'update':stats([x for c in combat['cases'] if c['mode']==mode and c['variant']==variant for x in c['updates']]),'interval':stats([x for c in combat['cases'] if c['mode']==mode and c['variant']==variant for x in c['intervals']])} for mode in ['classic','current'] for variant in ['off','baseline','candidate']]}
 r.save(OUT/'performance.json',performance)
 for row in rows:assert row['update'][1]['mean']<row['update'][0]['mean'],('no paired update benefit',row)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':4987,'combat_windows':12,'performance':rows,'limits':'RV update cost is not game FPS. Native combat evolves nondeterministically; off is native rendering in the same CS scene. Pixel verification retains parent hierarchy. FOV/memory code is unchanged from D37; no new FOV/memory test count claimed.'})
 print(json.dumps(performance,ensure_ascii=False,indent=2));print('D38 REVIEW PASS')
if __name__=='__main__':main()
