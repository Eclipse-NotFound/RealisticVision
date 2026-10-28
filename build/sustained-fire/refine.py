from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/sustained-fire-output/candidates'
source=OUT/'trailing/src';dest=OUT/'trailing-v2/src';assert not dest.exists()
s=(source/'RealisticVisionMod.as').read_text()
s=s.replace('var drawClip:Rectangle=null;','var drawRight:Number=-1,drawBottom:Number=-1;')
old='drawClip=new Rectangle(drawX,drawY,Math.min(BitmapData(raster.m2e).width*drawScale,clipRight*Tile.tileX+2*drawScale-drawX),Math.min(BitmapData(raster.m2e).height*drawScale,clipBottom*Tile.tileY+2*drawScale-drawY)); // D54_TRAILING'
new='drawRight=Math.min(BitmapData(raster.m2e).width*drawScale,clipRight*Tile.tileX+2*drawScale-drawX);drawBottom=Math.min(BitmapData(raster.m2e).height*drawScale,clipBottom*Tile.tileY+2*drawScale-drawY); // D54_TRAILING'
assert old in s;s=s.replace(old,new)
start=s.index('         var clipChanged:Boolean=');end=s.index('\n',start)
s=s[:start]+'         var clipChanged:Boolean=record.drawRight!==drawRight || record.drawBottom!==drawBottom;'+s[end:]
s=s.replace('else if(drawClip!=null){','else if(drawRight>=0){').replace('shape.graphics.drawRect(drawClip.x,drawClip.y,drawClip.width,drawClip.height);','shape.graphics.drawRect(drawX,drawY,drawRight,drawBottom);').replace('record.drawClip=drawClip;','record.drawRight=drawRight;record.drawBottom=drawBottom;')
shutil.copytree(source,dest);(dest/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
print('Prepared numeric clip bookkeeping; same clip geometry')
