"""Pair each frame's RV update with its next arrival, retain every run/window."""
from pathlib import Path
import hashlib,json,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
def stat(values):
 v=sorted(values);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
results={}
for name in sys.argv[1:]:
 path=OUT/name/'evidence/result.json';data=json.loads(path.read_text());groups={};windows=[]
 for index,c in enumerate(data['cases']):
  frames=[f for f in c['frames'] if 'nextInterval' in f]
  assert frames and len(frames)==c['sampleFrames']-1
  if c['crowd']>0:assert c['attacks']>0 and c['maxProjectiles']>0,(name,index)
  key=f"{c['crowd']}/{c['mode']}/{c['variant']}"
  g=groups.setdefault(key,{'intervals':[],'rv':[],'diagnostic':[],'windows':[]})
  g['intervals'] += [f['nextInterval'] for f in frames];g['rv'] += [f['rv'] for f in frames];g['diagnostic'] += [f['diagnosticMs'] for f in frames];g['windows'].append(index)
  windows.append({'index':index,'key':key,'frame':stat([f['nextInterval'] for f in frames]),'rv':stat([f['rv'] for f in frames]),'attacks':c['attacks'],'maxProjectiles':c['maxProjectiles'],'maxParticles':c['maxParticles'],'retained':c['retained']})
 results[name]={'source':hashlib.sha256(path.read_bytes()).hexdigest(),'scene':data['scene'],'groups':{k:{'frame':stat(g['intervals']),'rv':stat(g['rv']),'diagnostic':stat(g['diagnostic']),'windows':g['windows']} for k,g in groups.items()},'windows':windows}
 for k,g in results[name]['groups'].items():print(name,k,json.dumps(g,ensure_ascii=False))
(OUT/'performance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
