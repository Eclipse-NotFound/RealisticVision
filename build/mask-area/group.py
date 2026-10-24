"""One reservation, sequential build/test steps, no overlapping game or compiler."""
from pathlib import Path
import contextlib,json,runpy,sys,time,traceback
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/mask-area-output'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));sys.path.insert(0,str(HERE))
import test_registry
Registration=test_registry.Registration
def main():
 plan=Path(sys.argv[1]);steps=json.loads(plan.read_text(encoding='utf-8'));logdir=OUT/'group-steps';logdir.mkdir(exist_ok=True)
 # Optional exact older reservations get their turn before this group joins.
 # The shared register currently arbitrates mutual exclusion, not FIFO order.
 older=set(sys.argv[2:]);deadline=time.monotonic()+900
 if older:print('Allow earlier registered tests to finish: '+','.join(sorted(older)),flush=True)
 while older:
  rows=test_registry.Registry().status()
  older={r['id'] for r in rows if r['id'] in older and r['state'] in ('waiting','running','needs-check')}
  if not older:break
  assert time.monotonic()<deadline,'Earlier tests still pending; no game started'
  time.sleep(5)
 with Registration(owner='RealisticVision / D45 顺序对照',purpose=plan.name,run_dir=logdir,evidence=logdir/(plan.stem+'.json'),wait=900) as record:
  test_registry.Registration=lambda **kwargs:contextlib.nullcontext(record)
  results=[]
  try:
   for args in steps:
    log=logdir/(str(time.time_ns())+'-'+args[0]+'.log');print('START '+' '.join(args),flush=True);old=sys.argv[:]
    try:
     sys.argv=[str(HERE/args[0]),*args[1:]]
     with log.open('w',encoding='utf-8') as out,contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):runpy.run_path(str(HERE/args[0]),run_name='__main__')
    except BaseException:
     with log.open('a',encoding='utf-8') as out:traceback.print_exc(file=out)
     print(log.read_text(encoding='utf-8')[-3500:],flush=True);raise
    finally:sys.argv=old
    results.append({'args':args,'log':str(log.relative_to(OUT))});(logdir/(plan.stem+'.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS '+' '.join(args),flush=True)
   record.outcome='passed';record.note='顺序子步骤完成；采用结论另看证据'
  finally:test_registry.Registration=Registration
if __name__=='__main__':main()
