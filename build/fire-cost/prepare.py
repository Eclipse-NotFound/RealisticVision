from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/fire-cost-output'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
assert sha(MOD/'release/RealisticVisionMod.swf')=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
OUT.mkdir();shutil.copytree(MOD/'build/mask-budget-output/production-combo-v4/src',OUT/'baseline/src')
frozen=OUT/'frozen';frozen.mkdir();shutil.copyfile(GAME/'pfe.swf',frozen/'pfe.swf')
for line in (GAME/'mods/loader-manifest.txt').read_text('utf-8-sig').splitlines():
 c=line.split('|')
 if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):
  shutil.copytree(GAME/'mods'/c[0]/'release',frozen/'mods'/c[0]/'release')
probe=(MOD/'build/maximized-flow/SavedFireProbe.as').read_text('utf8').replace('build/maximized-flow-output','build/fire-cost-output')
(HERE/'SavedFireProbe.as').write_text(probe,'utf8',newline='\n')
(OUT/'inputs.json').write_text(json.dumps({'files':{p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()},'runner':sha(MOD/'build/maximized-flow/run.py')},indent=2)+'\n','utf8',newline='\n')
print('Frozen accurate production source and current package set')
