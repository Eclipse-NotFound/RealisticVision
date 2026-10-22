"""Guarded atomic RV-only deployment, with a new D36 backup and rollback."""
from pathlib import Path
import package
MOD=package.MOD
source=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8')
source=source.replace('import production as package','import package')
source=source.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='ab461ff3bdf77544bfb3e7f45b67265429d52280721fa8b8321ba92be2f23871'")
source=source.replace('settings-recovery','native-performance').replace('D35','D37')
source=source[:source.index("if __name__=='__main__':")]
exec(compile(source,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
