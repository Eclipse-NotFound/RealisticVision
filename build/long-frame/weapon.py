from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/weapon.py').read_text(encoding='utf-8').replace('native-performance-output','long-frame-output').replace('D37','D39')
exec(compile(s,str(HERE/'weapon.py'),'exec'),globals())
