"""Merge only tested D38 production differences; preserve authority development."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/development.py').read_text(encoding='utf-8')
source=source.replace('D37','D38').replace('build/combat-visibility-output/production/src','build/native-performance-output/production/src')
exec(compile(source,str(HERE/'development.py'),'exec'),globals())
