"""One shared reservation covers build, clean timing and validation."""
from pathlib import Path
import contextlib,json,runpy,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];sys.path.insert(0,str(HERE))
import perf
r=perf.r;Registration=r.Registration
name=sys.argv[1];reverse='--reverse' in sys.argv[2:]
with Registration(owner='RealisticVision / D52 双候选战斗',purpose=name,run_dir=perf.OUT/name,evidence=perf.OUT/name/'analysis.json',wait=900) as rec:
 r.Registration=lambda **kw:contextlib.nullcontext(rec)
 try:
  perf.build(name,full=True,large=False,frames=240 if reverse else 180,warmup=210,candidate='classic',controlled=True,reverse=reverse)
  if reverse:
   first=json.loads((perf.OUT/'comparison-01/build.json').read_text())
   second=json.loads((perf.OUT/name/'build.json').read_text())
   assert first['selected']==second['selected'],'Installed selection changed'
   compared=[]
   for rel,digest in first['files'].items():
    if rel.endswith('.swf') and 'CombatRenderProbe' not in Path(rel).parts:
     assert second['files'].get(rel)==digest, 'Installed/test bytes changed: '+rel
     compared.append(rel)
   r.save(perf.OUT/name/'repeat-input-check.json',{'identical':compared,'reference':'comparison-01','reverse':True})
  perf.run(name)
  sys.argv=[str(HERE/'verify-results.py'),'combat',name]
  runpy.run_path(str(HERE/'verify-results.py'),run_name='__main__')
  rec.outcome='passed';rec.note='16窗完整组合对照及加载/输入核对完成，采用结论另判'
 finally:r.Registration=Registration
