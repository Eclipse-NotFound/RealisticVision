"""Sequential final checks. Each tool keeps its normal shared registration."""
from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
if __name__=='__main__':
 for command in [
  ['weapon.py','build','weapon-final','--candidate','candidate-03'],
  ['weapon.py','run','weapon-final'],
  ['package.py','build'],
  ['package.py','check'],
 ]:
  subprocess.run([sys.executable,'-X','utf8',str(HERE/command[0]),*command[1:]],cwd=MOD,check=True)
