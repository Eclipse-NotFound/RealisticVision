package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import fe.World;
  import fe.loc.Tile;
  import fe.unit.UnitPlayer;
  import fe.graph.Grafon;
  public class SharedExplorationHarness extends Sprite {
    private var failures:int=0;
    private function check(v:Boolean,msg:String):void { if(!v)failures++;trace((v?"PASS ":"FAIL ")+msg); }
    public function SharedExplorationHarness() {
      try { run(); } catch(e:Error) { failures++;trace(e.getStackTrace()); }
      trace("SHARED COMPLETE failures="+failures);NativeApplication.nativeApplication.exit(failures?1:0);
    }
    private function step(m:RealisticVisionMod,n:int=40):void { for(var i:int=0;i<n;i++){ m.frameCount++;m.onFrameInner(); } }
    private function run():void {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.main=new Sprite();
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
      var m:RealisticVisionMod=new RealisticVisionMod();m.mswRegistered=true;m.publishExploration(w.main);step(m);
      var api:Object=w.main.getChildByName("RVExplorationAPI")["api"];
      check(api.version===1&&api.active(loc),"standalone RV publishes optional API without RConnect");
      var x:int=17,y:int=7,i:int=x+y*24,px:int=4+x*8,py:int=4+y*8;
      check(m.fov[i]==0&&m.seenSub[y*8*m.subW+x*8]!=1,"fixture target hidden behind wall");
      loc.getTile(x,y).visi=loc.getTile(x,y).t_visi=0;
      var nativeBefore:Number=loc.getTile(x,y).visi;
      var fovBefore:String=JSON.stringify(m.fov),seenBefore:String=JSON.stringify(m.seenSub),localBefore:String=JSON.stringify(m.explored);
      var sight:BitmapData=m.currentSight.clone();
      var rows:Array=[];
      for(var ry:int=0;ry<18;ry++){var row:String="";for(var rx:int=0;rx<24;rx++)row+=(ry==y&&rx==x)?"f1000000000000000":"00000000000000000";rows.push(row);}
      check(!api.merge(loc,["broken"]),"malformed payload rejected atomically");
      check(api.merge(loc,rows),"valid subcell history accepted");
      check(JSON.stringify(m.fov)==fovBefore&&JSON.stringify(m.explored)==localBefore&&JSON.stringify(m.seenSub)==seenBefore,
        "merge never writes local FOV or personal exploration");
      step(m);
      check((m.fogCache.getPixel32(px,py)>>>24)==166,"current shared subcell uses configured memory brightness");
      check((m.fogCache.getPixel32(px+1,py)>>>24)==255,"adjacent unseen subcell stays black");
      check(m.currentSight.compare(sight)===0,"shared memory does not expand current sight");
      var walls:Array=rows.concat();
      walls[8]=walls[8].substr(0,10*17)+"f0000000000000000"+walls[8].substr(11*17);
      check(api.merge(loc,walls),"remote wall light accepted as display input");
      step(m);
      check(m.currentSight.compare(sight)===0,"shared wall light does not grant unit visibility");
      check(loc.getTile(x,y).visi===nativeBefore&&loc.getTile(x,y).t_visi===nativeBefore,"native interaction values unchanged");
      var captured:Array=api.capture(loc);
      check(captured[y].substr(x*17+1,16)=="0000000000000000","API exports only locally explored subcells");
      m.cfgDim=0.8;step(m);
      check((m.fogCache.getPixel32(px,py)>>>24)==51,"memory brightness setting still controls shared area");
      m.cfgMode="classic";m.resetRoom(w,loc);step(m);
      check(m.memoryExplored(i)&&m.explored[i]!=1,"classic uses separate shared exploration");
      check((m.classicMemoryRaw.getPixel32(x,y+1)&255)==204,"classic uses configured shared memory shade");
      m.cfgMode="vanilla";m.resetRoom(w,loc);step(m);
      check(!api.active(loc)&&api.capture(loc)==null,"vanilla mode advertises native fallback");
      m.cfgMode="current";m.resetRoom(w,loc);step(m);
      check((m.fogCache.getPixel32(px,py)>>>24)==51,"shared partial history survives mode switches");
      m.cfgEnabled=false;check(!api.active(loc),"disabled RV advertises native fallback");m.cfgEnabled=true;
      var next:MotionLocation=new MotionLocation();next.id=loc.id;next.gg=loc.gg;w.loc=next;step(m);
      check(m.sharedLight==null&&!m.memorySeen(y*8*m.subW+x*8),"same-id new room does not inherit shared history");
      w.loc=loc;step(m);check(m.sharedLight!=null&&m.memorySeen(y*8*m.subW+x*8),"returning to existing room retains shared history");
      m.resetOff();check(m.sharedLight==null,"world reset releases shared map");
    }
  }
}
