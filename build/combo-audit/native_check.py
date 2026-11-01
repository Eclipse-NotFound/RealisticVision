"""Read-only check of the current host's already-exported main-loop bytecode."""
from pathlib import Path
import sys,importlib.util,hashlib,json
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; MOD=HERE.parents[1];GAME=MOD.parents[1]
CS=GAME/'mods/ContinuousScene/build'
sp=importlib.util.spec_from_file_location('rv_readonly_pcode',CS/'pcode_plan.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
old=CS/'generated/camera-a80-budget-20261031/base.xml'
new=CS/'generated/camera-adaptive-quality-20261101/candidate.xml'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(GAME/'pfe.swf')==sha(new.with_suffix('.swf'))=='8321e4e7068672b2afa1fb17da3d8c21d9e95074a76354aece8b10894e025643'
left=m.abc_methods(old);right=m.abc_methods(new)
checked={}
for key in left:
    if key.startswith(('fe.MainMenu::','MainFE::')):
        a=left[key];b=right[key]
        assert (None if a is None else a[1].attrib)==(None if b is None else b[1].attrib),key
        checked[key]=None if a is None else hashlib.sha256(a[1].attrib['codeBytes'].encode()).hexdigest()
assert any('mainStep' in k for k in checked),list(checked)
dest=MOD/'build/combo-audit-output/native-source';dest.mkdir(exist_ok=True)
data={'host':sha(GAME/'pfe.swf'),'basis':'D58 verified native mainStep protocol; unchanged method bodies in existing FFDec exports',
      'exports':{str(p):sha(p) for p in (old,new)},'methods':checked}
(dest/'checked.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print('Verified',len(checked),'MainMenu/MainFE method bodies')
