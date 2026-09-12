package {
  import flash.display.*;
  import flash.events.*;
  import flash.net.URLRequest;
  import flash.system.*;
  import flash.utils.*;
  import flash.desktop.NativeApplication;
  [SWF(width="1280",height="720",frameRate="30")]
  public class GameProbe extends Sprite {
    private var gameMain:*;
    private var mod:Loader=new Loader();
    private var worldClass:Class;
    private var modClass:Class;
    private var timer:Timer=new Timer(200);
    private var phase:int=0;
    private var ticks:int=0;
    private var settled:int=0;
    private var scene:String;
    public function GameProbe(main:*,requestedScene:String="random_mane") {
      scene=requestedScene;
      gameMain=main;
      gameReady(null);
      timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
    }
    private function error(e:Event):void {trace("GAME_PROBE FAIL "+e);NativeApplication.nativeApplication.exit(1);}
    private function gameReady(e:Event):void {
      worldClass=gameMain.loaderInfo.applicationDomain.getDefinition("fe.World") as Class;
      var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(gameMain.loaderInfo.applicationDomain));
      ctx.allowCodeImport=true;
      mod.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {
        modClass=mod.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod") as Class;
      });
      mod.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,error);
      mod.load(new URLRequest("app:/WallMod.swf"),ctx);
    }
    private function tick(e:Event):void {
      try {
        if(++ticks>300) {trace("GAME_PROBE FAIL timeout phase="+phase);NativeApplication.nativeApplication.exit(1);return;}
        if(!worldClass || !modClass) return;
        var w:*=worldClass["w"];
        if(!w || !w.landData || !w.allLandsLoaded) return;
        if(w.verror && w.verror.visible) {trace("GAME_PROBE FAIL game dialog "+w.verror.txt.text);NativeApplication.nativeApplication.exit(1);return;}
        if(phase==0) {w.mm.active=false;w.newGame(-1,"LP",null);phase=1;trace("GAME_PROBE new game");return;}
        if(phase==1 && w.gg && w.loc && w.loc.active && w.game.curLandId) {
          if(scene=="training") {
            trace("GAME_PROBE training start land="+w.game.curLandId+" loc="+w.loc.id);
            w.pers.healAll();w.game.beginMission("rbl");phase=10;return;
          }
          w.pers.healAll();w.game.beginMission("random_mane");phase=2;trace("GAME_PROBE travel random_mane");return;
        }
        if(scene=="training" && phase==10 && w.loc && w.loc.active && w.game.curLandId=="rbl" && w.land.act.id=="rbl") {
          if(w.land.locX!=0 || w.land.locY!=0) throw new Error("Unexpected base entrance");
          w.gg.setPos(w.loc.limX-60,600);
          if(w.land.gotoLoc(2)==null) throw new Error("Training room entrance blocked");
          w.gg.setPos(1080,640);phase=2;return;
        }
        if(scene=="training" && phase==2 && w.loc && w.loc.active && w.game.curLandId=="rbl" && w.land.locX==1 && w.land.locY==0) {
          if(++settled<20) return;
          phase=3;w.mm.active=true;captureTraining(w);NativeApplication.nativeApplication.exit(0);return;
        }
        if(phase==2 && w.loc && w.loc.active && w.game.curLandId=="random_mane" && w.land.act.id=="random_mane") {
          if(++settled<20) return;
          phase=3;w.mm.active=true;capture(w);NativeApplication.nativeApplication.exit(0);
        }
        if(ticks%25==0) trace("GAME_PROBE waiting phase="+phase+" loc="+(w.loc?w.loc.id:"none"));
      } catch(err:Error) {trace("GAME_PROBE FAIL "+err.getStackTrace());NativeApplication.nativeApplication.exit(1);}
    }
    private function emit(name:String,b:BitmapData):void {
      var bytes:ByteArray=b.encode(b.rect,new PNGEncoderOptions());var hex:String="";
      for(var i:int=0;i<bytes.length;i++){var h:String=bytes[i].toString(16);hex+=(h.length==1?"0":"")+h;}
      trace("PNG "+name+" "+hex);
    }
    private function shot(w:*):BitmapData {
      var b:BitmapData=new BitmapData(w.loc.spaceX*40,w.loc.spaceY*40,false,0);
      b.draw(w.grafon.visual,null,null,null,null,true);return b;
    }
    private function capture(w:*):void {
      var loc:*=w.loc;
      trace("GAME_PROBE capture "+loc.id+" "+loc.spaceX+"x"+loc.spaceY+" nativeBlack="+loc.black);
      w.black=true;loc.black=true;loc.base=false;
      w.grafon.setLight();w.grafon.visLight.visible=true;
      var reference:BitmapData=shot(w);emit("game-vanilla",reference);
      var snapshot:Array=[];
      for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++)
        snapshot.push([loc.getTile(x,y).visi,loc.getTile(x,y).t_visi]);
      var m:*=new modClass();
      for each(var mode:String in ["current","classic"]) {
        m.cfgMode=mode;m.resetRoom(w,loc);m.computeFov(loc);
        // Fix memory at zero for the original-wall equivalence comparison.
        m.cfgFadeStep=0;
        for(var i:int=0;i<loc.spaceX*loc.spaceY;i++) m.visCur[i]=1;
        for(var f:int=0;f<3;f++) {
          m.frameCount=f*2;m.fogDirty=true;
          if(mode=="current") m.applyVision(w,loc,f==0);else m.applyVisionClassic(w,loc,f==0);
        }
        var actual:BitmapData=shot(w);emit("game-"+mode,actual);
        var delta:int=0,count:int=0;
        for(y=0;y<actual.height;y++)for(x=0;x<actual.width;x++) {
          if(loc.getTile(int(x/40),int(y/40)).opac<1)continue;
          var a:uint=actual.getPixel(x,y),r:uint=reference.getPixel(x,y);
          delta=Math.max(delta,Math.abs((a&255)-(r&255)),Math.abs(((a>>8)&255)-((r>>8)&255)),Math.abs(((a>>16)&255)-((r>>16)&255)));count++;
        }
        var mutations:int=0;
        for(y=0;y<loc.spaceY;y++)for(x=0;x<loc.spaceX;x++) {
          var t:*=loc.getTile(x,y),old:Array=snapshot[x+y*loc.spaceX];
          if(t.visi!==old[0] || t.t_visi!==old[1])mutations++;
        }
        trace("GAME_PROBE "+mode+" wallPixels="+count+" maxChannelDelta="+delta+" nativeMutations="+mutations);
        if(count==0 || delta>2 || mutations) throw new Error("wall comparison failed");
      }
      trace("GAME_PROBE PASS");
    }
    private function captureTraining(w:*):void {
      var loc:*=w.loc;
      trace("GAME_PROBE training capture "+loc.id+" "+loc.spaceX+"x"+loc.spaceY+" player="+w.gg.X+","+w.gg.Y);
      w.black=true;loc.black=true;loc.base=false;
      w.grafon.setLight();w.grafon.visLight.visible=true;
      emit("training-vanilla",shot(w));
      var data:Object={room:loc.id,width:loc.spaceX,height:loc.spaceY,eye:[w.gg.X,w.gg.Y-w.gg.scY*0.75],tiles:[]};
      var snapshot:Array=[];
      for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++) {
        var t:*=loc.getTile(x,y);
        snapshot.push([t.visi,t.t_visi]);
        data.tiles.push({x:x,y:y,opac:t.opac,phis:t.phis,visi:t.visi});
      }
      var previous:*;
      for each(var mode:String in ["classic","current"]) {
        if(previous && previous.fogVis) previous.fogVis.visible=false;
        var m:*=new modClass();m.cfgMode=mode;m.resetRoom(w,loc);m.computeFov(loc);
        for(var f:int=0;f<24;f++) {
          m.frameCount=f;m.fogDirty=true;
          if(mode=="current")m.applyVision(w,loc,f==0);else m.applyVisionClassic(w,loc,f==0);
        }
        emit("training-"+mode,shot(w));
        var fog:BitmapData=new BitmapData(loc.spaceX*40,loc.spaceY*40,false,0xffffff);
        fog.draw(m.fogVis,null,null,null,null,true);emit("training-"+mode+"-fog",fog);fog.dispose();
        if(mode=="classic") {
          for(var i:int=0;i<data.tiles.length;i++) {
            data.tiles[i].fov=m.fov[i];data.tiles[i].explored=m.explored[i];data.tiles[i].memory=m.memCur[i];
          }
        }
        var mutations:int=0;
        for(y=0;y<loc.spaceY;y++)for(x=0;x<loc.spaceX;x++) {
          t=loc.getTile(x,y);var old:Array=snapshot[x+y*loc.spaceX];
          if(t.visi!==old[0] || t.t_visi!==old[1])mutations++;
        }
        if(mutations)throw new Error("Training capture changed native brightness");
        trace("GAME_PROBE training "+mode+" nativeMutations="+mutations);
        var started:int=getTimer();
        for(f=0;f<60;f++) {
          m.frameCount=f*2;m.fogDirty=f%3==0;
          if(mode=="current")m.applyVision(w,loc,f%3==0);else m.applyVisionClassic(w,loc,f%3==0);
        }
        trace("GAME_PROBE PERF "+mode+" 60 render updates ms="+(getTimer()-started)+" room=48x25");
        previous=m;
      }
      trace("DATA training "+JSON.stringify(data));
      trace("GAME_PROBE CAPTURED training (visual diagnosis only)");
    }
  }
}
