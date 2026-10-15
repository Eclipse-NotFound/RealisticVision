package {
   import flash.display.*;
   import flash.desktop.NativeApplication;
   import flash.geom.*;
   import flash.utils.getTimer;

   public class SurfaceChecks extends Sprite {
      private var failures:int=0;
      private var passed:int=0;
      private var tiles:Array=[];
      private var front:Sprite=new Sprite();
      private var pixels:BitmapData=new BitmapData(400,320,true,0);
      private var shade:Sprite=new Sprite();
      private var scene:Sprite=new Sprite();
      private var surface:RVWallSurface=new RVWallSurface();
      private var loc:Object;
      private var knownTiles:Object={};
      public function SurfaceChecks() {
         try { run(); } catch(e:Error) { failures++;trace("FAIL exception "+e.getStackTrace()); }
         trace("SURFACE COMPLETE passed="+passed+" failures="+failures);
         NativeApplication.nativeApplication.exit(failures?1:0);
      }
      private function check(ok:Boolean,description:String):void {
         if(ok)passed++;else failures++;trace((ok?"PASS ":"FAIL ")+description);
      }
      private function known(x:int,y:int):Boolean {return knownTiles[x+","+y]===true;}
      private function update(view:Rectangle=null):void {
         surface.update(shade,{visFront:front},loc,view||new Rectangle(0,0,10,8),known);
      }
      private function shot():BitmapData {
         var b:BitmapData=new BitmapData(400,320,false,0xffffff);
         b.draw(scene,null,null,null,null,true);return b;
      }
      private function grey(b:BitmapData,x:int,y:int):int {return b.getPixel(x,y)&255;}
      private function referenceMatches(description:String):void {
         update();var actual:BitmapData=shot(),raw:BitmapData=new BitmapData(400,320,true,0);raw.draw(front);
         var reference:Sprite=new Sprite();reference.graphics.beginFill(0);reference.graphics.drawRect(0,0,400,320);
         var texture:Bitmap=new Bitmap(raw),maskPixels:Bitmap=new Bitmap(surface.field,"auto",true);
         texture.cacheAsBitmap=maskPixels.cacheAsBitmap=true;maskPixels.scaleX=maskPixels.scaleY=5;
         texture.mask=maskPixels;reference.addChild(texture);reference.addChild(maskPixels);
         var expected:BitmapData=new BitmapData(400,320,false,0);expected.draw(reference,null,null,null,null,true);
         var maximum:int=0,where:String="";
         for(var y:int=0;y<320;y++)for(var x:int=0;x<400;x++){
            var a:uint=actual.getPixel(x,y),b:uint=expected.getPixel(x,y);
            var difference:int=Math.max(Math.abs((a&255)-(b&255)),Math.abs(((a>>8)&255)-((b>>8)&255)),Math.abs((a>>16)-(b>>16)));
            if(difference>maximum){maximum=difference;where=x+","+y+" actual="+a.toString(16)+" expected="+b.toString(16);}
         }
         check(maximum<=1,description+" max="+maximum+" "+where);actual.dispose();raw.dispose();expected.dispose();
      }
      private function run():void {
         var x:int,y:int;
         for(y=0;y<8;y++)for(x=0;x<10;x++)tiles.push({opac:(x>=2&&x<=6&&y>=2&&y<=5)?1:0,zForm:0});
         var self:SurfaceChecks=this;
         loc={spaceX:10,spaceY:8,getTile:function(tx:int,ty:int):Object{return self.tiles[tx+ty*10];}};
         pixels.fillRect(new Rectangle(80,80,200,160),0xffffffff);
         // A transparent bite, an opaque lip outside the nominal grid, and an antialiased rim.
         pixels.fillRect(new Rectangle(140,80,10,12),0);
         pixels.fillRect(new Rectangle(75,120,5,20),0xffffffff);
         pixels.setPixel32(100,80,0x80ffffff);
         front.addChild(new Bitmap(pixels));
         scene.addChild(shade);
         shade.blendMode="layer";shade.graphics.beginFill(0);shade.graphics.drawRect(0,0,400,320);shade.graphics.endFill();
         update();var b:BitmapData=shot();check(grey(b,180,85)==0,"unexplored wall stays black");b.dispose();
         for(x=2;x<=6;x++)knownTiles[x+",1"]=true;
         for(y=2;y<=5;y++)knownTiles["1,"+y]=true;
         update();b=shot();
         check(grey(b,180,85)>245,"explored top face retains a bright strip");
         check(grey(b,84,160)>245,"explored vertical face retains a bright strip");
         check(grey(b,180,100)>90&&grey(b,180,100)<220,"surface fades smoothly into the wall");
         check(grey(b,180,140)==0,"thick wall core stays fully black");
         check(grey(b,180,235)==0&&grey(b,275,160)==0,"unexplored opposite faces stay black");
         check(grey(b,180,75)==0&&grey(b,145,85)==0,"no cutout in air or transparent rock notches");
         check(grey(b,77,130)>245,"native opaque lip outside tile grid is protected");
         check(grey(b,100,80)>115&&grey(b,100,80)<140,"native alpha limits antialiased rim erasure");
         referenceMatches("patch compositor matches independent native bitmap-mask rendering");
         var overlayData:BitmapData=new BitmapData(12,80,true,0x80c06030),overlay:Bitmap=new Bitmap(overlayData);
         overlay.x=80;overlay.y=120;front.addChild(overlay);
         referenceMatches("overlapping translucent foreground layers preserve native colour and alpha");
         overlay.transform.colorTransform=new ColorTransform(0.8,0.9,1,1,20);
         referenceMatches("colour-transform fallback matches native rendering");
         front.removeChild(overlay);overlayData.dispose();update();
         var old:BitmapData=b.clone(),tc:int=surface.terrainUpdates,fc:int=surface.fieldUpdates;
         for(var i:int=0;i<30;i++)update();b.dispose();b=shot();
         check(uint(old.compare(b))==0,"unchanged exploration keeps the same wall pixels");
         check(surface.terrainUpdates==tc&&surface.fieldUpdates==fc,"stable frames reuse wall surface caches");old.dispose();b.dispose();
         // In-place foreground edits must not leave bright holes after damage.
         pixels.fillRect(new Rectangle(170,80,20,15),0);update();b=shot();
         check(grey(b,180,85)==0,"in-place alpha changes invalidate protection without a tile change");b.dispose();
         // Recreated fog children must stay below the eraser.
         var newFog:Shape=new Shape();newFog.graphics.beginFill(0);newFog.graphics.drawRect(0,0,400,320);shade.addChild(newFog);
         update();b=shot();check(grey(b,84,160)>245,"new fog children do not cover the protective cutout");b.dispose();shade.removeChild(newFog);
         // A half-height top exposes only the actual lower material.
         tiles[4+2*10].zForm=2;knownTiles["4,2"]=true;
         pixels.fillRect(new Rectangle(160,80,40,40),0);pixels.fillRect(new Rectangle(160,100,40,20),0xffffffff);
         update();b=shot();check(grey(b,180,103)>245&&grey(b,180,90)==0,"half-height face follows the actual top and leaves air dark");b.dispose();
         // Same-size room switch cannot retain explored faces.
         loc={spaceX:10,spaceY:8,getTile:loc.getTile};knownTiles={};update();b=shot();
         check(grey(b,84,160)==0,"same-size new room clears old wall exploration");b.dispose();
         knownTiles["1,3"]=true;update(new Rectangle(1,2,6,4));
         b=shot();check(grey(b,84,130)>245&&grey(b,180,140)==0,"nonzero viewport origin retains world-space alignment");b.dispose();
         var viewport:Sprite=new Sprite();scene.addChild(viewport);viewport.addChild(shade);
         viewport.scrollRect=new Rectangle(40,80,240,160);viewport.x=40;viewport.y=80;
         shade.scrollRect=viewport.scrollRect;shade.x=40;shade.y=80;
         b=shot();check(grey(b,84,130)>245&&grey(b,180,140)==0,"nested large-scene scrollRect compensation keeps wall registration");b.dispose();
         var chunkData:BitmapData=new BitmapData(100,100,true,0);
         chunkData.fillRect(new Rectangle(10,10,8,80),0xffffffff);
         var chunk:Bitmap=new Bitmap(chunkData);chunk.scrollRect=new Rectangle(10,10,80,80);chunk.x=80;chunk.y=80;
         front.removeChildAt(0);front.addChild(chunk);update(new Rectangle(1,2,6,4));b=shot();
         check(grey(b,84,130)>245&&grey(b,94,130)==0,"chunk gutter is cropped before applying world offset");b.dispose();
         chunk.visible=false;update(new Rectangle(1,2,6,4));b=shot();check(grey(b,84,130)==0,"hidden chunk is removed from wall protection");b.dispose();
         chunk.visible=true;chunkData.fillRect(chunkData.rect,0);update(new Rectangle(1,2,6,4));b=shot();
         check(grey(b,84,130)==0,"chunk damage updates live mask without a bitmap replacement");b.dispose();
         chunk.bitmapData=pixels;chunk.scrollRect=null;chunk.x=0;chunk.y=0;update(new Rectangle(1,2,6,4));b=shot();
         check(grey(b,84,130)>245,"replaced foreground bitmap restores the correct mask");b.dispose();
         var start:int=getTimer();for(i=0;i<100;i++)update(new Rectangle(1,2,6,4));
         trace("SURFACE PERF stable100="+(getTimer()-start)+"ms terrain="+surface.terrainUpdates+" field="+surface.fieldUpdates);
         surface.reset();b=shot();check(grey(b,84,130)==0&&surface.owner==null&&surface.field==null,"world reset releases old pixels and room references");b.dispose();
         update(new Rectangle(1,2,6,4));b=shot();check(grey(b,84,130)>245,"surface rebuilds correctly after world reset");b.dispose();
      }
   }
}
