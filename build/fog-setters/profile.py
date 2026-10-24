"""Original D44 hotspot diagnosis; never a production-performance comparison."""
from pathlib import Path
import importlib.util,json,shutil,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('d49_profile_driver',HERE/'perf.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
name=sys.argv[1];out=d.OUT;target=out/'candidates/profile-base/src'
assert not target.exists();shutil.copytree(d.BASE,target)
original=d.r.fp.instrument
def instrument(source,methods):
 methods=methods+['worldVisualHasFilters','classicLogicRegion','finishCurrentMask','fillLitTile','fillMemoryTile','fillWallTile','recalcTile']
 source=original(source,methods)
 start=source.index('public function profiled_applyWorldVisual(');end=source.index('public function worldVisualHasFilters(',start)
 block=source[start:end];brace=block.index('{')+1;block=block[:brace]+'\nvar segmentStart:int=getTimer();\n'+block[brace:]
 markers=[('         this.refreshMask(raster,[x0,y0,x1,y1]);','worldBounds'),('         // Leave fully lit native visuals untouched.','worldRaster'),('         if(raster.fullyLit)','worldCoverage'),('         if(record==null)\n         {\n            record={shape:','worldSupport')]
 for marker,key in markers:
  assert block.count(marker)==1,marker
  block=block.replace(marker,'profile["'+key+'"] = Number(profile["'+key+'"]||0)+getTimer()-segmentStart;segmentStart=getTimer();\n'+marker)
 return source[:start]+block+source[end:]
d.r.fp.instrument=instrument
with d.r.Registration(owner='RealisticVision / D49 原版热点细分',purpose=name,run_dir=out/name,evidence=out/name/'hotspots.json',wait=900) as record:
 import contextlib
 d.r.Registration=lambda **kwargs:contextlib.nullcontext(record)
 d.build(name,full=True,frames=180,warmup=90,candidate='profile-base',controlled=True,profile=True)
 d.run(name)
 data=json.loads((out/name/'evidence/result.json').read_text())
 summary=[]
 for row in data['cases']:
  assert row['attacks']>0 and row['maxProjectiles']>0
  summary.append({'mode':row['mode'],'profileMsPerSample':{k:round(v/180,4) for k,v in row['profile'].items()},'callsPerSample':{k:round(v/180,2) for k,v in row['calls'].items()},'limitation':'Nested times overlap; instrumentation adds cost. Not deployment performance evidence.'})
 d.r.save(out/name/'hotspots.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
