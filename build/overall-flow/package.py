"""Build the selected six-class snapshot, excluding authority development."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/package.py').read_text(encoding='utf-8').replace('native-performance-output','overall-flow-output').replace('v0.33.4-native-performance','v0.33.7-classic-scan')
exec(compile(s,str(HERE/'package.py'),'exec'),globals())
