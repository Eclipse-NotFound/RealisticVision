"""Reuse guarded atomic RV-only deployment; D36 identity and proof are local."""
from pathlib import Path
import package
MOD=package.MOD
source=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8')
source=source.replace('import production as package','import package')
source=source.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='7852f61e083993e69431d5d8ca2fdf3c07d4068715946d04b3e796cecbe86764'")
source=source.replace('settings-recovery','combat-visibility').replace('D35','D36')
source=source[:source.index("if __name__=='__main__':")]
exec(compile(source,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
