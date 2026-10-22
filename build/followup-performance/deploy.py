"""Guarded RV-only replacement, D37 backup, formal smoke, and failure rollback."""
from pathlib import Path
import package
MOD=package.MOD
source=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8')
source=source.replace('import production as package','import package')
source=source.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='187d287b06fea10e6057c8e80287352062cff7577d075181261ddc0d04111272'")
source=source.replace('settings-recovery','followup-performance').replace('D35','D38')
source=source[:source.index("if __name__=='__main__':")]
exec(compile(source,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
