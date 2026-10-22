"""Stage D40 investigation only and leave four authority WIP changes unstaged."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/closeout.py').read_text(encoding='utf-8').replace('native-performance','overall-flow').replace('v0334-20261022','20261023').replace('D37','D40').replace('2026-10-22-overall-flow.md','2026-10-23-overall-flow.md')
s=s.replace("'src/RealisticVisionMod.as','src/RVWallSurface.as',",'')
exec(compile(s,str(HERE/'closeout.py'),'exec'),globals())
