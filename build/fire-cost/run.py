"""Pinned isolated native runner. New outputs only; diagnostics never deploy."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/fire-cost-output'
sys.path.insert(0,str(HERE));sys.path.insert(1,str(MOD/'build/maximized-flow'))
from instrument import once
source=MOD/'build/maximized-flow/run.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==json.loads((OUT/'inputs.json').read_text())['runner']
s=source.read_text('utf8').replace('build/maximized-flow-output','build/fire-cost-output').replace('RealisticVision / 最大化与重画复用','RealisticVision / 开火分配与绘制')
chosen=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--source=')),None)
if chosen:
 assert chosen.isidentifier() and (OUT/'candidates'/chosen/'src').is_dir()
 s=s.replace("OUT/'candidate/src'", "OUT/'candidates'/"+repr(chosen)+"/'src'")
elif '--allocation' not in sys.argv:
 s=once(s,"sources=[('rv',BASE),('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')]","sources=[('rv',BASE)]")
if '--allocation' in sys.argv:
 s=once(s,"sources=[('rv',BASE),('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')]","sources=[('rv',BASE)]")
 s=s.replace('from cpu_sampler import OwnedCpuSampler','from instrument import instrument as count_allocations\nfrom cpu_sampler import OwnedCpuSampler')
 s=once(s,'  if plain:\n','  s=count_allocations(s)\n  if plain:\n')
 marker=" s=(HERE/'SavedFireProbe.as').read_text()"
 s=once(s,marker,marker+'''
 s=s.replace("['off','normal','normal','off']","['normal-fixed','normal-moving']")
 s=s.replace('SAMPLE_COUNT=360','SAMPLE_COUNT=240').replace('WARMUP_COUNT=90','WARMUP_COUNT=60')
 s=s.replace('w.gg.setPos(low+80,floor);',"w.gg.setPos(low+80+(row.variant=='normal-moving'?120*Math.sin(age/25):0),floor);")
 s=s.replace('var t:int=getTimer();rv.frameCount++;','rv.fireReset();var t:int=getTimer();rv.frameCount++;')
 s=s.replace('previousFrame={nativeEnemyShotLowerBound:', 'previousFrame={allocation:rv.fireFrame(),nativeEnemyShotLowerBound:')
''')
if '--lighting-cross' in sys.argv:
 assert '--allocation' not in sys.argv and not chosen
 for rel,h in json.loads((OUT/'optional-lad.json').read_text()).items():assert hashlib.sha256((OUT/rel).read_bytes()).hexdigest()==h
 s=once(s,"('RealisticVisionMod','LightAndDarknessMod')","('RealisticVisionMod',)")
 line="selected.append(c[1]);shutil.copytree((OUT/reuse if reuse else OUT/'frozen')/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)"
 s=once(s,line,line+"\n    if c[1]=='LightAndDarknessMod' and (OUT/'frozen/mods/LightAndDarkness/atmosphere.json').exists():shutil.copyfile(OUT/'frozen/mods/LightAndDarkness/atmosphere.json',folder/'mods/LightAndDarkness/atmosphere.json')")
 marker=" s=(HERE/'SavedFireProbe.as').read_text()"
 s=once(s,marker,marker+'''
 s=s.replace("['off','normal','normal','off']","['off','normal','normal-noshotlight','off-noshotlight','off-noshotlight','normal-noshotlight','normal','off']")
 s=s.replace('private var phase:int=0,','private var ladRuntime:*,shotLights:Boolean;private var phase:int=0,')
 s=s.replace('var p:Object=plan[index];', 'var p:Object=plan[index];var ladCarrier:*=host.getChildByName("LightAndDarknessCarrier");if(!ladCarrier||!ladCarrier.ladAPI)throw new Error("lighting carrier missing");ladRuntime=ladCarrier.ladAPI.runtime;ladRuntime.setEnabled(false);ladRuntime.setEnabled(true);shotLights=p.variant.indexOf("noshotlight")<0;ladRuntime.atmosphere.settings.projectiles=shotLights;')
 s=s.replace('if(age==WARMUP_COUNT)row.sampleStart=', 'if(age==WARMUP_COUNT){if(!ladRuntime.enabled||ladRuntime.atmosphere.settings.projectiles!==shotLights)throw new Error("lighting diagnostic not applied");row.ladStart={enabled:ladRuntime.enabled,projectiles:shotLights,renders:ladRuntime.renders,late:ladRuntime.lateRenders,captured:ladRuntime.projectiles.captured,lighting:ladRuntime.lighting.snapshot()};}if(age==WARMUP_COUNT)row.sampleStart=')
 s=s.replace('previousFrame={nativeEnemyShotLowerBound:', 'previousFrame={lightingMs:ladRuntime.field.elapsedMs,lightingPulses:ladRuntime.projectiles.pulseCount,nativeEnemyShotLowerBound:')
 s=s.replace('row.sampleEnd={utcMs:', 'row.ladEnd={enabled:ladRuntime.enabled,projectiles:ladRuntime.atmosphere.settings.projectiles,renders:ladRuntime.renders,late:ladRuntime.lateRenders,captured:ladRuntime.projectiles.captured};row.sampleEnd={utcMs:')
''')
(OUT/'generated-runner.py').write_text(s,'utf8',newline='\n')
exec(compile(s,str(source),'exec'),{'__name__':'__main__','__file__':str(HERE/'run.py')})
