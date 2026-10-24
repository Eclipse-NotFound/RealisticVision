from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/effect-visibility/closeout.py').read_text(encoding='utf-8').replace('effect-visibility-v0338-20261023','effect-load-v0339-20261024').replace('2026-10-23-effect-visibility.md','2026-10-24-effect-load.md').replace('build/effect-visibility','build/effect-load').replace('D42','D43')
exec(compile(s,str(HERE/'closeout.py'),'exec'),globals())
