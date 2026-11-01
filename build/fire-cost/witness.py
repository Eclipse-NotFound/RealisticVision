"""Skip allocating a difference bitmap only when inequality is already proven."""
from pathlib import Path
import hashlib,json,shutil
from instrument import once
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/fire-cost-output';target=OUT/'candidates/witness/src'
assert not target.exists();shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text('utf8')
old='''            var maskDelta:Object = bd.compare(previousInput);
            if(maskDelta is uint && uint(maskDelta) == 0) return;
            if(maskDelta is BitmapData) BitmapData(maskDelta).dispose();'''
new='''            // Counts and a remembered pixel can prove inequality, never equality.
            // If neither proves a change, retain the complete native comparison.
            var provenChange:Boolean=matches>=0 && rec.maskMatchCount!==undefined && rec.maskMatchCount>=0 && matches!=rec.maskMatchCount;
            if(!provenChange && rec.maskWitnessX>=0 && rec.maskWitnessX<bd.width && rec.maskWitnessY>=0 && rec.maskWitnessY<bd.height)
               provenChange=bd.getPixel32(rec.maskWitnessX,rec.maskWitnessY)!=uint(rec.maskWitnessColor);
            if(provenChange){
               // FIRE_PROVEN_CHANGE
            } else {
               var maskDelta:Object = bd.compare(previousInput);
               if(maskDelta is uint && uint(maskDelta) == 0) return;
               if(maskDelta is BitmapData){
                  var deltaBounds:Rectangle=BitmapData(maskDelta).getColorBoundsRect(0xffffffff,0,false);
                  var witnessY:int=deltaBounds.y;
                  for(var witnessX:int=deltaBounds.x;witnessX<deltaBounds.right;witnessX++)
                     if(bd.getPixel32(witnessX,witnessY)!=previousInput.getPixel32(witnessX,witnessY)){
                        rec.maskWitnessX=witnessX;rec.maskWitnessY=witnessY;break;
                     }
                  BitmapData(maskDelta).dispose();
               }
            }'''
s=once(s,old,new)
old='         previousInput.copyPixels(bd,bd.rect,this.fogPoint);'
new=old+'''
         rec.maskMatchCount=matches;
         if(rec.maskWitnessX>=0 && rec.maskWitnessX<bd.width && rec.maskWitnessY>=0 && rec.maskWitnessY<bd.height)
            rec.maskWitnessColor=bd.getPixel32(rec.maskWitnessX,rec.maskWitnessY);
         else rec.maskWitnessX=-1;'''
s=once(s,old,new)
p.write_text(s,'utf8',newline='\n')
(target.parent/'sources.json').write_text(json.dumps({q.relative_to(target).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in target.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
print('Created exact inequality candidate, no equality shortcut')
