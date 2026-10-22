"""Small falsifiable candidates, each based on the frozen installed source."""
from prepare import OUT
import shutil
def replace(s,a,b):
 assert s.count(a)==1,a[:100];return s.replace(a,b)
def noops():
 dest=OUT/'candidate-01';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest/'src')
 p=dest/'src/RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'private var contourUpdates:int = 0;','private var contourUpdates:int = 0;\n      private var contourFogVersion:int = -1;')
 s=replace(s,'parent.setChildIndex(wallPixels,parent.numChildren-1);','if(parent.getChildIndex(wallPixels)!=parent.numChildren-1)parent.setChildIndex(wallPixels,parent.numChildren-1);')
 s=replace(s,'contourDirty=contourLayoutDirty=true;mode=-1;', 'contourDirty=contourLayoutDirty=true;contourFogVersion=-1;mode=-1;')
 s=replace(s,'contourBitmap.bitmapData=contourFog;', 'contourFogVersion=-1;contourBitmap.bitmapData=contourFog;')
 s=replace(s,'contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);', '''if(contourFogVersion!=fieldUpdates){
            contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);
            contourFogVersion=fieldUpdates;
         }''')
 s=replace(s,'airPixels.mask=airClip;', 'if(airPixels.mask!==airClip)airPixels.mask=airClip;')
 s=replace(s,'wallPixels.mask=solidClip;base.mask=onClip;', 'if(wallPixels.mask!==solidClip)wallPixels.mask=solidClip;if(base.mask!==onClip)base.mask=onClip;')
 s=replace(s,'}else base.mask=baseClip;', '}else if(base.mask!==baseClip)base.mask=baseClip;')
 p.write_text(s,encoding='utf-8',newline='\n')
 p=dest/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 # Compare the live property, so other code cannot leave a stale cached value.
 s=replace(s,'this.fogVis.scrollRect = sceneView;', 'var presentView:Rectangle=this.fogVis.scrollRect;\n            if(presentView==null || !presentView.equals(sceneView))this.fogVis.scrollRect = sceneView;')
 s=replace(s,'this.fogVis.scrollRect = null;', 'if(this.fogVis.scrollRect!=null)this.fogVis.scrollRect = null;')
 s=replace(s,'this.fogShadow.scrollRect = this.fogVis.scrollRect;', '''var shadowView:Rectangle=this.fogShadow.scrollRect, requestedView:Rectangle=this.fogVis.scrollRect;
         if(shadowView==null?requestedView!=null:requestedView==null||!shadowView.equals(requestedView))this.fogShadow.scrollRect=requestedView;''')
 s=replace(s,'this.fogShadow.transform.colorTransform = this.infraCT;', 'if(!sameColor(this.fogShadow.transform.colorTransform,this.infraCT))this.fogShadow.transform.colorTransform = this.infraCT;')
 s=replace(s,'this.fogShadow.transform.colorTransform = this.defCT;', 'if(!sameColor(this.fogShadow.transform.colorTransform,this.defCT))this.fogShadow.transform.colorTransform = this.defCT;')
 at=s.index('      /** 透传模式')
 s=s[:at]+'''      private function sameColor(a:ColorTransform,b:ColorTransform):Boolean {
         return a.redMultiplier==b.redMultiplier && a.greenMultiplier==b.greenMultiplier && a.blueMultiplier==b.blueMultiplier && a.alphaMultiplier==b.alphaMultiplier
            && a.redOffset==b.redOffset && a.greenOffset==b.greenOffset && a.blueOffset==b.blueOffset && a.alphaOffset==b.alphaOffset;
      }

'''+s[at:]
 s=s.replace('u.vis.mask = s2;', 'if(u.vis.mask!==s2)u.vis.mask = s2;').replace('u.hpbar.mask = s3;', 'if(u.hpbar.mask!==s3)u.hpbar.mask = s3;')
 s=s.replace('visual.cacheAsBitmap=true;visual.mask=shape;', 'if(!visual.cacheAsBitmap)visual.cacheAsBitmap=true;if(visual.mask!==shape)visual.mask=shape;')
 p.write_text(s,encoding='utf-8',newline='\n')
