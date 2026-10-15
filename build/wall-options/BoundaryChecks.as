package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   public class BoundaryChecks extends Sprite {
      private var failures:int=0,passed:int=0;
      private var scene:Sprite=new Sprite(),fog:Sprite=new Sprite(),base:Sprite=new Sprite(),front:Sprite=new Sprite();
      private var pixels:BitmapData=new BitmapData(400,320,true,0),tiles:Array=[],knownTiles:Object={};
      private var surface:RVWallSurface=new RVWallSurface(),loc:Object;
      private var brightness:Number=1,enabled:Boolean=false;
      public function BoundaryChecks(){try{run();}catch(e:Error){failures++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("BOUNDARY COMPLETE passed="+passed+" failures="+failures);NativeApplication.nativeApplication.exit(failures?1:0);}
      private function check(ok:Boolean,label:String):void{if(ok)passed++;else failures++;trace((ok?"PASS ":"FAIL ")+label);}
      private function update(view:Rectangle=null):void {
         var self:BoundaryChecks=this;
         surface.update(fog,base,{visFront:front},loc,view||new Rectangle(0,0,10,8),
            function(x:int,y:int):Boolean{return self.knownTiles[x+","+y]===true;},
            function(...args):Number{return self.brightness;},enabled);
      }
      private function shot():BitmapData {var b:BitmapData=new BitmapData(400,320,false,0xffffff);b.draw(scene,null,null,null,null,true);return b;}
      private function grey(b:BitmapData,x:int,y:int):int{return b.getPixel(x,y)&255;}
      private function shade(value:Number):void {
         base.graphics.clear();base.graphics.beginFill(0,1-value);base.graphics.drawRect(0,0,400,320);base.graphics.endFill();
         base.graphics.beginFill(0);base.graphics.drawRect(80,80,200,160);base.graphics.endFill();
      }
      private function run():void {
         for(var y:int=0;y<8;y++)for(var x:int=0;x<10;x++)tiles.push({opac:x>=2&&x<=6&&y>=2&&y<=5?1:0,zForm:0});
         var self:BoundaryChecks=this;
         loc={spaceX:10,spaceY:8,getTile:function(x:int,y:int):Object{return self.tiles[x+y*10];}};
         pixels.fillRect(new Rectangle(80,80,200,160),0xffffffff);pixels.fillRect(new Rectangle(140,80,10,12),0);
         pixels.fillRect(new Rectangle(75,120,5,20),0xffffffff);pixels.setPixel32(100,80,0x80ffffff);
         front.addChild(new Bitmap(pixels));scene.addChild(front);scene.addChild(fog);fog.addChild(base);shade(1);
         update();var image:BitmapData=shot();check(grey(image,180,85)==0,"unexplored face remains black with constant brightness off");image.dispose();
         for(x=2;x<=6;x++)knownTiles[x+",1"]=true;
         for(y=2;y<=5;y++)knownTiles["1,"+y]=true;
         brightness=0;shade(0);update();image=shot();
         check(grey(image,145,85)==0&&grey(image,180,140)==0,"new cached patch with zero source and target light stays black");image.dispose();
         brightness=1;shade(1);
         update();image=shot();
         check(grey(image,145,85)>=245,"OFF corrects rectangular wall-shadow spill into visible air notch");
         check(grey(image,180,85)>=245&&grey(image,84,160)>=245,"OFF retains normally lit top and side faces");
         check(grey(image,180,140)==0&&grey(image,275,160)==0,"core and unexplored back face remain black");
         check(grey(image,30,60)==255,"floor far from wall is unchanged");image.dispose();
         brightness=.35;shade(.35);update();image=shot();
         check(Math.abs(grey(image,180,85)-89)<=2,"OFF wall follows remembered floor brightness");
         check(Math.abs(grey(image,145,85)-89)<=2,"OFF fixes spill in remembered transparent notches without making them bright");
         check(grey(image,180,140)==0,"OFF remembered deep core remains black");var off:BitmapData=image;
         enabled=true;update();image=shot();
         check(grey(image,180,85)>=245,"ON keeps explored rock face bright in memory");
         check(grey(image,145,85)==grey(off,145,85),"ON does not brighten the air notch");
         check(grey(image,30,60)==grey(off,30,60),"ON does not change floor away from wall");
         check(grey(image,100,80)>grey(off,100,80)&&grey(image,100,80)<245,"native antialiased alpha limits the brightening");
         check(grey(image,180,140)==0&&grey(image,275,160)==0,"ON leaves core and unknown reverse side black");image.dispose();
         enabled=false;update();image=shot();var diff:Object=image.compare(off);
         check(diff is uint&&uint(diff)==0,"ON to OFF immediately restores the corrected dim picture");
         if(diff is BitmapData)BitmapData(diff).dispose();image.dispose();off.dispose();
         brightness=.8;shade(.8);update();image=shot();check(Math.abs(grey(image,180,85)-204)<=2,"stationary native lighting changes update OFF wall brightness");image.dispose();
         brightness=.35;shade(.35);enabled=true;update();var before:int=surface.fieldUpdates;
         for(var n:int=0;n<20;n++)update();check(surface.fieldUpdates==before,"stable frames reuse face field and patch geometry");
         pixels.fillRect(new Rectangle(170,80,20,15),0);update();image=shot();
         check(Math.abs(grey(image,180,85)-89)<=2,"in-place wall damage switches to corrected air shading immediately");image.dispose();
         tiles[4+2*10].zForm=2;knownTiles["4,2"]=true;pixels.fillRect(new Rectangle(160,80,40,40),0);pixels.fillRect(new Rectangle(160,100,40,20),0xffffffff);
         update();image=shot();check(grey(image,180,103)>=245&&grey(image,180,90)<110,"half-height wall protects material without lighting the air above");image.dispose();
         loc={spaceX:10,spaceY:8,getTile:loc.getTile};knownTiles={};update();image=shot();
         check(grey(image,84,130)==0&&base.mask==null,"room change clears old exploration and replacement mask");image.dispose();
         knownTiles["1,3"]=true;update(new Rectangle(1,2,6,4));image=shot();check(grey(image,84,130)>=245,"nonzero viewport keeps contour aligned");image.dispose();
         var viewport:Sprite=new Sprite();scene.addChild(viewport);viewport.addChild(fog);viewport.scrollRect=new Rectangle(40,80,240,160);viewport.x=40;viewport.y=80;
         fog.scrollRect=viewport.scrollRect;fog.x=40;fog.y=80;image=shot();check(grey(image,84,130)>=245,"nested camera scroll compensation preserves patch alignment");image.dispose();
         var chunkPixels:BitmapData=new BitmapData(100,100,true,0);chunkPixels.fillRect(new Rectangle(10,10,8,80),0xffffffff);
         var chunk:Bitmap=new Bitmap(chunkPixels);chunk.scrollRect=new Rectangle(10,10,80,80);chunk.x=80;chunk.y=80;
         front.removeChildAt(0);front.addChild(chunk);update(new Rectangle(1,2,6,4));image=shot();
         check(grey(image,84,130)>=245&&grey(image,94,130)<200,"chunk gutter and actual empty pixels remain distinct");image.dispose();
         chunk.visible=false;update(new Rectangle(1,2,6,4));image=shot();check(grey(image,84,130)<110,"hidden foreground chunk does not leave a bright wall ghost");image.dispose();
         chunk.visible=true;chunk.transform.colorTransform=new ColorTransform(.8,.9,1,.5,10);update(new Rectangle(1,2,6,4));image=shot();
         check(grey(image,84,130)>100&&grey(image,84,130)<245,"colour-transform fallback respects effective foreground alpha");image.dispose();
         surface.reset();check(base.mask==null&&surface.owner==null&&surface.field==null,"reset releases cache, old room and base mask");
         update(new Rectangle(1,2,6,4));check(base.mask!=null,"contour renderer rebuilds after reset");
      }
   }
}
