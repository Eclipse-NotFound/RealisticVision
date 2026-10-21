"""Pin the final evidence before the RV-only deployment is allowed."""
import json,re,statistics
import production as p
r=p.run;OUT=p.OUT

def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def main():
 manifest=read('production-singlepass/manifest.json')
 assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 source=p.PACKAGE/'src'
 for rel,digest in manifest['sources'].items():
  assert r.sha(source/rel)==digest
  assert r.sha(p.investigate.SOURCES['fixed6']/rel)==digest
 checks=read('checks-09/result.json');assert len(checks)==4 and all(c['exit']==0 for c in checks)
 for name,count in [('LazyClassicChecks',1536),('SettingsChecks',90)]:
  log=(OUT/'checks-09'/(name+'.txt')).read_text(encoding='utf-8')
  assert 'passed='+str(count)+' failed=0' in log and 'FAIL ' not in log
 for name in ['SoftHarness','SharedExplorationHarness']:
  log=(OUT/'checks-09'/(name+'.txt')).read_text(encoding='utf-8');assert 'COMPLETE' in log and 'failures=0' in log and 'FAIL ' not in log
 native=read('final-native-01/evidence/result.json')
 assert len(native['checks'])==32 and all(c['exact'] for c in native['checks']) and 'error' not in native
 native_build=read('final-native-01/build.json')
 assert native_build['left']=='d33' and native_build['right']=='fixed6' and native_build['verify']
 for name in ['baseline-trial-05','final-native-01','final-combat-01']:
  folder=OUT/name;build=read(name+'/build.json')
  assert build['right']=='fixed6' and not build['profile']
  for rel,digest in build['files'].items():assert r.sha(folder/rel)==digest
  assert read(name+'/last-run.json')['exit']==0
  for rel in manifest['sources']:
   exact=(source/rel).read_text(encoding='utf-8')
   assert (folder/'candidate-src'/rel).read_text(encoding='utf-8')==re.sub(r'\bprivate\b','public',exact)
  log=(folder/'air-output.log').read_text(encoding='utf-8')
  assert 'FRAME COMPLETE' in log and 'FAIL ' not in log
  pid=read(name+'/last-run.json')['pid']
  foreign=[(sample['time'],process) for sample in read(name+'/environment.json') for process in sample['processes'] if process['pid']!=pid]
  assert not foreign,(name,foreign)
 trial=read('baseline-trial-05/evidence/result.json');assert len(trial['cases'])==4
 performance=[]
 for c in trial['cases']:
  assert all(len(x)==120 for x in c['updates']+c['draws'])
  totals=[[u+d for u,d in zip(c['updates'][i],c['draws'][i])] for i in range(2)]
  mean=[statistics.mean(v) for v in totals]
  assert mean[1]<=mean[0],(c['spec'],mean)
  performance.append({'case':c['spec'],'mean_total':mean})
 combat=read('final-combat-01/evidence/result.json');assert len(combat['cases'])==8 and 'error' not in combat
 assert all(c['attackStarts']>0 and c['maxProjectiles']>0 and len(c['updates'])==120 for c in combat['cases'])
 settings=read('production-singlepass/settings.json');assert len(settings)==2 and all(c['exit']==0 and c['passed']==18 for c in settings)
 host=r.sha(p.GAME/'pfe.swf')
 for name in ['baseline-trial-05','final-native-01','final-combat-01']:
  assert r.sha(OUT/name/'pfe.swf')==host,'Host changed; inspect and revalidate affected checks'
  assert r.sha(OUT/name/'mods/ContinuousScene/release/ContinuousSceneMod.swf')==r.sha(p.GAME/'mods/ContinuousScene/release/ContinuousSceneMod.swf')
 paths=[]
 for name in ['checks-09','baseline-trial-05','final-native-01','final-combat-01','production-singlepass']:
  paths += [f for f in (OUT/name).rglob('*') if f.is_file() and (f.suffix in ['.json','.log'] or f.name.endswith('Checks.txt') or f.name.endswith('Harness.txt') or f.name=='classes.txt') and 'storage' not in f.parts]
 evidence={f.relative_to(OUT).as_posix():r.sha(f) for f in paths}
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':host,'evidence':evidence,'checks':1731,'combat_windows':8,'performance':performance,'limits':'RV update plus fog drawing, not overall FPS; maximum spikes remain reportable.'})
 print('FINAL REVIEW PASS; 1731 checks plus 8 native combat windows')

if __name__=='__main__':main()