def alpha_only():
 dest=OUT/'candidate-02';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest/'src')
 p=dest/'src/RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'if(!full)contourScratch.fillRect(contourScratch.rect,0);', '''if(full){
               // A single untransformed bitmap fully covers this patch. Only
               // alpha contributes to its silhouette; RGB changes such as
               // scorch marks cannot invalidate the mask. Read every frame.
               var alphaNext:BitmapData=patch.next;
               alphaNext.copyChannel(plan[0].data,plan[0].region,origin,BitmapDataChannel.ALPHA,BitmapDataChannel.ALPHA);
               var alphaDelta:Object=alphaNext.compare(patch.alpha);
               if(!(alphaDelta is uint && uint(alphaDelta)==0)){
                  var alphaSwap:BitmapData=patch.alpha;patch.alpha=alphaNext;patch.next=alphaSwap;
                  contourDirty=true;patch.runs=null;
                  if(alphaDelta is BitmapData)BitmapData(alphaDelta).dispose();
               }
               patch.directAlpha=true;
               continue;
            }
            if(!full)contourScratch.fillRect(contourScratch.rect,0);''')
 s=replace(s,'if(delta is uint&&uint(delta)==0)continue;', 'if(delta is uint&&uint(delta)==0 && patch.directAlpha!==true)continue;\n         patch.directAlpha=false;')
 p.write_text(s,encoding='utf-8',newline='\n')
def sample_lookup():
 dest=OUT/'candidate-03';assert not dest.exists();shutil.copytree(OUT/'candidate-02/src',dest/'src')
 p=dest/'src/RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'private var kernelOffsets:Array=[];', 'private var scaledAlphas:Vector.<int>=new Vector.<int>(65536,true);\n      private var kernelOffsets:Array=[];')
 s=replace(s,'wallPixels.mouseEnabled=wallPixels.mouseChildren=false;', '''wallPixels.mouseEnabled=wallPixels.mouseChildren=false;
         // All samples use integer alpha and light in [0,255]. Keep the exact
         // rounding, but compute each pair once instead of once per wall face.
         for(var alphaValue:int=0;alphaValue<256;alphaValue++)for(var lightValue:int=0;lightValue<256;lightValue++)
            scaledAlphas[(alphaValue<<8)+lightValue]=Math.round(alphaValue*lightValue/255);''')
 s=replace(s,'var value8:int=Math.round(alpha*intensity/255);','var value8:int=scaledAlphas[(alpha<<8)+intensity];')
 p.write_text(s,encoding='utf-8',newline='\n')
def display_window():
 dest=OUT/'candidate-04';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest/'src')
 p=dest/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'private var fogBase:Sprite = null;', 'private var fogBase:Sprite = null;\n      private var windowFog:BitmapData,windowWall:BitmapData;')
 s=replace(s,'this.updateWallSurface(w,loc);','this.updateWallSurface(w,loc);\n         this.syncDisplayWindow();')
 at=s.index('      /** 透传模式')
 s=s[:at]+'''      /** Keep logical fields unchanged; upload/display only the visible part
       * of the large 5px fields. Integer crop retains texel phase and a wide
       * offscreen gutter. Constant-bright raster snapshots keep full sources. */
      private function syncDisplayWindow():void {
         if(this.fogBitmap==null || this.classicWallShadeBmp==null)return;
         if(this.cfgWallBright || (this.spaceX<=48 && this.spaceY<=25) || this.wallViewBounds==null){
            this.fogBitmap.bitmapData=this.fogBmp;this.classicWallShadeBmp.bitmapData=this.classicWallShade;
            this.fogBitmap.x=this.fogBitmap.y=this.classicWallShadeBmp.x=this.classicWallShadeBmp.y=-FOG_PAD*Tile.tileX/FOG_SUB;
            if(this.windowFog!=null){this.windowFog.dispose();this.windowWall.dispose();this.windowFog=this.windowWall=null;}
            return;
         }
         var r:Rectangle=this.wallViewBounds.clone();
         r.x=FOG_PAD+r.x*FOG_SUB;r.y=FOG_PAD+r.y*FOG_SUB;r.width*=FOG_SUB;r.height*=FOG_SUB;
         r.inflate(2,2);r=r.intersection(this.fogRect);
         if(this.windowFog==null || this.windowFog.width!=r.width || this.windowFog.height!=r.height){
            if(this.windowFog!=null){this.windowFog.dispose();this.windowWall.dispose();}
            this.windowFog=new BitmapData(r.width,r.height,true,0);this.windowWall=new BitmapData(r.width,r.height,true,0);
         }
         this.windowFog.copyPixels(this.fogBmp,r,this.fogPoint);
         this.fogBitmap.bitmapData=this.windowFog;
         this.fogBitmap.x=(r.x-FOG_PAD)*Tile.tileX/FOG_SUB;this.fogBitmap.y=(r.y-FOG_PAD)*Tile.tileY/FOG_SUB;
         if(this.cfgMode=="classic")this.windowWall.copyPixels(this.classicWallShade,r,this.fogPoint);
         this.classicWallShadeBmp.bitmapData=this.windowWall;
         this.classicWallShadeBmp.x=this.fogBitmap.x;this.classicWallShadeBmp.y=this.fogBitmap.y;
      }

