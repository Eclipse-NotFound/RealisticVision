"""Experimental stable wall viewport. Must pass native pixel and timing checks.

Only the display-only wall helper gets a two-tile gutter; FOV/paint/exploration
and per-frame terrain sampling stay unchanged. This is not part of optimize.py
until accepted. Candidate snapshots and prior runs are retained.
"""
from pathlib import Path
import shutil
from optimize import MOD, replace_one

OUT=MOD/'build/frame-performance-output'

def optimize(s):
    s=replace_one(s,'      private var classifiedSight:Vector.<uint>;',
        '      private var wallViewBounds:Rectangle;\n      private var wallViewOwner:Location;\n      private var classifiedSight:Vector.<uint>;')
    s=replace_one(s,'         this.wallSurface.reset();\n         this.curLoc = null;',
        '         this.wallSurface.reset();\n         this.wallViewBounds = null; this.wallViewOwner = null;\n         this.curLoc = null;')
    s=replace_one(s,'         this.currentSightData = null;\n         this.classifiedSight = null;',
        '         this.currentSightData = null;\n         this.wallViewBounds = null; this.wallViewOwner = null;\n         this.classifiedSight = null;')
    s=replace_one(s,'''         this.wallSurface.update(this.fogShadow,this.fogBase,w.grafon,loc,this.scenePaintBounds(),''',
'''         var view:Rectangle = this.scenePaintBounds();
         if(!this.cfgWallBright && (this.spaceX > 48 || this.spaceY > 25) && view.width > 0 && view.height > 0)
         {
            // The ordinary paint bounds already include four offscreen tiles.
            // A further two-tile gutter retains wall geometry while the camera
            // moves inside it. Terrain, exploration and light still refresh on
            // every call; the actual fog and logical sight keep their old bounds.
            // Constant-bright compositing retains its exact original extent:
            // changing that extent can alter its intermediate raster rounding.
            if(this.wallViewOwner !== loc || this.wallViewBounds == null || !this.wallViewBounds.containsRect(view))
            {
               var left:int = Math.max(0,int(view.left)-2);
               var top:int = Math.max(0,int(view.top)-2);
               this.wallViewBounds = new Rectangle(left,top,
                  Math.min(this.spaceX,view.right+2)-left,Math.min(this.spaceY,view.bottom+2)-top);
               this.wallViewOwner = loc;
            }
            view = this.wallViewBounds;
         }
         this.wallSurface.update(this.fogShadow,this.fogBase,w.grafon,loc,view,''')
    return s

if __name__=='__main__':
    checkpoint=OUT/'frame-04'
    if not checkpoint.exists():shutil.copytree(OUT/'candidate',checkpoint)
    target=OUT/'candidate/src/RealisticVisionMod.as'
    target.write_text(optimize((checkpoint/'src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')),encoding='utf-8')
