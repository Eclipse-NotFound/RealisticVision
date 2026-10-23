from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parents[2]/'build/boundary-load-output'
if __name__=='__main__':
 path=OUT/'performance.json';data=json.loads(path.read_text())
 (OUT/'performance-decision.json').write_text(json.dumps({
  'accepted':True,'performance_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'reason':'Classic dense moving masks improve in profiled and unprofiled pairs; native classic mean/P95 improve. Current same-input updates improve modestly; full-frame mean +1.26%, P95 unchanged, maximum lower: treated as essentially unchanged, not a proven whole-frame improvement.',
  'limits':'All tail latency is not solved. Native NPC/world evolution is nondeterministic; no FPS conversion from local replay. Both modes remain slower than RV-off in this fixture. Functional and deployment gates still required.'
 },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
