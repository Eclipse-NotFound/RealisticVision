"""Experimental large-scene sight classification without a full bitmap readback."""
import shutil
from optimize import MOD, replace_one

OUT=MOD/'build/frame-performance-output'

def optimize(s):
    s=replace_one(s,'''         // Large scenes snapshot sight only when a visible unit needs it.
         // Invalidation still happens on every fog/wall change; all units in a
         // frame share one exact snapshot. Empty and fully hidden areas allocate none.''',
'''         // Start a sight generation only when a visible unit needs it.
         // Small rooms keep the existing full snapshot; large rooms classify
         // exact queried tiles lazily. Fog/wall writes invalidate both paths.''')
    s=replace_one(s,'''            this.currentSightData = this.currentSight.getVector(this.currentSight.rect);
         if(this.cfgMode == "current" && this.currentSightData != null)''',
'''            // Large maps need only the tiles actually touched by unit bounds.
            // An empty vector identifies this unchanged logical field. Every
            // write to currentSight above invalidates it before hideEnemies;
            // classification and masks run synchronously against that field.
            this.currentSightData = new Vector.<uint>();
         if(this.cfgMode == "current" && this.currentSightData != null)''')
    s=replace_one(s,'''                     var start:int=(FOG_PAD+ty*MASK_SUB)*width+FOG_PAD+tx*MASK_SUB;
                     kind=data[start]!=0?2:1;
                     for(var row:int=0;row<MASK_SUB && kind!=3;row++)
                        for(var col:int=0;col<MASK_SUB;col++)
                           if((data[start+row*width+col]!=0?2:1)!=kind){kind=3;break;}''',
'''                     var tileData:Vector.<uint> = data;
                     var tileStride:int = width;
                     var start:int=(FOG_PAD+ty*MASK_SUB)*width+FOG_PAD+tx*MASK_SUB;
                     if(data.length==0)
                     {
                        tileData=this.currentSight.getVector(new Rectangle(
                           FOG_PAD+tx*MASK_SUB,FOG_PAD+ty*MASK_SUB,MASK_SUB,MASK_SUB));
                        tileStride=MASK_SUB;start=0;
                     }
                     kind=tileData[start]!=0?2:1;
                     for(var row:int=0;row<MASK_SUB && kind!=3;row++)
                        for(var col:int=0;col<MASK_SUB;col++)
                           if((tileData[start+row*tileStride+col]!=0?2:1)!=kind){kind=3;break;}''')
    s=replace_one(s,'''            // Preserve the original fallback for unusual out-of-room bounds.
            var first:int=-1;''',
'''            // Preserve the original fallback for unusual out-of-room bounds.
            if(this.currentSightData.length==0)
               this.currentSightData=this.currentSight.getVector(this.currentSight.rect);
            var first:int=-1;''')
    return s

if __name__=='__main__':
    checkpoint=OUT/'view-05'
    if not checkpoint.exists():shutil.copytree(OUT/'candidate',checkpoint)
    target=OUT/'candidate/src/RealisticVisionMod.as'
    target.write_text(optimize((OUT/'frame-04/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')),encoding='utf-8')
