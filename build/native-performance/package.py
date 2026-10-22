"""Build only the selected production snapshot, never the authority development tree."""
import importlib.util,sys,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
sys.path.insert(0,str(MOD/'build/regression-recovery'))
spec=importlib.util.spec_from_file_location('d35_package',MOD/'build/regression-recovery/production.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.OUT=MOD/'build/native-performance-output';p.PACKAGE=p.OUT/'production';p.VERSION='v0.33.4-native-performance'
p.run.OUT=p.OUT;p.investigate.OUT=p.OUT;p.investigate.SOURCES['fixed6']=p.OUT/'production-input/src'
run=p.run;OUT=p.OUT;GAME=p.GAME;PACKAGE=p.PACKAGE;VERSION=p.VERSION
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','check']);args=a.parse_args()
 p.build() if args.action=='build' else p.check()
