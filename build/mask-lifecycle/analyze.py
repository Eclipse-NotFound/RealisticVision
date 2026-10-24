"""Associate measured releases with following complete-frame intervals."""
from pathlib import Path
import hashlib,json,re,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-lifecycle-output'
def stats(rows):
 values=sorted(x['nextInterval'] for x in rows if 'nextInterval' in x)
 return {'n':len(values),'mean':sum(values)/len(values) if values else None,'p95':values[int(.95*(len(values)-1))] if values else None,'max':max(values,default=None),'>100':sum(v>100 for v in values),'>200':sum(v>200 for v in values)}
for name in sys.argv[1:]:
 folder=OUT/name;build=json.loads((folder/'build.json').read_text());result=json.loads((folder/'evidence/result.json').read_text())
 for rel,digest in build['files'].items():assert hashlib.sha256((folder/rel).read_bytes()).hexdigest()==digest,rel
 assert json.loads((folder/'last-run.json').read_text())['exit']==0
 log=(folder/'air-output.log').read_text(encoding='utf-8-sig')
 selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==selected
 assert set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==selected
 assert 'ModLoader[err_' not in log and len(result['cases'])==4
 report={'run':name,'cases':[]}
 for index,case in enumerate(result['cases']):
  assert len(case['frames'])==case['sampleFrames'] and case['attacks']>0 and case['maxProjectiles']>0
  frames=[f for f in case['frames'] if 'nextInterval' in f];released=[f for f in frames if f['releasedRasters']>0]
  near={f['age']+delta for f in released for delta in range(4)}
  row={'index':index,'mode':case['mode'],'all':stats(frames),'actualRelease':stats(released),'releaseOrNext3':stats([f for f in frames if f['age'] in near]),'other':stats([f for f in frames if f['age'] not in near]),'releaseFrames':released,'longFrames':[f for f in frames if f['nextInterval']>200],'retained':case['retained']}
  report['cases'].append(row)
  print(json.dumps({k:v for k,v in row.items() if k not in ['releaseFrames','longFrames','retained']},ensure_ascii=False))
  print('release frames:',[(f['worldPass'],f['releasedRasters'],f['releasedPixels'],f['nextInterval'],f['sweepMs']) for f in released])
  print('long frames:',[(f['worldPass'],f['nextInterval'],f['rv'],f['releasedRasters']) for f in row['longFrames']])
 (folder/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
