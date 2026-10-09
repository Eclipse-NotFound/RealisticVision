package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.utils.getTimer;
  import fe.World;
  import fe.loc.Tile;
  import fe.unit.UnitPlayer;
  import fe.graph.Grafon;
  // Compiled only with a private-to-public test copy, never into production.
  public class ExplorationCacheHarness extends Sprite {
    private var failures:int=0, comparisons:int=0;
    private function check(ok:Boolean,s:String):void {if(!ok)failures++;trace((ok?"PASS ":"FAIL ")+s);}
    public function ExplorationCacheHarness() {
      try {run();}catch(e:Error){failures++;trace(e.getStackTrace());}
      trace("CACHE COMPLETE failures="+failures+" comparisons="+comparisons);
      NativeApplication.nativeApplication.exit(failures?1:0);
    }
    private function compare(m:RealisticVisionMod,loc:MotionLocation):void {
      var expected:Array=m.referenceCapture(loc), actual:Array=m.captureExploration(loc);
      comparisons++;
      if(JSON.stringify(expected)!==JSON.stringify(actual))throw new Error("cache mismatch at "+comparisons);
      // A caller replacing a returned row must not corrupt the internal cache.
      if(actual!=null)actual[0]="caller-owned";
      if(JSON.stringify(expected)!==JSON.stringify(m.captureExploration(loc)))throw new Error("returned row alias");
    }
    private function run():void {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.main=new Sprite();
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
      var m:RealisticVisionMod=new RealisticVisionMod();m.mswRegistered=true;
      var rooms:Array=[loc];
      for(var room:int=0;room<5;room++) {
        if(room>0){loc=new MotionLocation();loc.id="cache-"+room;loc.gg=w.gg;rooms.push(loc);w.loc=loc;}
        if(room==2){loc.spaceX=18;loc.spaceY=24;}
        m.cfgMode="current";m.resetRoom(w,loc);
        compare(m,loc);
        for(var i:int=0;i<90;i++) {
          loc.gg.X=120+(i*13)%700;loc.gg.Y=160+(i*11)%420;
          loc.getTile(6,8).opac=(i%11)/10;
          loc.getTile(7,9).water=(i%3)==0?1:0;
          loc.opacWater=(i%7)/8;
          // Light must be sampled even when the subcell string is cached.
          loc.getTile(17,7).visi=(i%16)/15;
          m.frameCount++;m.onFrameInner();compare(m,loc);
          if(i==30||i==60){m.cfgMode=i==30?"classic":"current";m.resetRoom(w,loc);compare(m,loc);}
          if(i==45){m.mergeExploration(loc,m.captureExploration(loc));compare(m,loc);}
        }
        check(true,"live visibility, partial history, brightness and mode changes agree in room "+room);
      }
      loc=rooms[0];w.loc=loc;m.resetRoom(w,loc);compare(m,loc);
      check(true,"return to an existing room rebuilds cache from restored history");
      m.cfgEnabled=false;compare(m,loc);m.cfgEnabled=true;
      m.cfgMode="vanilla";m.resetRoom(w,loc);compare(m,loc);
      check(true,"disabled and vanilla API fallbacks are unchanged");
      m.cfgMode="current";m.resetRoom(w,loc);compare(m,loc);
      var start:int=getTimer();for(i=0;i<300;i++)m.referenceCapture(loc);
      var originalMs:int=getTimer()-start;start=getTimer();for(i=0;i<300;i++)m.captureExploration(loc);
      trace("CACHE BENCH "+JSON.stringify({iterations:300,originalMs:originalMs,cachedMs:getTimer()-start,tiles:loc.spaceX*loc.spaceY}));
      m.resetOff();check(m.explorationBits==null,"world reset releases packed history");
      m.resetRoom(w,loc);compare(m,loc);check(true,"world reset and same room rebuild have no stale strings");
    }
  }
}
