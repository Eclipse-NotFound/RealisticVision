"""D54: use the shared 1:1 raster directly as an alpha mask when aligned."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/pixel-cache/src'
OUT=MOD/'build/sustained-fire-output/candidates/direct-cache/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
start=s.index('      private function applyWorldVisual(visual:')
end=s.index('      private function worldScreenMask(',start)
part=s[start:end].replace('var shape:Shape=record.shape as Shape;','var shape:DisplayObject=record.shape as DisplayObject;')
a=part.index('         var clipChanged:Boolean=');b=part.index('         if(shape.parent!==visual.parent)',a)
part=part[:a]+'''         if(crop!=(shape is Bitmap)){
            if(shape.parent!=null)shape.parent.removeChild(shape);
            shape=crop?new Bitmap():new Shape();record.shape=shape;
            record.raster=null;record.revision=-1;
         }
         if(crop){
            var bitmap:Bitmap=shape as Bitmap;
            if(bitmap.bitmapData!==raster.screenMask)bitmap.bitmapData=raster.screenMask;
            if(bitmap.x!==drawX)bitmap.x=drawX;
            if(bitmap.y!==drawY)bitmap.y=drawY;
         }else if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark){
            if(drawDark)Shape(shape).graphics.clear();
            else Shape(shape).graphics.copyFrom(Shape(raster.m2).graphics);
         }
         record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;
''' + part[b:]
s=s[:start]+part+s[end:]
start=s.index('      private function releaseWorldVisual(');end=s.index('      private function disposeWorldMask(',start)
part=s[start:end].replace('var shape:Shape=record.shape as Shape;','var shape:DisplayObject=record.shape as DisplayObject;')
s=s[:start]+part+s[end:]
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
