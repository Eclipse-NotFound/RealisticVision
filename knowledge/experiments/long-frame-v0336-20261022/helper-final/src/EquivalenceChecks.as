package {
   import flash.display.*;
   import flash.geom.*;
   import flash.filters.BlurFilter;
   import flash.desktop.NativeApplication;

   /** Strict output equality against the frozen D28 production helper. */
   public class EquivalenceChecks extends Sprite {
      private var passed:int=0,failed:int=0;
      private var oldSurface:BaselineWallSurface=new BaselineWallSurface();
      private var surface:RVWallSurface=new RVWallSurface();
      private var oldFog:Sprite=new Sprite(),fog:Sprite=new Sprite();
      private var oldBase:Sprite,base:Sprite,front:Sprite=new Sprite();
      private var tiles:Array=[],loc:Object;
      private var pixels:BitmapData=new BitmapData(400,320,true,0);
      private var intensity:Number=.35,known:Boolean=true,bright:Boolean=false;
      public function EquivalenceChecks(){
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
      private function compare(label:String,view:Rectangle=null,zoom:Number=1):void {
         var self:EquivalenceChecks=this;
         var isKnown:Function=function(x:int,y:int):Boolean{return self.known&&(y==1||x==1);};
         var light:Function=function(x:int,y:int,wx:Number,wy:Number,dir:int):Number{return self.intensity*(.5+.5*wx/400);};
         view=view||new Rectangle(0,0,10,8);
         oldSurface.update(oldFog,oldBase,{visFront:front},loc,view,isKnown,light,bright);
         surface.update(fog,base,{visFront:front},loc,view,isKnown,light,bright);
         for each(var fieldName:String in ["sampleStarts","samplePixels","sampleAlphas","sampleCells"])
            if(String(oldSurface[fieldName])!=String(surface[fieldName]))throw new Error("sample table mismatch "+fieldName+" "+label);
         var a:BitmapData=new BitmapData(600,480,false,0xffffff),b:BitmapData=a.clone();
         var transform:Matrix=new Matrix(zoom,0,0,zoom,.25,.5);
         a.draw(oldFog,transform,null,null,null,true);b.draw(fog,transform,null,null,null,true);
         var delta:Object=a.compare(b),ok:Boolean=delta is uint&&uint(delta)==0;
         if(ok)passed++;else failed++;
         trace((ok?"PASS ":"FAIL ")+label+" exact pixels");
         if(delta is BitmapData)BitmapData(delta).dispose();a.dispose();b.dispose();
      }
      private function run():void {
         var self:EquivalenceChecks=this;
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
         for(var frame:int=0;frame<40;frame++){
            intensity=(frame*37%256)/255;bright=frame%3!=0;known=frame%7!=0;
            tiles[2+2*10].zForm=frame%3;
            pixels.fillRect(new Rectangle(80,80,20,20),frame%2?0xff224466:0);
            compare("changing light, partial wall, alpha and option "+frame);
         }
         known=true;bright=true;intensity=.35;
         var chunk:Bitmap=new Bitmap(pixels);chunk.scrollRect=new Rectangle(20,20,320,260);chunk.x=20;chunk.y=20;
         front.removeChildAt(0);front.addChild(chunk);compare("chunk scroll under ON");
         var overlap:Bitmap=new Bitmap(new BitmapData(45,35,true,0x802a4b6c));overlap.x=80;overlap.y=80;
         front.addChild(overlap);compare("overlapping translucent chunks ON");
         overlap.visible=false;compare("hidden overlap ON");
         front.transform.colorTransform=new ColorTransform(1,.8,.7,.65,2,3,4);compare("transformed foreground ON");
         bright=false;compare("transformed foreground OFF");
         front.transform.colorTransform=new ColorTransform();front.visible=false;compare("hidden foreground");
         front.visible=true;compare("foreground shown again");
         bright=true;intensity=Number.NaN;compare("NaN light retains old coercion");
         intensity=1;compare("valid light after NaN");
         for each(var enabled:Boolean in [false,true]){
            bright=enabled;known=true;intensity=.35;
            for(var step:int=0;step<80;step++){
               var vx:int=step%3,vy:int=int(step/3)%3;
               if(step%7==0){tiles[3+3*10].opac=step%14==0?0:1;tiles[4+2*10].zForm=step%3;}
               if(step%9==0)pixels.fillRect(new Rectangle(140,80,10,15),step%18==0?0:0x80ffffff);
               compare("moving cache, tile/alpha change "+enabled+"/"+step,new Rectangle(vx,vy,7+step%2,5+step%2),[.658333,.75,1,1.25][step%4]);
            }
         }
         bright=false;known=true;compare("before interrupted geometry scan");
         tiles[3+3*10].opac=tiles[3+3*10].opac?0:1;
         var originalGet:Function=loc.getTile;
         loc.getTile=function(x:int,y:int):Object{if(x==6&&y==6)throw new Error("expected fixture interruption");return originalGet(x,y);};
         var interrupted:int=0;
         for each(var tested:* in [oldSurface,surface])try{
            tested.update(tested===surface?fog:oldFog,tested===surface?base:oldBase,{visFront:front},loc,new Rectangle(0,0,10,8),function(x:int,y:int):Boolean{return true;},function(...args):Number{return .35;},false);
         }catch(expected:Error){interrupted++;}
         if(interrupted!=2)throw new Error("missing interrupted scans");
         loc.getTile=originalGet;compare("geometry retry after interrupted scan");
         for each(var zoom:Number in [.75,1,1.25,1.5]){
            bright=false;compare("OFF fractional camera "+zoom,null,zoom);
            bright=true;compare("ON fractional camera "+zoom,null,zoom);
         }
      }
   }
}
