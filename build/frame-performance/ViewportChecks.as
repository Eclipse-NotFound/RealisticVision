package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   import fe.World;
   import fe.loc.*;
   import fe.graph.Grafon;

   public class ViewportChecks extends Sprite {
      public function ViewportChecks(){
         var failures:int=0,count:int=0;
         try {
            Tile.tileX=Tile.tileY=40;
            var w:ViewportWorld=new ViewportWorld(),loc:ViewportLocation=new ViewportLocation();World.w=w;w.loc=loc;
            var graph:ViewportGrafon=new ViewportGrafon();w.grafon=graph;graph.visFront=new Sprite();
            var terrain:BitmapData=new BitmapData(3200,1600,true,0);graph.visFront.addChild(new Bitmap(terrain));
            var canvasA:BitmapData=new BitmapData(480,320,false,0xffffff),canvasB:BitmapData=canvasA.clone();
            for each(var mode:String in ["current","classic"])for each(var bright:Boolean in [false,true]) {
               var before:int=failures;
               var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod();
               for each(var m:* in [a,b]) {
                  m.spaceX=loc.spaceX;m.spaceY=loc.spaceY;m.curLoc=loc;m.cfgMode=mode;m.cfgWallBright=bright;
                  m.explored=[];m.memCur=[];m.fov=[];
                  for(var i:int=0;i<80*40;i++){m.explored[i]=true;m.memCur[i]=0.4;m.fov[i]=2;}
                  m.fogRaw=new BitmapData(80*8+8,40*8+8,true,0x65000000);
                  m.fogShadow=new Sprite();m.fogBase=new Sprite();m.fogShadow.addChild(m.fogBase);
                  m.fogBase.graphics.beginBitmapFill(m.fogRaw,new Matrix(5,0,0,5,-20,-20),false,true);
                  m.fogBase.graphics.drawRect(-20,-20,3240,1640);m.fogBase.graphics.endFill();
               }
               for(var frame:int=0;frame<48;frame++) {
                  var scale:Number=[.75,1,1.25,1][int(frame/12)];
                  var cameraX:Number=200+(frame%12)*37.25,cameraY:Number=350+(frame%7)*19.5;
                  w.cam={scaleV:scale,vx:-cameraX*scale,vy:-cameraY*scale,screenX:480,screenY:320};
                  terrain.fillRect(terrain.rect,0);
                  for(i=0;i<loc.tiles.length;i++){
                     var tile:Tile=loc.tiles[i];tile.opac=(i%80==14||i%80==23||int(i/80)==17)?1:0;
                     if(frame%9==4&&i%80==14&&int(i/80)==14)tile.opac=0;
                     if(tile.opac)terrain.fillRect(new Rectangle((i%80)*40+3,int(i/80)*40+2,34,36),0xff334455);
                  }
                  // Transparent notches, a changing opaque decal and a partial alpha edge.
                  terrain.fillRect(new Rectangle(560,540,30,19),0);
                  terrain.fillRect(new Rectangle(570,600+(frame%5),8,8),frame%2?0x55334455:0xff334455);
                  for each(m in [a,b]){
                     m.fogRaw.fillRect(m.fogRaw.rect,uint(40+frame*3)<<24);
                     for(i=0;i<80*40;i++){m.memCur[i]=(frame%7)/8;m.explored[i]=!(frame%8==3&&i%80>22);}
                     m.updateWallSurface(w,loc);
                  }
                  var mat:Matrix=new Matrix(scale,0,0,scale,w.cam.vx,w.cam.vy);
                  canvasA.fillRect(canvasA.rect,0xffffff);canvasB.fillRect(canvasB.rect,0xffffff);
                  canvasA.draw(a.fogShadow,mat,null,null,null,true);canvasB.draw(b.fogShadow,mat,null,null,null,true);
                  var delta:Object=canvasA.compare(canvasB);count++;
                  if(!(delta is uint&&uint(delta)==0)){failures++;trace("FAIL viewport "+mode+" bright="+bright+" frame="+frame);if(delta is BitmapData)BitmapData(delta).dispose();}
               }
               trace((failures==before?"PASS ":"FAIL ")+"viewport group "+mode+" bright="+bright+" tested=48 cumulativeFailures="+failures);
               a.wallSurface.reset();b.wallSurface.reset();a.fogRaw.dispose();b.fogRaw.dispose();
            }
            canvasA.dispose();canvasB.dispose();terrain.dispose();
         } catch(e:Error){failures++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("VIEWPORT COMPLETE comparisons="+count+" failures="+failures);NativeApplication.nativeApplication.exit(failures?1:0);
      }
   }
}
import fe.World;
import fe.loc.*;
import fe.graph.Grafon;
import flash.display.Sprite;
class ViewportWorld extends World {public var cam:Object;}
class ViewportGrafon extends Grafon {public var visFront:Sprite;}
class ViewportLocation extends Location {
      public var tiles:Array=[];
      public function ViewportLocation(){spaceX=80;spaceY=40;for(var i:int=0;i<80*40;i++){var t:Tile=new Tile();t.opac=0;t.visi=t.t_visi=.7;tiles.push(t);}}
      override public function getTile(x:int,y:int):Tile {return tiles[x+y*spaceX];}
}
