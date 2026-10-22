package {
 import flash.display.*;import flash.desktop.NativeApplication;
 import fe.World;import fe.loc.Tile;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class MemoryTileChecks extends Sprite {
  private var passed:int=0;
  public function MemoryTileChecks(){try{run();trace("MEMORY TILES COMPLETE passed="+passed);NativeApplication.nativeApplication.exit(0);}catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function fixture(cls:Class,dim:Number):Object {
   var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;loc.lDist1=100;loc.lDist2=380;
   var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;
   w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   var m:*=new cls();m.mswRegistered=true;m.cfgMode="current";m.cfgDim=dim;m.cfgSoftCurrent=30;
   return {w:w,loc:loc,m:m};
  }
  private function same(a:BitmapData,b:BitmapData):Boolean {var d:Object=a.compare(b);if(d is BitmapData){d.dispose();return false;}return d===0;}
  private function run():void {
   Tile.tileX=Tile.tileY=40;World.fps=30;
   for each(var dim:Number in [0,.35,.6,1])for each(var shared:Boolean in [false,true]){
    var a:Object=fixture(FovBaselineVision,dim),b:Object=fixture(RealisticVisionMod,dim);
    for(var frame:int=0;frame<60;frame++){
     for each(var o:Object in [a,b]){
      World.w=o.w;o.loc.gg.X=80+(frame%20)*38;o.loc.gg.Y=480+(int(frame/20)%2)*80;
      if(frame==10)o.loc.getTile(10,8).opac=0;
      if(frame==20)o.loc.getTile(10,8).opac=1;
      if(frame==30)o.m.cfgDim=1-dim;
      if(frame==40)o.m.resetOff();
      o.m.frameCount++;o.m.onFrameInner();
      if(shared && (frame==15 || frame==25)){
       var rows:Array=[];
       for(var y:int=0;y<o.loc.spaceY;y++){
        var row:String="";for(var x:int=0;x<o.loc.spaceX;x++)row+=(x==8&&y==10?(frame==15?"f01f00000000000f0":"f0fffffffffffffff"):"00000000000000000");rows.push(row);
       }
       if(!o.m.mergeExploration(o.loc,rows))throw new Error("shared input invalid");
       o.m.frameCount++;o.m.onFrameInner();
      }
     }
     for each(var key:String in ["fogCache","fogBmp","currentSight"]){if(!same(a.m[key],b.m[key]))throw new Error(key+" frame="+frame+" dim="+dim+" shared="+shared);passed++;}
     if(JSON.stringify(a.m.seenSub)!=JSON.stringify(b.m.seenSub))throw new Error("exploration frame="+frame);passed++;
    }
    a.m.resetOff();b.m.resetOff();
   }
  }
 }
}
