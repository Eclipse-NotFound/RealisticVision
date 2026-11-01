from pathlib import Path
import importlib.util,json,re,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output';HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shot_light_checks',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();folder.mkdir()
with r.Registration(owner='RealisticVision / 开火光带等价',purpose=folder.name,run_dir=folder,evidence=folder/'validation.json',wait=1800) as rec:
 for variant,name in [('lighting-baseline','BaselineTrail'),('candidate','CandidateTrail')]:
  s=(OUT/variant/'src/lad/LadTrailRaster.as').read_text('utf8').replace('package lad {','package {').replace('LadTrailRaster',name)
  s=re.sub(r'\bprivate\b','public',s)
  if variant=='candidate':
   s=s.replace('public static const MAX_VISITS:int=65536;','public static const MAX_VISITS:int=65536;public var fastSame:int=0,fastAdjacent:int=0;')
   s=s.replace('/* SHOT_SAME_CELL */','fastSame++;').replace('/* SHOT_ADJACENT */','fastAdjacent++;')
  (folder/(name+'.as')).write_text(s,'utf8',newline='\n')
 (folder/'TrailChecks.as').write_bytes((HERE/'TrailChecks.as').read_bytes())
 r.runner.compile(folder/'TrailChecks.as',folder/'TrailChecks.swf',[folder])
 r.save(folder/'build.json',{p.name:r.sha(p) for p in folder.iterdir() if p.is_file()})
 code,log=r.air(folder,'TrailChecks.swf',rec,240)
 passed=code==0 and 'TRAIL COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':passed,'exit':code})
 print(log[-2500:]);assert passed
 rec.outcome='passed';rec.note='90000射线、完整光带ARGB及预算/清理对照；局部计时不等于游戏FPS'
