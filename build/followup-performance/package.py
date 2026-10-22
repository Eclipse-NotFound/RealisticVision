"""Build the exact six production classes, with the existing real-settings probe."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/package.py').read_text(encoding='utf-8')
source=source.replace('native-performance-output','followup-performance-output').replace('v0.33.4-native-performance','v0.33.5-followup-performance')
exec(compile(source,str(HERE/'package.py'),'exec'),globals())
