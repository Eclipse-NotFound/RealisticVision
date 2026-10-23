"""Review exact inputs, functional assertions and measured performance separately."""
from pathlib import Path
import json,re,statistics,argparse
import package as p
OUT=p.OUT;r=p.run
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def stats(a):
 s=sorted(a)
 return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(a),'over50':sum(x>50 for x in a),'over100':sum(x>100 for x in a)}
def normal(s):return re.sub(r'\bprivate\b','public',s.replace(p.VERSION,'v0.33.6-long-frame'))
def analyze():
 data={'paired':[],'native':[],'environment':{}}
 for c in read('stress-03-timing/evidence/result.json')['cases']:
  assert all(len(x)==80 for x in c['updates']+c['draws'])
  data['paired'].append({'case':c['spec'],'update':[stats(x) for x in c['updates']],'updateDraw':[stats([u+d for u,d in zip(c['updates'][i],c['draws'][i])]) for i in range(2)]})
 trace=read('native-final/evidence/result.json');assert len(trace['cases'])==12
 for c in trace['cases']:
  assert len(c['frames'])==240 and c['grounded']>=220 and c['walkDistance']>300 and c['reversals']>=1
  assert c['attackStarts']>0 and c['maxProjectiles']>0
  for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart'] and a['rvEnd']-a['rvStart']==a['rv'] and a['outsideRV']==a['nextInterval']-a['rv']>=0
 for mode in ['classic','current']:
  for variant in ['off','baseline','candidate']:
   rows=[x for c in trace['cases'] if c['mode']==mode and c['variant']==variant for x in c['frames'] if 'nextInterval' in x]
   data['native'].append({'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'update':stats([x['rv'] for x in rows]),'outsideRV':stats([x['outsideRV'] for x in rows]),'longest':sorted(rows,key=lambda x:x['nextInterval'],reverse=True)[:2]})
 for name in ['stress-03-timing','native-final']:
  samples=read(name+'/environment.json');pid=read(name+'/last-run.json')['pid']
  assert not [(x['time'],proc) for x in samples for proc in x['processes'] if proc['pid']!=pid],name
  minimum=min(x['available_bytes'] for x in samples)/1024**3;assert minimum>=3,(name,minimum)
  data['environment'][name]={'minimumGiB':round(minimum,3),'samples':len(samples),'pid':pid}
 r.save(OUT/'performance.json',data)
 for c in data['paired']:print(c)
 for c in data['native']:print({k:v for k,v in c.items() if k!='longest'})
 return data
def verify():
 analyze()
 manifest=read('production/manifest.json');assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==r.sha(OUT/'production-input/src'/rel)==digest
  prod=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  assert prod==normal((OUT/'candidate-03/src'/rel).read_text(encoding='utf-8-sig'))
  if rel!='RealisticVisionMod.as':assert prod==normal((OUT/'candidate-00/src'/rel).read_text(encoding='utf-8-sig'))
  for name in ['safe-exact-03-parent','safe-extent-parent','stress-03-timing','weapon-final']:
   assert prod==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(name,rel)
  traced=(OUT/'native-final/candidate-src'/rel).read_text(encoding='utf-8-sig').replace('\n public var profile:Object={},calls:Object={};\n','')
  assert prod==normal(traced),rel
 for name,count in [('safe-exact-03-parent',64),('safe-extent-parent',6)]:
  checks=read(name+'/evidence/result.json')['checks'];assert len(checks)==count and all(x['exact'] for x in checks)
  text=(OUT/name/'RecoveryFrameProbeMod.as').read_text(encoding='utf-8');assert text.index('parentCapture(ca,a,w);parentCapture(cb,b,w);')<text.index('if(b.cfgMode=="classic"){a.classicLogicRegion')
 # Dynamic fill-reference verification is reusable only for the identical method.
 extract=lambda s:s.split('function applyMask(')[1].split('function finishCurrentMask(')[0]
 assert extract((OUT/'candidate-01/src/RealisticVisionMod.as').read_text(encoding='utf-8'))==extract((OUT/'candidate-03/src/RealisticVisionMod.as').read_text(encoding='utf-8'))
 assert read('render-checks-02/result.json')['exit']==0 and 'RENDER COMPLETE passed=589 reused=216' in (OUT/'render-checks-02/result.txt').read_text()
 weapon=read('weapon-final/evidence/result.json');assert len(weapon['checks'])==52 and all(x['pass'] for x in weapon['checks'])
 assert all(x['pixels']==0 for x in weapon['rows'] if x['variant']=='candidate')
 settings=read('production/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 loads={}
 for name in ['native-final','safe-exact-03-parent','safe-extent-parent','stress-03-timing','weapon-final']:
  log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig')
  requested=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log));assert requested and requested==ok and not re.search(r'ModLoader\[err_',log)
  loads[name]=sorted(ok)
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
 # Existing production dependencies must still match the full-combination run.
 full=read('native-final/build.json')
 for rel,digest in full['files'].items():
  if rel.startswith('mods/') and rel.endswith('.swf') and 'RecoveryFrameProbe' not in rel:
   assert r.sha(p.GAME/rel)==digest,('installed dependency drift',rel)
 decision=read('performance-decision.json');assert decision['accepted'] is True and decision['performance_sha256']==r.sha(OUT/'performance.json')
 names=['safe-exact-03-parent','safe-extent-parent','stress-03-timing','native-final','weapon-final','production','render-checks-02']
 evidence={}
 for name in names:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png','.as']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 for name in ['performance.json','performance-decision.json','selected.json','inputs.json']:evidence[name]=r.sha(OUT/name)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':747,'native_windows':12,'loading':loads})
 print('D41 REVIEW PASS')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['analyze','verify']);x=a.parse_args();analyze() if x.action=='analyze' else verify()
