"""Collect complete timed windows, retaining failed post-timing checks separately."""
from pathlib import Path
import json,statistics
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combo-audit-output'
def stats(values):
    a=sorted(values)
    return {'n':len(a),'mean':statistics.mean(a),'median':statistics.median(a),'p95':a[int(.95*(len(a)-1))],
            'p99':a[int(.99*(len(a)-1))],'max':a[-1],'>100':sum(x>100 for x in a)}
result={}
for folder in sorted(OUT.glob('[0-9][0-9]-*')):
    p=folder/'evidence/result.json'
    if not p.exists() or not (folder/'last-run.json').exists():continue
    d=json.loads(p.read_text(encoding='utf-8'));groups={};windows=[];peaks=[]
    for i,c in enumerate(d['cases']):
        frames=[f for f in c['frames'] if 'nextInterval' in f]
        assert len(frames)==c['sampleFrames']-1,(folder.name,c['variant'],len(frames))
        assert c['activeSamples']==c['sampleFrames']
        if 'idle' not in c['variant']:assert c['samplePlayerShotsLowerBound']>20
        if c['crowd']>0:assert c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots']>50
        for f in frames:
            if 'nativeNext' in f:
                assert f['worldStepsNext']==1
                assert sum(f[k] for k in ['nativeNext','otherHandlersNext','afterProbe','probeMs'])==f['nextInterval']
            if f['nextInterval']>250:peaks.append({'case':i,'variant':c['variant'],**f})
        metrics=['nextInterval','rv']+(['nativeNext','otherHandlersNext','afterProbe','probeMs'] if 'nativeNext' in frames[0] else [])
        groups.setdefault(c['variant'],[]).extend(frames)
        windows.append({'index':i,'variant':c['variant'],'crowd':c['crowd'],'metrics':{k:stats([f[k] for f in frames]) for k in metrics},
                       'samplePlayerShots':c['samplePlayerShotsLowerBound'],'meanParticles':statistics.mean(f['particles'] for f in frames),
                       'maskInventory':c['maskInventory'],'retained':c['retained']})
    result[folder.name]={'scene':d['scene'],'postTimingError':d.get('error'),'lastRun':json.loads((folder/'last-run.json').read_text()),
      'environment':json.loads((folder/'environment.json').read_text()),'groups':{v:{k:stats([f[k] for f in fs]) for k in metrics} for v,fs in groups.items()},
      'windows':windows,'peaksOver250':peaks,'audit':d.get('audit')}
(OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,d in result.items():
    print(name, d['scene']['screen'], 'error='+str(d['postTimingError']))
    for v,g in d['groups'].items():
        print(' ',v, 'frame',round(g['nextInterval']['mean'],2),'median',g['nextInterval']['median'],'p95',g['nextInterval']['p95'],
              'RV',round(g['rv']['mean'],2),'after',round(g.get('afterProbe',{}).get('mean',0),2))
