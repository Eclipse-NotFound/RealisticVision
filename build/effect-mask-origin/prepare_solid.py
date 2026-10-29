"""D56 experiment: keep mask geometry, use geometric clipping on opaque support."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/solid/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)
         {
            if(drawDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
new='''         var solid:Boolean=!drawDark && this.worldVisualFullyLit(visual,bounds,x0,y0,raster);
         if(solid){ // D56_SOLID
         }
         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || record.solid!==solid)
         {
            if(drawDark)shape.graphics.clear();
            else if(solid){
               shape.graphics.clear();shape.graphics.beginFill(0xffffff,1);
               shape.graphics.drawRect(Math.max(0,x0-MASK_PAD_X)*Tile.tileX,Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY,
                  BitmapData(raster.m2e).width*Tile.tileX/MASK_SUB,BitmapData(raster.m2e).height*Tile.tileY/MASK_SUB);
               shape.graphics.endFill();
            }
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;','record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;record.solid=solid;')
s=s.replace('if(shape.cacheAsBitmap!==!drawDark)shape.cacheAsBitmap=!drawDark;','if(shape.cacheAsBitmap!==(!drawDark && !solid))shape.cacheAsBitmap=!drawDark && !solid;')
ref=(MOD/'build/frame-attribution-output/candidates/identity/src/RealisticVisionMod.as').read_text()
a=ref.index('      private function worldVisualFullyLit(');b=ref.index('      private function worldVisualHasFilters(',a)
where='      private function worldVisualHasFilters('
assert s.count(where)==1;s=s.replace(where,ref[a:b]+where)
p.write_text(s,encoding='utf-8',newline='\n')
