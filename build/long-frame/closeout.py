from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/closeout.py').read_text(encoding='utf-8').replace('native-performance','long-frame').replace('v0334','v0336').replace('D37','D39').replace('2026-10-22-long-frame.md','2026-10-22-long-frame-triggers.md')
exec(compile(s,str(HERE/'closeout.py'),'exec'),globals())
