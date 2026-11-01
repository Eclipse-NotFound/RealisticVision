"""Independent second candidate: intersect the two hard wall masks once.

Keep the floor branch experiment, but remove the remaining nested hard mask.
All source rectangles have integer world coordinates; no alpha masks change.
The original masks remain available for fallback and exact-frame comparison.
"""
from pathlib import Path
import json, hashlib, shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/maximized-flow-output'
assert not (OUT/'floor-candidate').exists()
shutil.copytree(OUT/'candidate',OUT/'floor-candidate')
p=OUT/'candidate/src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
s=s.replace('private var fogBase:Sprite = null;', '''private var fogBase:Sprite = null;
      private var contourWallClip:Shape = new Shape();
      private var contourWallRevision:int = -1;
      private var contourWallStructure:int = -1;
      private var contourWallLoc:Object = null;''')
old='if(this.wallLayer.mask != this.wallClip) this.wallLayer.mask = this.wallClip;'
assert s.count(old)==1
s=s.replace(old,'''if(this.wallLayer.mask != this.wallClip && this.wallLayer.mask != this.contourWallClip)
            this.wallLayer.mask = this.wallClip;
         if(this.cfgWallBright){this.wallLayer.mask=this.wallClip;this.wallClip.visible=true;}''')
old='''            this.cfgWallBright);
         this.wallCacheLoc'''
assert s.count(old)==1
s=s.replace(old,'''            this.cfgWallBright);
         this.syncContourClipping(loc);
         this.wallCacheLoc''')
pos=s.index('      /** Read light from the open side')
s=s[:pos]+'''      /** The floor is already outside this contour. Intersect the two hard
       * wall masks when geometry changes, retaining all original wall rasters. */
      private function syncContourClipping(loc:Location):void
      {
         var source:DisplayObject=this.fogBase.mask;
         if(this.cfgWallBright || source==null)
         {
            this.wallLayer.mask=this.wallClip;this.wallClip.visible=true;
            this.contourWallClip.visible=false;
            return;
         }
         if(this.contourWallLoc!==loc || this.contourWallRevision!=this.wallSurface.contourRevision
            || this.contourWallStructure!=this.wallStructureVersion)
         {
            this.wallSurface.drawWallClip(this.contourWallClip,loc);
            this.contourWallLoc=loc;this.contourWallRevision=this.wallSurface.contourRevision;
            this.contourWallStructure=this.wallStructureVersion;
         }
         if(this.contourWallClip.parent!==this.fogBase)this.fogBase.addChild(this.contourWallClip);
         this.wallLayer.mask=this.contourWallClip;this.contourWallClip.visible=true;
         this.wallClip.visible=false;
         this.fogBase.mask=null;source.visible=false;
      }

'''+s[pos:]
p.write_text(s,encoding='utf-8',newline='\n')
p=OUT/'candidate/src/RVWallSurface.as';s=p.read_text(encoding='utf-8')
s=s.replace('private var contourUpdates:int = 0;', 'private var contourUpdates:int = 0;\n      private var contourRects:Vector.<int>=new Vector.<int>();')
old='''               shape.graphics.drawRect(drawX,drawY,drawWidth,drawHeight);
               if(role!=0)'''
assert s.count(old)==1
s=s.replace(old,'''               shape.graphics.drawRect(drawX,drawY,drawWidth,drawHeight);
               if(role!=0)contourRects.push(drawX,drawY,drawWidth,drawHeight);
               if(role!=0)''')
old='''         clip.graphics.drawRect(-80,-80,loc.spaceX*CELL+160,oy+80);
         clip.graphics.drawRect(-80,oy+h,loc.spaceX*CELL+160,loc.spaceY*CELL+80-oy-h);
         clip.graphics.drawRect(-80,oy,ox+80,h);
         clip.graphics.drawRect(ox+w,oy,loc.spaceX*CELL+80-ox-w,h);
         for each(var rect:Rectangle in supportComplement)
            clip.graphics.drawRect(ox+rect.x,oy+rect.y,rect.width,rect.height);'''
new='''         if(clip===baseClip)contourRects.length=0;
         emitContourRect(clip,-80,-80,loc.spaceX*CELL+160,oy+80);
         emitContourRect(clip,-80,oy+h,loc.spaceX*CELL+160,loc.spaceY*CELL+80-oy-h);
         emitContourRect(clip,-80,oy,ox+80,h);
         emitContourRect(clip,ox+w,oy,loc.spaceX*CELL+80-ox-w,h);
         for each(var rect:Rectangle in supportComplement)
            emitContourRect(clip,ox+rect.x,oy+rect.y,rect.width,rect.height);'''
assert s.count(old)==1;s=s.replace(old,new)
pos=s.index('      private function rebuildPieces():void')
s=s[:pos]+'''      private function emitContourRect(clip:Shape,x:int,y:int,w:int,h:int):void {
         clip.graphics.drawRect(x,y,w,h);
         if(clip===baseClip && w>0 && h>0)contourRects.push(x,y,w,h);
      }

      public function get contourRevision():int {return contourUpdates;}

      /** Intersect known positive rectangles with opaque collision tiles.
       * Keep partial-tile tops: the original wallClip includes the full tile. */
      public function drawWallClip(target:Shape,loc:*):void {
         var g:flash.display.Graphics=target.graphics;g.clear();g.beginFill(0xffffff);
         for(var i:int=0;i<contourRects.length;i+=4){
            var left:int=Math.max(0,contourRects[i]),top:int=Math.max(0,contourRects[i+1]);
            var right:int=Math.min(loc.spaceX*CELL,contourRects[i]+contourRects[i+2]);
            var bottom:int=Math.min(loc.spaceY*CELL,contourRects[i+1]+contourRects[i+3]);
            for(var y:int=top;y<bottom;){
               var ty:int=int(y/CELL),endY:int=Math.min(bottom,(ty+1)*CELL);
               var run:int=-1;
               for(var x:int=left;x<right;){
                  var tx:int=int(x/CELL),endX:int=Math.min(right,(tx+1)*CELL);
                  var solid:Boolean=loc.getTile(tx,ty).opac>=1;
                  if(solid && run<0)run=x;
                  if(!solid && run>=0){g.drawRect(run,y,x-run,endY-y);run=-1;}
                  x=endX;
               }
               if(run>=0)g.drawRect(run,y,right-run,endY-y);
               y=endY;
            }
         }
         g.endFill();
      }

'''+s[pos:]
p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'candidate/change.json').write_text(json.dumps({'kind':'intersect-wall-hard-masks','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'candidate/src').glob('*.as')}},indent=2)+'\n',encoding='utf-8')
