"""Keep diagnostics, same-input CPU work and full frame intervals separate."""
from prepare import OUT
import argparse,json,statistics
def stats(v):
 s=sorted(v)
 return {'n':len(s),'mean':round(statistics.mean(s),3),'p95':s[int(.95*(len(s)-1))],'max':max(s),'over50':sum(x>50 for x in s)} if s else None
def main(name):
 root=OUT/name;data=json.loads((root/'evidence/result.json').read_text());out=[]
 for case in data['cases']:
  if 'spec' in case:
   out.append({'spec':case['spec'],'updates':[stats(x) for x in case['updates']],'draws':[stats(x) for x in case['draws']], 'stages':case.get('stages'), 'helper':case.get('helper')})
  else:
   f=case['frames'];rows=[r for r in f if 'nextInterval' in r]
   assert all(r['rvEnd']-r['rvStart']==r['rv'] and r['rvStart']>=r['liveStart'] and r['nextInterval']>=r['rv'] for r in rows)
   groups={'interval':[r['nextInterval'] for r in rows],'rv':[r['rv'] for r in rows],'driver':[r['rvStart']-r['liveStart'] for r in rows],'remaining':[r['nextInterval']-(r['rvEnd']-r['liveStart']) for r in rows],'crossing':[r['rv'] for r in rows if r['viewChanged']]}
   # Only consecutive sequence pairs are aligned; the inter-listener gap is
   # not labelled GPU. It also includes other callbacks and scheduling.
   pairs=[(a,b) for a,b in zip(f,f[1:]) if b['serial']==a['serial']+1 and a['rvEnd']<=b['earlyTime']<=b['liveStart']]
   groups['nextEarlyToLive']=[b['liveStart']-b['earlyTime'] for a,b in pairs]
   groups['rvEndToNextEarly']=[b['earlyTime']-a['rvEnd'] for a,b in pairs]
   out.append({'mode':case['mode'],'variant':case['variant'],'displayExclusion':case.get('displayExclusion',False),**{k:stats(v) for k,v in groups.items()},'longRV':sum(r['rv']>50 for r in rows),'longOutsideRV':sum(r['outsideRV']>50 for r in rows),'top':sorted(rows,key=lambda r:r['nextInterval'],reverse=True)[:6]})
 env=json.loads((root/'environment.json').read_text());summary={'run':name,'minAvailableGiB':min(e['available_bytes'] for e in env)/1024**3,'cases':out,'checks':len(data.get('checks',[]))}
 (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 for c in out:print(json.dumps({k:v for k,v in c.items() if k not in ['top','stages','helper']}))
 print('minAvailableGiB',summary['minAvailableGiB'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');x=a.parse_args();main(x.name)
