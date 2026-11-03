"""Recompute frame statistics and matched-input checks from raw evidence."""
from collections import defaultdict
from pathlib import Path
import hashlib, json, statistics, sys
from run import OUT, r


def stats(xs):
    ordered = sorted(xs)
    run = longest = 0
    for x in xs:
        run = run + 1 if x > 50 else 0
        longest = max(longest, run)
    return dict(n=len(xs), mean=round(statistics.mean(xs), 4),
        p95=ordered[int(.95*(len(xs)-1))], maximum=max(xs),
        over50=sum(x>50 for x in xs), over100=sum(x>100 for x in xs),
        longestOver50=longest)


def analyze(name):
    folder=OUT/name
    data=json.loads((folder/'evidence/result.json').read_text('utf8'))
    build=json.loads((folder/'build.json').read_text('utf8'))
    env=json.loads((folder/'environment.json').read_text('utf8'))
    if any(max(c['intervals'])>5000 for c in data['cases']):
        env['performanceEligible']=False
        if not any('interruption' in reason for reason in env['reasons']):
            env['reasons'].append('Multi-second interruption in raw frame intervals')
    groups=defaultdict(list); windows=[]
    for c in data['cases']:
        groups[c['scenario'],c['variant']].append(c)
        windows.append(dict(scenario=c['scenario'],variant=c['variant'],
            frame=stats(c['intervals']),rv=stats(c['updates']),shotsLower=c['shotsLower'],
            activeFrames=c['activeFrames'],maxProjectiles=c['maxProjectiles'],
            positions=hashlib.sha256(json.dumps(c['positions']).encode()).hexdigest(),
            profile=c.get('profile'),calls=c.get('calls'),audit=c.get('audit')))
    combined={}
    for (scenario,variant),cs in groups.items():
        # Long-frame streaks must not bridge independent windows.
        frame=stats([x for c in cs for x in c['intervals']])
        frame['longestOver50']=max(stats(c['intervals'])['longestOver50'] for c in cs)
        combined.setdefault(scenario,{})[variant]=dict(frame=frame,
            rv=stats([x for c in cs for x in c['updates']]),
            shotsLower=[c['shotsLower'] for c in cs])
    for scenario,variants in combined.items():
        a,b=variants['baseline'],variants['candidate']
        variants['delta']={k:dict(ms=round(b[k]['mean']-a[k]['mean'],4),
            percent=round((b[k]['mean']/a[k]['mean']-1)*100,2) if a[k]['mean'] else None)
            for k in ['frame','rv']}
    output=dict(run=name,scene=data['scene'],config=data['cases'][0]['config'],
        sameByteAA=build['baseline']==build['candidate'],environment=env,
        windows=windows,combined=combined)
    r.save(folder/'summary.json',output)
    print(json.dumps(dict(run=name,eligible=env['performanceEligible'],combined=combined),indent=2))


if __name__=='__main__':
    for name in sys.argv[1:]:analyze(name)
