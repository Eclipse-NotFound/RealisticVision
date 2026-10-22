"""Retain the D36 native child-weapon regression under the D37 candidate."""
from pathlib import Path
import argparse,importlib.util
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/native-performance-output'
spec=importlib.util.spec_from_file_location('weapon_d36',MOD/'build/combat-visibility/run.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.OUT=OUT;old.r.OUT=OUT
def build(name,candidate):
 source=(MOD/'build/combat-visibility/run.py').read_text(encoding='utf-8')
 text=source[source.index('def build('):source.index('\ndef functional(')]
 text=text.replace('/RealisticVision/build/combat-visibility-output/','/RealisticVision/build/native-performance-output/')
 text=text.replace("OUT/'candidate/src'","OUT/candidate_name/'src'")
 old.candidate_name=candidate
 exec(text,old.__dict__);old.build(name,True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--candidate',default='candidate-10');a=p.parse_args()
 build(a.name,a.candidate) if a.action=='build' else old.functional(a.name)
