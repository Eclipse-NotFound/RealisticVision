from pathlib import Path
import package
MOD=package.MOD
s=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8').replace('import production as package','import package')
s=s.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='6dbbae60eb09ff8f42d34e31edc92fb9f83009ba918e9145980c6d289723d8ba'")
s=s.replace('settings-recovery','effect-visibility').replace('D35','D42')
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
