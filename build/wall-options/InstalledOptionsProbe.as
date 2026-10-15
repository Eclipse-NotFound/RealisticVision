package {
  import flash.display.*;
  import flash.events.*;
  import flash.net.URLRequest;
  import flash.system.*;
  import flash.utils.*;
  import flash.desktop.NativeApplication;
  import flash.filesystem.*;
  import fe.World;

  /** Loads the unchanged production SWF. Game stubs belong to this probe only. */
  [SWF(width="1280",height="800",frameRate="30")]
  public class InstalledOptionsProbe extends Sprite {
    private var pages:Object = {};
    private var config:File = File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt");
    private var restoring:Boolean;
    private var start:int = getTimer();
    private var tested:Boolean = false;
    private var passed:int = 0;
    private var timer:Timer = new Timer(50);
    public function InstalledOptionsProbe() {
      restoring = config.exists;
      World.w = new World(); World.w.main = this; World.w.allStat = 0;
      var carrier:MovieClip = new MovieClip(); carrier.name = "ModSettingsCarrier";
      carrier["modAPI"] = {keybindVersion:1, localizationVersion:1,
        registerPage:function(id:String,title:String,rows:Array,close:Function,hint:String,meta:Object=null):void { pages[id] = rows; }};
      addChild(carrier);
      var loader:Loader = new Loader();
      var ctx:LoaderContext = new LoaderContext(false, ApplicationDomain.currentDomain); ctx.allowCodeImport = true;
      var root:Sprite = this;
      loader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {
        var cls:Class = loader.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod") as Class;
        cls["init"](root);
      });
      loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,function(e:Event):void { fail(String(e)); });
      loader.contentLoaderInfo.uncaughtErrorEvents.addEventListener(UncaughtErrorEvent.UNCAUGHT_ERROR,function(e:UncaughtErrorEvent):void {e.preventDefault();fail(String(e.error));});
      loader.load(new URLRequest("candidate.swf"),ctx);
      timer.addEventListener(TimerEvent.TIMER,tick); timer.start();
    }
    private function row(page:String,key:String):Object {
      for each(var item:Object in pages[page]) if(item.key == key) return item;
      return null;
    }
    private function readConfig():String {
      var stream:FileStream = new FileStream();stream.open(config,FileMode.READ);
      var text:String = stream.readUTFBytes(stream.bytesAvailable);stream.close();return text;
    }
    private function check(ok:Boolean,msg:String):void {if(!ok)throw new Error(msg);passed++;trace("PASS "+msg);}
    private function fail(msg:String):void {trace("FAIL "+msg);NativeApplication.nativeApplication.exit(1);}
    private function tick(e:Event):void {
      try {
        if(getTimer()-start>45000)throw new Error("timeout waiting for continuing heartbeat");
        if(!tested && pages.realisticvision && pages["realisticvision-hotkeys"]) {
          check(pages.realisticvision.length == 8,"settings page has eight controls");
          check(pages["realisticvision-hotkeys"].length == 3,"installed hotkey page retained");
          var bright:Object = row("realisticvision","wallbright");
          var mode:Object = row("realisticvision","mode");
          check(bright != null && bright.kind == "check" && bright.def === true,"wall option is a default-on checkbox");
          check(bright.get() === !restoring,restoring ? "off preference loaded in second process" : "missing old-config key defaults to on");
          check(mode.get() === 2,"current rendering mode retained");
          bright.set(restoring);
          check(bright.get() === restoring,"wall option responds immediately");
          check(readConfig().indexOf("wallbright="+(restoring ? "1" : "0")) >= 0,"wall preference saved immediately");
          mode.set(1);
          check(mode.get() === 1 && bright.get() === restoring,"classic mode preserves wall preference");
          mode.set(2);
          check(mode.get() === 2 && bright.get() === restoring,"current mode preserves wall preference");
          check(row("realisticvision-hotkeys","mode").get().code == 123,"mode hotkey remains F12 by default");
          tested = true;
        }
        if(tested) {
          var runtime:FileStream = new FileStream();
          runtime.open(File.applicationStorageDirectory.resolvePath("RVision.log"),FileMode.READ);
          var log:String = runtime.readUTFBytes(runtime.bytesAvailable); runtime.close();
          log = log.substr(log.lastIndexOf("init ok "));
          if(log.indexOf("tick 181") >= 0) {
            trace("INSTALLED OPTIONS COMPLETE passed="+passed+" restoring="+restoring);
            NativeApplication.nativeApplication.exit(0);
          }
        }
      } catch(err:Error) { fail(err.getStackTrace()); }
    }
  }
}