'''+s[at:]
 # Snapshot path must see the complete source before it draws the native fog.
 s=replace(s,'if(this.fogShadow == null) return;', '''if(this.fogShadow == null) return;
         if(this.cfgWallBright)this.syncDisplayWindow();''')
 p.write_text(s,encoding='utf-8',newline='\n')
def classic_scan():
 dest=OUT/'candidate-05';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest/'src')
 p=dest/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);\n         this.prepareClassicCells(loc);', 'this.prepareClassicCells(loc,true);')
 s=replace(s,'private function prepareClassicCells(loc:Location):void','private function prepareClassicCells(loc:Location,advance:Boolean=false):void')
 s=replace(s,'var alpha:int=this.tileFogAlpha(loc,x,y),memory:Number=this.memCur[i];\n            var known:Boolean=this.memoryExplored(i),solid:Boolean=loc.getTile(x,y).opac>=1;', '''var memory:Number=this.memCur[i];
            if(advance){
               var target:Number=!loc.retDark && this.fov[i]==FOV_NONE?1:0;
               if(memory<target)memory=Math.min(target,memory+this.cfgFadeStep);
               else if(memory>target)memory=Math.max(target,memory-this.cfgFadeStep);
               this.memCur[i]=memory;
            }
            // Read each native tile once. The former nested helpers fetched
            // the same tile three times during this full-room pass.
            var tile:Tile=loc.getTile(x,y);
            var solid:Boolean=tile.opac>=1;
            var known:Boolean=this.explored[i]==1 || (this.sharedExplored!=null && this.sharedExplored[i]==1);
            var alpha:int=255;
            if(x!=0 && y!=0){
               var light:Number=Math.max(0,Math.min(1,tile.visi));
               if(!loc.retDark && this.sharedLight!=null)light=Math.max(light,Number(this.sharedLight[i]));
               if(this.cfgViewScale!=1 && this.rangeRoom===loc && this.rangeLight!=null)light=Math.max(light,Number(this.rangeLight[i])||0);
               if(tile.opac<1 && this.fov[i]==FOV_DIM)light=Math.max(light,this.cfgDoorDim);
               alpha=Math.floor((1-light)*255);
            }''')
 p.write_text(s,encoding='utf-8',newline='\n')
def late_display():
 dest=OUT/'candidate-06';assert not dest.exists();shutil.copytree(OUT/'candidate-04/src',dest/'src')
 p=dest/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 s=replace(s,'this.updateWallSurface(w,loc);\n         this.syncDisplayWindow();\n         this.hideEnemies(w,loc,needFov);','''this.updateWallSurface(w,loc);
         this.hideEnemies(w,loc,needFov);
         // Classic's canonical unit-mask pass can update wall-shade pixels.
         // Snapshot only after every producer has finished for this frame.
         this.syncDisplayWindow();''')
 p.write_text(s,encoding='utf-8',newline='\n')
if __name__=='__main__':
 import sys
 late_display() if 'late' in sys.argv else classic_scan() if 'classic' in sys.argv else display_window() if 'window' in sys.argv else sample_lookup() if 'lookup' in sys.argv else alpha_only() if 'alpha' in sys.argv else noops()
