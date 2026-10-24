"""Reuse the frozen visibility fixtures, with explicit positive-hit evidence."""
from pathlib import Path
import ast,json
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
assert not (HERE/'validate.py').exists(),'Historical scaffold: preserve frozen D47 checks'
s=(MOD/'build/mask-area/validate.py').read_text(encoding='utf-8').replace('mask-area','frame-attribution').replace('d45','d47').replace('D45','D47').replace('tileclip','identity')
needle="  src=folder/'src';r.public(OUT/'candidates'/candidate/'src',src)"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
  source=src/'RealisticVisionMod.as';code=source.read_text(encoding='utf-8')
  code=code.replace('public var worldPass:int = 0;','public var worldPass:int = 0; public var identityHits:int=0;')
  assert code.count('// D47_IDENTITY_HIT')==1
  source.write_text(code.replace('// D47_IDENTITY_HIT','this.identityHits++;'),encoding='utf-8',newline='\\n')''')
needle="  (folder/'EffectLoadChecks.as').write_text(test,encoding='utf-8')"
assert s.count(needle)==1
s=s.replace(needle,"  test=test.replace('if(++f>=360){','if(++f>=360){trace(\"IDENTITY hits=\"+b.identityHits);check(b.identityHits>0,\"identity mask removal exercised\");')\n"+needle)
ast.parse(s);(HERE/'validate.py').write_text(s,encoding='utf-8',newline='\n')
(HERE/'native-identity.as.inc').write_bytes((MOD/'build/mask-area/native-identity.as.inc').read_bytes())
steps=[['validate.py','dense-build','identity-pixels-01','--candidate','identity'],['validate.py','dense-run','identity-pixels-01'],['validate.py','native-build','identity-native-01','--candidate','identity'],['validate.py','native-run','identity-native-01']]
(HERE/'identity-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Strict image and native identity checks prepared')
