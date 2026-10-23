from pathlib import Path
import package
MOD=package.MOD
s=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8').replace('import production as package','import package')
s=s.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='83d8e590c062e181b70bd5cabef2200084d5e81aaca081d1d1ebc347205c7e65'")
s=s.replace('settings-recovery','boundary-performance').replace('D35','D41')
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
