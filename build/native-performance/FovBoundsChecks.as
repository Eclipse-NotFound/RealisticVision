package {
 import flash.display.*;
 import flash.desktop.NativeApplication;
 import fe.World;import fe.loc.Tile;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class FovBoundsChecks extends Sprite {
  private var passed:int=0;
  public function FovBoundsChecks(){try{run();trace("FOV BOUNDS COMPLETE passed="+passed);NativeApplication.nativeApplication.exit(0);}catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function fixture(cls:Class):Object {
   var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;
   w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   var m:*=new cls();m.mswRegistered=true;m.resetRoom(w,loc);return {m:m,w:w,loc:loc};
  }
  private function run():void {
   Tile.tileX=Tile.tileY=40;World.fps=30;
   var a:Object=fixture(FovBaselineVision),b:Object=fixture(RealisticVisionMod),index:int=0;
   for each(var mode:String in ["classic","current"])for each(var radius:int in [40,80,160,300,999,2000])for each(var scale:Number in [.5,1,3])for each(var p:Array in [[-10,0],[5,40],[200,500],[480,440],[959,879],[1020,900],[399.9,400.1],[0,0]]){
    for each(var o:Object in [a,b]){
     World.w=o.w;o.m.cfgMode=mode;o.m.cfgViewScale=scale;o.loc.lDist1=radius/2;o.loc.lDist2=radius;
     o.loc.gg.X=p[0];o.loc.gg.Y=p[1];o.loc.opacWater=.45;
     o.loc.getTile(index%20+2,int(index/20)%16+2).opac=index%3==0?1:(index%3==1?.3:0);
     o.loc.getTile(9,10).water=index%2;o.m.computeFov(o.loc);
    }
    for each(var key:String in ["fov","br","litArr","explored"]){
     if(JSON.stringify(a.m[key])!=JSON.stringify(b.m[key]))throw new Error("field "+key+" "+mode+" r="+radius+" scale="+scale+" position="+p);
     passed++;
    }
    index++;
   }
  }
 }
}
