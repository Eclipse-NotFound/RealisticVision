"""Summarize complete intervals within each paired combat process."""
from pathlib import Path
import json,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-lifecycle-output'
def stats(values):
 v=sorted(values)
 return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v),'>200':sum(x>200 for x in v)}
for name in sys.argv[1:]:
 folder=OUT/name;d=json.loads((folder/'evidence/result.json').read_text());groups={};windows=[]
 for index,c in enumerate(d['cases']):
  frames=[f for f in c['frames'] if 'nextInterval' in f]
  key=c['mode']+'/'+c['variant'];g=groups.setdefault(key,{'frames':[],'windows':[]});g['frames']+=frames;g['windows'].append(index)
  windows.append({'index':index,'mode':c['mode'],'variant':c['variant'],'frame':stats([f['nextInterval'] for f in frames]),'rv':stats([f['rv'] for f in frames]),'attacks':c['attacks'],'maxProjectiles':c['maxProjectiles']})
 for key,g in groups.items():
  frames=g.pop('frames');g['frame']=stats([f['nextInterval'] for f in frames]);g['rv']=stats([f['rv'] for f in frames]);print(key,json.dumps(g))
 (folder/'paired.json').write_text(json.dumps({'groups':groups,'windows':windows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
