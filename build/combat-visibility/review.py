import json,re,statistics
import package as p
r=p.run;OUT=p.OUT
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def stats(a):
 s=sorted(a);return {'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(a)}
def main():
 manifest=read('production/manifest.json');assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 for rel,digest in manifest['sources'].items():assert r.sha(OUT/'candidate/src'/rel)==r.sha(p.PACKAGE/'src'/rel)==digest
 checks=read('checks-01/result.json');assert len(checks)==4 and all(x['exit']==0 for x in checks)
 assert read('checks-01/batch.json')['checks']==65
 weapon=read('regress-full-03/evidence/result.json');assert len(weapon['checks'])==52 and all(x['pass'] for x in weapon['checks'])
 assert all(x['pixels']==0 for x in weapon['rows'] if x['variant']=='candidate')
 exact=read('exact-01/evidence/result.json');assert len(exact['checks'])==32 and all(x['exact'] for x in exact['checks'])
 perf=read('timing-02/evidence/result.json');assert len(perf['cases'])==4
 rows=[]
 for c in perf['cases']:
  assert all(len(x)==120 for x in c['updates']+c['draws'])
  rows.append({'case':c['spec'],'update':[stats(x) for x in c['updates']],'total':[stats([u+d for u,d in zip(c['updates'][i],c['draws'][i])]) for i in range(2)]})
 combat=read('combat-02/evidence/result.json');assert len(combat['cases'])==8 and all(c['attackStarts']>0 and c['maxProjectiles']>0 and len(c['updates'])==120 for c in combat['cases'])
 settings=read('production/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 for name in ['exact-01','timing-02','combat-02']:
  for rel in manifest['sources']:
   assert (OUT/name/'candidate-src'/rel).read_text(encoding='utf-8')==re.sub(r'\bprivate\b','public',(p.PACKAGE/'src'/rel).read_text(encoding='utf-8'))
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
  assert r.sha(OUT/name/'mods/ContinuousScene/release/ContinuousSceneMod.swf')==r.sha(p.GAME/'mods/ContinuousScene/release/ContinuousSceneMod.swf')
  pid=read(name+'/last-run.json')['pid']
  assert not [(s['time'],x) for s in read(name+'/environment.json') for x in s['processes'] if x['pid']!=pid]
 evidence={}
 for name in ['checks-01','regress-full-03','exact-01','timing-02','combat-02','production']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png']:
    evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':1848,'combat_windows':8,'performance':rows,'limits':'Measured RV updates and fog draw, not overall FPS. Native combat remains nondeterministic.'})
 r.save(OUT/'performance.json',{'paired':rows,'combat':[{'variant':c['variant'],'mode':c['mode'],'update':stats(c['updates']),'interval':stats(c['intervals']),'attacks':c['attackStarts']} for c in combat['cases']]})
 print(json.dumps(rows,ensure_ascii=False,indent=2));print('D36 REVIEW PASS')
if __name__=='__main__':main()
