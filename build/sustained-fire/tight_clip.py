"""D54: clip unused mask pixels on an exactly aligned screen lattice only."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/integer/src'
OUT=MOD/'build/sustained-fire-output/candidates/tight/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
old='''            var clipLeft:int=Math.max(0,x0-1),clipTop:int=Math.max(0,y0-1);
            var clipRight:int=Math.min(this.spaceX,x1+2),clipBottom:int=Math.min(this.spaceY,y1+2);
            drawClip=new Rectangle(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);'''
new='''            // Integer parent-to-screen translation preserves the original
            // bitmap sampling phase. Retain two pixels beyond native bounds;
            // transformed/filter-bearing scenes keep the original full mask.
            var clipLeft:int=Math.max(drawX,Math.floor(bounds.left)-2);
            var clipTop:int=Math.max(drawY,Math.floor(bounds.top)-2);
            var clipRight:int=Math.min(drawX+BitmapData(raster.m2e).width*drawScale,Math.ceil(bounds.right)+2);
            var clipBottom:int=Math.min(drawY+BitmapData(raster.m2e).height*drawScale,Math.ceil(bounds.bottom)+2);
            drawClip=new Rectangle(clipLeft,clipTop,clipRight-clipLeft,clipBottom-clipTop);'''
assert s.count(old)==1
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s.replace(old,new),encoding='utf-8',newline='\n')
