"""Crop only after rendering the original full mask on the existing pixel lattice."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=MOD/'build/sustained-fire-output/candidates/pixel-cache/src'
dest=OUT/'candidates/raster-crop/src';assert not dest.exists();shutil.copytree(BASE,dest)
(dest.parent/'input.json').write_text(json.dumps({p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*.as')},indent=2)+'\n',encoding='utf-8')
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''            clipLeft=Math.max(0,x0-MASK_PAD_X);clipTop=Math.max(0,y0-MASK_PAD_TOP);
            clipRight=clipLeft+BitmapData(raster.m2e).width/MASK_SUB;clipBottom=clipTop+BitmapData(raster.m2e).height/MASK_SUB;'''
new='''            clipLeft=Math.max(drawX,Math.floor(bounds.left)-2);
            clipTop=Math.max(drawY,Math.floor(bounds.top)-2);
            clipRight=Math.min(drawX+BitmapData(raster.m2e).width*drawScale,Math.ceil(bounds.right)+2);
            clipBottom=Math.min(drawY+BitmapData(raster.m2e).height*drawScale,Math.ceil(bounds.bottom)+2);'''
assert s.count(old)==1;s=s.replace(old,new)
old='shape.graphics.drawRect(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);shape.graphics.endFill();'
assert s.count(old)==1;s=s.replace(old,'shape.graphics.drawRect(clipLeft,clipTop,clipRight-clipLeft,clipBottom-clipTop);shape.graphics.endFill();')
p.write_text(s,encoding='utf-8',newline='\n')
