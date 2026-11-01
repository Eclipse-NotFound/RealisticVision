from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/performance-survey-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists(), 'Never overwrite a prior census'
assert sha(MOD/'release/RealisticVisionMod.swf')=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
OUT.mkdir()
shutil.copytree(MOD/'build/mask-budget-output/production-combo-v4/src',OUT/'baseline/src')
frozen=OUT/'frozen';frozen.mkdir();shutil.copyfile(GAME/'pfe.swf',frozen/'pfe.swf')
for line in (GAME/'mods/loader-manifest.txt').read_text('utf-8-sig').splitlines():
 c=line.split('|')
 if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):
  shutil.copytree(GAME/'mods'/c[0]/'release',frozen/'mods'/c[0]/'release')
probe=(MOD/'build/maximized-flow/SavedFireProbe.as').read_text('utf8').replace('build/maximized-flow-output','build/performance-survey-output')
assert "['off','normal','normal','off']" in probe
probe=probe.replace("['off','normal','normal','off']","['normal-fixed','normal-moving']").replace('SAMPLE_COUNT=360','SAMPLE_COUNT=180').replace('WARMUP_COUNT=90','WARMUP_COUNT=45')
probe=probe.replace('w.gg.setPos(low+80,floor);',"w.gg.setPos(low+80+(row.variant=='normal-moving'?120*Math.sin(age/25):0),floor);")
probe=probe.replace('var t:int=getTimer();rv.frameCount++;', 'if(age==WARMUP_COUNT){rv.survey={};rv.wallSurface.survey={};rv.profile={};rv.calls={};}\n    var t:int=getTimer();rv.frameCount++;')
probe=probe.replace('row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);','row.survey=rv.survey;row.wallSurvey=rv.wallSurface.survey;row.settings={dim:rv.cfgDim,motionstep:rv.cfgMotionStep,currentsoft:rv.cfgSoftCurrent,maskCurrent:rv.maskBlurCurrent.blurX,maskClassic:rv.maskBlurClassic.blurX};row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);')
(HERE/'SavedFireProbe.as').write_text(probe,'utf8',newline='\n')
files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'inputs.json').write_text(json.dumps({'files':files,'runtime_runner':sha(MOD/'build/maximized-flow/run.py'),'probe_source':sha(MOD/'build/maximized-flow/SavedFireProbe.as')},indent=2)+'\n','utf8')
print('Prepared diagnostic-only census with current frozen package set')
