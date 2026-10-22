"""Validate D40 source provenance, exact images and native-control performance."""
import json,re
import package as p
from analyze import stats
r=p.run;OUT=p.OUT
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def normal(s):return re.sub(r'\bprivate\b','public',s.replace(p.VERSION,'v0.33.6-long-frame')).replace('\n public var profile:Object={},calls:Object={};\n','')
def loaded(name):
 log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig')
 requested=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log))
 assert requested and requested==ok and 'ModLoader[err_' not in log,(name,requested-ok)
 return sorted(ok)
def pool(data):
 result=[]
 for mode in ['classic','current']:
  for variant in ['off','baseline','candidate']:
   rows=[f for c in data['cases'] if c['mode']==mode and c['variant']==variant for f in c['frames'] if 'nextInterval' in f]
   result.append({'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'rv':stats([x['rv'] for x in rows]),'outsideRV':stats([x['outsideRV'] for x in rows]),'over100':sum(x['nextInterval']>100 for x in rows),'over100WithRVUnder25':sum(x['nextInterval']>100 and x['rv']<25 for x in rows)})
 return result
def main():
 manifest=read('production/manifest.json');assert manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf') and manifest['version']==p.VERSION
 assert read('selected.json')['candidate']=='candidate-05'
 names=['safe-classic-parent','safe-shared-parent','timing-classic-visible','classic-full-sweep','native-walk-final','native-walk-reverse']
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==r.sha(OUT/'production-input/src'/rel)==digest
  prod=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  assert prod==normal((OUT/'candidate-05/src'/rel).read_text(encoding='utf-8-sig'))
  if rel!='RealisticVisionMod.as':assert prod==normal((OUT/'candidate-00/src'/rel).read_text(encoding='utf-8-sig'))
  for name in names:assert prod==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(name,rel)
 for name,count in [('safe-classic-parent',64),('safe-shared-parent',32)]:
  data=read(name+'/evidence/result.json');assert len(data['checks'])==count and all(x['exact'] for x in data['checks'])
  probe=(OUT/name/'RecoveryFrameProbeMod.as').read_text(encoding='utf-8')
  assert 'parentCapture(ca,a,w);parentCapture(cb,b,w);' in probe
 settings=read('production/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 native=read('native-walk-final/evidence/result.json');reverse=read('native-walk-reverse/evidence/result.json')
 for name,data in [('native-walk-final',native),('native-walk-reverse',reverse)]:
  assert len(data['cases'])==12 and not read(name+'/build.json')['profile']
  for c in data['cases']:
   assert c['nativeKeys'] and c['grounded']>=220 and c['walkDistance']>=300 and c['reversals']>=1 and c['attackStarts']>0 and c['maxProjectiles']>0,c
   assert len(c['frames'])==240
   for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart'] and a['rvEnd']-a['rvStart']==a['rv'] and a['outsideRV']==a['nextInterval']-a['rv']>=0
 environments={};loading={}
 for name in names:
  loading[name]=loaded(name);pid=read(name+'/last-run.json')['pid'];env=read(name+'/environment.json')
  assert not [(x['time'],proc) for x in env for proc in x['processes'] if proc['pid']!=pid],name
  environments[name]={'minAvailableGiB':round(min(x['available_bytes'] for x in env)/1024**3,3),'samples':len(env),'pid':pid};assert environments[name]['minAvailableGiB']>=3
  for rel in ['pfe.swf','mods/ContinuousScene/release/ContinuousSceneMod.swf']:assert r.sha(OUT/name/rel)==r.sha(p.GAME/rel)
 # Check all enabled full-combination source bytes, not just load success.
 frozen=read('inputs.json')['production'];pins={}
 for rel,digest in frozen.items():
  path=p.GAME/rel
  if path.suffix=='.swf' and ('.before' in path.name or path.name!='pfe.swf' and not path.stem.endswith('Mod')):continue
  assert r.sha(path)==digest,rel;pins[rel]=digest
  if path.suffix=='.swf' and path.name!='RealisticVisionMod.swf':
   for name in ['classic-full-sweep','native-walk-final','native-walk-reverse']:
    copied=OUT/name/rel
    if copied.exists():assert r.sha(copied)==digest,(name,rel)
 paired=[]
 for c in read('timing-classic-visible/evidence/result.json')['cases']:
  assert all(len(x)==120 for x in c['updates']+c['draws'])
  paired.append({'spec':c['spec'],'updates':[stats(x) for x in c['updates']],'draws':[stats(x) for x in c['draws']]})
 perf={'paired':paired,'native':pool(native),'reverse':pool(reverse),'sweep':pool(read('classic-full-sweep/evidence/result.json')),'nativeActivity':[{k:c[k] for k in ['mode','variant','grounded','walkDistance','reversals','attackStarts','maxProjectiles']} for c in native['cases']],'reverseActivity':[{k:c[k] for k in ['mode','variant','grounded','walkDistance','reversals','attackStarts','maxProjectiles']} for c in reverse['cases']],'loading':loading,'environment':environments,'limits':'Only classic code changed. Native windows use actual controls and live evolving NPC activity, not deterministic whole-frame causal replay. Off is full mod combination with RV off, not clean vanilla. Local CPU is not FPS. Sampled environment cannot rule out short system interference; reverse only enumerates all processes before/after play and samples owned process during play. system-battle observer is intrusive and excluded.'}
 perf['nativeLongFrames']=[{'mode':c['mode'],'variant':c['variant'],'frames':sorted([x for x in c['frames'] if 'nextInterval' in x],key=lambda x:x['nextInterval'],reverse=True)[:3]} for c in native['cases']]
 r.save(OUT/'performance.json',perf)
 evidence={}
 for name in names+['production']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 # Functional green alone does not authorize promoting this performance experiment.
 r.save(OUT/'verified.json',{'status':'FUNCTIONAL_PASS_RELEASE_HELD','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'installed_inputs':pins,'evidence':evidence,'checks':132,'native_windows':24,'limits':perf['limits']})
 print(json.dumps({'paired':paired,'native':perf['native'],'reverse':perf['reverse'],'environment':environments},ensure_ascii=False,indent=2));print('D40 FUNCTIONAL PASS; RELEASE HELD')
if __name__=='__main__':main()
