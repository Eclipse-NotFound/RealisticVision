"""Read frozen evidence only; do not run during a performance comparison."""
from pathlib import Path
import json,gzip,hashlib
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/performance-survey-output'
result={'scope':'Archived endpoint inventory, not new timing or a matched-size comparison','cases':[],'sources':{}}
for run in ['01-maximized-baseline','02-floor-branch','03-merged-large','05-palette-repeat']:
    p=MOD/'knowledge/experiments/maximized-flow-20261101'/run/'evidence/result.json.gz'
    result['sources'][str(p.relative_to(MOD))]=hashlib.sha256(p.read_bytes()).hexdigest()
    data=json.loads(gzip.decompress(p.read_bytes()))
    for c in data['cases']:
        if c['variant'] not in ['normal','candidate']:continue
        nodes=c.get('treeEnd',{}).get('nodes',[])
        world=next((v for v in nodes if v['id']==1),{})
        retained=c['retained']
        pixels=sum(retained[k] for k in ['rawPixels','softPixels','previousPixels'])
        result['cases'].append({'run':run,'mode':c['mode'],'variant':c['variant'],'stage':c['stageScreen'],
            'displayState':c['windowDisplayState'],'worldMatrix':world.get('screenMatrix'),
            'cropHitsOverWarmupAndSample':retained.get('optimizedCalls'),'retainedRasters':retained['rasters'],
            'retainedBitmapBytes':pixels*4,'visibleRecords':retained['visuals'],'maskInventory':c['maskInventory']})
(OUT/'history.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
print('Archived endpoints analyzed:',len(result['cases']))
