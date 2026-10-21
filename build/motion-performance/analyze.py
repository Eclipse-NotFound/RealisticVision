"""Summarize paired, uninstrumented D33 workloads without claiming game FPS."""
import argparse, json, statistics
import run

def stats(values):
    ordered=sorted(values)
    return {'n':len(values),'mean':round(statistics.mean(values),3),'median':statistics.median(values),'p95':ordered[int(.95*(len(values)-1))],'max':max(values),'over33':sum(x>33 for x in values),'over50':sum(x>50 for x in values)}

def analyze(name):
    folder=run.OUT/name;data=json.loads((folder/'evidence/result.json').read_text());build=json.loads((folder/'build.json').read_text());receipt=json.loads((folder/'last-run.json').read_text())
    assert receipt['exit']==0 and not build['profile'] and not build['verify'] and not build['live']
    rows=[]
    for c in data['cases']:
        totals=[[u+d for u,d in zip(c['updates'][i],c['draws'][i])] for i in [0,1]]
        result={'spec':c['spec'],'update':[stats(v) for v in c['updates']],'draw':[stats(v) for v in c['draws']],'total':[stats(v) for v in totals]}
        result['mean_reduction_percent']=round((1-result['total'][1]['mean']/result['total'][0]['mean'])*100,2)
        rows.append(result)
    samples=json.loads((folder/'environment.json').read_text())
    windows=[(c['measuredStart']/1000-1,c['measuredEnd']/1000+1) for c in data['cases'] if 'measuredStart' in c]
    measured=[s for s in samples if any(lo<=s['time']<=hi for lo,hi in windows)]
    def env_summary(items):
        return {'samples':len(items),'min_available_gib':round(min(s['available_bytes'] for s in items)/1024**3,3) if items else None,'foreign_air_java':[{**s,'processes':[p for p in s['processes'] if p['pid']!=receipt['pid']]} for s in items if any(p['pid']!=receipt['pid'] for p in s['processes'])]}
    result={'run':name,'units':'ms; RV update plus offscreen fog draw, not complete game frame time','scene':data.get('scene'),'rows':rows,'environment':env_summary(samples),'measured_environment':env_summary(measured),'input_sha256':run.sha(folder/'evidence/result.json'),'build_sha256':run.sha(folder/'build.json')}
    run.save(folder/'analysis.json',result)
    print(json.dumps([{'spec':r['spec'],'total':r['total'],'reduction':r['mean_reduction_percent']} for r in rows],ensure_ascii=False,indent=2))

def analyze_live(name):
    folder=run.OUT/name;data=json.loads((folder/'evidence/result.json').read_text())
    receipt=json.loads((folder/'last-run.json').read_text())
    assert receipt['exit']==0 and len(data['cases'])==8
    assert all(c['attackStarts']>0 and c['maxProjectiles']>0 and c['unitsEnd']>0 for c in data['cases'])
    rows=[]
    for mode in ['current','classic']:
        for variant in ['baseline','candidate']:
            cases=[c for c in data['cases'] if c['mode']==mode and c['variant']==variant]
            rows.append({'mode':mode,'variant':variant,'updates':stats(sum([c['updates'] for c in cases],[])),
                         'intervals':stats(sum([c['intervals'] for c in cases],[])),
                         'attacks':sum(c['attackStarts'] for c in cases),'projectiles':max(c['maxProjectiles'] for c in cases)})
    env=json.loads((folder/'environment.json').read_text())
    result={'rows':rows,'boundary':'Native ABBA observation; random scene and evolving combat are not deterministic paired inputs.',
            'min_available_gib':min(s['available_bytes'] for s in env)/1024**3,
            'foreign_air_java':[s for s in env if any(p['pid']!=receipt['pid'] for p in s['processes'])],
            'input_sha256':run.sha(folder/'evidence/result.json'),'build_sha256':run.sha(folder/'build.json')}
    run.save(folder/'live-analysis.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');analyze(p.parse_args().name)
