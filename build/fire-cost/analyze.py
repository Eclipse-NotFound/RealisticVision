"""Small, reproducible summaries of completed native runs; no FPS inference."""
from pathlib import Path
import json, math, statistics, sys

OUT = Path(__file__).resolve().parents[2] / 'build/fire-cost-output'

def stats(values):
    values = sorted(values)
    if not values:
        return None
    return dict(n=len(values), mean=round(statistics.mean(values), 3),
                p95=values[math.ceil(len(values) * .95)-1], max=values[-1],
                over100=sum(v > 100 for v in values))

for name in sys.argv[1:]:
    run = OUT / name
    data = json.loads((run / 'evidence/result.json').read_text('utf8'))
    windows, grouped = [], {}
    for i, row in enumerate(data['cases']):
        frames = row['frames']
        complete = [f for f in frames if 'nextInterval' in f]
        item = dict(index=i, mode=row['mode'], variant=row['variant'],
                    frame=stats([f['nextInterval'] for f in complete]),
                    rv=stats([f['rv'] for f in complete]),
                    samples=len(frames),
                    playerShots=row['samplePlayerShotsLowerBound'],
                    enemyShots=row['sampleNativeEnemyShotsLowerBound'],
                    stage=row['stageScreen'])
        if 'ladStart' in row:
            item.update(ladStart=row['ladStart'], ladEnd=row['ladEnd'],
                        lightField=stats([f['lightingMs'] for f in complete]),
                        lightPulses=stats([f['lightingPulses'] for f in complete]))
        if frames and 'allocation' in frames[0]:
            alloc = [sum(f['allocation'][j] for f in frames) for j in range(9)]
            item['allocation'] = alloc
            item['newMiB'] = round(alloc[1]*4/2**20, 3)
            item['retirementFrames'] = [dict(age=f['age'], allocation=f['allocation'],
                rv=f['rv'], frame=f.get('nextInterval')) for f in frames if f['allocation'][6]]
            item['memoryDropsOver20MiB'] = [dict(age=f['age'], rv=f['rv'],
                frame=f.get('nextInterval'), dropMiB=round((f['memoryBefore']-f['memoryAfter'])/2**20,3))
                for f in frames if f['memoryBefore']-f['memoryAfter'] > 20*2**20]
            item['longestFrames'] = sorted(complete,key=lambda f:f['nextInterval'],reverse=True)[:5]
        windows.append(item)
        grouped.setdefault(row['mode']+'/'+row['variant'], []).extend(complete)
    summary = dict(run=name, completed=True, environment=json.loads((run/'environment.json').read_text('utf8')),
                   groups={k:dict(frame=stats([f['nextInterval'] for f in fs]),
                                  rv=stats([f['rv'] for f in fs])) for k,fs in grouped.items()},
                   windows=windows)
    (run/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
    print(json.dumps(dict(run=name,groups=summary['groups'],
                         windows=[{k:v for k,v in w.items() if k in ('index','mode','variant','frame','rv','lightField','lightPulses','playerShots','enemyShots')} for w in windows]),ensure_ascii=False))
