from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
code=(MOD/'build/native-performance/weapon.py').read_text(encoding='utf-8').replace('native-performance-output','boundary-load-output').replace("default='candidate-10'","default='candidate-02'")
exec(compile(code,str(HERE/'weapon.py'),'exec'),globals())
