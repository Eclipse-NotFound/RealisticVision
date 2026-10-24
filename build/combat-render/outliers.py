"""Describe long-frame observations without assigning unmeasured render time."""
from pathlib import Path
import json,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-render-output'
result={}
for name in sys.argv[1:]:
    data=json.loads((OUT/name/'evidence/result.json').read_text())
    rows=[]
    for index,case in enumerate(data['cases']):
        for i,frame in enumerate(case['frames'][:-1]):
            if frame['nextInterval']<=200:continue
            following=case['frames'][i+1]
            rows.append({'case':index,'mode':case['mode'],'variant':case['variant'],
                'age':frame['age'],'intervalMs':frame['nextInterval'],'rvMs':frame['rv'],
                'particles':frame['particles'],'projectiles':frame['projectiles'],
                'masks':frame['masks'],'worldPass':frame['worldPass'],
                'memoryBetweenMiB':(following['memoryBefore']-frame['memoryAfter'])/1024**2})
    result[name]=rows
(OUT/'outliers.json').write_text(json.dumps({'note':'Memory drops are association only; outside the RV call includes native final rendering and scheduling. No samples excluded.','runs':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,rows in result.items():print(name,len(rows),'frames >200ms')
