from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/overall-flow/measure.py').read_text(encoding='utf-8').replace('overall-flow-output','effect-load-v2-output').replace('candidate-00','baseline')
exec(compile(s,str(HERE/'measure.py'),'exec'),globals())
