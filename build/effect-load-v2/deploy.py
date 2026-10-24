from pathlib import Path
import package
MOD=package.MOD
s=(MOD/'build/regression-recovery/deploy.py').read_text(encoding='utf-8').replace('import production as package','import package')
s=s.replace("OLD='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'", "OLD='0dbe0d7a95b8e496fb393d7fcd75f88d60c34a1d0fabb33266b122e3fa04f2bf'")
s=s.replace('settings-recovery','effect-load').replace('D35','D43')
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
if __name__=='__main__':
 decision=json.loads((OUT/'performance-decision.json').read_text(encoding='utf-8'))
 assert decision['accepted'] and decision['performance']==run.sha(OUT/'performance.json')
 assert decision['swf']==run.sha(CANDIDATE)
 main()
