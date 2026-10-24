"""Only report verified partitions, never call the residual pure GPU time."""
from pathlib import Path
import hashlib,json,re,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/frame-attribution-output'
def stat(values):
 v=sorted(values);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v),'>200':sum(x>200 for x in v)}
for name in sys.argv[1:]:
 folder=OUT/name;build=json.loads((folder/'build.json').read_text());d=json.loads((folder/'evidence/result.json').read_text())
 for rel,digest in build['files'].items():assert hashlib.sha256((folder/rel).read_bytes()).hexdigest()==digest,rel
 assert json.loads((folder/'last-run.json').read_text())['exit']==0
 log=(folder/'air-output.log').read_text(encoding='utf-8-sig');selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==selected
 assert 'ModLoader[err_' not in log and 'D47 COMPLETE' in log and len(d['cases'])==16
 groups={};windows=[];long=[]
 keys=['nextInterval','nativeNext','otherHandlersNext','afterProbe','probeMs','rv','diagnosticMs']
 for i,c in enumerate(d['cases']):
  assert len(c['frames'])==c['sampleFrames']
  if c['crowd']>0:assert c['attacks']>0 and c['maxProjectiles']>0
  frames=[f for f in c['frames'] if 'nextInterval' in f]
  for f in frames:
   assert f['worldStepsNext']==1
   assert f['probeMs']+f['nativeNext']+f['otherHandlersNext']+f['afterProbe']==f['nextInterval']
   assert min(f[k] for k in keys)>=0
  group=str(c['crowd'])+'/'+c['mode']+'/'+c['variant'];groups.setdefault(group,[]).extend(frames)
  windows.append({'window':i,'group':group,'stats':{k:stat([f[k] for f in frames]) for k in keys},'attacks':c['attacks'],'maxProjectiles':c['maxProjectiles']})
  long += [{'window':i,'group':group,**f} for f in frames if f['nextInterval']>150]
 summary={g:{k:stat([f[k] for f in frames]) for k in keys} for g,frames in groups.items()}
 result={'groups':summary,'windows':windows,'longFrames':long,'limits':'afterProbe includes rendering, other events, pre-native handlers, frame pacing and scheduling; not pure GPU time. Native is the directly wrapped mainStep call; RV is a subset of probeMs.'}
 (folder/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 for g,r in summary.items():print(g,json.dumps({k:round(v['mean'],2) for k,v in r.items()}),'max',r['nextInterval']['max'])
 print('longest intervals:',json.dumps(sorted(long,key=lambda f:f['nextInterval'],reverse=True)[:8],ensure_ascii=False))
