"""Candidate 1: apply the wall-material contour only to the wall branch.

The default contour includes every open tile, so clipping the already floor-
clipped fog again is redundant. The bright-wall option keeps the original tree.
Only an isolated exact production-source copy is modified.
"""
from pathlib import Path
import hashlib, json

MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/maximized-flow-output'
p=OUT/'candidate/src/RealisticVisionMod.as'
s=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8')
old='''         for each(var fogChild:DisplayObject in [this.fogBitmap,this.wallLayer,this.wallClip,this.floorClip])
            if(fogChild.parent != this.fogBase) this.fogBase.addChild(fogChild);'''
new='''         for each(var fogChild:DisplayObject in [this.fogBitmap,this.wallLayer,this.wallClip,this.floorClip])
         {
            // The ordinary contour excludes only material notches in opaque
            // tiles. floorClip already excludes those tiles. Avoid applying the
            // detailed contour to the whole floor a second time. Bright walls
            // intentionally exclude material in open tiles too; retain that tree.
            var fogParent:Sprite = !this.cfgWallBright && (fogChild === this.fogBitmap || fogChild === this.floorClip)
               ? this.fogShadow : this.fogBase;
            if(fogChild.parent != fogParent)
            {
               if(fogParent === this.fogShadow) fogParent.addChildAt(fogChild,0);
               else fogParent.addChild(fogChild);
            }
         }'''
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
(OUT/'candidate/change.json').write_text(json.dumps({'kind':'floor-outside-material-contour','source':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
