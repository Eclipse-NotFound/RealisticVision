package
{
   import fe.*;
   import flash.display.Loader;
   import flash.display.LoaderInfo;
   import flash.display.MovieClip;
   import flash.display.StageAlign;
   import flash.events.Event;
   import flash.events.IOErrorEvent;
   import flash.net.URLRequest;
   import flash.system.LoaderContext;
   import flash.ui.ContextMenu;
   import flash.ui.ContextMenuItem;
   import flash.utils.getQualifiedClassName;
   
   public class MainFE extends MovieClip
   {
      
      public var zastavka:MovieClip;
      
      internal var mainMenu:MainMenu;
      
      internal var sandyLoader:Loader;
      
      internal var rconnectLoader:Loader;
      
      internal var rvLoader:Loader;
      
      public function MainFE()
      {
         super();
         stage.scaleMode = "noScale";
         stage.align = StageAlign.TOP_LEFT;
         stage.color = 0;
         var _loc1_:ContextMenu = new ContextMenu();
         _loc1_.hideBuiltInItems();
         _loc1_.builtInItems.quality = true;
         contextMenu = _loc1_;
         _loc1_.customItems.push(new ContextMenuItem("Привет!",false,true,false));
         stop();
         addEventListener(Event.ENTER_FRAME,this.onEnterFrameLoader);
      }
      
      internal function onEnterFrameLoader(param1:Event) : *
      {
         var _loc2_:uint = loaderInfo.bytesLoaded;
         var _loc3_:uint = loaderInfo.bytesTotal;
         if(this.zastavka.alpha < 1)
         {
            this.zastavka.alpha += 0.05;
         }
         this.zastavka.progres.text = "Loading " + Math.round(_loc2_ / _loc3_ * 100) + "%";
         if(_loc2_ >= _loc3_)
         {
            this.zastavka.visible = false;
            removeEventListener(Event.ENTER_FRAME,this.onEnterFrameLoader);
            nextFrame();
            this.mainMenu = new MainMenu(this);
            this.loadSandevistanMod();
            this.loadRConnectMod();
            this.loadRVisionMod();
         }
      }
      
      internal function loadSandevistanMod() : *
      {
         var _loc1_:LoaderContext;
         trace("SandyMod: load start");
         try
         {
            this.sandyLoader = new Loader();
            _loc1_ = new LoaderContext(false);
            this.sandyLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onSandevistanModLoaded);
            this.sandyLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onSandevistanModError);
            this.sandyLoader.load(new URLRequest("app:/mods/Sandevistan/release/SandevistanMod.swf"),_loc1_);
            trace("SandyMod: load issued");
         }
         catch(err:*)
         {
            trace("SandyMod: load threw " + err);
         }
      }
      
      internal function onSandevistanModError(param1:IOErrorEvent) : *
      {
         trace("SandyMod: IOError " + param1.text);
      }
      
      internal function onSandevistanModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("SandyMod: complete fired");
         try
         {
            trace("SandyMod: content=" + param1.currentTarget.content);
            trace("SandyMod: qname=" + getQualifiedClassName(param1.currentTarget.content));
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("SandevistanMod");
            trace("SandyMod: class=" + _loc2_);
            _loc2_.init(this);
            trace("SandyMod: init returned");
         }
         catch(err:*)
         {
            trace("SandyMod load/init error: " + err);
         }
      }
      
      internal function loadRConnectMod() : *
      {
         var _loc1_:LoaderContext;
         trace("RConnectMod: load start");
         try
         {
            this.rconnectLoader = new Loader();
            _loc1_ = new LoaderContext(false);
            this.rconnectLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onRConnectModLoaded);
            this.rconnectLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onRConnectModError);
            this.rconnectLoader.load(new URLRequest("app:/mods/Rconnect/release/RConnectMod.swf"),_loc1_);
            trace("RConnectMod: load issued");
         }
         catch(err:*)
         {
            trace("RConnectMod: load threw " + err);
         }
      }
      
      internal function onRConnectModError(param1:IOErrorEvent) : *
      {
         trace("RConnectMod: IOError " + param1.text);
      }
      
      internal function onRConnectModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("RConnectMod: complete fired");
         try
         {
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("RConnectMod");
            trace("RConnectMod: class=" + _loc2_);
            _loc2_.init(this);
            trace("RConnectMod: init returned");
         }
         catch(err:*)
         {
            trace("RConnectMod load/init error: " + err);
         }
      }
      
      internal function loadRVisionMod() : *
      {
         var _loc1_:LoaderContext;
         trace("RVision: load start");
         try
         {
            this.rvLoader = new Loader();
            _loc1_ = new LoaderContext(false);
            this.rvLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onRVisionModLoaded);
            this.rvLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onRVisionModError);
            this.rvLoader.load(new URLRequest("app:/mods/RealisticVision/release/RealisticVisionMod.swf"),_loc1_);
            trace("RVision: load issued");
         }
         catch(err:*)
         {
            trace("RVision: load threw " + err);
         }
      }
      
      internal function onRVisionModError(param1:IOErrorEvent) : *
      {
         trace("RVision: IOError " + param1.text);
      }
      
      internal function onRVisionModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("RVision: complete fired");
         try
         {
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("RealisticVisionMod");
            trace("RVision: class=" + _loc2_);
            _loc2_.init(this);
            trace("RVision: init returned");
         }
         catch(err:*)
         {
            trace("RVision load/init error: " + err);
         }
      }
   }
}

