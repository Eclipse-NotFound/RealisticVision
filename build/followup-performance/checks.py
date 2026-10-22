"""D38 retains D37 regression fixtures, including the historical whole-field oracle."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/checks.py').read_text(encoding='utf-8')
source=source.replace('native-performance-output','followup-performance-output').replace('D37','D38')
# LazyClassic's D33 oracle intentionally stays whole-field; replacing that oracle
# with D37 without materializing its lazy field would invalidate the comparison.
source=source.replace("MOD/'build/combat-visibility-output/production/src/RVWallSurface.as'","MOD/'build/native-performance-output/production/src/RVWallSurface.as'")
exec(compile(source,str(HERE/'checks.py'),'exec'),globals())
