from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/closeout.py').read_text(encoding='utf-8').replace('native-performance','boundary-load').replace('v0334','v0337').replace('D37','D41').replace('20261022','20261023').replace('2026-10-22-boundary-load.md','2026-10-23-boundary-load.md')
exec(compile(s,str(HERE/'closeout.py'),'exec'),globals())
