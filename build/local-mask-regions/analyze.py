from pathlib import Path
import json,sys,statistics
MOD=Path(__file__).resolve().parents[2];folder=MOD/'build/local-mask-regions-output'/sys.argv[1]
exit_code=json.loads((folder/'last-run.json').read_text('utf8'))['exit']
partial=next((x.split('=',1)[1] for x in sys.argv[2:] if x.startswith('--partial=')),None)
if partial:
 assert Path(partial).name==partial and partial.startswith('result-') and partial.endswith('.json')
 assert exit_code!=0, 'Successful runs must use the final result'
else:assert exit_code==0
raw=json.loads((folder/'evidence'/(partial or 'result.json')).read_text('utf8'))
def stats(values):
 s=sorted(values)
 return {'n':len(s),'mean':statistics.mean(s),'median':statistics.median(s),'p95':s[int(.95*(len(s)-1))],'max':max(s),'>100':sum(x>100 for x in s)}
result={'source':partial or 'result.json','complete':not bool(partial),'exit':exit_code,
        'environment':json.loads((folder/'environment.json').read_text('utf8')),'cases':[],'groups':{},'changes':{}}
if partial:
 result['performanceEligible']=False
 result['limitation']='Incomplete timed-out run; partial statistics are diagnostic only. Endpoint environment eligibility cannot override this.'
groups={}
for i,c in enumerate(raw['cases']):
 f=[x for x in c['frames'] if 'nextInterval' in x]
 assert c['activeSamples']==len(c['frames']),('inactive',i,c['activeSamples'])
 row={'index':i,'mode':c['mode'],'variant':c['variant'],'screen':c['stageScreen'],
      'frame':stats([x['nextInterval'] for x in f]),'rv':stats([x['rv'] for x in f]),
      'playerShots':c['samplePlayerShotsLowerBound'],'enemyShots':c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots'],
      'xRange':[min(x[0] for x in c['positions']),max(x[0] for x in c['positions'])]}
 result['cases'].append(row);groups.setdefault(c['mode']+'/'+c['variant'],[]).extend(f)
for key,frames in groups.items():result['groups'][key]={'frame':stats([x['nextInterval'] for x in frames]),'rv':stats([x['rv'] for x in frames])}
for mode in ['current','classic']:
 base=[x for x in result['cases'] if x['mode']==mode and x['variant']=='normal']
 if len(base)!=2:continue
 for variant in ['candidate','vector']:
  other=[x for x in result['cases'] if x['mode']==mode and x['variant']==variant]
  if len(other)!=2:continue
  key=mode+'/'+variant
  result['changes'][key]={'meanChangeMs':result['groups'][key]['frame']['mean']-result['groups'][mode+'/normal']['frame']['mean'],
                        'rvChangeMs':result['groups'][key]['rv']['mean']-result['groups'][mode+'/normal']['rv']['mean'],
                        'forwardChangeMs':other[0]['frame']['mean']-base[0]['frame']['mean'],
                        'returnChangeMs':other[1]['frame']['mean']-base[1]['frame']['mean']}
out=folder/('partial-analysis.json' if partial else 'paired-analysis.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
print(json.dumps({k:result[k] for k in ['complete','exit','performanceEligible','limitation','environment','groups','changes'] if k in result},ensure_ascii=False,indent=2))
