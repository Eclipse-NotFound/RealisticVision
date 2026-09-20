package {
  import flash.display.*;
  import flash.events.*;
  import flash.net.URLRequest;
  import flash.system.*;
  import flash.utils.*;
  import flash.desktop.NativeApplication;
  public class GameMotionProbe extends Sprite {
    private var gameMain:*,worldClass:Class,modClass:Class;
    private var mod:Loader=new Loader(),timer:Timer=new Timer(200);
    private var phase:int=0,ticks:int=0,settled:int=0;
    public function GameMotionProbe(main:*) {
      gameMain=main;worldClass=main.loaderInfo.applicationDomain.getDefinition("fe.World") as Class;
      var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(main.loaderInfo.applicationDomain));ctx.allowCodeImport=true;
      mod.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void{modClass=mod.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod") as Class;});
      mod.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,function(e:Event):void{trace("MOTION_GAME ERROR "+e);NativeApplication.nativeApplication.exit(1);});
      mod.load(new URLRequest("app:/MotionMod.swf"),ctx);timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
    }
    private function tick(e:Event):void {
      try{
        if(++ticks>300)throw Error("timeout phase "+phase);
        if(!worldClass||!modClass)return;var w:*=worldClass["w"];
        if(!w||!w.landData||!w.allLandsLoaded)return;
        if(w.verror && w.verror.visible)throw Error(w.verror.txt.text);
        if(phase==0){w.mm.active=false;w.newGame(-1,"LP",null);phase=1;return;}
        if(phase==1 && w.gg && w.loc && w.loc.active && w.game.curLandId){w.pers.healAll();w.game.beginMission("rbl");phase=2;return;}
        if(phase==2 && w.loc && w.loc.active && w.game.curLandId=="rbl" && w.land.act.id=="rbl"){
          w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw Error("room blocked");w.gg.setPos(480,640);phase=3;return;
        }
        if(phase==3 && w.loc && w.loc.active && w.land.locX==1 && w.land.locY==0){
          if(++settled<20)return;phase=4;w.mm.active=true;
          MotionCapture.run(w,modClass,gameMain.stage.frameRate);
          NativeApplication.nativeApplication.exit(0);
        }
      }catch(err:Error){trace("MOTION_GAME ERROR "+err.getStackTrace());NativeApplication.nativeApplication.exit(1);}
    }
  }
}
