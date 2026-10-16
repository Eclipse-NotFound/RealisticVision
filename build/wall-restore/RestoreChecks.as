package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   public class RestoreChecks extends Sprite {
      private var failures:int=0,passed:int=0;
      private var scene:Sprite=new Sprite(),fog:Sprite=new Sprite(),base:Sprite=new Sprite(),front:Sprite=new Sprite();
      private var pixels:BitmapData=new BitmapData(400,320,true,0),tiles:Array=[],knownTiles:Object={};
      private var surface:RVWallSurface=new RVWallSurface(),loc:Object;
      private var brightness:Number=1,enabled:Boolean=false;
      public function RestoreChecks(){try{run();}catch(e:Error){failures++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("RESTORE COMPLETE passed="+passed+" failures="+failures);NativeApplication.nativeApplication.exit(failures?1:0);}
      private function check(ok:Boolean,label:String):void{if(ok)passed++;else failures++;trace((ok?"PASS ":"FAIL ")+label);}
      private function update(view:Rectangle=null):void {
         var self:RestoreChecks=this;
         surface.update(fog,base,{visFront:front},loc,view||new Rectangle(0,0,10,8),
            function(x:int,y:int):Boolean{return self.knownTiles[x+","+y]===true;},
            function(...args):Number{return self.brightness;},enabled);
      }
      private function shot():BitmapData {var b:BitmapData=new BitmapData(400,320,false,0xffffff);b.draw(scene,null,null,null,null,true);return b;}
      private function grey(b:BitmapData,x:int,y:int):int{return b.getPixel(x,y)&255;}
      private function shade(value:Number):void {
         base.graphics.clear();base.graphics.beginFill(0,1-value);base.graphics.drawRect(0,0,400,320);base.graphics.endFill();
         // Deliberately dark native wall: off must preserve its field, not paint a new bright rim.
         base.graphics.beginFill(0,.8);base.graphics.drawRect(80,80,200,160);base.graphics.endFill();
         base.graphics.beginFill(0);base.graphics.drawRect(120,120,120,80);base.graphics.endFill();
      }
      private function run():void {
         for(var y:int=0;y<8;y++)for(var x:int=0;x<10;x++)tiles.push({opac:x>=2&&x<=6&&y>=2&&y<=5?1:0,zForm:0});
         var self:RestoreChecks=this;
         loc={spaceX:10,spaceY:8,getTile:function(x:int,y:int):Object{return self.tiles[x+y*10];}};
         pixels.fillRect(new Rectangle(80,80,200,160),0xffffffff);pixels.fillRect(new Rectangle(140,80,10,12),0);
         pixels.fillRect(new Rectangle(75,120,5,20),0xffffffff);pixels.setPixel32(100,80,0x80ffffff);
         front.addChild(new Bitmap(pixels));scene.addChild(front);scene.addChild(fog);fog.addChild(base);shade(1);
         var original:BitmapData=shot();update();var image:BitmapData=shot();
         check(grey(image,145,85)==grey(original,145,85),"unexplored notch stays native dark");image.dispose();
         for(x=2;x<=6;x++)knownTiles[x+",1"]=true;
         for(y=2;y<=5;y++)knownTiles["1,"+y]=true;
         update();image=shot();
         check(grey(image,145,85)>=245,"OFF repairs visible air notch");
         var changed:int=0;for(y=0;y<320;y++)for(x=0;x<400;x++)
            if(pixels.getPixel32(x,y)>>>24 && image.getPixel(x,y)!=original.getPixel(x,y))changed++;
         check(changed==0,"OFF every material pixel preserves the original wall field: changes="+changed);
         check(grey(image,180,140)==0,"deep wall core remains black");
         check(grey(image,30,60)==255,"distant floor unchanged");image.dispose();original.dispose();
         for each(var zoom:Number in [.75,1.25,1.5]){
            surface.reset();var matrix:Matrix=new Matrix(zoom,0,0,zoom,.25,.5);
            original=new BitmapData(600,480,false,0xffffff);original.draw(scene,matrix,null,null,null,true);
            update();image=new BitmapData(600,480,false,0xffffff);image.draw(scene,matrix,null,null,null,true);
            check(image.getPixel(int(180*zoom),int(85*zoom))==original.getPixel(int(180*zoom),int(85*zoom))
               &&image.getPixel(int(180*zoom),int(140*zoom))==0,"fractional zoom "+zoom+" retains native wall gradient and black core");
            check(grey(image,int(145*zoom),int(85*zoom))>=245,"fractional zoom "+zoom+" keeps notch free of wall spill");image.dispose();original.dispose();
         }
         brightness=.35;shade(.35);update();image=shot();
         check(Math.abs(grey(image,145,85)-89)<=2,"OFF notch dims with floor visibility");
         var off:BitmapData=image;enabled=true;update();image=shot();
         check(grey(image,180,85)>=245,"ON retains optional explored bright face");
         check(grey(image,145,85)==grey(off,145,85),"ON cannot brighten transparent notch");
         check(grey(image,180,140)==0,"ON deep core stays black");image.dispose();
         enabled=false;update();image=shot();var diff:Object=image.compare(off);
         check(diff is uint&&uint(diff)==0,"toggle ON OFF restores exact default image");
         if(diff is BitmapData)BitmapData(diff).dispose();image.dispose();off.dispose();
         pixels.fillRect(new Rectangle(170,80,20,15),0);update();image=shot();
         check(Math.abs(grey(image,180,85)-89)<=2,"in-place material damage reveals dim air immediately");image.dispose();
         var chunkPixels:BitmapData=new BitmapData(80,80,true,0);chunkPixels.fillRect(new Rectangle(10,10,60,60),0xffffffff);
         chunkPixels.fillRect(new Rectangle(30,10,8,10),0);
         var chunk:Bitmap=new Bitmap(chunkPixels);chunk.scrollRect=new Rectangle(10,10,60,60);chunk.x=chunk.y=80;
         front.removeChildAt(0);front.addChild(chunk);update();image=shot();
         check(Math.abs(grey(image,105,85)-89)<=2&&grey(image,95,85)<30,"chunk gutter maps air and material to their world positions");image.dispose();
         var extra:Bitmap=new Bitmap(new BitmapData(20,20,true,0));extra.x=extra.y=80;front.addChild(extra);update();image=shot();
         check(Math.abs(grey(image,105,85)-89)<=2&&grey(image,95,85)<30,"multiple overlapping chunks preserve actual alpha");image.dispose();
         chunk.visible=false;update();image=shot();check(Math.abs(grey(image,95,85)-89)<=2,"hidden chunk immediately becomes air");image.dispose();
         chunk.visible=true;front.transform.colorTransform=new ColorTransform(1,1,1,.5);update();image=shot();
         check(Math.abs(grey(image,105,85)-89)<=2&&grey(image,95,85)<30,"transformed foreground fallback keeps material shading and clears air");image.dispose();
         front.visible=false;update();check(base.mask==null,"hidden foreground detaches correction mask");front.visible=true;front.transform.colorTransform=new ColorTransform();
         front.removeChild(extra);front.removeChild(chunk);front.addChild(new Bitmap(pixels));
         update(new Rectangle(1,1,7,6));image=shot();check(Math.abs(grey(image,180,85)-89)<=2,"offset viewport retains contour alignment");image.dispose();
         var viewport:Sprite=new Sprite();scene.addChild(viewport);viewport.addChild(fog);viewport.scrollRect=new Rectangle(40,40,280,240);viewport.x=40;viewport.y=40;
         fog.scrollRect=viewport.scrollRect;fog.x=40;fog.y=40;image=shot();check(Math.abs(grey(image,180,85)-89)<=2,"nested camera scroll preserves alignment");image.dispose();
         surface.reset();check(base.mask==null,"reset restores unmasked original");
         // A different same-sized room must not retain explored holes.
         knownTiles={};loc={spaceX:10,spaceY:8,getTile:loc.getTile};update();image=shot();
         check(grey(image,180,85)<30,"new room does not reuse old corrected cutouts");image.dispose();
      }
   }
}
