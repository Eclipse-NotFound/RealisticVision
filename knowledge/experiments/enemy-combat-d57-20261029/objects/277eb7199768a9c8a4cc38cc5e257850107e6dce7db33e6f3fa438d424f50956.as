package fe
{
   import fe.graph.Displ;
   import fe.inter.PipBuck;
   import fe.inter.PipPageOpt;
   import flash.display.LoaderInfo;
   import flash.display.MovieClip;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.events.MouseEvent;
   import flash.net.FileFilter;
   import flash.net.FileReference;
   import flash.text.StyleSheet;
   import flash.text.TextFormat;
   import flash.utils.Timer;
   
   public class MainMenu
   {
      
      internal var version:String = "1.0.2";
      
      internal var mm:MovieClip;
      
      public var main:Sprite;
      
      internal var world:World;
      
      public var active:Boolean = true;
      
      public var loaded:Boolean = false;
      
      internal var newGameMode:int = 2;
      
      internal var newGameDif:int = 2;
      
      internal var loadCell:int = -1;
      
      internal var loadReg:int = 0;
      
      internal var command:int = 0;
      
      internal var com:String = "";
      
      internal var mmp:MovieClip;
      
      internal var pip:PipBuck;
      
      internal var displ:Displ;
      
      internal var animOn:Boolean = true;
      
      internal var langReload:Boolean = false;
      
      internal var kolDifs:int = 5;
      
      internal var kolOpts:int = 6;
      
      internal var butsLang:Array;
      
      internal var stn:int = 0;
      
      public var style:StyleSheet = new StyleSheet();
      
      internal var styleObj:Object = new Object();
      
      internal var format:TextFormat = new TextFormat();
      
      internal var file:FileReference = new FileReference();
      
      internal var ffil:Array;
      
      internal var arr:Array = new Array();
      
      internal var mainTimer:Timer;
      
      public function MainMenu(param1:Sprite)
      {
         super();
         this.main = param1;
         this.mm = new visMainMenu();
         this.mm.dialLoad.visible = false;
         this.mm.dialNew.visible = false;
         this.mm.dialAbout.visible = false;
         this.main.stage.addEventListener(Event.RESIZE,this.resizeDisplay);
         this.main.stage.addEventListener(Event.ENTER_FRAME,this.mainStep);
         this.showButtons(false);
         this.mainMenuOn();
         var _loc2_:Object = LoaderInfo(this.main.root.loaderInfo).parameters;
         this.world = new World(this.main,_loc2_);
         this.world.mm = this;
         this.mm.testtest.visible = this.world.testMode;
         this.mm.info.visible = false;
         Snd.initSnd();
         this.setMenuSize();
         this.displ = new Displ(this.mm.pipka,this.mm.groza);
         this.mm.groza.visible = false;
         this.format.font = "_sans";
         this.format.color = 16777215;
         this.format.size = 28;
         this.styleObj.fontWeight = "bold";
         this.styleObj.color = "#FFFF00";
         this.style.setStyle(".yel",this.styleObj);
         this.styleObj.fontWeight = "normal";
         this.styleObj.color = "#00FF99";
         this.styleObj.fontSize = "12";
         this.style.setStyle(".music",this.styleObj);
         this.styleObj.fontWeight = "normal";
         this.styleObj.color = "#66FF66";
         this.styleObj.fontSize = undefined;
         this.style.setStyle("a",this.styleObj);
         this.styleObj.textDecoration = "underline";
         this.style.setStyle("a:hover",this.styleObj);
         this.mm.info.txt.styleSheet = this.style;
         this.mm.link.l1.styleSheet = this.style;
         this.mm.link.l2.styleSheet = this.style;
      }
      
      public function mainMenuOn() : *
      {
         this.active = true;
         this.mm.butNewGame.addEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butNewGame.addEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butLoadGame.addEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butLoadGame.addEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butContGame.addEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butContGame.addEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butOpt.addEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butOpt.addEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butAbout.addEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butAbout.addEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butOpt.addEventListener(MouseEvent.CLICK,this.funOpt);
         this.mm.butNewGame.addEventListener(MouseEvent.CLICK,this.funNewGame);
         this.mm.butLoadGame.addEventListener(MouseEvent.CLICK,this.funLoadGame);
         this.mm.butContGame.addEventListener(MouseEvent.CLICK,this.funContGame);
         this.mm.butAbout.addEventListener(MouseEvent.CLICK,this.funAbout);
         this.mm.adv.addEventListener(MouseEvent.CLICK,this.funAdv);
         this.mm.adv.addEventListener(MouseEvent.RIGHT_CLICK,this.funAdvR);
         if(!this.main.contains(this.mm))
         {
            this.main.addChild(this.mm);
         }
         this.file.addEventListener(Event.SELECT,this.selectHandler);
         this.file.addEventListener(Event.COMPLETE,this.completeHandler);
      }
      
      public function mainMenuOff() : *
      {
         var _loc1_:* = undefined;
         this.active = false;
         this.mm.butNewGame.removeEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butNewGame.removeEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butLoadGame.removeEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butLoadGame.removeEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butContGame.removeEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butContGame.removeEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butOpt.removeEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butOpt.removeEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butAbout.removeEventListener(MouseEvent.MOUSE_OVER,this.funOver);
         this.mm.butAbout.removeEventListener(MouseEvent.MOUSE_OUT,this.funOut);
         this.mm.butOpt.removeEventListener(MouseEvent.CLICK,this.funOpt);
         this.mm.butNewGame.removeEventListener(MouseEvent.CLICK,this.funNewGame);
         this.mm.butLoadGame.removeEventListener(MouseEvent.CLICK,this.funLoadGame);
         this.mm.butContGame.removeEventListener(MouseEvent.CLICK,this.funContGame);
         this.mm.butAbout.removeEventListener(MouseEvent.CLICK,this.funAbout);
         this.mm.adv.removeEventListener(MouseEvent.CLICK,this.funAdv);
         this.mm.adv.removeEventListener(MouseEvent.RIGHT_CLICK,this.funAdvR);
         this.file.removeEventListener(Event.SELECT,this.selectHandler);
         this.file.removeEventListener(Event.COMPLETE,this.completeHandler);
         for each(_loc1_ in this.butsLang)
         {
            if(_loc1_)
            {
               _loc1_.removeEventListener(MouseEvent.CLICK,this.funLang);
            }
         }
         if(this.main.contains(this.mm))
         {
            this.main.removeChild(this.mm);
         }
         this.world.vwait.visible = true;
         this.world.vwait.progres.text = Res.guiText("loading");
      }
      
      public function funNewGame(param1:MouseEvent) : *
      {
         this.world.mmArmor = false;
         this.mainLoadOff();
         this.mainNewOn();
      }
      
      public function funLoadGame(param1:MouseEvent) : *
      {
         this.world.mmArmor = true;
         this.mainNewOff();
         this.loadReg = 0;
         this.mainLoadOn();
      }
      
      public function funContGame(param1:MouseEvent) : *
      {
         var _loc5_:Object = null;
         var _loc2_:int = 0;
         var _loc3_:Number = 0;
         var _loc4_:* = 0;
         while(_loc4_ <= this.world.saveKol)
         {
            _loc5_ = World.w.getSave(_loc4_);
            if((Boolean(_loc5_)) && Boolean(_loc5_.est) && _loc5_.date > _loc3_)
            {
               _loc2_ = _loc4_;
               _loc3_ = Number(_loc5_.date);
            }
            _loc4_++;
         }
         _loc5_ = World.w.getSave(_loc2_);
         if((Boolean(_loc5_)) && Boolean(_loc5_.est))
         {
            this.mainMenuOff();
            this.loadCell = _loc2_;
            this.command = 3;
         }
         else
         {
            this.mainNewOn();
            this.mainLoadOff();
         }
      }
      
      public function funOver(param1:MouseEvent) : *
      {
         (param1.currentTarget as MovieClip).fon.scaleX = 1;
         (param1.currentTarget as MovieClip).fon.alpha = 1.5;
      }
      
      public function funOut(param1:MouseEvent) : *
      {
         (param1.currentTarget as MovieClip).fon.scaleX = 0.7;
         (param1.currentTarget as MovieClip).fon.alpha = 1;
      }
      
      public function setLangButtons() : *
      {
         var _loc1_:* = undefined;
         var _loc2_:* = undefined;
         var _loc3_:MovieClip = null;
         this.butsLang = new Array();
         if(this.world.kolLangs > 1)
         {
            _loc1_ = this.world.kolLangs;
            for each(_loc2_ in this.world.langsXML.lang)
            {
               _loc1_--;
               _loc3_ = new butLang();
               this.butsLang[_loc1_] = _loc3_;
               _loc3_.lang.text = _loc2_[0];
               _loc3_.y = -_loc1_ * 40;
               _loc3_.n.text = _loc2_.@id;
               _loc3_.n.visible = false;
               _loc3_.addEventListener(MouseEvent.CLICK,this.funLang);
               this.mm.lang.addChild(_loc3_);
            }
         }
      }
      
      public function setMainLang() : *
      {
         var _loc1_:* = undefined;
         this.setMainButton(this.mm.butContGame,Res.guiText("contgame"));
         this.setMainButton(this.mm.butNewGame,Res.guiText("newgame"));
         this.setMainButton(this.mm.butLoadGame,Res.guiText("loadgame"));
         this.setMainButton(this.mm.butOpt,Res.guiText("options"));
         this.setMainButton(this.mm.butAbout,Res.guiText("about"));
         this.mm.dialNew.title.text = Res.guiText("newgame");
         this.mm.dialLoad.title.text = Res.guiText("loadgame");
         this.mm.dialLoad.title2.text = Res.guiText("select_slot");
         this.mm.version.htmlText = "<b>" + Res.guiText("version") + " " + this.version + "</b>";
         this.mm.dialLoad.butCancel.text.text = this.mm.dialNew.butCancel.text.text = Res.guiText("cancel");
         this.mm.dialLoad.butFile.text.text = Res.pipText("loadfile");
         this.mm.dialLoad.warn.text = this.mm.dialNew.warn.text = Res.guiText("loadwarn");
         this.mm.dialNew.infoName.text = Res.guiText("inputname");
         this.mm.dialNew.hardOpt.text = Res.guiText("hardopt");
         this.mm.dialNew.butOk.text.text = "OK";
         this.mm.dialNew.inputName.text = Res.txt("u","littlepip");
         this.mm.dialNew.maxChars = 32;
         _loc1_ = 0;
         while(_loc1_ < this.kolDifs)
         {
            this.mm.dialNew["dif" + _loc1_].mode.text = Res.guiText("dif" + _loc1_);
            this.mm.dialNew["dif" + _loc1_].modeinfo.text = Res.formatText(Res.txt("g","dif" + _loc1_,1));
            _loc1_++;
         }
         _loc1_ = 1;
         while(_loc1_ <= this.kolOpts)
         {
            this.mm.dialNew["infoOpt" + _loc1_].text = Res.guiText("opt" + _loc1_);
            _loc1_++;
         }
         this.mm.dialNew.butVid.mode.text = Res.guiText("butvid");
         if(this.world.app)
         {
            this.world.app.setLang();
         }
         this.mm.adv.text = Res.advText(this.world.nadv);
         this.mm.adv.y = this.main.stage.stageHeight - this.mm.adv.textHeight - 40;
         this.mm.info.txt.htmlText = Res.txt("g","inform") + "<br>" + Res.txt("g","inform",1);
         this.mm.info.visible = this.mm.info.txt.text.length > 0;
         this.setScrollInfo();
      }
      
      internal function setMainButton(param1:MovieClip, param2:String) : *
      {
         param1.txt.text = param2;
         param1.glow.text = param2;
         param1.txt.visible = param1.glow.textWidth < 1;
      }
      
      public function setMenuSize() : *
      {
         this.mm.adv.y = this.main.stage.stageHeight - this.mm.adv.textHeight - 40;
         this.mm.version.y = this.main.stage.stageHeight - 58;
         this.mm.link.y = this.main.stage.stageHeight - 125;
         var _loc1_:* = this.main.stage.stageHeight - 400;
         if(_loc1_ < 280)
         {
            _loc1_ = 280;
         }
         this.mm.dialLoad.x = this.mm.dialNew.x = this.world.app.vis.x = this.main.stage.stageWidth / 2;
         this.mm.dialLoad.y = this.mm.dialNew.y = this.world.app.vis.y = _loc1_;
         this.mm.lang.x = this.main.stage.stageWidth - 30;
         this.mm.lang.y = this.main.stage.stageHeight - 50;
         this.mm.info.txt.height = this.mm.info.scroll.height = this.mm.link.y - this.mm.info.y - 20;
         this.setScrollInfo();
      }
      
      internal function setScrollInfo() : *
      {
         if(this.mm.info.txt.height < this.mm.info.txt.textHeight)
         {
            this.mm.info.scroll.maxScrollPosition = this.mm.info.txt.maxScrollV;
            this.mm.info.scroll.visible = true;
         }
         else
         {
            this.mm.info.scroll.visible = false;
         }
      }
      
      public function resizeDisplay(param1:Event) : *
      {
         this.world.resizeScreen();
         if(this.active)
         {
            this.setMenuSize();
         }
      }
      
      public function mainLoadOn() : *
      {
         var _loc2_:MovieClip = null;
         var _loc3_:Object = null;
         var _loc4_:Object = null;
         this.mm.dialLoad.visible = true;
         this.mm.dialLoad.title2.visible = this.loadReg == 1;
         this.mm.dialLoad.title.visible = this.loadReg == 0;
         this.mm.dialLoad.slot0.visible = this.loadReg == 0;
         this.mm.dialLoad.info.text = "";
         this.mm.dialLoad.nazv.text = "";
         this.mm.dialLoad.pers.visible = false;
         this.arr = new Array();
         var _loc1_:* = 0;
         while(_loc1_ <= this.world.saveKol)
         {
            _loc2_ = this.mm.dialLoad["slot" + _loc1_];
            _loc3_ = World.w.getSave(_loc1_);
            _loc4_ = PipPageOpt.saveObj(_loc3_,_loc1_);
            this.arr.push(_loc4_);
            _loc2_.id.text = _loc1_;
            _loc2_.id.visible = false;
            if(_loc3_ != null && _loc3_.est != null)
            {
               _loc2_.nazv.text = _loc1_ == 0 ? Res.pipText("autoslot") : Res.pipText("saveslot") + " " + _loc1_;
               _loc2_.ggName.text = _loc3_.pers.persName == null ? "-------" : _loc3_.pers.persName;
               if(_loc3_.pers.level != null)
               {
                  _loc2_.ggName.text += " (" + _loc3_.pers.level + ")";
               }
               if(_loc3_.pers.dead)
               {
                  _loc2_.nazv.text += " [†]";
               }
               else if(_loc3_.pers.hardcore)
               {
                  _loc2_.nazv.text += " {!}";
               }
               _loc2_.date.text = _loc3_.date == null ? "-------" : Res.getDate(_loc3_.date);
               _loc2_.land.text = _loc3_.date == null ? "" : Res.txt("m",_loc3_.game.land).substr(0,18);
            }
            else
            {
               _loc2_.nazv.text = Res.pipText("freeslot");
               _loc2_.ggName.text = _loc2_.land.text = _loc2_.date.text = "";
            }
            _loc2_.addEventListener(MouseEvent.CLICK,this.funLoadSlot);
            _loc2_.addEventListener(MouseEvent.MOUSE_OVER,this.funOverSlot);
            _loc1_++;
         }
         this.mm.dialLoad.butCancel.addEventListener(MouseEvent.CLICK,this.funLoadCancel);
         this.mm.dialLoad.butFile.addEventListener(MouseEvent.CLICK,this.funLoadFile);
         this.animOn = false;
      }
      
      public function mainLoadOff() : *
      {
         var _loc2_:MovieClip = null;
         this.mm.dialLoad.visible = false;
         if(this.mm.dialLoad.butCancel.hasEventListener(MouseEvent.CLICK))
         {
            this.mm.dialLoad.butCancel.removeEventListener(MouseEvent.CLICK,this.funLoadCancel);
            this.mm.dialLoad.butFile.removeEventListener(MouseEvent.CLICK,this.funLoadFile);
         }
         var _loc1_:* = 0;
         while(_loc1_ <= this.world.saveKol)
         {
            _loc2_ = this.mm.dialLoad["slot" + _loc1_];
            if(_loc2_.hasEventListener(MouseEvent.CLICK))
            {
               _loc2_.removeEventListener(MouseEvent.CLICK,this.funLoadSlot);
               _loc2_.removeEventListener(MouseEvent.MOUSE_OVER,this.funOverSlot);
            }
            _loc1_++;
         }
         this.animOn = true;
      }
      
      public function funLoadCancel(param1:MouseEvent) : *
      {
         this.mainLoadOff();
      }
      
      public function funLoadSlot(param1:MouseEvent) : *
      {
         this.loadCell = param1.currentTarget.id.text;
         if(this.loadReg == 1 && this.loadCell == 0)
         {
            return;
         }
         if(this.loadReg == 0 && param1.currentTarget.ggName.text == "")
         {
            return;
         }
         this.mainLoadOff();
         this.mainMenuOff();
         this.command = 3;
         if(this.loadReg == 1)
         {
            this.com = "new";
         }
         else
         {
            this.com = "load";
         }
      }
      
      public function funOverSlot(param1:MouseEvent) : *
      {
         PipPageOpt.showSaveInfo(this.arr[param1.currentTarget.id.text],this.mm.dialLoad);
      }
      
      public function funLoadFile(param1:MouseEvent) : *
      {
         this.ffil = [new FileFilter(Res.pipText("gamesaves") + " (*.sav)","*.sav")];
         this.file.browse(this.ffil);
      }
      
      private function selectHandler(param1:Event) : void
      {
         this.file.load();
      }
      
      private function completeHandler(param1:Event) : void
      {
         var _loc2_:Object = null;
         try
         {
            _loc2_ = this.file.data.readObject();
            if(Boolean(_loc2_) && _loc2_.est == 1)
            {
               this.loadCell = 99;
               this.world.loaddata = _loc2_;
               this.mainLoadOff();
               this.mainMenuOff();
               this.command = 3;
               this.com = "load";
               return;
            }
         }
         catch(err:*)
         {
         }
         trace("Error load");
      }
      
      public function mainNewOn() : *
      {
         var _loc1_:* = undefined;
         this.mm.dialNew.visible = true;
         this.mm.dialNew.butCancel.addEventListener(MouseEvent.CLICK,this.funNewCancel);
         this.mm.dialNew.butOk.addEventListener(MouseEvent.CLICK,this.funNewOk);
         this.mm.dialNew.butVid.addEventListener(MouseEvent.CLICK,this.funNewVid);
         _loc1_ = 0;
         while(_loc1_ < this.kolDifs)
         {
            this.mm.dialNew["dif" + _loc1_].addEventListener(MouseEvent.CLICK,this.funNewDif);
            this.mm.dialNew["dif" + _loc1_].addEventListener(MouseEvent.MOUSE_OVER,this.infoMode);
            _loc1_++;
         }
         _loc1_ = 1;
         while(_loc1_ <= this.kolOpts)
         {
            this.mm.dialNew["infoOpt" + _loc1_].addEventListener(MouseEvent.MOUSE_OVER,this.infoOpt);
            this.mm.dialNew["checkOpt" + _loc1_].addEventListener(MouseEvent.MOUSE_OVER,this.infoOpt);
            _loc1_++;
         }
         this.updNewMode();
         this.mm.dialNew.pers.gotoAndStop(2);
         this.mm.dialNew.pers.gotoAndStop(1);
         this.animOn = false;
      }
      
      public function mainNewOff() : *
      {
         var _loc1_:* = undefined;
         this.mm.dialNew.visible = false;
         if(this.mm.dialNew.butCancel.hasEventListener(MouseEvent.CLICK))
         {
            this.mm.dialNew.butCancel.removeEventListener(MouseEvent.CLICK,this.funNewCancel);
         }
         if(this.mm.dialNew.butOk.hasEventListener(MouseEvent.CLICK))
         {
            this.mm.dialNew.butOk.removeEventListener(MouseEvent.CLICK,this.funNewOk);
         }
         if(this.mm.dialNew.butOk.hasEventListener(MouseEvent.CLICK))
         {
            this.mm.dialNew.butVid.removeEventListener(MouseEvent.CLICK,this.funNewVid);
            _loc1_ = 0;
            while(_loc1_ < this.kolDifs)
            {
               this.mm.dialNew["dif" + _loc1_].removeEventListener(MouseEvent.CLICK,this.funNewDif);
               this.mm.dialNew["dif" + _loc1_].removeEventListener(MouseEvent.MOUSE_OVER,this.infoMode);
               _loc1_++;
            }
         }
         this.animOn = true;
      }
      
      public function funAdv(param1:MouseEvent) : *
      {
         ++this.world.nadv;
         if(this.world.nadv >= this.world.koladv)
         {
            this.world.nadv = 0;
         }
         this.mm.adv.text = Res.advText(this.world.nadv);
         this.mm.adv.y = this.main.stage.stageHeight - this.mm.adv.textHeight - 40;
      }
      
      public function funAdvR(param1:MouseEvent) : *
      {
         --this.world.nadv;
         if(this.world.nadv < 0)
         {
            this.world.nadv = this.world.koladv - 1;
         }
         this.mm.adv.text = Res.advText(this.world.nadv);
         this.mm.adv.y = this.main.stage.stageHeight - this.mm.adv.textHeight - 40;
      }
      
      public function funNewCancel(param1:MouseEvent) : *
      {
         this.mainNewOff();
      }
      
      public function funNewOk(param1:MouseEvent) : *
      {
         this.mainNewOff();
         if(this.mm.dialNew.checkOpt2.selected)
         {
            this.loadReg = 1;
            this.mainLoadOn();
         }
         else
         {
            this.mainMenuOff();
            this.loadCell = -1;
            this.command = 3;
            this.com = "new";
         }
      }
      
      public function funNewVid(param1:MouseEvent) : *
      {
         this.setMenuSize();
         this.mm.dialNew.visible = false;
         this.world.app.attach(this.mm,this.funVidOk,this.funVidOk);
      }
      
      public function funVidOk() : *
      {
         this.mm.dialNew.visible = true;
         this.world.app.detach();
         this.mm.dialNew.pers.gotoAndStop(2);
         this.mm.dialNew.pers.gotoAndStop(1);
      }
      
      public function funNewDif(param1:MouseEvent) : *
      {
         if(param1.currentTarget == this.mm.dialNew.dif0)
         {
            this.newGameDif = 0;
         }
         if(param1.currentTarget == this.mm.dialNew.dif1)
         {
            this.newGameDif = 1;
         }
         if(param1.currentTarget == this.mm.dialNew.dif2)
         {
            this.newGameDif = 2;
         }
         if(param1.currentTarget == this.mm.dialNew.dif3)
         {
            this.newGameDif = 3;
         }
         if(param1.currentTarget == this.mm.dialNew.dif4)
         {
            this.newGameDif = 4;
         }
         this.updNewMode();
      }
      
      internal function updNewMode() : *
      {
         this.mm.dialNew.dif0.fon.gotoAndStop(1);
         this.mm.dialNew.dif1.fon.gotoAndStop(1);
         this.mm.dialNew.dif2.fon.gotoAndStop(1);
         this.mm.dialNew.dif3.fon.gotoAndStop(1);
         this.mm.dialNew.dif4.fon.gotoAndStop(1);
         if(this.newGameDif == 0)
         {
            this.mm.dialNew.dif0.fon.gotoAndStop(2);
         }
         if(this.newGameDif == 1)
         {
            this.mm.dialNew.dif1.fon.gotoAndStop(2);
         }
         if(this.newGameDif == 2)
         {
            this.mm.dialNew.dif2.fon.gotoAndStop(2);
         }
         if(this.newGameDif == 3)
         {
            this.mm.dialNew.dif3.fon.gotoAndStop(2);
         }
         if(this.newGameDif == 4)
         {
            this.mm.dialNew.dif4.fon.gotoAndStop(2);
         }
      }
      
      internal function infoMode(param1:MouseEvent) : *
      {
         this.mm.dialNew.modeinfo.htmlText = param1.currentTarget.modeinfo.text;
      }
      
      internal function infoOpt(param1:MouseEvent) : *
      {
         var _loc2_:* = int(param1.currentTarget.name.substr(param1.currentTarget.name.length - 1));
         this.mm.dialNew.modeinfo.htmlText = Res.formatText(Res.txt("g","opt" + _loc2_,1));
      }
      
      public function funOpt(param1:MouseEvent) : *
      {
         this.mainNewOff();
         this.mainLoadOff();
         this.world.pip.onoff();
      }
      
      public function funLang(param1:MouseEvent) : *
      {
         this.mm.loading.text = "";
         var _loc2_:* = param1.currentTarget.n.text;
         if(_loc2_ == this.world.lang)
         {
            return;
         }
         this.world.defuxLang(_loc2_);
         if(_loc2_ == this.world.langDef)
         {
            this.setMainLang();
         }
         else
         {
            this.langReload = true;
            this.showButtons(false);
            this.mm.loading.text = "Loading";
         }
      }
      
      internal function showButtons(param1:Boolean) : *
      {
         this.mm.lang.visible = this.mm.butNewGame.visible = this.mm.butLoadGame.visible = this.mm.butContGame.visible = this.mm.butOpt.visible = this.mm.butAbout.visible = param1;
      }
      
      public function funAbout(param1:MouseEvent) : *
      {
         var s:String;
         var event:MouseEvent = param1;
         this.mm.dialAbout.title.text = Res.guiText("about");
         s = Res.formatText(Res.txt("g","about",1));
         s += "<br><br>" + Res.guiText("usedmusic") + "<br>";
         s += "<br><span class=\'music\'>" + Res.formatText(Res.d.gui.(@id == "usedmusic").info[0]) + "</span>";
         s += "<br><br><a href=\'https://creativecommons.org/licenses/by-nc/4.0/legalcode\'>Music CC-BY License</a>";
         this.mm.dialAbout.txt.styleSheet = this.style;
         this.mm.dialAbout.txt.htmlText = s;
         this.mm.dialAbout.visible = true;
         this.mm.dialAbout.butCancel.addEventListener(MouseEvent.CLICK,this.funAboutOk);
         this.mm.dialAbout.scroll.maxScrollPosition = this.mm.dialAbout.txt.maxScrollV;
      }
      
      public function funAboutOk(param1:MouseEvent) : *
      {
         this.mm.dialAbout.visible = false;
         this.mm.dialAbout.butCancel.removeEventListener(MouseEvent.CLICK,this.funAboutOk);
      }
      
      internal function step() : *
      {
         if(this.langReload)
         {
            if(this.world.textLoaded)
            {
               this.langReload = false;
               this.showButtons(true);
               if(this.world.textLoadErr)
               {
                  this.mm.loading.text = "Language loading error";
               }
               else
               {
                  this.mm.loading.text = "";
               }
               this.world.pip.updateLang();
               this.setMainLang();
            }
            return;
         }
         if(this.loaded)
         {
            if(this.animOn && !this.world.pip.active)
            {
               this.displ.anim();
            }
            if(this.world.allLandsLoaded && this.world.textLoaded)
            {
               if(this.world.musicKol > this.world.musicLoaded)
               {
                  this.mm.loading.text = "Music loading " + this.world.musicLoaded + "/" + this.world.musicKol;
               }
               else
               {
                  this.mm.loading.text = "";
               }
            }
            return;
         }
         if(this.world.grafon.resIsLoad)
         {
            ++this.stn;
            this.mm.loading.text = "Loading " + Math.floor(this.stn / 30) + "\n";
            if(this.world.textLoaded)
            {
               this.world.init2();
            }
            if(this.world.allLandsLoaded && this.world.textLoaded)
            {
               this.setLangButtons();
               this.setMainLang();
               this.loaded = true;
               this.showButtons(true);
               return;
            }
            this.mm.loading.text += this.world.load_log;
         }
         else
         {
            this.mm.loading.text = "Loading " + Math.round(this.world.grafon.progressLoad * 100) + "%";
         }
      }
      
      public function log(param1:String) : *
      {
         this.mm.loading.text += param1 + "; ";
      }
      
      public function mainStep(param1:Event) : void
      {
         var _loc2_:Object = null;
         if(this.active)
         {
            this.step();
         }
         else if(this.command > 0)
         {
            --this.command;
            if(this.command == 1 && !this.mm.dialNew.checkOpt1.selected && this.com == "new")
            {
               this.world.setLoadScreen(0);
            }
            if(this.command == 0)
            {
               if(this.com == "new")
               {
                  _loc2_ = {
                     "dif":this.newGameDif,
                     "propusk":this.mm.dialNew.checkOpt1.selected,
                     "hardcore":this.mm.dialNew.checkOpt2.selected,
                     "fastxp":this.mm.dialNew.checkOpt3.selected,
                     "rndpump":this.mm.dialNew.checkOpt4.selected,
                     "hardskills":this.mm.dialNew.checkOpt5.selected,
                     "hardinv":this.mm.dialNew.checkOpt6.selected
                  };
                  if(_loc2_.hardcore)
                  {
                     _loc2_.autoSaveN = this.loadCell;
                  }
                  this.loadCell = -1;
               }
               this.world.newGame(this.loadCell,this.mm.dialNew.inputName.text,_loc2_);
            }
         }
         else
         {
            this.world.step();
         }
      }
   }
}

