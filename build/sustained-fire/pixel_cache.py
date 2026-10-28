"""D54: try sharing an exact 1:1 pre-rasterized mask, without clipping geometry."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/integer-v2/src'
OUT=MOD/'build/sustained-fire-output/candidates/pixel-cache/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
s=s.replace('         // 位图填充绘制进矢量 Shape', '         if(rec.worldRaster)rec.screenInputRevision=int(rec.screenInputRevision)+1;\n         // 位图填充绘制进矢量 Shape')
s=s.replace('clipLeft=Math.max(0,x0-1);clipTop=Math.max(0,y0-1);','clipLeft=Math.max(0,x0-MASK_PAD_X);clipTop=Math.max(0,y0-MASK_PAD_TOP);')
s=s.replace('clipRight=Math.min(this.spaceX,x1+2);clipBottom=Math.min(this.spaceY,y1+2);','clipRight=clipLeft+BitmapData(raster.m2e).width/MASK_SUB;clipBottom=clipTop+BitmapData(raster.m2e).height/MASK_SUB;\n            this.worldScreenMask(raster,drawX,drawY,drawScale);')
s=s.replace('shape.graphics.beginBitmapFill(BitmapData(raster.m2e),new Matrix(drawScale,0,0,drawScale,drawX,drawY),false,true);','shape.graphics.beginBitmapFill(BitmapData(raster.screenMask),new Matrix(1,0,0,1,drawX,drawY),false,false);')
needle='      // All calls in one world pass are synchronous.'
helper='''      private function worldScreenMask(raster:Object,x:Number,y:Number,scale:Number):void
      {
         var source:BitmapData=raster.m2e as BitmapData;
         var target:BitmapData=raster.screenMask as BitmapData;
         var width:int=source.width*scale,height:int=source.height*scale;
         if(target==null || target.width!=width || target.height!=height){
            if(target!=null)target.dispose();
            raster.screenMask=target=new BitmapData(width,height,true,0);
            raster.screenRevision=-1;
         }
         if(raster.screenRevision!==raster.screenInputRevision){
            target.fillRect(target.rect,0);
            target.draw(Shape(raster.m2),new Matrix(1,0,0,1,-x,-y));
            raster.screenRevision=raster.screenInputRevision;
         }
      }

'''
assert s.count(needle)==1;s=s.replace(needle,helper+needle)
s=s.replace('["m2d","m2e","maskInput"]','["m2d","m2e","maskInput","screenMask"]')
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
