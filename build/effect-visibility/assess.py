from pathlib import Path
import json,hashlib,statistics,argparse
OUT=Path(__file__).resolve().parents[2]/'build/effect-visibility-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):
 s=sorted(values);return {'mean':round(statistics.mean(s),3),'p95':s[int(.95*(len(s)-1))],'max':max(s)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--accept',action='store_true');a=p.parse_args()
 path=OUT/'native-final-02/evidence/result.json';d=json.loads(path.read_text());assert len(d['cases'])==12 and not d.get('error')
 rows=[]
 for mode in ['current','classic']:
  for v in ['off','baseline','candidate']:
   frames=[f for c in d['cases'] if c['mode']==mode and c['variant']==v for f in c['frames'] if 'nextInterval' in f]
   rows.append({'mode':mode,'variant':v,'interval':stats([f['nextInterval'] for f in frames]),'update':stats([f['rv'] for f in frames])})
 print(json.dumps(rows,indent=2))
 if a.accept:
  target=OUT/'performance-decision.json';assert not target.exists()
  target.write_text(json.dumps({'accepted':True,'native_result':sha(path),'candidate_source':sha(OUT/'candidate/src/RealisticVisionMod.as'),'scope':'D42 correctness fix; full-combination native mercenary shooting and directional movement','reason':'Accept the visibility fix with the measured extra updater cost recorded. Same-session whole-frame results are considered separately from RV update cost; this is not a claim of performance parity with vanilla or elimination of long frames. Native world evolution and warm-up prevent a deterministic FPS causal claim.','measurements':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
