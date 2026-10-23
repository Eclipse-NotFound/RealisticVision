from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/package.py').read_text(encoding='utf-8').replace('native-performance-output','boundary-load-output').replace('v0.33.4-native-performance','v0.33.7-boundary-performance')
exec(compile(s,str(HERE/'package.py'),'exec'),globals())
