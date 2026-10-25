package {
   import flash.display.*;
   import flash.events.*;
   import flash.net.URLRequest;
   import flash.system.*;
   import flash.utils.*;
   import flash.geom.*;
   import flash.filesystem.*;
   import flash.desktop.NativeApplication;

   public class RecoveryFrameProbeMod extends Sprite {
      private static const LARGE:Boolean=CONFIG::largeScene;
      private static const VERIFY:Boolean=CONFIG::verifyPixels;
      private static const LIVE:Boolean=CONFIG::liveFrames;
      private static var instance:RecoveryFrameProbeMod;
      public static function init(main:*):void {instance=new RecoveryFrameProbeMod(main);}
      private var host:*, worldClass:Class, classes:Object={},loaders:Array=[];
      private var timer:Timer=new Timer(150),phase:int=0,ticks:int=0,settled:int=0;
      private var cases:Array=[{"mode": "classic", "dense": true, "bright": false, "dim": 0.35, "soft": 0, "distance": 1}, {"mode": "classic", "dense": true, "bright": false, "dim": 0.6, "soft": 40, "distance": 3}, {"mode": "classic", "dense": true, "bright": true, "dim": 0, "soft": 0, "distance": 0.5}, {"mode": "classic", "dense": true, "bright": true, "dim": 1, "soft": 40, "distance": 1}, {"mode": "current", "dense": true, "bright": false, "dim": 0.35, "soft": 0, "distance": 1}, {"mode": "current", "dense": true, "bright": false, "dim": 0.6, "soft": 40, "distance": 3}, {"mode": "current", "dense": true, "bright": true, "dim": 0, "soft": 0, "distance": 0.5}, {"mode": "current", "dense": true, "bright": true, "dim": 1, "soft": 40, "distance": 1}];
      private var measuredStart:Number=0;
      private var caseIndex:int=0,frame:int=-30,mods:Array=[],times:Array=[],draws:Array=[],previousTime:int=0,intervals:Array=[];
      private var nativeUnits:Array,testUnits:Array=[],canvas:BitmapData;
      private var result:Object={cases:[],checks:[],ready:0};
      private var liveOrder:Array=["baseline","candidate","candidate","baseline","off"],liveIndex:int=0,liveAge:int=0,liveLast:int=0,liveMod:*,liveRow:Object;
      public function RecoveryFrameProbeMod(main:*=null){
         if(main==null)return;host=main;worldClass=host.loaderInfo.applicationDomain.getDefinition("fe.World") as Class;
         for each(var name:String in ["baseline","candidate"])load(name);
         timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
      }
      private function load(name:String):void{
         var l:Loader=new Loader();loaders.push(l);
         l.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void{classes[name]=l.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod");});
         var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));ctx.allowCodeImport=true;
         l.load(new URLRequest("app:/"+name+".swf"),ctx);
      }
      private function save():void{
         var path:String=File.applicationDirectory.nativePath.replace(/\\/g,"/");
         if(path.indexOf("/RealisticVision/build/classic-inputs-output/")<0)throw new Error("wrong output root");
         var fs:FileStream=new FileStream();fs.open(new File(path+"/evidence/result.json"),FileMode.WRITE);fs.writeUTFBytes(JSON.stringify(result));fs.close();
      }
      private function tick(e:Event):void{
         try{
            if(++ticks>1600)throw new Error("timeout "+phase);
            var w:*=worldClass["w"];
            if(!classes.baseline||!classes.candidate||!w||!w.allLandsLoaded||!w.landData)return;
            if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
            if(phase==0){w.mm.active=false;w.newGame(-1,"LP",null);phase=1;return;}
            if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.game.curLandId){
               if(LARGE){var carrier:*=host.getChildByName("ContinuousSceneCarrier");if(!carrier||!carrier.sceneAPI.ready||w.t_exit!=0||!w.game.lands.continuous_scene)return;}
               w.pers.healAll();w.game.beginMission(LARGE?"continuous_scene":"rbl");phase=2;return;
            }
            if(LARGE&&phase==2&&w.loc&&w.loc.active&&w.game.curLandId=="continuous_scene"&&w.land.act.id=="continuous_scene"&&w.t_exit==0){phase=3;return;}
            if(phase==2&&w.loc&&w.loc.active&&w.game.curLandId=="rbl"&&w.land.act.id=="rbl"){
               w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw new Error("training entry");w.gg.setPos(480,640);phase=3;return;
            }
            if(phase==3&&w.loc&&w.loc.active&&(LARGE||(w.land.locX==1&&w.land.locY==0))){
               if(++settled<15)return;w.mm.active=true;w.black=true;w.loc.black=true;w.loc.base=false;
               nativeUnits=w.loc.units;
               if(LIVE){timer.stop();w.mm.active=false;w.godMode=true;w.gg.invulner=true;startLive(w);host.stage.addEventListener(Event.ENTER_FRAME,liveStep,false,-10000);return;}
               makeUnits(w);canvas=new BitmapData(w.cam.screenX,w.cam.screenY,false,0xffffff);
               result.scene={large:LARGE,width:w.loc.spaceX,height:w.loc.spaceY,nativeUnits:nativeUnits.length,verification:VERIFY};
               timer.delay=10;phase=4;startCase(w);return;
            }
            if(phase==4)step(w);
         }catch(error:Error){timer.stop();trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);try{save();}catch(ignore:Error){}NativeApplication.nativeApplication.exit(1);}
      }
      private function startLive(w:*):void{
         if(liveMod){liveMod.restoreAll(w,w.loc);if(liveMod.fogVis){liveMod.fogVis.visible=false;if(liveMod.fogVis.parent)liveMod.fogVis.parent.removeChild(liveMod.fogVis);}}
         var name:String=liveOrder[liveIndex],cls:Class=classes[name=="off"?"candidate":name];liveMod=new cls();
         liveMod.cfgMode="current";liveMod.cfgEnabled=name!="off";liveMod.cfgWallBright=false;liveMod.mswRegistered=true;liveMod.cfgBaseRooms={};liveMod.resetRoom(w,w.loc);
         liveAge=0;liveLast=0;liveRow={variant:name,intervals:[],updates:[],unitsStart:w.loc.units.length,stageFps:host.stage.frameRate,size:[w.loc.spaceX,w.loc.spaceY]};
         trace("LIVE START "+liveIndex+" "+name);
      }
      private function liveStep(e:Event):void{
         try{
            var w:*=worldClass["w"];if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
            var now:int=getTimer();if(liveAge>=30&&liveLast)liveRow.intervals.push(now-liveLast);liveLast=now;
            w.ctr.clearAll();w.gg.ggControl=false;w.gg.setPos(360+(liveAge%120)*4,640);w.gg.setVisPos();w.cam.calc(w.gg);
            var start:int=getTimer();liveMod.frameCount++;liveMod.onFrameInner();if(liveAge>=30)liveRow.updates.push(getTimer()-start);
            if(++liveAge<210)return;
            liveRow.unitsEnd=w.loc.units.length;result.cases.push(liveRow);save();trace("LIVE END "+liveIndex+" "+liveRow.variant);
            if(++liveIndex<liveOrder.length){startLive(w);return;}
            host.stage.removeEventListener(Event.ENTER_FRAME,liveStep);trace("FRAME COMPLETE live");NativeApplication.nativeApplication.exit(0);
         }catch(error:Error){host.stage.removeEventListener(Event.ENTER_FRAME,liveStep);trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);save();NativeApplication.nativeApplication.exit(1);}
      }
      private function makeUnits(w:*):void{
         var uc:Class=host.loaderInfo.applicationDomain.getDefinition("fe.unit.Unit") as Class;
         for(var i:int=0;i<96;i++){
            var u:*=new uc();u.id="rv-perf-"+i;u.fraction=2;u.npc=false;u.player=false;u.invis=false;u.sost=1;
            u.scX=38+(i%3)*12;u.scY=38+(i%4)*8;u.X=160+(i%16)*60;u.Y=500+int(i/16)*72;
            var vis:MovieClip=new MovieClip();vis.graphics.beginFill(0x34a865);vis.graphics.drawRect(-20,-40,40,40);vis.graphics.endFill();
            vis.x=u.X;vis.y=u.Y;u.vis=vis;w.grafon.visObjs[2].addChild(vis);
            testUnits.push(u);
         }
      }
      private function startCase(w:*):void{
         var c:Object=cases[caseIndex];w.loc.units=c.dense?testUnits:[];
         for each(var u:* in testUnits)u.vis.visible=c.dense;
         mods=[];times=[[],[]];draws=[[],[]];frame=-30;intervals=[];previousTime=0;
         for each(var name:String in ["baseline","candidate"]){
            var cls:Class=classes[name],m:*=new cls();m.cfgMode=c.mode;m.cfgDim=c.dim;m.cfgSoftClassic=c.soft;m.cfgSoftCurrent=c.soft;m.cfgViewScale=c.distance;m.cfgWallBright=c.bright;m.cfgEnabled=true;m.cfgAutoTest=false;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,w.loc);mods.push(m);
         }
         trace("FRAME CASE "+caseIndex+" "+JSON.stringify(c)+" size="+w.loc.spaceX+"x"+w.loc.spaceY+" units="+w.loc.units.length);
      }
      private function state(m:*):String{return JSON.stringify({fov:m.fov,seen:m.seenSub,explored:m.explored,mem:m.memCur});}
      private function step(w:*):void{
         if(frame==0)measuredStart=new Date().time;
         var now:int=getTimer();if(frame>=0&&previousTime)intervals.push(now-previousTime);previousTime=now;
         var p:int=(frame+30)%120;w.gg.setPos(360+p*(LARGE?12:4),640);w.gg.setVisPos();w.cam.calc(w.gg);var zoom:Number=[1,0.75,1.25,0.5][int((frame+30)/30)%4];w.cam.scaleV=zoom;w.cam.vx=-Math.max(0,Math.min(w.loc.limX*zoom-w.cam.screenX,w.gg.X*zoom-w.cam.screenX/2));w.cam.vy=-Math.max(0,Math.min(w.loc.limY*zoom-w.cam.screenY,w.gg.Y*zoom-w.cam.screenY/2));w.loc.lighting();w.loc.lighting2();
         w.pers.infravis=int((frame+30)/30)%2;var order:Array=(frame&1)?[1,0]:[0,1];
         for each(var index:int in order){
            var m:*=mods[index];
            for each(var other:* in mods)if(other.fogVis)other.fogVis.visible=false;
            if(m.fogVis && frame%15==1){m.fogVis.visible=false;m.fogShadow.transform.colorTransform=new ColorTransform(.7,.6,.5,.8,1,2,3,4);m.fogShadow.blendMode="add";m.fogShadow.scrollRect=new Rectangle(3,5,117,119);m.fogShadow.x=9;m.fogShadow.y=11;}
            var start:int=getTimer();m.frameCount++;m.onFrameInner();var elapsed:int=getTimer()-start;
            if(frame>=0)times[index].push(elapsed);
            start=getTimer();canvas.fillRect(canvas.rect,0xffffff);canvas.draw(m.fogVis,displayMatrix(m,w),null,null,null,true);
            if(frame>=0)draws[index].push(getTimer()-start);
         }
         if(frame==-1){for each(m in mods){if("profile" in m){m.profile={};m.calls={};m.wallSurface.profile={};m.wallSurface.calls={};}}}
         if(VERIFY&&frame>=0&&frame%15==0)verify(w);
         if(++frame<120)return;
         var c:Object=cases[caseIndex],entry:Object={measuredStart:measuredStart,measuredEnd:new Date().time,spec:c,updates:times,draws:draws,pairedIntervals:intervals,stages:[],helper:[],counts:[],helperCounts:[]};
         for each(m in mods){
            if("profile" in m){entry.stages.push(m.profile);entry.helper.push(m.wallSurface.profile);entry.counts.push(m.calls);entry.helperCounts.push(m.wallSurface.calls);}
            m.restoreAll(w,w.loc);if(m.fogVis)m.fogVis.visible=false;
         }
         result.cases.push(entry);save();trace("FRAME RESULT "+caseIndex+" "+JSON.stringify({stages:entry.stages,helper:entry.helper,counts:entry.counts}));
         if(++caseIndex<cases.length){startCase(w);return;}
         w.loc.units=nativeUnits;timer.stop();canvas.dispose();if(result.ready==0)throw new Error("private cache not exercised");trace("PRIVATE READY "+result.ready);trace("FRAME COMPLETE");NativeApplication.nativeApplication.exit(0);
      }
      private function equal(a:BitmapData,b:BitmapData):Boolean{var d:Object=a.compare(b),ok:Boolean=d is uint&&uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;}
      private function dumpImage(image:BitmapData,name:String):void {var path:String=File.applicationDirectory.nativePath.replace(/\\/g,"/");if(path.indexOf("/RealisticVision/build/classic-inputs-output/")<0)throw new Error("wrong image output");var f:FileStream=new FileStream();f.open(new File(path+"/evidence/"+name+".png"),FileMode.WRITE);f.writeBytes(image.encode(image.rect,new PNGEncoderOptions()));f.close();}
      private function sameField(a:*,b:*,key:String):Boolean {if(key!="fogCache"||b.cfgMode!="classic")return equal(a[key],b[key]);var r:Rectangle=new Rectangle(4,4,b.spaceX*8,b.spaceY*8),x:BitmapData=new BitmapData(r.width,r.height,true,0),y:BitmapData=x.clone();x.copyPixels(a[key],r,new Point());y.copyPixels(b[key],r,new Point());var ok:Boolean=equal(x,y);x.dispose();y.dispose();return ok;}
      private function displayMatrix(m:*,w:*):Matrix {var mat:Matrix=m.fogVis.transform.matrix;var camera:Matrix=new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,w.cam.vx,w.cam.vy);mat.concat(camera);return mat;}
      private function parentCapture(image:BitmapData,m:*,w:*):void {var node:Sprite=m.fogVis,original:DisplayObjectContainer=node.parent,index:int=original?original.getChildIndex(node):-1,wrapper:Sprite=new Sprite();wrapper.addChild(node);try {image.draw(wrapper,new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,w.cam.vx,w.cam.vy),null,null,null,true);} finally {if(original)original.addChildAt(node,index);else wrapper.removeChild(node);}}
      private function verify(w:*):void{
         var a:*=mods[0],b:*=mods[1],ok:Boolean=true;
         for each(var field:String in ["fogCache","fogBmp","wallRaw","currentSight"]){if(a[field]&&b[field]&&!equal(a[field],b[field]))throw new Error("pixel mismatch "+field+" case="+caseIndex+" frame="+frame);}
         if(state(a)!=state(b))throw new Error("logical state mismatch "+frame);
         for each(var u:* in testUnits){
            if(a.enemyState(w.loc,u)!=b.enemyState(w.loc,u))throw new Error("enemy classification mismatch");
            var ar:Object=a.unitVis[u],br:Object=b.unitVis[u];
            if(ar&&br&&ar.state==2&&br.state==2&&(!equal(ar.m2d,br.m2d)||!equal(ar.m2e,br.m2e)))throw new Error("enemy mask mismatch");
         }
         var ca:BitmapData=canvas.clone(),cb:BitmapData=canvas.clone();
         var mat:Matrix=new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,LARGE?w.cam.vx:-120,LARGE?w.cam.vy:-240);
         a.fogVis.visible=true;b.fogVis.visible=true;ca.fillRect(ca.rect,0xffffff);cb.fillRect(cb.rect,0xffffff);parentCapture(ca,a,w);parentCapture(cb,b,w);
         ok=equal(ca,cb);if(!ok){dumpImage(ca,"baseline");dumpImage(cb,"candidate");var dd:BitmapData=ca.compare(cb) as BitmapData;trace("DIFFERENCE "+dd.getColorBoundsRect(0xFFFFFFFF,0,false)+" camera="+w.cam.vx+","+w.cam.vy+" view="+b.scenePaintBounds()+" frame="+b.frameCount);dumpImage(dd,"difference");dd.dispose();}ca.dispose();cb.dispose();if(!ok)throw new Error("composited fog mismatch");
         if(b.classicLogicInterpolated)result.ready++;result.checks.push({caseIndex:caseIndex,frame:frame,exact:true});
         trace("PASS exact native frame "+caseIndex+"/"+frame);
      }
   }
}
