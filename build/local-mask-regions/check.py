from pathlib import Path
import importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/local-mask-regions-output'
from oracle import instrument
spec=importlib.util.spec_from_file_location('regions_runtime',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();folder.mkdir()
with r.Registration(owner='RealisticVision / 精确区域内容',purpose=sys.argv[1],run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';r.public(OUT/'candidate/src',src)
 p=src/'RealisticVisionMod.as';p.write_text(instrument(p.read_text('utf8')),'utf8',newline='\n')
 base=re.sub(r'\bprivate\b','public',(OUT/'baseline/src/RealisticVisionMod.as').read_text('utf8')).replace('RealisticVisionMod','BaselineVision')
 (src/'BaselineVision.as').write_text(base,'utf8',newline='\n')
 probe=folder/'RegionChecks.as';probe.write_bytes((HERE/'RegionChecks.as').read_bytes())
 (folder/'RegionGrafon.as').write_bytes((HERE/'RegionGrafon.as').read_bytes())
 (folder/'RegionWorld.as').write_bytes((HERE/'RegionWorld.as').read_bytes())
 if '--large' in sys.argv:
  location=(MOD/'build/motion-tests/MotionLocation.as').read_text('utf8').replace('spaceX=24;spaceY=18','spaceX=64;spaceY=30')
  location=location.replace('public var tiles:Array=[];','public var tiles:Array=[];public var space:Array=[];')
  location=location.replace('tiles[x+y*spaceX]=t;','tiles[x+y*spaceX]=t;if(space[x]==null)space[x]=[];space[x][y]=t;')
  (folder/'MotionLocation.as').write_text(location,'utf8',newline='\n')
 r.runner.compile(probe,folder/'RegionChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'RegionChecks.swf',rec,120);ok=code==0 and 'REGION COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':ok,'exit':code});print(log[-1800:]);assert ok
 rec.outcome='passed';rec.note='真实更新函数、全部当前位格及显示消费者对照；非性能排名'
