from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];O=M/'build/enemy-combat-output'
D=O/'candidates/unit_clip/src';assert not D.exists();shutil.copytree(O/'baseline/src',D)
p=D/'RealisticVisionMod.as';s=p.read_text()
old='''         var s2:Shape=rec.m2 as Shape,s3:Shape=rec.m3 as Shape;
         if(!s2.cacheAsBitmap)'''
new='''         var s2:Shape=rec.m2 as Shape,s3:Shape=rec.m3 as Shape;
         if(this.cfgMode=="current"){
            if(rec.bodyDraw==null)rec.bodyDraw={shape:new Shape(),revision:-1};
            if(rec.barDraw==null)rec.barDraw={shape:new Shape(),revision:-1};
            s2=rec.bodyDraw.shape;s3=rec.barDraw.shape;
            this.drawUnitMask(u.vis,s2,rec,rec.bodyDraw);
            this.drawUnitMask(u.hpbar,s3,rec,rec.barDraw);
         }
         if(!s2.cacheAsBitmap)'''
assert s.count(old)==1;s=s.replace(old,new)
marker='      private function refreshMask(rec:Object,bb:Array):void'
helper='''      /** Preserve the complete sampling field. Each target owns its display
       * rectangle, so an extended weapon or a clamped health bar is not cropped
       * to its owner's body. Only integer unscaled parents use the tight path. */
      private function drawUnitMask(visual:DisplayObject,shape:Shape,raster:Object,record:Object):void
      {
         if(visual==null || visual.parent==null)return;
         var clip:Rectangle=null;
         var matrix:Matrix=visual.parent.transform.concatenatedMatrix;
         var origin:Array=String(raster.maskBounds).split(",");
         var x:Number=int(origin[0])*Tile.tileX,y:Number=int(origin[1])*Tile.tileY;
         var scale:Number=Tile.tileX/MASK_SUB;
         var bitmap:BitmapData=raster.m2e as BitmapData;
         if(matrix.a==1 && matrix.d==1 && matrix.b==0 && matrix.c==0
            && matrix.tx==Math.floor(matrix.tx) && matrix.ty==Math.floor(matrix.ty)
            && !this.worldVisualHasFilters(visual)){
            var bounds:Rectangle=visual.getBounds(visual.parent);
            if(isFinite(bounds.x)&&isFinite(bounds.y)&&isFinite(bounds.width)&&isFinite(bounds.height)){
               var left:Number=Math.max(x,(Math.floor(bounds.left/scale)-2)*scale);
               var top:Number=Math.max(y,(Math.floor(bounds.top/scale)-2)*scale);
               var right:Number=Math.min(x+bitmap.width*scale,(Math.ceil(bounds.right/scale)+2)*scale);
               var bottom:Number=Math.min(y+bitmap.height*scale,(Math.ceil(bounds.bottom/scale)+2)*scale);
               clip=new Rectangle(left,top,Math.max(0,right-left),Math.max(0,bottom-top)); // D57_CLIP
            }
         }
         var changed:Boolean=(clip==null)!=(record.clip==null) || (clip!=null && (record.clip==null||!clip.equals(record.clip)));
         if(record.raster!==raster || record.revision!=raster.maskRevision || changed){
            shape.graphics.clear();
            if(clip==null)shape.graphics.copyFrom(Shape(raster.m2).graphics);
            else {
               shape.graphics.beginBitmapFill(bitmap,new Matrix(scale,0,0,scale,x,y),false,true);
               shape.graphics.drawRect(clip.x,clip.y,clip.width,clip.height);shape.graphics.endFill();
            }
            record.raster=raster;record.revision=raster.maskRevision;record.clip=clip;
         }
      }

'''
assert s.count(marker)==1;s=s.replace(marker,helper+marker)
old='''         if(s3 != null && s3.parent != null) { s3.parent.removeChild(s3); }
         rec.lastFov = -1;'''
new='''         if(s3 != null && s3.parent != null) { s3.parent.removeChild(s3); }
         for each(var draw:Object in [rec.bodyDraw,rec.barDraw])if(draw!=null){
            var clipped:Shape=draw.shape as Shape;if(clipped!=null&&clipped.parent!=null)clipped.parent.removeChild(clipped);
         }
         rec.lastFov = -1;'''
assert s.count(old)==1;s=s.replace(old,new)
old='''         if(record.revision != unitRecord.maskRevision)
         {'''
new='''         if(this.cfgMode=="current")this.drawUnitMask(visual,shape,unitRecord,record);
         else if(record.revision != unitRecord.maskRevision)
         {'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('unit_clip candidate prepared; not deployed')
