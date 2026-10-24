"""D45 tile-aligned mask-area experiment on exact installed D44 source."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output';BASE=MOD/'build/combat-render-output/production-final2/src'
pins=json.loads((OUT/'inputs.json').read_text())
assert all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==sha for p,sha in pins['sources'].items())
dest=OUT/'candidates/tileclip/src';assert not dest.exists()
source=(BASE/'RealisticVisionMod.as').read_text(encoding='utf-8-sig')
old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)
         {
            if(drawDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
new='''         // Keep the old sampling lattice; test whether unused outer tiles
         // can be omitted without changing Flash's cached alpha rendering.
         var drawClip:Rectangle=null;
         var drawX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;
         var drawY:Number=Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY;
         var drawScale:Number=Tile.tileX/MASK_SUB;
         if(!drawDark && !this.worldVisualHasFilters(visual)){
            var clipLeft:int=Math.max(0,x0-1),clipTop:int=Math.max(0,y0-1);
            var clipRight:int=Math.min(this.spaceX,x1+2),clipBottom:int=Math.min(this.spaceY,y1+2);
            drawClip=new Rectangle(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);
         }
         var clipChanged:Boolean=(drawClip==null)!=(record.drawClip==null) || (drawClip!=null && (record.drawClip==null || !drawClip.equals(record.drawClip)));
         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || clipChanged)
         {
            if(drawDark)shape.graphics.clear();
            else if(drawClip!=null){
               shape.graphics.clear();
               shape.graphics.beginBitmapFill(BitmapData(raster.m2e),new Matrix(drawScale,0,0,drawScale,drawX,drawY),false,true);
               shape.graphics.drawRect(drawClip.x,drawClip.y,drawClip.width,drawClip.height);shape.graphics.endFill();
            }
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);
            record.drawClip=drawClip;'''
assert source.count(old)==1
shutil.copytree(BASE,dest)
(dest/'RealisticVisionMod.as').write_text(source.replace(old,new),encoding='utf-8',newline='\n')
print('Prepared exact D44 baseline with tile-aligned crop only')
