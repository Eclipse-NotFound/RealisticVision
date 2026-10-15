package {
   import flash.display.*;
   import flash.geom.*;
   import flash.filters.BlurFilter;
   import flash.desktop.NativeApplication;

   /** Differential check against the frozen, repeated-draw implementation.
    * The only intended difference is how often the original fog is drawn. */
   public class DrawOnceChecks extends Sprite {
      private var passed:int=0,failed:int=0;
      private var oldSurface:RepeatedWallSurface=new RepeatedWallSurface();
      private var surface:RVWallSurface=new RVWallSurface();
      private var oldFog:Sprite=new Sprite(),fog:Sprite=new Sprite();
      private var oldBase:Sprite,base:Sprite,front:Sprite=new Sprite();
      private var tiles:Array=[],loc:Object;
      private var pixels:BitmapData=new BitmapData(400,320,true,0);
      private var intensity:Number=.35,known:Boolean=true,bright:Boolean=false;
      public function DrawOnceChecks(){
         try{run();}catch(e:Error){failed++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("DRAW ONCE COMPLETE passed="+passed+" failed="+failed);
         NativeApplication.nativeApplication.exit(failed?1:0);
      }
      private function makeBase(offset:int=0):Sprite {
         var group:Sprite=new Sprite(),raw:BitmapData=new BitmapData(80,64,true,0);
         for(var y:int=0;y<64;y++)for(var x:int=0;x<80;x++)raw.setPixel32(x,y,uint((x*11+y*3+offset)%256)<<24);
         var ground:Bitmap=new Bitmap(raw,"auto",true);ground.scaleX=ground.scaleY=5;
         ground.filters=[new BlurFilter(4,4,3)];group.addChild(ground);
         var wall:Sprite=new Sprite(),clip:Shape=new Shape();
         wall.graphics.beginFill(0,.8);wall.graphics.drawRect(0,0,400,320);wall.graphics.endFill();
         clip.graphics.beginFill(0xffffff);clip.graphics.drawRect(80,80,200,160);clip.graphics.endFill();
         group.addChild(wall);group.addChild(clip);wall.mask=clip;return group;
      }
      private function compare(label:String,view:Rectangle=null):void {
         var self:DrawOnceChecks=this;
         var isKnown:Function=function(x:int,y:int):Boolean{return self.known&&(y==1||x==1);};
         var light:Function=function(x:int,y:int,wx:Number,wy:Number,dir:int):Number{return self.intensity*(.5+.5*wx/400);};
         view=view||new Rectangle(0,0,10,8);
         oldSurface.update(oldFog,oldBase,{visFront:front},loc,view,isKnown,light,bright);
         surface.update(fog,base,{visFront:front},loc,view,isKnown,light,bright);
         var a:BitmapData=new BitmapData(400,320,false,0xffffff),b:BitmapData=a.clone();
         a.draw(oldFog,null,null,null,null,true);b.draw(fog,null,null,null,null,true);
         var delta:Object=a.compare(b),ok:Boolean=delta is uint&&uint(delta)==0;
         if(ok)passed++;else failed++;
         trace((ok?"PASS ":"FAIL ")+label+" exact pixels");
         if(delta is BitmapData)BitmapData(delta).dispose();a.dispose();b.dispose();
      }
      private function run():void {
         var self:DrawOnceChecks=this;
         for(var y:int=0;y<8;y++)for(var x:int=0;x<10;x++)tiles.push({opac:x>=2&&x<=6&&y>=2&&y<=5?1:0,zForm:0});
         loc={spaceX:10,spaceY:8,getTile:function(x:int,y:int):Object{return self.tiles[x+y*10];}};
         pixels.fillRect(new Rectangle(80,80,200,160),0xffffffff);
         pixels.fillRect(new Rectangle(140,80,10,15),0);pixels.fillRect(new Rectangle(180,80,8,15),0x80ffffff);
         front.addChild(new Bitmap(pixels));
         oldBase=makeBase();base=makeBase();oldFog.addChild(oldBase);fog.addChild(base);
         compare("OFF remembered contour with blurred and masked base");
         compare("unchanged cached contour");
         bright=true;compare("ON remembered contour with native alpha");
         intensity=1;compare("visible contour");
         bright=false;compare("OFF visible contour");
         known=false;compare("unknown contour");
         known=true;pixels.fillRect(new Rectangle(80,100,20,30),0);compare("damaged alpha");
         compare("offset viewport",new Rectangle(1,2,6,4));
         compare("resized viewport",new Rectangle(0,0,8,7));
         oldFog.removeChild(oldBase);fog.removeChild(base);
         oldBase=makeBase(91);base=makeBase(91);oldFog.addChildAt(oldBase,0);fog.addChildAt(base,0);
         compare("changed original fog");
         surface.reset();oldSurface.reset();compare("room reset");
      }
   }
}
