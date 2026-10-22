"""D40 complete-frame comparison and separate overlay-display exclusion."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
code=(MOD/'build/long-frame/trace.py').read_text(encoding='utf-8')
code=code[:code.index("if __name__=='__main__':")].replace('long-frame-output','overall-flow-output').replace('D39','D40')
exec(compile(code,str(HERE/'trace.py'),'exec'),globals())
original_source=source_probe
def probe(short=False):
 s=original_source(short)
 s=s.replace('eventSequence:events,frames:[],','eventSequence:events,frames:[],displayExclusion:'+str(options.exclude).lower()+',')
 s=s.replace('if(++liveAge<330)','if(++liveAge<210)')
 # Complete marker timings surround only synchronous calls. A following start
 # still includes remaining world work, display and scheduling.
 if options.exclude:
  s=s.replace('var view:Rectangle=liveMod.wallViewBounds;', 'if(liveOrder[liveIndex]=="candidate" && liveMod.fogVis)liveMod.fogVis.visible=false;\n            var view:Rectangle=liveMod.wallViewBounds;')
  s=s.replace('["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]','["baseline","candidate","candidate","baseline","baseline","candidate","candidate","baseline"]')
  s=s.replace('liveIndex<6','liveIndex<4')
 if options.battle:
  s=s.replace('scenario="sweep"','scenario="battle"')
 if options.system:
  s=s.replace('lastTrace={viewChanged:', 'lastTrace={epoch:new Date().time,viewChanged:')
 return s
source_probe=probe
# D39 measured this fixture below 1.2 GiB. Match its 5 GiB start gate and retain
# per-second memory samples; final acceptance still requires >=3 GiB available.
body=(MOD/'build/motion-performance/run.py').read_text(encoding='utf-8')
body=body[body.index('def run(name):'):body.index('\ndef repeat(')]
body=body.replace('>=6*1024**3','>=5*1024**3').replace('Less than 6 GiB','Less than 5 GiB')
exec(body,r.__dict__)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run']);a.add_argument('name');a.add_argument('--full',action='store_true');a.add_argument('--exclude',action='store_true');a.add_argument('--battle',action='store_true');a.add_argument('--system',action='store_true');a.add_argument('--candidate',default='candidate-00');options=a.parse_args()
 if options.system:
  import time,psutil
  prior_environment=r.environment
  def observed():
   env=prior_environment();meta=OUT/options.name/'running.json'
   if meta.exists():
    try:
     identity=json.loads(meta.read_text());process=psutil.Process(identity['pid'])
     env['owned']={'pid':process.pid,'cpu':process.cpu_times()._asdict(),'io':process.io_counters()._asdict(),'memory':process.memory_info()._asdict(),'threads':[t._asdict() for t in process.threads()]}
    except (psutil.Error,OSError,ValueError) as error:env['sampleError']=str(type(error).__name__)
   env['sampleEnd']=time.time();return env
  r.environment=observed
  exec(body.replace('stop.wait(1)','stop.wait(0.1)'),r.__dict__)
 build(options.name,options.full,options.candidate,False,True) if options.action=='build' else run(options.name)
