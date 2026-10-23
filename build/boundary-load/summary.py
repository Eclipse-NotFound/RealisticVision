from pathlib import Path
import json,statistics,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/boundary-load-output'
for name in sys.argv[1:]:
 data=json.loads((OUT/name/'evidence/result.json').read_text(encoding='utf-8'))
 print(name)
 for c in data.get('cases',[]):
  print(c['spec'],'update',[round(statistics.mean(v),2) for v in c['updates']],
   'mask',[round(d.get('applyMask',0)/len(c['updates'][0]),2) for d in c.get('stages',[])],
   'logic',[round(d.get('classicLogicRegion',0)/len(c['updates'][0]),2) for d in c.get('stages',[])],
   'wall',[round(d.get('updateWallSurface',0)/len(c['updates'][0]),2) for d in c.get('stages',[])])
 print('keys',list(data),'checks',len(data.get('checks',[])))
