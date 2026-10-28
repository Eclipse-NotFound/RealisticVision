"""Freeze the validated D54 current-only code as an exact six-class package."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
# Reuse the exact-package and isolated settings checks, rebinding every output.
s=(MOD/'build/combat-render/package.py').read_text()
s=s.replace("HERE/'run.py'", "MOD/'build/combat-render/run.py'")
s=s.replace("run=d.r;OUT=d.OUT;GAME=d.GAME;PACKAGE=OUT/'production-final2';VERSION='v0.33.10-render-cache'", "run=d.r;OUT=MOD/'build/sustained-fire-output';GAME=d.GAME;PACKAGE=OUT/'production';VERSION='v0.33.11-trailing-cache'")
s=s.replace("OUT/'candidates/bindings/src'", "OUT/'candidates/trailing-current/src'")
s=s.replace('v0.33.9-effect-load','v0.33.10-render-cache').replace('D44','D54')
s=s.replace("resource='offline'", "resource='game',wait=900")
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(HERE/'package.py'),'exec'),globals())
if __name__=='__main__':{'build':build,'inspect':inspect,'check':check}[sys.argv[1]]()
