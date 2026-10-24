from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/effect-visibility/package.py').read_text(encoding='utf-8').replace('effect-visibility-output','effect-load-v2-output').replace('v0.33.8-effect-visibility','v0.33.9-effect-load').replace('v0.33.7-boundary-performance','v0.33.8-effect-visibility')
exec(compile(s,str(HERE/'package.py'),'exec'),globals())
