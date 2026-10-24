"""Prepare a fresh D46 fixture; never rebuild the completed release observation."""
from pathlib import Path
import ast,json
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=HERE/'run.py';s=p.read_text(encoding='utf-8')
s=s.replace("s=(HERE/'CombatRenderProbeMod.as').read_text", "s=(HERE/('CombatRenderCandidateProbeMod.as' if candidate else 'CombatRenderProbeMod.as')).read_text")
old="        source.write_text(patch(source.read_text(encoding='utf-8')),encoding='utf-8',newline='\\n')"
assert s.count(old)==1;s=s.replace(old,"        if candidate is None:source.write_text(patch(source.read_text(encoding='utf-8')),encoding='utf-8',newline='\\n')")
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
s=(MOD/'build/mask-area/CombatRenderProbeMod.as').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('D45','D46')
(HERE/'CombatRenderCandidateProbeMod.as').write_text(s,encoding='utf-8',newline='\n')
s=(MOD/'build/mask-area/validate.py').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('d45','d46').replace('D45','D46').replace('tileclip','carry')
needle="  src=folder/'src';r.public(OUT/'candidates'/candidate/'src',src)"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
  source=src/'RealisticVisionMod.as';code=source.read_text(encoding='utf-8')
  code=code.replace('public var worldPass:int = 0;','public var worldPass:int = 0; public var reuseHits:int=0;')
  code=code.replace('rec.coverageFov=this.fovVersion;\\n               return;', '{rec.coverageFov=this.fovVersion;this.reuseHits++;}\\n               return;')
  source.write_text(code,encoding='utf-8',newline='\\n')''')
needle="  (folder/'EffectLoadChecks.as').write_text(test,encoding='utf-8')"
assert s.count(needle)==1
s=s.replace(needle,"  test=test.replace('if(++f>=360){','if(++f>=360){trace(\"CARRY exact-input hits=\"+b.reuseHits);check(b.reuseHits>0,\"coverage reuse path exercised\");')\n"+needle)
needle="  test=test.replace('trace(\"LOAD COMPLETE passed=\"+passed);NativeApplication','removeEventListener(Event.ENTER_FRAME,step);trace(\"LOAD COMPLETE passed=\"+passed);NativeApplication')"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
  # Deliberately advance only the version, preserving the complete input. This
  # is the claimed shortcut; the first pass still exercises changed fields.
  test=test.replace('var ca:BitmapData=imageOf(la)', \'\'\'a.fovVersion++;b.fovVersion++;
   for(var repeatIndex:int=0;repeatIndex<count;repeatIndex++){a.applyWorldVisual(aa[repeatIndex]);b.applyWorldVisual(bb[repeatIndex]);}
   var ca:BitmapData=imageOf(la)\'\'\')''')
ast.parse(s);(HERE/'validate.py').write_text(s,encoding='utf-8',newline='\n')
(HERE/'native-identity.as.inc').write_bytes((MOD/'build/mask-area/native-identity.as.inc').read_bytes())
s=(MOD/'build/mask-area/check_runs.py').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('D45','D46')
(HERE/'check_runs.py').write_text(s,encoding='utf-8',newline='\n')
steps=[['validate.py','dense-build','carry-pixels-01','--candidate','carry'],['validate.py','dense-run','carry-pixels-01'],['validate.py','native-build','carry-native-01','--candidate','carry'],['validate.py','native-run','carry-native-01'],['run.py','build','carry-controlled-01','--full','--controlled','--candidate','carry','--frames','180','--warmup','210'],['run.py','run','carry-controlled-01']]
(HERE/'carry-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Carry strict pixels, native, and paired full-frame steps prepared')
