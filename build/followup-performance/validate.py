"""Run selected final suites sequentially, using each suite's shared registration."""
from pathlib import Path
import argparse,subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
def run(script,*args):subprocess.run([sys.executable,'-X','utf8',str(HERE/script),*args],cwd=MOD,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['performance','weapon']);a=p.parse_args()
 if a.suite=='performance':
  for name,extra in [('timing-final-visible',[]),('native-final',['--live','--native'])]:
   run('measure.py','build',name,'--candidate','candidate-04',*extra);run('measure.py','run',name)
 else:
  run('weapon.py','build','weapon-final','--candidate','candidate-04');run('weapon.py','run','weapon-final')
