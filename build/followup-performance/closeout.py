"""Stage only D38, retaining exact raw evidence and four external changes."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/closeout.py').read_text(encoding='utf-8')
source=source.replace('native-performance','followup-performance').replace('v0334','v0335').replace('D37','D38')
exec(compile(source,str(HERE/'closeout.py'),'exec'),globals())
