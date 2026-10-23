"""Sequential registered checks; does not deploy."""
from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
def task(script,*args):
 print('CHECK',script,*args,flush=True)
 subprocess.run([sys.executable,'-X','utf8',str(HERE/script),*args],check=True)
if __name__=='__main__':
 task('native_walk.py','build','native-final-02','--lean')
 task('native_walk.py','run','native-final-02','--lean')
 task('measure.py','build','safe-final-parent','--candidate','candidate','--verify','--wide')
 task('measure.py','run','safe-final-parent')
 task('package.py','build')
 task('package.py','check')
