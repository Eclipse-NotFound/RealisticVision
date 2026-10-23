from pathlib import Path
import importlib.util,sys,argparse,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
sys.path.insert(0,str(MOD/'build/regression-recovery'))
spec=importlib.util.spec_from_file_location('d42_package',MOD/'build/regression-recovery/production.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.OUT=MOD/'build/effect-visibility-output';p.PACKAGE=p.OUT/'production-final';p.VERSION='v0.33.8-effect-visibility'
p.run.OUT=p.OUT;p.investigate.OUT=p.OUT;p.investigate.SOURCES['fixed6']=p.OUT/'production-final-input/src'
run=p.run;OUT=p.OUT;GAME=p.GAME;PACKAGE=p.PACKAGE;VERSION=p.VERSION
def build():
 assert not (OUT/'production-final-input').exists()
 shutil.copytree(OUT/'candidate/src',OUT/'production-final-input/src')
 path=OUT/'production-final-input/src/RealisticVisionMod.as';s=path.read_text(encoding='utf-8');assert 'v0.33.7-boundary-performance' in s
 path.write_text(s.replace('v0.33.7-boundary-performance',VERSION),encoding='utf-8',newline='\n');p.build()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','check']);x=a.parse_args();build() if x.action=='build' else p.check()
