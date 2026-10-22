"""Reuse the frozen D35 paired driver with new D36 inputs/output only."""
from pathlib import Path
import sys, argparse, importlib.util
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combat-visibility-output'
spec=importlib.util.spec_from_file_location('d35',MOD/'build/regression-recovery/investigate.py')
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
inv.OUT=OUT;inv.r.OUT=OUT
inv.SOURCES['d35']=MOD/'build/regression-recovery-output/production-singlepass/src'
inv.SOURCES['d36']=OUT/'candidate/src'
# Build function's probe output guard points at its historical output. Generate
# a local copy of that function with the guard updated; never change old files.
src=(MOD/'build/regression-recovery/investigate.py').read_text(encoding='utf-8')
start=src.index('def build(');end=src.index('\ndef analyze(',start)
function=src[start:end].replace('/RealisticVision/build/regression-recovery-output/','/RealisticVision/build/combat-visibility-output/')
exec(function,inv.__dict__)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run','analyze']);p.add_argument('name');p.add_argument('--profile',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args()
 if a.action=='build':inv.build(a.name,'d35','d36',a.verify,a.profile,a.live)
 elif a.action=='run':inv.r.run(a.name)
 else:inv.analyze(a.name)
