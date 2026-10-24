package
{
   import fe.*;
   import flash.display.Loader;
   import flash.display.LoaderInfo;
   import flash.display.MovieClip;
   import flash.display.StageAlign;
   import flash.events.Event;
   import flash.events.IOErrorEvent;
   import flash.net.SharedObject;
   import flash.net.URLLoader;
   import flash.net.URLRequest;
   import flash.system.LoaderContext;
   import flash.ui.ContextMenu;
   import flash.ui.ContextMenuItem;
   import flash.utils.Dictionary;
   import flash.utils.getQualifiedClassName;
   
   public class MainFE extends MovieClip
   {
      
      public var zastavka:MovieClip;
      
      internal var mainMenu:MainMenu;
      
      internal var modLoaderStatusReady:Boolean;
      
      internal var modLoaderRunId:String;
      
      internal var manifestUrlLoader:URLLoader;
      
      internal var modEntryByLoader:Dictionary;
      
      internal var sandyLoader:Loader;
      
      internal var rconnectLoader:Loader;
      
      internal var rvLoader:Loader;
      
      internal var mswLoader:Loader;
      
      internal var tdfcLoader:Loader;
      
      internal var modSettingsLoader:Loader;
      
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
            this.loadModsFromManifest();
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
      
      internal function loadMSWMod() : *
      {
         var _loc1_:LoaderContext;
         trace("MSWMod: load start");
         try
         {
            this.mswLoader = new Loader();
            _loc1_ = new LoaderContext(false);
            this.mswLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onMSWModLoaded);
            this.mswLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onMSWModError);
            this.mswLoader.load(new URLRequest("app:/mods/MoreSkills&Weapons/release/MoreSkillsWeaponsMod.swf"),_loc1_);
            trace("MSWMod: load issued");
         }
         catch(err:*)
         {
            trace("MSWMod: load threw " + err);
         }
      }
      
      internal function onMSWModError(param1:IOErrorEvent) : *
      {
         trace("MSWMod: IOError " + param1.text);
      }
      
      internal function onMSWModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("MSWMod: complete fired");
         try
         {
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("MoreSkillsWeaponsMod");
            trace("MSWMod: class=" + _loc2_);
            _loc2_.init(this);
            trace("MSWMod: init returned");
         }
         catch(err:*)
         {
            trace("MSWMod load/init error: " + err);
         }
      }
      
      internal function loadTDFCMod() : *
      {
         var _loc1_:LoaderContext;
         trace("TDFC: load start");
         try
         {
            this.tdfcLoader = new Loader();
            _loc1_ = new LoaderContext(false);
            this.tdfcLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onTDFCModLoaded);
            this.tdfcLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onTDFCModError);
            this.tdfcLoader.load(new URLRequest("app:/mods/TDFC/release/TDFCMod.swf"),_loc1_);
            trace("TDFC: load issued");
         }
         catch(err:*)
         {
            trace("TDFC: load threw " + err);
         }
      }
      
      internal function onTDFCModError(param1:IOErrorEvent) : *
      {
         trace("TDFC: IOError " + param1.text);
      }
      
      internal function onTDFCModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("TDFC: complete fired");
         try
         {
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("TDFCMod");
            trace("TDFC: class=" + _loc2_);
            _loc2_.init(this);
            trace("TDFC: init returned");
         }
         catch(err:*)
         {
            trace("TDFC load/init error: " + err);
         }
      }
      
      internal function loadRandomRoomsMod() : *
      {
         var _loc1_:LoaderContext;
         var _loc2_:Loader;
         trace("RandomRoomsMod: load start");
         try
         {
            _loc2_ = new Loader();
            _loc1_ = new LoaderContext(false);
            _loc2_.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onRandomRoomsModLoaded);
            _loc2_.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onRandomRoomsModError);
            _loc2_.load(new URLRequest("app:/mods/RandomRooms/release/RandomRoomsMod.swf"),_loc1_);
            trace("RandomRoomsMod: load issued");
         }
         catch(err:*)
         {
            try
            {
               SharedObject.getLocal("rr_loader","/").data["loaderr"] = String(err);
            }
            catch(e:*)
            {
            }
            trace("RandomRoomsMod: load threw " + err);
         }
      }
      
      internal function onRandomRoomsModError(param1:IOErrorEvent) : *
      {
         try
         {
            SharedObject.getLocal("rr_loader","/").data["ioerr"] = param1.text;
         }
         catch(e:*)
         {
         }
         trace("RandomRoomsMod: IOError " + param1.text);
      }
      
      internal function onRandomRoomsModLoaded(param1:Event) : *
      {
         var _loc2_:*;
         trace("RandomRoomsMod: complete fired");
         try
         {
            _loc2_ = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition("RandomRoomsMod");
            trace("RandomRoomsMod: class=" + _loc2_);
            _loc2_.init(this);
            trace("RandomRoomsMod: init returned");
         }
         catch(err:*)
         {
            try
            {
               SharedObject.getLocal("rr_loader","/").data["initerr"] = String(err);
            }
            catch(e:*)
            {
            }
            trace("RandomRoomsMod load/init error: " + err);
         }
      }
      
      internal function loadModSettingsMod() : void
      {
         try
         {
            this.modSettingsLoader = new Loader();
            this.modSettingsLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onModSettingsLoaded);
            this.modSettingsLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onModSettingsError);
            this.modSettingsLoader.load(new URLRequest("app:/mods/ModSettings/release/ModSettingsMod.swf"),new LoaderContext(false));
         }
         catch(err:*)
         {
            this.modSettingsStatus("load error: " + err);
         }
      }
      
      internal function onModSettingsLoaded(event:Event) : void
      {
         var entry:*;
         try
         {
            entry = LoaderInfo(event.currentTarget).applicationDomain.getDefinition("ModSettingsMod");
            entry.init(this);
            this.modSettingsStatus("init returned");
         }
         catch(err:*)
         {
            this.modSettingsStatus("init error: " + err);
         }
      }
      
      internal function onModSettingsError(event:IOErrorEvent) : void
      {
         this.modSettingsStatus("IO error: " + event.text);
      }
      
      internal function modSettingsStatus(message:String) : void
      {
         var status:SharedObject;
         trace("ModSettings: " + message);
         try
         {
            status = SharedObject.getLocal("ModSettingsLoader","/");
            status.data.status = message;
            status.flush();
         }
         catch(err:*)
         {
         }
      }
      
      internal function loadModsFromManifest() : *
      {
         var so:SharedObject;
         this.modLoaderRunId = "run_" + String(new Date().time) + "_" + String(int(Math.random() * 1000000));
         this.modLoaderStatusReady = false;
         try
         {
            so = SharedObject.getLocal("ModLoader","/");
            so.clear();
            so.data["session"] = this.modLoaderRunId;
            this.modLoaderStatusReady = so.flush() == "flushed";
         }
         catch(err:*)
         {
            this.modLoaderStatusReady = false;
         }
         this.modLoaderStatus("boot_start","v2 run=" + this.modLoaderRunId);
         try
         {
            this.manifestUrlLoader = new URLLoader();
            this.manifestUrlLoader.addEventListener(Event.COMPLETE,this.onManifestLoaded);
            this.manifestUrlLoader.addEventListener(IOErrorEvent.IO_ERROR,this.onManifestLoaderError);
            this.manifestUrlLoader.load(new URLRequest("app:/mods/loader-manifest.txt"));
         }
         catch(err:*)
         {
            this.modLoaderStatus("err_loader","manifest load threw " + err);
         }
      }
      
      internal function onManifestLoaderError(param1:IOErrorEvent) : *
      {
         this.modLoaderStatus("err_loader","manifest IOError " + param1.text);
      }
      
      internal function onManifestLoaded(param1:Event) : *
      {
         var colIdx:int;
         var urlText:String;
         var lines:Array;
         var i:int;
         var parts:Array;
         var ldr:Loader;
         var ctxt:LoaderContext;
         var line:String;
         var dir:String;
         var entry:String;
         var seen:Dictionary;
         var enabledCount:int;
         try
         {
            urlText = this.loaderInfo.url;
            colIdx = 2;
            if(urlText.indexOf("pfeUI") >= 0)
            {
               colIdx = 4;
            }
            else if(urlText.indexOf("DLC") >= 0)
            {
               colIdx = 3;
            }
            this.modEntryByLoader = new Dictionary();
            seen = new Dictionary();
            lines = String(this.manifestUrlLoader.data).split("\n");
            i = 0;
            for(; i < lines.length; i++)
            {
               line = this.modLoaderTrimText(String(lines[i]).split("\r").join(""));
               if(line.length > 0 && line.charAt(0) != "#")
               {
                  parts = line.split("|");
                  if(parts.length != 5)
                  {
                     this.modLoaderStatus("err_manifest_" + i,"line " + (i + 1) + " needs 5 columns");
                  }
                  else
                  {
                     dir = this.modLoaderTrimText(String(parts[0]));
                     entry = this.modLoaderTrimText(String(parts[1]));
                     if(dir.length == 0 || entry.length == 0 || dir == "." || dir.indexOf("..") >= 0 || dir.indexOf("/") >= 0 || dir.indexOf("\\") >= 0 || dir.indexOf(":") >= 0 || dir.indexOf("?") >= 0 || dir.indexOf("#") >= 0 || dir.indexOf("%") >= 0 || entry.indexOf("/") >= 0 || entry.indexOf("\\") >= 0 || entry.indexOf(".") >= 0 || entry.indexOf(" ") >= 0 || entry.indexOf(":") >= 0 || entry.indexOf("?") >= 0 || entry.indexOf("#") >= 0 || entry.indexOf("%") >= 0)
                     {
                        this.modLoaderStatus("err_manifest_" + i,"line " + (i + 1) + " invalid directory or entry");
                     }
                     else if(this.modLoaderTrimText(String(parts[2])) != "0" && this.modLoaderTrimText(String(parts[2])) != "1" || this.modLoaderTrimText(String(parts[3])) != "0" && this.modLoaderTrimText(String(parts[3])) != "1" || this.modLoaderTrimText(String(parts[4])) != "0" && this.modLoaderTrimText(String(parts[4])) != "1")
                     {
                        this.modLoaderStatus("err_manifest_" + i,"line " + (i + 1) + " invalid switch");
                     }
                     else if(seen[entry] != null)
                     {
                        this.modLoaderStatus("err_manifest_" + i,"line " + (i + 1) + " duplicate entry " + entry);
                     }
                     else
                     {
                        seen[entry] = true;
                        if(this.modLoaderTrimText(String(parts[colIdx])) == "1")
                        {
                           try
                           {
                              ldr = new Loader();
                              ctxt = new LoaderContext(false);
                              this.modEntryByLoader[ldr] = entry;
                              ldr.contentLoaderInfo.addEventListener(Event.COMPLETE,this.onModSwfLoaded);
                              ldr.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,this.onModSwfError);
                              this.modLoaderStatus("requested_" + entry,"line " + (i + 1));
                              ldr.load(new URLRequest("app:/mods/" + dir + "/release/" + entry + ".swf"),ctxt);
                              enabledCount++;
                           }
                           catch(rowErr:*)
                           {
                              this.modLoaderStatus("err_" + entry,"line " + (i + 1) + " load threw " + rowErr);
                           }
                           continue;
                        }
                     }
                  }
               }
            }
            this.modLoaderStatus("boot","v2 col=" + colIdx + " requested=" + enabledCount);
         }
         catch(err:*)
         {
            this.modLoaderStatus("err_loader","manifest parse threw " + err);
         }
      }
      
      internal function onModSwfError(param1:IOErrorEvent) : *
      {
         var ldr:Loader;
         try
         {
            ldr = LoaderInfo(param1.currentTarget).loader;
            this.modLoaderStatus("err_" + this.modEntryByLoader[ldr],"IOError " + param1.text);
         }
         catch(err:*)
         {
            this.modLoaderStatus("err_loader","SWF IOError handler threw " + err);
         }
      }
      
      internal function onModSwfLoaded(param1:Event) : *
      {
         var ldr:Loader;
         var entry:String;
         var cls:*;
         try
         {
            ldr = LoaderInfo(param1.currentTarget).loader;
            entry = String(this.modEntryByLoader[ldr]);
            cls = LoaderInfo(param1.currentTarget).applicationDomain.getDefinition(entry);
            cls.init(this);
            this.modLoaderStatus("ok_" + entry,"init");
         }
         catch(err:*)
         {
            this.modLoaderStatus("err_" + entry,"load/init error " + err);
         }
      }
      
      internal function modLoaderTrimText(value:String) : String
      {
         var textValue:String = value.split("﻿").join("");
         while(textValue.length > 0 && (textValue.charAt(0) == " " || textValue.charAt(0) == "\t"))
         {
            textValue = textValue.substr(1);
         }
         while(textValue.length > 0 && (textValue.charAt(textValue.length - 1) == " " || textValue.charAt(textValue.length - 1) == "\t"))
         {
            textValue = textValue.substr(0,textValue.length - 1);
         }
         return textValue;
      }
      
      internal function modLoaderStatus(key:String, message:String) : *
      {
         var so:SharedObject;
         trace("ModLoader[" + key + "] " + message);
         if(!this.modLoaderStatusReady)
         {
            return;
         }
         try
         {
            so = SharedObject.getLocal("ModLoader","/");
            so.data[key] = this.modLoaderRunId + "|" + message + " @" + new Date().time;
            if(so.flush() != "flushed")
            {
               this.modLoaderStatusReady = false;
            }
         }
         catch(err:*)
         {
            this.modLoaderStatusReady = false;
         }
      }
   }
}

