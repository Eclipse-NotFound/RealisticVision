from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];O=M/'build/enemy-combat-output';D=O/'candidates/unit_clip_v2/src'
assert not D.exists();shutil.copytree(O/'candidates/unit_clip/src',D)
p=D/'RealisticVisionMod.as';s=p.read_text()
old='''         if(this.cfgMode=="current"){
            if(rec.bodyDraw==null)'''
new='''         if(this.cfgMode=="current"){
            if(s2.parent!=null)s2.parent.removeChild(s2);
            if(s3.parent!=null)s3.parent.removeChild(s3);
            if(rec.bodyDraw==null)'''
assert s.count(old)==1;s=s.replace(old,new)
old='''            this.drawUnitMask(u.hpbar,s3,rec,rec.barDraw);
         }
         if(!s2.cacheAsBitmap)'''
new='''            this.drawUnitMask(u.hpbar,s3,rec,rec.barDraw);
         } else {
            for each(var draw:Object in [rec.bodyDraw,rec.barDraw])if(draw!=null){
               var clipped:Shape=draw.shape as Shape;if(clipped!=null&&clipped.parent!=null)clipped.parent.removeChild(clipped);
            }
         }
         if(!s2.cacheAsBitmap)'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
