"""Crop all blank sides only on the unchanged screen pixel lattice."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];BASE=MOD/'build/combat-render-output/production-final2/src';OUT=MOD/'build/sustained-fire-output/candidates/integer/src';assert not OUT.exists()
template=(MOD/'build/mask-area/prepare.py').read_text();ns={}
exec(template[template.index("old='''"):template.index('assert source.count(old)')],ns)
old,new=ns['old'],ns['new']
new=new.replace('var drawClip:Rectangle=null;','var drawClip:Rectangle=null;\n         var screenMatrix:Matrix=visual.parent.transform.concatenatedMatrix;')
new=new.replace('if(!drawDark && !this.worldVisualHasFilters(visual)){','if(this.cfgMode=="current" && !drawDark && screenMatrix.a==1 && screenMatrix.d==1 && screenMatrix.b==0 && screenMatrix.c==0 && screenMatrix.tx==Math.floor(screenMatrix.tx) && screenMatrix.ty==Math.floor(screenMatrix.ty) && !this.worldVisualHasFilters(visual)){ // D54_TRAILING')
s=(BASE/'RealisticVisionMod.as').read_text();assert s.count(old)==1
shutil.copytree(BASE,OUT);(OUT/'RealisticVisionMod.as').write_text(s.replace(old,new),encoding='utf-8',newline='\n')
