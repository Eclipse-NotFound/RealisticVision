"""Reuse the verified single-file atomic replacement and formal-path smoke."""
from pathlib import Path
import package
MOD=package.MOD
s=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8').replace('import production as package','import package')
s=s.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'","OLD='bf4ac9cd87272b03fae7ec22ee67d045f037362f412ee801cad3f9ba9fe3afef'")
s=s.replace('settings-recovery','mask-binding').replace('D35','D44')
s=s.replace("assert run.sha(GAME/'pfe.swf')==proof['host'],'Host changed after validation'", "assert run.sha(GAME/'pfe.swf')==proof['host'],'Host changed after validation'\n        for rel,digest in proof['combination'].items():assert run.sha(GAME/rel)==digest,'Installed combination changed: '+rel")
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
