"""D56 v2: retain old representation outside the integer parent lattice."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
dest=OUT/'candidates/local-guard/src';assert not dest.exists()
shutil.copytree(OUT/'candidates/local/src',dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
s=s.replace('private var worldPass:int = 0;','private var worldPass:int = 0;\n      private var worldOrigins:Dictionary = new Dictionary(true);')
old='if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)'
new='var localOrigin:Boolean=this.worldOriginAllowed(visual.parent);\n         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || record.localOrigin!==localOrigin)'
assert s.count(old)==1;s=s.replace(old,new)
old='''            else {
               var originX:Number='''
new='''            else if(!localOrigin) {
               shape.graphics.copyFrom(Shape(raster.m2).graphics);
               if(shape.x!=0)shape.x=0;if(shape.y!=0)shape.y=0;
            }
            else {
               var originX:Number='''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;','record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;record.localOrigin=localOrigin;')
where='      private function releaseWorldVisual('
method='''      private function worldOriginAllowed(parent:DisplayObjectContainer):Boolean
      {
         var entry:Object=this.worldOrigins[parent];
         if(entry==null){entry={pass:-1,ok:false};this.worldOrigins[parent]=entry;}
         if(entry.pass!=this.worldPass){
            var m:Matrix=parent.transform.concatenatedMatrix;
            entry.ok=m.a==1 && m.b==0 && m.c==0 && m.d==1 && m.tx==int(m.tx) && m.ty==int(m.ty) && parent.filters.length==0;
            entry.pass=this.worldPass;
         }
         return entry.ok;
      }

'''
assert s.count(where)==1;s=s.replace(where,method+where)
s=s.replace('this.worldMasks={};this.worldPass=0;','this.worldMasks={};this.worldPass=0;this.worldOrigins=new Dictionary(true);')
p.write_text(s,encoding='utf-8',newline='\n')
