from prepare import MOD,OUT
import json,statistics
def stats(v):
 s=sorted(v);return [round(statistics.mean(s),2),s[int(.95*(len(s)-1))],max(s)] if s else None
records=[]
for name in ['trace-final','trace-full-01']:
 data=json.loads((MOD/'build/long-frame-output'/name/'evidence/result.json').read_text())
 for c in data['cases']:
  rows=c['frames'];out={'run':name,'mode':c['mode'],'variant':c['variant'],'scenario':c['scenario'],'rv':stats([x['rv'] for x in rows])}
  if name=='trace-final':
   rows=[x for x in rows if 'nextInterval' in x];out.update(driver=stats([x['rvStart']-x['liveStart'] for x in rows]),afterRV=stats([x['nextInterval']-(x['rvEnd']-x['liveStart']) for x in rows]),interval=stats([x['nextInterval'] for x in rows]))
  else:
   for group in ['rvStages','helper']:
    out[group]={k:stats([x[group].get(k,0) for x in rows]) for k in sorted(set().union(*(x[group].keys() for x in rows)))}
  records.append(out);print(json.dumps(out))
 (OUT/'prior-analysis.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
