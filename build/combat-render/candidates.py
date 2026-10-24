"""D44 disposable candidates, always derived from the installed D43 source."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/effect-load-v3-output/production-final/src'
OUT=MOD/'build/combat-render-output/candidates'

def prepare(name):
    dest=OUT/name/'src'
    assert not dest.exists(), 'Never overwrite a frozen candidate'
    source=(BASE/'RealisticVisionMod.as').read_text(encoding='utf-8-sig')
    assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='563c3833fd58429c4a00d251f17ad4c26e916213af4259d3f066bfbf302af74e'
    if name=='guard':
        replacements={
          's2.cacheAsBitmap=true;s3.cacheAsBitmap=true;':'if(!s2.cacheAsBitmap)s2.cacheAsBitmap=true;if(!s3.cacheAsBitmap)s3.cacheAsBitmap=true;',
          'u.vis.cacheAsBitmap=true;u.vis.mask=s2;':'if(!u.vis.cacheAsBitmap)u.vis.cacheAsBitmap=true;if(u.vis.mask!==s2)u.vis.mask=s2;',
          'u.hpbar.cacheAsBitmap=true;u.hpbar.mask=s3;':'if(!u.hpbar.cacheAsBitmap)u.hpbar.cacheAsBitmap=true;if(u.hpbar.mask!==s3)u.hpbar.mask=s3;',
          'visual.cacheAsBitmap=true;visual.mask=shape;':'if(!visual.cacheAsBitmap)visual.cacheAsBitmap=true;if(visual.mask!==shape)visual.mask=shape;',
          'shape.cacheAsBitmap=!raster.fullyDark;visual.cacheAsBitmap=raster.fullyDark?record.cache:true;visual.mask=shape;':
          'if(shape.cacheAsBitmap!==!raster.fullyDark)shape.cacheAsBitmap=!raster.fullyDark;\n         var useCache:Boolean=raster.fullyDark?record.cache:true;\n         if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;\n         if(visual.mask!==shape)visual.mask=shape;'
        }
        for a,b in replacements.items():
            assert source.count(a)==1,a
            source=source.replace(a,b)
    elif name=='bitmap':
        source=(OUT/'guard/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        start=source.index('      private function applyWorldVisual(visual:DisplayObject):void')
        end=source.index('      private function disposeWorldMask(',start)
        part=source[start:end]
        replacements={
          'record={shape:new Shape(),baseMask:':'record={shape:new Bitmap(null,"never",true),baseMask:',
          'var shape:Shape=record.shape as Shape;':'var shape:Bitmap=record.shape as Bitmap;',
          'if(raster.fullyDark)shape.graphics.clear();\n            else shape.graphics.copyFrom(Shape(raster.m2).graphics);':
          'shape.bitmapData=raster.fullyDark?null:BitmapData(raster.m2e);\n            shape.scaleX=Tile.tileX/MASK_SUB;shape.scaleY=Tile.tileY/MASK_SUB;\n            shape.x=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;\n            shape.y=Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY;'
        }
        for a,b in replacements.items():
            assert part.count(a)==(2 if a=='var shape:Shape=record.shape as Shape;' else 1),(a,part.count(a))
            part=part.replace(a,b)
        source=source[:start]+part+source[end:]
    elif name=='trim':
        source=(OUT/'guard/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        start=source.index('      private function applyWorldVisual(visual:DisplayObject):void')
        end=source.index('      private function releaseWorldVisual(',start)
        part=source[start:end]
        old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==raster.fullyDark)
         {
            if(raster.fullyDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
        new='''         var drawClip:Rectangle=null;
         var drawX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;
         var drawY:Number=Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY;
         var drawScale:Number=Tile.tileX/MASK_SUB;
         if(!raster.fullyDark && !this.worldVisualHasFilters(visual)){
            drawClip=new Rectangle(Math.floor(bounds.left)-2,Math.floor(bounds.top)-2,
               Math.ceil(bounds.right)-Math.floor(bounds.left)+4,Math.ceil(bounds.bottom)-Math.floor(bounds.top)+4);
            drawClip=drawClip.intersection(new Rectangle(drawX,drawY,BitmapData(raster.m2e).width*drawScale,BitmapData(raster.m2e).height*drawScale));
         }
         var clipChanged:Boolean=(drawClip==null)!=(record.drawClip==null) || (drawClip!=null && (record.drawClip==null || !drawClip.equals(record.drawClip)));
         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==raster.fullyDark || clipChanged)
         {
            if(raster.fullyDark)shape.graphics.clear();
            else if(drawClip!=null){
               shape.graphics.clear();
               shape.graphics.beginBitmapFill(BitmapData(raster.m2e),new Matrix(drawScale,0,0,drawScale,drawX,drawY),false,true);
               shape.graphics.drawRect(drawClip.x,drawClip.y,drawClip.width,drawClip.height);shape.graphics.endFill();
            }
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);
            record.drawClip=drawClip;'''
        assert part.count(old)==1
        part=part.replace(old,new)
        helper='''      private function worldVisualHasFilters(visual:DisplayObject):Boolean
      {
         if(visual.filters.length>0)return true;
         var container:DisplayObjectContainer=visual as DisplayObjectContainer;
         if(container!=null)for(var i:int=0;i<container.numChildren;i++)
            if(this.worldVisualHasFilters(container.getChildAt(i)))return true;
         return false;
      }

'''
        source=source[:start]+part+helper+source[end:]
    elif name=='support':
        source=(OUT/'guard/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        start=source.index('      private function applyWorldVisual(visual:DisplayObject):void')
        end=source.index('      private function releaseWorldVisual(',start)
        part=source[start:end];cut=part.index('         if(record==null)\n         {\n            record={shape:new Shape()')
        prefix='''         var drawDark:Boolean=raster.fullyDark;
         if(!drawDark && !this.worldVisualHasFilters(visual)){
            var supportData:BitmapData=raster.m2e as BitmapData;
            var supportX:int=(x0-Math.max(0,x0-MASK_PAD_X))*MASK_SUB;
            var supportY:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*MASK_SUB;
            // Include neighbouring low-resolution samples used by bilinear
            // smoothing. Filtered descendants keep the complete old support.
            var supportRect:Rectangle=new Rectangle(supportX-1,supportY-1,(x1-x0+1)*MASK_SUB+2,(y1-y0+1)*MASK_SUB+2).intersection(supportData.rect);
            drawDark=!supportData.hitTest(this.fogPoint,1,supportRect);
         }
'''
        part=part[:cut]+prefix+part[cut:].replace('raster.fullyDark','drawDark')
        helper='''      private function worldVisualHasFilters(visual:DisplayObject):Boolean
      {
         if(visual.filters.length>0)return true;
         var container:DisplayObjectContainer=visual as DisplayObjectContainer;
         if(container!=null)for(var i:int=0;i<container.numChildren;i++)
            if(this.worldVisualHasFilters(container.getChildAt(i)))return true;
         return false;
      }

'''
        source=source[:start]+part+helper+source[end:]
    elif name=='support2':
        source=(OUT/'support/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        source=source.replace('      private var worldMasks:Object = {};','      private var worldMasks:Object = {};\n      private var worldSupportRect:Rectangle = new Rectangle();')
        old='''         if(!drawDark && !this.worldVisualHasFilters(visual)){
            var supportData:BitmapData=raster.m2e as BitmapData;
            var supportX:int=(x0-Math.max(0,x0-MASK_PAD_X))*MASK_SUB;
            var supportY:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*MASK_SUB;
            // Include neighbouring low-resolution samples used by bilinear
            // smoothing. Filtered descendants keep the complete old support.
            var supportRect:Rectangle=new Rectangle(supportX-1,supportY-1,(x1-x0+1)*MASK_SUB+2,(y1-y0+1)*MASK_SUB+2).intersection(supportData.rect);
            drawDark=!supportData.hitTest(this.fogPoint,1,supportRect);
         }'''
        new='''         if(!drawDark){
            var supportData:BitmapData=raster.m2e as BitmapData;
            var supportX:int=(x0-Math.max(0,x0-MASK_PAD_X))*MASK_SUB;
            var supportY:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*MASK_SUB;
            // Keep bilinear neighbours, reusing one synchronous scratch rect.
            this.worldSupportRect.x=Math.max(0,supportX-1);
            this.worldSupportRect.y=Math.max(0,supportY-1);
            this.worldSupportRect.width=Math.min(supportData.width,supportX+(x1-x0+1)*MASK_SUB+1)-this.worldSupportRect.x;
            this.worldSupportRect.height=Math.min(supportData.height,supportY+(y1-y0+1)*MASK_SUB+1)-this.worldSupportRect.y;
            // Reading filters clones their array. Inspect that tree only when
            // the alpha test has established a possible transparent shortcut.
            if(!supportData.hitTest(this.fogPoint,1,this.worldSupportRect) && !this.worldVisualHasFilters(visual))drawDark=true;
         }'''
        assert source.count(old)==1
        source=source.replace(old,new)
    elif name=='bindings':
        source=(OUT/'support2/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        replacements={
            'u.vis.mask = null;':'if(u.vis.mask != null)u.vis.mask = null;',
            'u.vis.cacheAsBitmap = false;':'if(u.vis.cacheAsBitmap)u.vis.cacheAsBitmap = false;',
            'u.hpbar.mask = null;':'if(u.hpbar.mask != null)u.hpbar.mask = null;',
            'u.hpbar.cacheAsBitmap = false;':'if(u.hpbar.cacheAsBitmap)u.hpbar.cacheAsBitmap = false;',
            'u.vis.visible = false;':'if(u.vis.visible)u.vis.visible = false;',
            'u.hpbar.visible = false;':'if(u.hpbar.visible)u.hpbar.visible = false;',
            'u.vis.visible = true;':'if(!u.vis.visible)u.vis.visible = true;',
            'visual.visible=false;record.hidden=true;':'if(visual.visible)visual.visible=false;record.hidden=true;',
            'wpn.vis.visible = visB;':'if(wpn.vis.visible != visB)wpn.vis.visible = visB;'
        }
        for old,new in replacements.items():
            assert source.count(old)==1,(old,source.count(old))
            source=source.replace(old,new)
    elif name=='tileclip':
        source=(OUT/'bindings/src/RealisticVisionMod.as').read_text(encoding='utf-8')
        old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)
         {
            if(drawDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
        new='''         // Diagnostic candidate: retain the original tile-aligned sampling
         // lattice while omitting empty outer tiles. Filtered visuals keep all.
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
        source=source.replace(old,new)
    else:raise ValueError(name)
    shutil.copytree(BASE,dest)
    (dest/'RealisticVisionMod.as').write_text(source,encoding='utf-8',newline='\n')
    return dest

if __name__=='__main__':
    import sys
    print(prepare(sys.argv[1]))
