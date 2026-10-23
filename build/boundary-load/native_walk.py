"""D41 reuses native directional movement, shooting and low-overhead observation."""
from pathlib import Path
import sys,types
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
code=(MOD/'build/long-frame/trace.py').read_text(encoding='utf-8')
code=code[:code.index("if __name__=='__main__':")].replace('long-frame-output','boundary-load-output').replace('D39','D41')
t=types.ModuleType('trace');t.__file__=str(HERE/'trace.py');exec(compile(code,t.__file__,'exec'),t.__dict__)
t.original_source=t.source_probe
body=(MOD/'build/motion-performance/run.py').read_text(encoding='utf-8');body=body[body.index('def run(name):'):body.index('\ndef repeat(')]
body=body.replace('>=6*1024**3','>=5*1024**3').replace('Less than 6 GiB','Less than 5 GiB');exec(body,t.r.__dict__)
sys.modules['trace']=t
code=(MOD/'build/overall-flow/native_walk.py').read_text(encoding='utf-8').replace('overall-flow-output','boundary-load-output').replace("'candidate-05'","'candidate-03'")
exec(compile(code,str(HERE/'native_walk.py'),'exec'),globals())
