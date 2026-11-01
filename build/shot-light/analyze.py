from pathlib import Path
import json,statistics,sys,collections
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'
def stats(values):
 v=sorted(values)
 return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
labels=['setup','terrain','ambient','stable','ordinary','cleanup','trail','total','renders','visits','rays','shadow','invalid','same','adjacent','other','painted','makeMs','blendMs','draws','raycalls','steps','fanMs','rasterMs','cacheHits']
for name in sys.argv[1:]:
 p=OUT/name;data=json.loads((p/'evidence/result.json').read_text());rows=[];groups=collections.defaultdict(list)
 for index,c in enumerate(data['cases']):
  for i,f in enumerate(c['frames'][:-1]):
   if 'lightingTotal' in f:
    following=c['frames'][i+1];assert following['age']==f['age']+1
    f['lightingTotalNext']=following['lightingTotal']
  fs=[f for f in c['frames'] if 'nextInterval' in f]
  row={'index':index,'mode':c['mode'],'variant':c['variant'],'frames':len(c['frames']),'intervals':len(fs),
    'playerShots':c['samplePlayerShotsLowerBound'],'nativeEnemyShots':c['sampleNativeEnemyShotsLowerBound'],'forcedEnemyShots':c['sampleForcedEnemyShots']}
  for label in ['nextInterval','rv','lightingMs','lightingTotal','lightingTotalNext']:
   if fs and label in fs[0]:row[label]=stats([f[label] for f in fs])
  if 'lightingProfile' in fs[0]:
   row['lightingPhases']={k:statistics.mean(f['lightingProfile'][i] for f in fs) for i,k in enumerate(labels[:len(fs[0]['lightingProfile'])])}
  for label in ['rasterChecks','geometryReuses','ladStart','ladEnd']:
   if label in c:row[label]=c[label]
  if 'lightSources' in fs[0]:
   sources=collections.defaultdict(lambda:[0,0,0,0])
   for f in fs:
    for k,v in f['lightSources'].items():
     for i,x in enumerate(v):sources[k][i]+=x
   row['sourceMeans']={k:[x/len(fs) for x in v] for k,v in sources.items()}
  groups[c['mode']+'/'+c['variant']].extend(fs);rows.append(row)
 aggregate={}
 for k,fs in groups.items():
  aggregate[k]={label:stats([f[label] for f in fs]) for label in ['nextInterval','rv','lightingMs','lightingTotal','lightingTotalNext'] if label in fs[0]}
 result={'scene':data['scene'],'environment':json.loads((p/'environment.json').read_text()),'rows':rows,'groups':aggregate}
 (p/'detailed-analysis.json').write_text(json.dumps(result,indent=2)+'\n','utf8',newline='\n')
 print(name)
 for row in rows:print(row['index'],row['mode'],row['variant'],{k:round(row[k]['mean'],2) for k in ['nextInterval','rv','lightingMs','lightingTotal'] if k in row},'checks',row.get('rasterChecks'),'reuse',row.get('geometryReuses'))
