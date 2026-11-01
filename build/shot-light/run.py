"""Isolated native shot-light profile; writes only inside RealisticVision."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/shot-light-output'
sys.path.insert(0,str(HERE));sys.path.insert(1,str(MOD/'build/maximized-flow'))
from profile import once
original=MOD/'build/maximized-flow/run.py'
assert hashlib.sha256(original.read_bytes()).hexdigest()==json.loads((OUT/'inputs.json').read_text())['nativeRunner']
s=original.read_text('utf8').replace('build/maximized-flow-output','build/shot-light-output').replace('RealisticVision / 最大化与重画复用','RealisticVision / 开火照明分段')
s=once(s,"sources=[('rv',BASE),('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')]","sources=[('rv',BASE)]")
s=once(s,"('RealisticVisionMod','LightAndDarknessMod')","('RealisticVisionMod',)")
s=s.replace('from cpu_sampler import OwnedCpuSampler','from build_lad import build_lighting\nfrom profile import instrument_field,instrument_trail,detail_field\nfrom raster import hybrid as raster_hybrid\nfrom geometry import hybrid as geometry_hybrid\nfrom direct_full import hybrid as direct_hybrid\nfrom cpu_sampler import OwnedCpuSampler')
line="selected.append(c[1]);shutil.copytree((OUT/reuse if reuse else OUT/'frozen')/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)"
s=once(s,line,line+"""
    if c[1]=='LightAndDarknessMod':
     if (OUT/'frozen/mods/LightAndDarkness/atmosphere.json').exists():shutil.copyfile(OUT/'frozen/mods/LightAndDarkness/atmosphere.json',folder/'mods/LightAndDarkness/atmosphere.json')
     lighting_source=folder/'lighting-src';is_raster='--raster-verify' in sys.argv or '--raster-pair' in sys.argv
     chosen='direct-circle-candidate/src' if '--direct-circle' in sys.argv else 'geometry-candidate/src' if '--geometry' in sys.argv else 'raster-candidate/src'
     shutil.copytree(OUT/(chosen if is_raster else 'lighting-baseline/src'),lighting_source)
     p=lighting_source/'lad/LadLightField.as'
     if is_raster:
      hybrid_fn=direct_hybrid if '--direct-circle' in sys.argv else geometry_hybrid if '--geometry' in sys.argv else raster_hybrid
      p.write_text(hybrid_fn(p.read_text('utf8'),(OUT/'lighting-baseline/src/lad/LadLightField.as').read_text('utf8'),'--raster-verify' in sys.argv),'utf8',newline='\\n')
      timed=p.read_text('utf8').replace('public var elapsedMs:int = 0;','public var elapsedMs:int = 0;public var frameElapsed:int=0;').replace('data.unlock();elapsedMs=getTimer()-started;','data.unlock();elapsedMs=getTimer()-started;frameElapsed+=elapsedMs;')
      p.write_text(timed,'utf8',newline='\\n')
     else:
      p.write_text(instrument_field(p.read_text('utf8')),'utf8',newline='\\n')
      if '--lights-detail' in sys.argv:p.write_text(detail_field(p.read_text('utf8')),'utf8',newline='\\n')
      p=lighting_source/'lad/LadTrailRaster.as';p.write_text(instrument_trail(p.read_text('utf8')),'utf8',newline='\\n')
     built_light=build_lighting(lighting_source,folder/'lighting-build')
     shutil.copyfile(built_light,folder/'mods/LightAndDarkness/release/LightAndDarknessMod.swf')
