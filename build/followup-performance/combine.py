"""Candidate 04 combines the independently tested logic-block and support-run changes."""
from pathlib import Path
import shutil
from logic_blocks import transform
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output'
if __name__=='__main__':
 dest=OUT/'candidate-04/src';assert not dest.exists();shutil.copytree(OUT/'candidate-03/src',dest)
 f=dest/'RealisticVisionMod.as';f.write_text(transform(f.read_text(encoding='utf-8-sig')),encoding='utf-8',newline='\n')
