"""Retain the child-weapon leak counterexample and full selected mod combination."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/weapon.py').read_text(encoding='utf-8')
source=source.replace('native-performance-output','followup-performance-output').replace('D37','D38')
exec(compile(source,str(HERE/'weapon.py'),'exec'),globals())
