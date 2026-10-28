"""Summarize startup and actual trigger frames without discarding cold fire."""
from pathlib import Path
import json,sys
MOD=Path(__file__).resolve().parents[2]
for name in sys.argv[1:]:
 p=MOD/'build/solo-fire-output'/name;d=json.loads((p/'evidence/result.json').read_text());groups={};events=[]
 for n,c in enumerate(d['cases']):
  for f in c['allFrames']:
   if 'nextInterval' not in f:continue
   k=c['variant']+('/trigger' if f['trigger'] else '/idle');groups.setdefault(k,[]).append(f['nextInterval'])
   if f['age']%120==60 or f['nextInterval']>80 or f['fireTime']>4:events.append({'case':n,'variant':c['variant'],**f})
 def stat(v):
  v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':max(v)}
 result={'groups':{k:stat(v) for k,v in groups.items()},'events':events}
 (p/'burst-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(name,result['groups'])
 print('First shot / long intervals:',[(f['variant'],f['age'],f['nextInterval'],f['rv'],f['fireTime']) for f in events])
