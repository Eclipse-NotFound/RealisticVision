"""Prototype: remove an identity alpha mask without changing native raster cache."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/frame-attribution-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
def patch(source):
 def replace(old,new):
  nonlocal source
  assert source.count(old)==1,old
  source=source.replace(old,new)
 replace('''         record.pass=this.worldPass;
         var shape:Shape=record.shape as Shape;''','''         record.pass=this.worldPass;
         var shape:Shape=record.shape as Shape;
         if(!drawDark && this.worldVisualFullyLit(visual,bounds,x0,y0,raster))
         {
            // Retain the same target rasterization as the former soft mask.
            // Releasing native caching here can change subpixel animation AA.
            if(visual.mask===shape)visual.mask=record.baseMask;
            if(shape.parent!=null)shape.parent.removeChild(shape);
            if(!visual.cacheAsBitmap)visual.cacheAsBitmap=true;
            record.identity=true;
            // D47_IDENTITY_HIT
            return;
         }
         record.identity=false;''')
 needle='      private function worldVisualHasFilters(visual:DisplayObject):Boolean'
 replace(needle,'''      private function worldVisualFullyLit(visual:DisplayObject,bounds:Rectangle,x0:int,y0:int,raster:Object):Boolean
      {
         var data:BitmapData=raster.m2e as BitmapData;
         if(data==null)return false;
         var cs:Number=Tile.tileX/MASK_SUB;
         var originX:int=Math.max(0,x0-MASK_PAD_X)*MASK_SUB;
         var originY:int=Math.max(0,y0-MASK_PAD_TOP)*MASK_SUB;
         // Full bilinear neighbourhood, plus an extra sample for raster edges.
         var left:int=int(Math.floor(bounds.left/cs))-originX-2;
         var top:int=int(Math.floor(bounds.top/cs))-originY-2;
         var right:int=int(Math.ceil(bounds.right/cs))-originX+2;
         var bottom:int=int(Math.ceil(bounds.bottom/cs))-originY+2;
         if(left<0||top<0||right>data.width||bottom>data.height||left>=right||top>=bottom)return false;
         var pixels:Vector.<uint>=data.getVector(new Rectangle(left,top,right-left,bottom-top));
         for each(var pixel:uint in pixels)if((pixel>>>24)!=255)return false;
         // Filter support can exceed getBounds, so keep those masks unchanged.
         return !this.worldVisualHasFilters(visual);
      }

'''+needle)
 replace('''         if(visual.mask===record.shape){visual.mask=record.baseMask;visual.cacheAsBitmap=record.cache;}''','''         if(visual.mask===record.shape || (record.identity===true && visual.mask===record.baseMask))
         {visual.mask=record.baseMask;visual.cacheAsBitmap=record.cache;}''')
 return source
if __name__=='__main__':
 assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
 target=OUT/'candidates/identity/src';assert not target.exists();shutil.copytree(BASE,target)
 p=target/'RealisticVisionMod.as';p.write_text(patch(p.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
 (target.parent/'manifest.json').write_text(json.dumps({p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*.as')},indent=2)+'\n',encoding='utf-8',newline='\n')
 print('Identity-mask candidate prepared; no formal changes')
