"""Keep compact, recomputable measurements in the tracked experiment directory."""
from pathlib import Path
import json
from run import MOD, OUT, r
from analyze import stats

dest=MOD/'knowledge/experiments/boundary-opt-20261103';dest.mkdir(exist_ok=True)
names=['p0-profile-03','dda-profile-03','zero-perf-01','zero-perf-02','aa-perf-01']
archive={'inputs':json.loads((OUT/'inputs.json').read_text('utf8')),'runs':{}}
for name in names:
    folder=OUT/name
    raw=folder/'evidence/result.json'
    data=json.loads(raw.read_text('utf8'))
    summary=json.loads((folder/'summary.json').read_text('utf8'))
    # Keep every measured time, all counters and input fingerprints. The larger
    # coordinate arrays stay in immutable build evidence, indexed by SHA256.
    rows=[]
    for c,w in zip(data['cases'],summary['windows']):
        row={k:v for k,v in c.items() if k!='positions'}
        row['positionsSHA256']=w['positions'];rows.append(row)
    archive['runs'][name]={'scene':data['scene'],'build':json.loads((folder/'build.json').read_text('utf8')),
        'source':str(raw),'sourceSHA256':r.sha(raw),'environment':summary['environment'],
        'cases':rows,'combined':summary['combined']}
archive['exact']=json.loads((OUT/'zero-exact-02/evidence/result.json').read_text('utf8'))
archive['production']=json.loads((OUT/'production/build.json').read_text('utf8'))
archive['smoke']=json.loads((OUT/'production-smoke-01/validation.json').read_text('utf8'))
archive['deployment']=json.loads((OUT/'deployment.json').read_text('utf8'))
(dest/'measurements.json').write_text(json.dumps(archive,ensure_ascii=False,separators=(',',':'))+'\n','utf8')
print(dest/'measurements.json')
