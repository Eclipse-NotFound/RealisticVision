"""D39 exact D38 baseline, same-input replay and parent-preserving capture."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/followup-performance/measure.py').read_text(encoding='utf-8')
s=s.replace("source=source.replace('native-performance-output','followup-performance-output')", "source=source.replace('native-performance-output','long-frame-output')")
s=s.replace("MOD/'build/native-performance-output/production/src'", "MOD/'build/followup-performance-output/production/src'")
exec(compile(s,str(HERE/'measure.py'),'exec'),globals())
