from prepare import OUT
from analyze import stats
import json,bisect
def main(name='system-battle'):
 root=OUT/name;data=json.loads((root/'evidence/result.json').read_text());env=json.loads((root/'environment.json').read_text())
 samples=[x for x in env if 'owned' in x];times=[x['time']*1000 for x in samples];rows=[];aggregate=[]
 for c in data['cases']:
  offsets=[x['epoch']-x['rvEnd'] for x in c['frames']];assert max(offsets)-min(offsets)<=5
  for f in c['frames']:
   if 'nextInterval' not in f or f['nextInterval']<100:continue
   start=f['epoch']-f['rvEnd']+f['liveStart'];end=start+f['nextInterval']
   lo=bisect.bisect_right(times,start)-1;hi=bisect.bisect_left(times,end)
   if lo<0 or hi>=len(samples):continue
   a,b=samples[lo],samples[hi];assert a['owned']['pid']==b['owned']['pid']
   cpu=lambda x:sum(x['owned']['cpu'][k] for k in ['user','system'])
   ta={t['id']:t['user_time']+t['system_time'] for t in a['owned']['threads']};tb={t['id']:t['user_time']+t['system_time'] for t in b['owned']['threads']}
   delta={str(t):round(1000*(tb[t]-ta[t]),3) for t in ta.keys()&tb.keys()}
   rows.append({'mode':c['mode'],'variant':c['variant'],'age':f['age'],'interval':f['nextInterval'],'rv':f['rv'],'outside':f['outsideRV'],'objects':f['objects'],'projectiles':f['projectiles'],'memoryChangeInRV':f['memoryAfter']-f['memoryBefore'],'samplingStartSpanMs':round(1000*(b['time']-a['time']),3),'processCPUObservedDeltaMs':round(1000*(cpu(b)-cpu(a)),3),'largestThreadMs':max(delta.values(),default=0),'threadCPU':delta,'ioDelta':{k:b['owned']['io'][k]-a['owned']['io'][k] for k in a['owned']['io']},'pageFaultDelta':b['owned']['memory'].get('num_page_faults',0)-a['owned']['memory'].get('num_page_faults',0)})
 for mode in ['current','classic']:
  for variant in ['off','baseline','candidate']:
   frames=[f for c in data['cases'] if c['mode']==mode and c['variant']==variant for f in c['frames'] if 'nextInterval' in f]
   aggregate.append({'mode':mode,'variant':variant,'interval':stats([r['nextInterval'] for r in frames]),'rv':stats([r['rv'] for r in frames]),'outside':stats([r['outsideRV'] for r in frames])})
 summary={'status':'diagnostic-insufficient-not-performance-acceptance','aggregate':aggregate,'sampleCount':len(samples),'maxSampleDurationMs':max(x['sampleEnd']-x['time'] for x in env)*1000,'longFrames':sorted(rows,key=lambda x:x['interval'],reverse=True),'note':'Corrects system-analysis.json: environment time precedes process enumeration, CPU reads occur later within sampleEnd. The costly observer reached 263 ms and may perturb playback. CPU deltas are NOT upper bounds for a particular frame and do not establish GC, GPU or scheduling causes. Original raw files retained; exclude this run from release performance acceptance.'}
 (root/'system-analysis-corrected.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({**summary,'longFrames':[{k:v for k,v in x.items() if k!='threadCPU'} for x in summary['longFrames'][:8]]},indent=2))
if __name__=='__main__':main()
