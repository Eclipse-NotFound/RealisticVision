"""Final D39 suites; every native/JVM group uses the official registry."""
from pathlib import Path
import argparse,subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
def run(script,*args):subprocess.run([sys.executable,'-X','utf8',str(HERE/script),*args],cwd=MOD,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['pixels','performance','weapon']);a=p.parse_args()
 if a.suite=='pixels':
  run('helper.py','helper-final','--candidate','candidate-04')
  for name,extra in [('exact-final-parent',[]),('wide-final-parent',['--wide'])]:
   run('measure.py','build',name,'--candidate','candidate-04','--verify',*extra);run('measure.py','run',name)
 elif a.suite=='performance':
  run('measure.py','build','timing-final-visible','--candidate','candidate-04');run('measure.py','run','timing-final-visible')
  run('trace.py','build','trace-final','--candidate','candidate-04','--full','--unprofile');run('trace.py','run','trace-final')
 else:
  run('weapon.py','build','weapon-final','--candidate','candidate-04');run('weapon.py','run','weapon-final')
