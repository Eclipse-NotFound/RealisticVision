package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   public class BoundaryRepro extends Sprite {
      public function BoundaryRepro() {
         var scene:Sprite=new Sprite(),fog:Sprite=new Sprite(),base:Sprite=new Sprite(),front:Sprite=new Sprite();
         var tiles:Array=[];
         for(var y:int=0;y<8;y++)for(var x:int=0;x<10;x++)tiles.push({opac:x>=2&&x<=6&&y>=2&&y<=5?1:0,zForm:0});
         var loc:Object={spaceX:10,spaceY:8,getTile:function(x:int,y:int):Object{return tiles[x+y*10];}};
         var pixels:BitmapData=new BitmapData(400,320,true,0);
         pixels.fillRect(new Rectangle(80,80,200,160),0xffffffff);
         pixels.fillRect(new Rectangle(140,80,10,12),0);
         front.addChild(new Bitmap(pixels));scene.addChild(front);scene.addChild(fog);fog.addChild(base);
         base.graphics.beginFill(0);base.graphics.drawRect(80,80,200,160);base.graphics.endFill();
         var known:Function=function(x:int,y:int):Boolean{return y==1&&x>=2&&x<=6;};
         var surface:*=new RVWallSurface();
         CONFIG::legacy { surface.update(fog,{visFront:front},loc,new Rectangle(0,0,10,8),known); }
         CONFIG::repaired { surface.update(fog,base,{visFront:front},loc,new Rectangle(0,0,10,8),known,function(...args):Number{return 1;},false); }
         var image:BitmapData=new BitmapData(400,320,false,0xffffff);image.draw(scene,null,null,null,null,true);
         var value:int=image.getPixel(145,85)&255;
         var ok:Boolean=value>=245;
         trace((ok?"PASS ":"FAIL ")+"visible air notch must not inherit rectangular wall shadow, brightness="+value);
         trace("REPRO COMPLETE");NativeApplication.nativeApplication.exit(ok?0:1);
      }
   }
}
