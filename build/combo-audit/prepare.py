"""Freeze review inputs and derive an isolated D58 replay; never touch release."""
from pathlib import Path
import hashlib, json, shutil, subprocess

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
OUT=MOD/'build/combo-audit-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists(), 'Inputs already frozen'
OUT.mkdir()
inputs={}
for name,path in [('baseline',MOD/'build/effect-mask-origin-output/production'),
                  ('candidate',MOD/'build/mask-budget-output/production-combo-v4')]:
    shutil.copytree(path/'src',OUT/name/'src')
    shutil.copyfile(path/'RealisticVisionMod.swf',OUT/name/'RealisticVisionMod.swf')
    inputs[name]={p.relative_to(path).as_posix():sha(p) for p in path.rglob('*') if p.is_file() and p.suffix in ('.as','.swf')}
assert sha(OUT/'candidate/RealisticVisionMod.swf')==sha(MOD/'release/RealisticVisionMod.swf')=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
inputs['installed']={str(p.relative_to(MOD.parents[1])):sha(p) for p in [MOD/'release/RealisticVisionMod.swf',MOD/'release/config.txt',MOD.parents[1]/'pfe.swf',MOD.parents[1]/'application.xml']}
(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
(OUT/'initial-status.txt').write_bytes(subprocess.check_output(['git','status','--porcelain'],cwd=MOD))
s=(MOD/'build/combat-split/run.py').read_text(encoding='utf-8')
s=s.replace("OUT=MOD/'build/combat-split-output'", "OUT=MOD/'build/combo-audit-output'")
s=s.replace("owner='RealisticVision / D58 存档轻机枪'", "owner='RealisticVision / combo-v4审核',resource='game'")
a=s.index(" sources=[('rv',BASE)]")
b=s.index(' for variant,source in sources:',a)
s=s[:a]+" sources=[('rv',BASE),('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')]\n"+s[b:]
s=s.replace("and c[1]!='RealisticVisionMod':", "and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):")
s=s.replace(" if '--sweep' in sys.argv:", " if '--moving' in sys.argv:s=s.replace('w.gg.setPos(low+80,floor);','w.gg.setPos(low+80+120*Math.sin(age/25),floor);')\n if '--sweep' in sys.argv:")
s=s.replace(" (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')", """ s=s.replace('var w:*=wc[\'w\'];w.ctr.clearAll();', 'host.stage.nativeWindow.activate();var w:*=wc[\'w\'];w.ctr.clearAll();')
 s=s.replace('row={crowd:p.n,','row={windowActive:host.stage.nativeWindow.active,activeSamples:0,crowd:p.n,')
 s=s.replace('var now:int=getTimer();','if(age>=WARMUP_COUNT&&host.stage.nativeWindow.active)row.activeSamples++;var now:int=getTimer();')
 (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')""")
# Use a literal with safe Python quoting for the AS3 snippet.
s=s.replace("s=s.replace('var w:*=wc['w'];w.ctr.clearAll();', 'host.stage.nativeWindow.activate();var w:*=wc['w'];w.ctr.clearAll();')", "s=s.replace(\"var w:*=wc['w'];w.ctr.clearAll();\", \"host.stage.nativeWindow.activate();var w:*=wc['w'];w.ctr.clearAll();\")")
(HERE/'run.py').write_text(s,encoding='utf-8',newline='\n')
p=(MOD/'build/combat-split/SavedFireProbe.as').read_text(encoding='utf-8').replace('/build/combat-split-output/','/build/combo-audit-output/')
(HERE/'SavedFireProbe.as').write_text(p,encoding='utf-8',newline='\n')
compile(s,str(HERE/'run.py'),'exec')
print('Inputs frozen; isolated replay ready')
