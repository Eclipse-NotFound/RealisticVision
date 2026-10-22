"""Pin D39's source, image equivalence, trigger measurements and exact package."""
from pathlib import Path
import json,re,statistics
import package as p
r=p.run;OUT=p.OUT
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def stats(a):
 if not a:return None
 s=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(a),'over50':sum(x>50 for x in a),'over100':sum(x>100 for x in a)}
def normal(s):return re.sub(r'\bprivate\b','public',s.replace(p.VERSION,'v0.33.5-followup-performance'))
def loaded(name):
 log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig')
 requested=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log))
 assert requested and requested==ok,(name,requested-ok)
 assert not re.search(r'ModLoader\[err_',log)
 return sorted(ok)
def main():
 manifest=read('production/manifest.json');assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 selected=read('selected.json');assert selected['candidate']=='candidate-04'
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==r.sha(OUT/'production-input/src'/rel)==digest
  prod=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  assert prod==normal((OUT/'candidate-04/src'/rel).read_text(encoding='utf-8-sig'))
  if rel!='RVWallSurface.as':assert prod==normal((OUT/'candidate-00/src'/rel).read_text(encoding='utf-8-sig')),('unplanned change',rel)
  for name in ['exact-final-parent','wide-final-parent','timing-final-visible','weapon-final']:
   assert prod==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(name,rel)
  traced=(OUT/'trace-final/candidate-src'/rel).read_text(encoding='utf-8-sig').replace('\n public var profile:Object={},calls:Object={};\n','')
  assert prod==normal(traced),('trace-final',rel)
 helper=read('helper-final/result.json');assert helper['exit']==0 and 'passed=230 failed=0' in '\n'.join(helper['summary'])
 for name,count in [('exact-final-parent',32),('wide-final-parent',64)]:
  data=read(name+'/evidence/result.json');assert len(data['checks'])==count and all(x['exact'] for x in data['checks'])
  assert 'parentCapture(ca,a,w);parentCapture(cb,b,w);' in (OUT/name/'RecoveryFrameProbeMod.as').read_text(encoding='utf-8')
 weapon=read('weapon-final/evidence/result.json');assert len(weapon['checks'])==52 and all(x['pass'] for x in weapon['checks'])
 assert all(x['pixels']==0 for x in weapon['rows'] if x['variant']=='candidate')
 settings=read('production/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 paired=[]
 for c in read('timing-final-visible/evidence/result.json')['cases']:
  assert all(len(x)==120 for x in c['updates']+c['draws'])
  paired.append({'case':c['spec'],'update':[stats(x) for x in c['updates']],'total':[stats([u+d for u,d in zip(c['updates'][i],c['draws'][i])]) for i in range(2)]})
 assert len(paired)==4
 trace=read('trace-final/evidence/result.json');assert len(trace['cases'])==12 and not read('trace-final/build.json')['profile']
 for c in trace['cases']:
  assert len(c['frames'])==300
  for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart'] and a['rvEnd']-a['rvStart']==a['rv'] and a['outsideRV']==a['nextInterval']-a['rv']>=0
 pooled=[]
 for mode in ['classic','current']:
  for variant in ['off','baseline','candidate']:
   rows=[x for c in trace['cases'] if c['mode']==mode and c['variant']==variant for x in c['frames'] if 'nextInterval' in x]
   changed=[x for x in rows if x['viewChanged']]
   pooled.append({'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'update':stats([x['rv'] for x in rows]),'viewChanges':stats([x['rv'] for x in changed]),'viewChangeIntervals':stats([x['nextInterval'] for x in changed]),'outsideRV':stats([x['outsideRV'] for x in rows]),'slowWithRVUnder25':sum(x['nextInterval']>50 and x['rv']<25 for x in rows)})
 environments={};loading={}
 for name in ['exact-final-parent','wide-final-parent','timing-final-visible','trace-final','weapon-final']:
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
  assert r.sha(OUT/name/'mods/ContinuousScene/release/ContinuousSceneMod.swf')==r.sha(p.GAME/'mods/ContinuousScene/release/ContinuousSceneMod.swf')
  loading[name]=loaded(name)
  if name=='weapon-final':continue # Functional-only driver has launch state, not a timing environment trace.
  pid=read(name+'/last-run.json')['pid'];samples=read(name+'/environment.json')
  assert not [(x['time'],proc) for x in samples for proc in x['processes'] if proc['pid']!=pid],name
  environments[name]={'min_available_gib':round(min(x['available_bytes'] for x in samples)/1024**3,3),'samples':len(samples),'pid':pid}
  assert environments[name]['min_available_gib']>=3,name
 perf={'paired':paired,'full_combo_sweep':pooled,'loading':loading,'environment':environments,'limits':'Same-input update/draw is not FPS. Full combo uses live NPC activity and scripted camera sweep; no deterministic whole-frame causality. EXIT_FRAME phase mapping rejected; outsideRV includes driver/camera/other scripts/render/scheduling.'}
 perf['longestIntervals']=[{'mode':c['mode'],'variant':c['variant'],'frames':sorted([x for x in c['frames'] if 'nextInterval' in x],key=lambda x:x['nextInterval'],reverse=True)[:3]} for c in trace['cases']]
 r.save(OUT/'performance.json',perf)
 evidence={}
 for name in ['helper-final','exact-final-parent','wide-final-parent','timing-final-visible','trace-final','weapon-final','production']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':414,'trigger_windows':12,'limits':perf['limits']})
 print(json.dumps(perf,ensure_ascii=False,indent=2));print('D39 REVIEW PASS')
if __name__=='__main__':main()
