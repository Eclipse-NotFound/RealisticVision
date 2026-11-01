"""Summarize exact complete intervals and owned-process CPU buckets."""
from pathlib import Path
import json, statistics, sys
HERE=Path(__file__).resolve().parent; MOD=HERE.parents[1]
OUT=MOD/'build/composite-followup-output'

def stats(a):
    if not a:return None
    a=sorted(a)
    return dict(n=len(a),mean=statistics.mean(a),median=statistics.median(a),p95=a[int(.95*(len(a)-1))],max=a[-1],over100=sum(v>100 for v in a))

def analyze(folder):
    data=json.loads((folder/'evidence/result.json').read_text())
    cpu=json.loads((folder/'cpu-samples.json').read_text())
    buckets=[]
    for a,b in zip(cpu['samples'],cpu['samples'][1:]):
        if a['errors'] or b['errors']:continue
        wall=(b['perf_counter_ns']-a['perf_counter_ns'])/1e6
        used=(b['kernel_time_100ns']+b['user_time_100ns']-a['kernel_time_100ns']-a['user_time_100ns'])/1e4
        # Queries happen within the measured call interval. Require its full
        # endpoint to lie inside the window before associating the CPU delta.
        buckets.append(dict(start=a['time_ns']/1e6,end=(b['time_ns']+b['query_duration_ns'])/1e6,wallMs=wall,cpuMs=used,cpuCores=used/wall,delayed=wall>1500))
    result={'scene':data['scene'],'environment':json.loads((folder/'environment.json').read_text()),'cases':[], 'longFrames':[]}
    groups={}
    for i,c in enumerate(data['cases']):
        frames=[f for f in c['frames'] if 'nextInterval' in f]
        group=groups.setdefault(c['variant'],[]);group.extend(frames)
        timer0=c['sampleStart']['timerMs'];utc0=c['sampleStart']['utcMs']
        for f in frames:
            if f['nextInterval']<100:continue
            start=utc0+f['probeEnd']-timer0;end=start+f['afterProbe']
            inner=[b for b in buckets if b['start']>=start and b['end']<=end]
            result['longFrames'].append(dict(case=i,variant=c['variant'],frame=f,cpuInterior=inner))
        sampleBuckets=[b for b in buckets if b['start']>=c['sampleStart']['utcMs'] and b['end']<=c['sampleEnd']['utcMs']]
        cpuMean=sum(b['cpuMs'] for b in sampleBuckets)/sum(b['wallMs'] for b in sampleBuckets) if sampleBuckets else None
        summary={k:stats([f[k] for f in frames]) for k in ['nextInterval','rv','afterProbe','nativeNext','otherHandlersNext','probeMs','particles','projectiles']}
        summary.update(index=i,variant=c['variant'],active=c['activeSamples'],shots=c['samplePlayerShotsLowerBound'],enemyShotsLowerBound=c['sampleNativeEnemyShotsLowerBound'],maskInventory=c['maskInventory'],cpuCores=cpuMean,cpuBucketCount=len(sampleBuckets))
        if 'cachePixels' in c:summary['cachePixels']=c['cachePixels']
        summary['display']={point:{'quality':c[point]['quality'],'roots':c[point]['roots'],'nonDefault':[{k:n[k] for k in ['id','parent','name','type','filters','cache','blend','mask','alpha','visible']} for n in c[point]['nodes'] if n['filters'] or n['cache'] or n['blend']!='normal'],'units':c[point]['units']} for point in ['treeStart','treeEnd']}
        result['cases'].append(summary)
    result['groups']={k:{metric:stats([f[metric] for f in fs]) for metric in ['nextInterval','rv','afterProbe','nativeNext','otherHandlersNext','probeMs']} for k,fs in groups.items()}
    if set(['normal','skip-hide','hide-fog','both']).issubset(groups):
        result['interaction']={metric:result['groups']['normal'][metric]['mean']-result['groups']['skip-hide'][metric]['mean']-result['groups']['hide-fog'][metric]['mean']+result['groups']['both'][metric]['mean'] for metric in ['nextInterval','rv','afterProbe']}
        result['interactionHalves']=[]
        for chunk in [result['cases'][:5],result['cases'][5:]]:
            g={c['variant']:c for c in chunk}
            result['interactionHalves'].append({m:g['normal'][m]['mean']-g['skip-hide'][m]['mean']-g['hide-fog'][m]['mean']+g['both'][m]['mean'] for m in ['nextInterval','rv','afterProbe']})
    result['cpuSampler']={'metadata':cpu['metadata'],'queryMs':stats([s['query_duration_ns']/1e6 for s in cpu['samples']]),'delayedBuckets':sum(b['delayed'] for b in buckets)}
    (folder/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'groups':result['groups'],'interaction':result.get('interaction'),'interactionHalves':result.get('interactionHalves'),'cpuSampler':result['cpuSampler']},ensure_ascii=False,indent=2))
    for c in result['cases']:print(c['index'],c['variant'],round(c['nextInterval']['mean'],2),'cpuCores',round(c['cpuCores'],3) if c['cpuCores'] is not None else None,'particles',round(c['particles']['mean'],1),'shots',c['shots'],'enemy',c['enemyShotsLowerBound'])
    for event in sorted(result['longFrames'],key=lambda e:e['frame']['nextInterval'],reverse=True)[:5]:
        f=event['frame'];print('Long frame',event['case'],event['variant'],{k:f[k] for k in ['age','nextInterval','rv','nativeNext','otherHandlersNext','afterProbe']},event['cpuInterior'])
    return result

if __name__=='__main__':analyze(OUT/sys.argv[1])
