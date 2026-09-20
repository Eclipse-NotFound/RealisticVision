package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.geom.*;
  import flash.utils.*;
  import fe.World;
  import fe.loc.Tile;
  import fe.graph.Grafon;
  import fe.unit.UnitPlayer;
  public class MotionHarness extends Sprite {
    public function MotionHarness() {
      try {run();NativeApplication.nativeApplication.exit(0);}
      catch(e:Error){trace("MOTION ERROR "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
    }
    private function emit(name:String,b:BitmapData):void {
      var a:ByteArray=b.encode(b.rect,new PNGEncoderOptions()),parts:Array=[],table:Array=[];
      for(var i:int=0;i<256;i++)table[i]=(i<16?"0":"")+i.toString(16);
      for(i=0;i<a.length;i++)parts.push(table[a[i]]);
      trace("PNG "+name+" "+parts.join(""));
    }
    private function shot(m:RealisticVisionMod):BitmapData {
      var b:BitmapData=new BitmapData(960,720,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);return b;
    }
    private function run():void {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);
      var m:RealisticVisionMod=new RealisticVisionMod();m.mswRegistered=true;m.cfgMode="current";
      // Actual normal scheduling, including startup fade, then constant-speed movement.
      for(var warm:int=0;warm<40;warm++){m.frameCount++;m.onFrameInner();}
      var frames:Array=[],shots:Array=[],last:BitmapData=m.fogBmp.clone(),frozen:int=0,maxFrozen:int=0,changed:int=0;
      for(var f:int=0;f<60;f++){
        loc.gg.X=200+4*(f+1);var oldV:int=m.fovVersion;
        m.motionPerf={};m.motionRays=0;m.motionTiles=0;
        var start:int=getTimer();m.frameCount++;m.onFrameInner();var cost:int=getTimer()-start;
        var diff:Object=m.fogBmp.compare(last),same:Boolean=diff is uint && uint(diff)==0;
        if(diff is BitmapData)BitmapData(diff).dispose();last.dispose();last=m.fogBmp.clone();
        if(same)frozen++;else{maxFrozen=Math.max(maxFrozen,frozen);frozen=0;changed++;}
        frames.push({f:f,x:loc.gg.X,eye:m.eyeX,ms:cost,recomputed:m.fovVersion!=oldV,changed:!same,pending:m.fogBlurPending,perf:m.motionPerf,rays:m.motionRays,tiles:m.motionTiles});
        if(f<24)shots.push(shot(m));
      }
      maxFrozen=Math.max(maxFrozen,frozen);
      trace("MOTION "+(maxFrozen>1?"RED":"GREEN")+" consecutive frozen frames="+maxFrozen+" display updates="+changed+"/60");
      trace("DATA "+JSON.stringify({frames:frames,maxFrozen:maxFrozen,updates:changed,worldStep:4,worldFPS:30}));
      for(f=0;f<shots.length;f++){emit("frame-"+(f<10?"0":"")+f,shots[f]);shots[f].dispose();}
      trace("MOTION COMPLETE");
    }
  }
}
