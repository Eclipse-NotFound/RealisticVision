from pathlib import Path
import types,sys,argparse
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/effect-visibility/run.py').read_text(encoding='utf-8').replace('effect-visibility-output','effect-load-output').replace('D42','D43')
s=s[:s.index("if __name__=='__main__':")]
exec(compile(s,str(HERE/'functional.py'),'exec'),globals())
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action');a.add_argument('name');x=a.parse_args();build(x.name,True) if x.action=='build' else execute(x.name)