""")
marker=" s=(HERE/'SavedFireProbe.as').read_text()"
s=once(s,marker,marker+"""
 s=s.replace("['off','normal','normal','off']","['normal-fixed','normal-moving']")
 s=s.replace('SAMPLE_COUNT=360','SAMPLE_COUNT=180').replace('WARMUP_COUNT=90','WARMUP_COUNT=60')
 if '--lights-detail' in sys.argv:s=s.replace('SAMPLE_COUNT=180','SAMPLE_COUNT=120')
 if '--raster-pair' in sys.argv:
  s=s.replace("['normal-fixed','normal-moving']","['normal-fixed','fast-fixed','fast-fixed','normal-fixed','normal-moving','fast-moving','fast-moving','normal-moving']")
  if '--reverse' in sys.argv:s=s.replace("['normal-fixed','fast-fixed','fast-fixed','normal-fixed','normal-moving','fast-moving','fast-moving','normal-moving']","['fast-fixed','normal-fixed','normal-fixed','fast-fixed','fast-moving','normal-moving','normal-moving','fast-moving']")
 if '--raster-verify' in sys.argv:s=s.replace("['normal-fixed','normal-moving']","['fast-fixed','fast-moving']").replace('SAMPLE_COUNT=180','SAMPLE_COUNT=120')
 s=s.replace('w.gg.setPos(low+80,floor);',"w.gg.setPos(low+80+(row.variant.indexOf('moving')>=0?120*Math.sin(age/25):0),floor);")
 s=s.replace('private var phase:int=0,','private var ladRuntime:*;private var phase:int=0,')
 s=s.replace('var p:Object=plan[index];','var p:Object=plan[index];var lc:*=host.getChildByName("LightAndDarknessCarrier");if(!lc||!lc.ladAPI)throw new Error("lighting carrier missing");ladRuntime=lc.ladAPI.runtime;ladRuntime.setEnabled(false);ladRuntime.setEnabled(true);ladRuntime.atmosphere.settings.projectiles=true;')
 if '--raster-pair' in sys.argv or '--raster-verify' in sys.argv:
  s=s.replace('private function inputFrame(e:Event):void {','private function inputFrame(e:Event):void {if(ladRuntime)ladRuntime.field.frameElapsed=0;')
  s=s.replace('ladRuntime.atmosphere.settings.projectiles=true;','ladRuntime.atmosphere.settings.projectiles=true;ladRuntime.field.rasterOptimized=p.variant.indexOf("fast")>=0;')
  s=s.replace('previousFrame={nativeEnemyShotLowerBound:','previousFrame={lightingTotal:ladRuntime.field.frameElapsed,rasterOptimized:ladRuntime.field.rasterOptimized,lightingMs:ladRuntime.field.elapsedMs,exposure:ladRuntime.lastExposure,nativeEnemyShotLowerBound:')
  s=s.replace('row.sampleEnd={utcMs:','row.rasterChecks=ladRuntime.field.rasterChecks;if(ladRuntime.field.rasterOptimized!=(row.variant.indexOf("fast")>=0))throw new Error("raster variant drift");row.sampleEnd={utcMs:')
  if '--raster-verify' in sys.argv:s=s.replace('row.rasterChecks=ladRuntime.field.rasterChecks;','row.rasterChecks=ladRuntime.field.rasterChecks;if(row.rasterChecks<50)throw new Error("raster check coverage");')
  if '--geometry' in sys.argv:s=s.replace('row.rasterChecks=ladRuntime.field.rasterChecks;','row.geometryReuses=ladRuntime.field.geometryReuses;row.rasterChecks=ladRuntime.field.rasterChecks;')
  if '--direct-circle' in sys.argv:s=s.replace('row.rasterChecks=ladRuntime.field.rasterChecks;','row.directRasters=ladRuntime.field.directRasters;row.rasterChecks=ladRuntime.field.rasterChecks;')
 else:
  s=s.replace('private function inputFrame(e:Event):void {','private function inputFrame(e:Event):void {if(ladRuntime)ladRuntime.field.perfReset();')
  s=s.replace('previousFrame={nativeEnemyShotLowerBound:','previousFrame={lightingProfile:ladRuntime.field.perf.concat(),lightingMs:ladRuntime.field.elapsedMs,exposure:ladRuntime.lastExposure,nativeEnemyShotLowerBound:')
  if '--lights-detail' in sys.argv:s=s.replace('previousFrame={lightingProfile:','previousFrame={lightSources:ladRuntime.field.perfSources,lightingProfile:')
 s=s.replace('if(age==WARMUP_COUNT)row.sampleStart=','if(age==WARMUP_COUNT){if(!ladRuntime.enabled||ladRuntime.atmosphere.settings.projectiles!==true)throw new Error("lighting disabled");row.ladStart={renders:ladRuntime.renders,late:ladRuntime.lateRenders};}if(age==WARMUP_COUNT)row.sampleStart=')
 s=s.replace('row.sampleEnd={utcMs:','row.ladEnd={renders:ladRuntime.renders,late:ladRuntime.lateRenders};row.sampleEnd={utcMs:')
""")
(OUT/'generated-runner.py').write_text(s,'utf8',newline='\n')
exec(compile(s,str(original),'exec'),{'__name__':'__main__','__file__':str(HERE/'run.py')})
