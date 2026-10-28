"""Single-file replacement with a new backup, exact pins and failure rollback."""
from pathlib import Path
import package
MOD=package.MOD
s=(MOD/'build/regression-recovery/deploy.py').read_text().replace('import production as package','import package')
s=s.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710'")
s=s.replace('settings-recovery','sustained-fire').replace('D35','D54')
s=s.replace("assert run.sha(GAME/'pfe.swf')==proof['host'],'Host changed after validation'", "assert run.sha(GAME/'pfe.swf')==proof['host'],'Host changed after validation'\n        for rel,digest in proof['combination'].items():assert run.sha(GAME/rel)==digest,'Installed combination changed: '+rel")
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':main()
