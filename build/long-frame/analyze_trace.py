"""Only the V2 consecutive-listener interval is used for phase attribution."""
from pathlib import Path
import argparse,json,statistics
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/long-frame-output'
def stats(a):
 if not a:return None
 s=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),2),'p95':s[int(.95*(len(s)-1))],'max':max(a),'over50':sum(x>50 for x in a)}
def analyze(name):
 folder=OUT/name;data=json.loads((folder/'evidence/result.json').read_text());summaries=[]
 version=json.loads((folder/'build.json').read_text()).get('traceVersion',1)
 for c in data['cases']:
  rows=[r for r in c['frames'] if 'nextInterval' in r]
  if version==2:
   assert all(r['rvEnd']-r['rvStart']==r['rv'] and r['rvStart']>=r['liveStart'] and r['nextInterval']>=r['rv'] for r in rows)
  slow=[r for r in rows if r['nextInterval']>50]
  rebuilt=[r for r in rows if r['helperCalls'].get('rebuildSamples',0)]
  summary={'traceVersion':version,'phaseValidity':'V1 EXIT_FRAME mapping rejected; RV timers only' if version==1 else 'consecutive liveStep; outsideRV includes driver, other game work, rendering and scheduling',
    'mode':c['mode'],'variant':c['variant'],'scenario':c['scenario'],'interval':stats([r['nextInterval'] for r in rows]) if version==2 else None,'rv':stats([r['rv'] for r in rows]),'outsideRV':stats([r['outsideRV'] for r in rows]) if version==2 else None,'rebuilt':stats([r['rv'] for r in rebuilt]),'rebuildHelper':stats([r['helper'].get('update',0) for r in rebuilt]),'slowFrames':slow,'top':sorted(rows,key=lambda r:r['rv'],reverse=True)[:5]}
  summaries.append(summary)
  print(json.dumps({k:v for k,v in summary.items() if k not in ['slowFrames','top']},ensure_ascii=False))
  for r in summary['top'][:2]:print(json.dumps(r,ensure_ascii=False))
 (folder/'trace-analysis-v2.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');x=a.parse_args();analyze(x.name)
