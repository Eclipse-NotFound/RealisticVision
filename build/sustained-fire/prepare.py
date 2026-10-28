"""D54 candidate: retain the old raster origin, crop only trailing blank area."""
from pathlib import Path
import shutil,hashlib,json
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/combat-render-output/production-final2/src'
OUT=MOD/'build/sustained-fire-output/candidates/trailing/src'
assert not OUT.exists()
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
# Reuse only the reviewed patch template, not the old runner or outputs.
namespace={}
template=(MOD/'build/mask-area/prepare.py').read_text()
start=template.index("old='''");end=template.index('assert source.count(old)')
exec(template[start:end],namespace)
old,new=namespace['old'],namespace['new']
new=new.replace('var clipLeft:int=Math.max(0,x0-1),clipTop:int=Math.max(0,y0-1);','var clipLeft:int=Math.max(0,x0-MASK_PAD_X),clipTop:int=Math.max(0,y0-MASK_PAD_TOP);')
new=new.replace('var clipRight:int=Math.min(this.spaceX,x1+2),clipBottom:int=Math.min(this.spaceY,y1+2);','var clipRight:int=Math.min(this.spaceX,x1+1),clipBottom:int=Math.min(this.spaceY,y1+1);')
new=new.replace('drawClip=new Rectangle(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);','drawClip=new Rectangle(drawX,drawY,Math.min(BitmapData(raster.m2e).width*drawScale,clipRight*Tile.tileX+2*drawScale-drawX),Math.min(BitmapData(raster.m2e).height*drawScale,clipBottom*Tile.tileY+2*drawScale-drawY)); // D54_TRAILING')
s=(BASE/'RealisticVisionMod.as').read_text();assert s.count(old)==1
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s.replace(old,new),encoding='utf-8',newline='\n')
check=(MOD/'build/solo-fire/check.py').read_text().replace('D53','D54').replace('solo-fire-output','sustained-fire-output').replace('candidates/early-dark/src','candidates/trailing/src').replace('earlyDarkHits','trailingHits').replace('// D53_EARLY_DARK','// D54_TRAILING').replace('EARLY DARK','TRAILING')
# The D53 label inside the replacement expression was changed by the first replace.
check=check.replace('// D54_EARLY_DARK','// D54_TRAILING')
(MOD/'build/sustained-fire/check.py').write_text(check,encoding='utf-8',newline='\n')
print('Prepared trailing-only candidate and strict comparison')
