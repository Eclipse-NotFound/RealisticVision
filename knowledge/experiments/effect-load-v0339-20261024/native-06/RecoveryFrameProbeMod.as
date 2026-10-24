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
      private var cases:Array=[{mode:"current",dense:false,bright:false},{mode:"current",dense:true,bright:false},{mode:"classic",dense:true,bright:false},{mode:"current",dense:true,bright:true}];
      private var measuredStart:Number=0;
      private var caseIndex:int=0,frame:int=-30,mods:Array=[],times:Array=[],draws:Array=[],previousTime:int=0,intervals:Array=[];
      private var nativeUnits:Array,testUnits:Array=[],canvas:BitmapData;
      private var result:Object={cases:[],checks:[]};
      private var traceEnter:int=0,traceExit:int=0,lastTrace:Object=null,traceSerial:int=0,events:Array=[];
      private var scenario:String="";
      private var crowd:Array=[];
      private var walkLow:Number=0,walkHigh:Number=0,walkFloor:Number=0,walkDirection:int=1,lastWalkX:Number=NaN;
      private var anchorX:Number=0,anchorY:Number=0,armedEnemy:*,attackTimers:Dictionary=new Dictionary(true);
      private var liveOrder:Array=["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"],liveIndex:int=0,liveAge:int=0,liveLast:int=0,liveMod:*,liveRow:Object;
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
         if(path.indexOf("/RealisticVision/build/effect-load-v3-output/")<0)throw new Error("wrong output root");
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
               if(LIVE){timer.stop();w.mm.active=false;w.godMode=true;w.gg.invulner=false;startLive(w);host.stage.addEventListener(Event.ENTER_FRAME,earlyFrame,false,1000000);host.stage.addEventListener(Event.EXIT_FRAME,exitFrame,false,-1000000);host.stage.addEventListener(Event.ENTER_FRAME,liveStep,false,-10000);return;}
               makeUnits(w);canvas=new BitmapData(1280,720,false,0xffffff);
               result.scene={large:LARGE,width:w.loc.spaceX,height:w.loc.spaceY,nativeUnits:nativeUnits.length,verification:VERIFY};
               timer.delay=10;phase=4;startCase(w);return;
            }
            if(phase==4)step(w);
         }catch(error:Error){timer.stop();trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);try{save();}catch(ignore:Error){}NativeApplication.nativeApplication.exit(1);}
      }
      private function startLive(w:*):void{
         if(liveMod){liveMod.restoreAll(w,w.loc);if(liveMod.fogVis){liveMod.fogVis.visible=false;if(liveMod.fogVis.parent)liveMod.fogVis.parent.removeChild(liveMod.fogVis);}}
         var name:String=liveOrder[liveIndex],cls:Class=classes[name=="off"?"candidate":name];liveMod=new cls();
         liveMod.cfgDim=0.6;liveMod.cfgSoftCurrent=25;liveMod.cfgMode=liveIndex<6?"current":"classic";liveMod.cfgEnabled=name!="off";liveMod.cfgWallBright=false;liveMod.mswRegistered=true;liveMod.cfgBaseRooms={};liveMod.resetRoom(w,w.loc);
         scenario="battle";liveAge=0;liveLast=0;lastTrace=null;liveRow={cameraScale:Number(w.cam.scaleV),variant:name,intervals:[],updates:[],unitsStart:w.loc.units.length,mode:liveMod.cfgMode,attackStarts:0,targetFrames:0,maxObjects:0,maxProjectiles:0,drivenFire:true,scenario:scenario,eventSequence:events,frames:[],nativeKeys:false,denseMercenaries:6,sampleFrames:120,grounded:0,walkDistance:0,reversals:0,stageFps:host.stage.frameRate,size:[w.loc.spaceX,w.loc.spaceY]};
         if(anchorX==0){
               var bestStart:int=-1,bestEnd:int=-1,bestY:int=0;
               // One-time fixture placement. Find a straight native solid floor
               // with three clear tiles above it and room to brake at both ends.
               for(var fy:int=6;fy<w.loc.spaceY-2 && bestStart<0;fy++){
                  var begin:int=-1;
                  for(var fx:int=2;fx<w.loc.spaceX-2;fx++){
                     var floorTile:*=w.loc.getTile(fx,fy);
                     var clear:Boolean=floorTile.opac>=1 && int(floorTile.zForm)==0;
                     for(var ay:int=1;ay<=3 && clear;ay++)if(w.loc.getTile(fx,fy-ay).opac>=1)clear=false;
                     if(clear){if(begin<0)begin=fx;}
                     else begin=-1;
                     if(begin>=0 && fx-begin>=15){bestStart=begin;bestEnd=fx;bestY=fy;break;}
                  }
               }
               if(bestStart<0)throw new Error("native walk platform unavailable");
               walkLow=(bestStart+2)*40;walkHigh=(bestEnd-1)*40;walkFloor=bestY*40;
               w.gg.setPos(walkLow+80,walkFloor-1);w.gg.setVisPos();w.ctr.clearAll();w.gg.ggControl=true;
               trace("NATIVE WALK floor="+walkFloor+" range="+walkLow+","+walkHigh);

               // Spawn a native raider, not a stationary UnitDamager trap.
               // Random scene populations need not contain an armed combatant.
               var raiderClass:Class=host.loaderInfo.applicationDomain.getDefinition("fe.unit.UnitMerc") as Class;
               armedEnemy=new raiderClass("1",10,null,{weap:"smg10"});
               anchorX=Math.min(w.loc.limX-200,w.gg.X+240);anchorY=w.gg.Y;
               armedEnemy.putLoc(w.loc,anchorX,anchorY);armedEnemy.invulner=true;
               w.loc.addObj(armedEnemy);w.loc.units.push(armedEnemy);armedEnemy.step();crowd.push(armedEnemy);
               for(var ci:int=0;ci<5;ci++){var enemy:*=new raiderClass("1",10,null,{weap:"smg10"});enemy.putLoc(w.loc,walkLow+70+ci*65,walkFloor-1);enemy.invulner=true;w.loc.addObj(enemy);w.loc.units.push(enemy);enemy.step();crowd.push(enemy);}
               if(!armedEnemy.currentWeapon||armedEnemy.currentWeapon.tip<=1)throw new Error("native ranged weapon missing");
            }
            armedEnemy.invulner=true;
            liveRow.enemyStart={hp:armedEnemy.hp,sost:armedEnemy.sost,weapon:armedEnemy.currentWeapon.id};
            trace("LIVE START "+liveIndex+" "+name+" "+liveMod.cfgMode+" anchor="+anchorX+","+anchorY+" enemy="+armedEnemy.id+" weapon="+armedEnemy.currentWeapon.id+" tip="+armedEnemy.currentWeapon.tip);
      }
      private function earlyFrame(e:Event):void{
         traceEnter=getTimer();traceSerial++;if(events.length<24)events.push(["early",traceSerial,traceEnter]);
      }
      private function exitFrame(e:Event):void{traceExit=getTimer();if(events.length<24)events.push(["exit",traceSerial,traceExit]);}

      private function counters(o:Object):Object{var result:Object={};for(var key:String in o)result[key]=o[key];return result;}
      private function liveStep(e:Event):void{
         try{
            var w:*=worldClass["w"];if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
            var now:int=getTimer();if(liveAge>=30&&liveLast)liveRow.intervals.push(now-liveLast);liveLast=now;
            var liveStart:int=getTimer();
            if(events.length<24)events.push(["live",traceSerial,liveStart]);
            if(lastTrace){lastTrace.nextInterval=liveStart-lastTrace.liveStart;lastTrace.outsideRV=lastTrace.nextInterval-lastTrace.rv;}
            var hostMs:int=liveStart-traceEnter;
            w.ctr.clearAll();w.gg.ggControl=true;
            if(w.gg.X>=walkHigh && walkDirection>0){walkDirection=-1;liveRow.reversals++;}
            else if(w.gg.X<=walkLow && walkDirection<0){walkDirection=1;liveRow.reversals++;}
            w.ctr.keyLeft=false;w.ctr.keyRight=false;w.ctr.keyRun=false;
            if(liveAge>=30){
               liveRow.maxFloorDeviation=Math.max(Number(liveRow.maxFloorDeviation)||0,Math.abs(w.gg.Y-walkFloor));
               if(w.gg.stay)liveRow.grounded++;
               if(lastWalkX==lastWalkX)liveRow.walkDistance+=Math.abs(w.gg.X-lastWalkX);
            }
            lastWalkX=w.gg.X;
            liveMod.profile={};liveMod.calls={};liveMod.wallSurface.profile={};liveMod.wallSurface.calls={};
            var memBefore:Number=System.totalMemory;
            if(liveAge==29)liveRow.calibrationStart=calibrate();var previousView:Rectangle=liveMod.wallViewBounds;var start:int=getTimer();liveMod.frameCount++;liveMod.onFrameInner();var rvMs:int=getTimer()-start;if(liveAge>=30)liveRow.updates.push(rvMs);
            var view:Rectangle=liveMod.wallViewBounds;
            lastTrace={grounded:w.gg.stay,dx:w.gg.dx,dy:w.gg.dy,epoch:new Date().time,viewChanged:view==null?previousView!=null:previousView==null||!view.equals(previousView),liveStart:liveStart,earlyTime:traceEnter,serial:traceSerial,rvStart:start,rvEnd:start+rvMs,age:liveAge,host:hostMs,rv:rvMs,position:[w.gg.X,w.gg.Y,w.cam.vx,w.cam.vy],memoryBefore:memBefore,memoryAfter:System.totalMemory,rvStages:counters(liveMod.profile),helper:counters(liveMod.wallSurface.profile),helperCalls:counters(liveMod.wallSurface.calls),fovVersion:liveMod.fovVersion,view:view?[view.x,view.y,view.width,view.height]:null,units:w.loc.units.length,attack:armedEnemy.currentWeapon.t_attack,ammo:armedEnemy.currentWeapon.hold};
            if(liveAge>=30)liveRow.frames.push(lastTrace);
            // Controlled native firing: only the isolated fixture invokes attack.
            // Weapon physics, projectiles, damage and the native world keep running.
            // Non-automatic weapons reset t_auto while the trigger is held.
            // Leave six native steps between presses so their latch releases.
            for each(var fighter:* in crowd){fighter.setCel(w.gg);if(liveAge%6==0)fighter.currentWeapon.attack();}
            for each(var actor:* in w.loc.units){
               if(actor.celUnit===w.gg)liveRow.targetFrames++;
               var weapon:*=actor.currentWeapon;
               if(weapon){if(weapon.t_attack>int(attackTimers[weapon]))liveRow.attackStarts++;attackTimers[weapon]=weapon.t_attack;}
            }
            var obj:*=w.loc.firstObj;var count:int=0,projectiles:int=0;while(obj&&count<5000){count++;if(getQualifiedClassName(obj).indexOf("Bullet")>=0)projectiles++;obj=obj.nobj;}liveRow.maxObjects=Math.max(liveRow.maxObjects,count);liveRow.maxProjectiles=Math.max(liveRow.maxProjectiles,projectiles);
            lastTrace.objects=count;lastTrace.projectiles=projectiles;
            if(++liveAge<150)return;liveRow.calibrationEnd=calibrate();

            liveRow.enemyEnd={hp:armedEnemy.hp,sost:armedEnemy.sost,attack:armedEnemy.currentWeapon.t_attack,reload:armedEnemy.currentWeapon.t_reload,ammo:armedEnemy.currentWeapon.hold};
            if(scenario=="battle" && (liveRow.attackStarts<1 || liveRow.maxProjectiles<1))throw new Error("combat fixture did not sustain native fire: "+JSON.stringify(liveRow.enemyEnd));
            liveRow.unitsEnd=w.loc.units.length;result.cases.push(liveRow);save();trace("LIVE END "+liveIndex+" "+liveRow.variant);
            if(++liveIndex<liveOrder.length){startLive(w);return;}
            host.stage.removeEventListener(Event.ENTER_FRAME,liveStep);trace("FRAME COMPLETE live");NativeApplication.nativeApplication.exit(0);
         }catch(error:Error){host.stage.removeEventListener(Event.ENTER_FRAME,liveStep);trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);save();NativeApplication.nativeApplication.exit(1);}
      }
      private function calibrate():Object {
         var begin:int=getTimer(),sum:Number=0;
         for(var i:int=0;i<1000000;i++)sum+=(i&7)*0.125;
         return {ms:getTimer()-begin,checksum:sum};
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
            var cls:Class=classes[name],m:*=new cls();m.cfgMode=c.mode;m.cfgWallBright=c.bright;m.cfgEnabled=true;m.cfgAutoTest=false;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,w.loc);mods.push(m);
         }
         trace("FRAME CASE "+caseIndex+" "+JSON.stringify(c)+" size="+w.loc.spaceX+"x"+w.loc.spaceY+" units="+w.loc.units.length);
      }
      private function state(m:*):String{return JSON.stringify({fov:m.fov,seen:m.seenSub,explored:m.explored,mem:m.memCur});}
      private function step(w:*):void{
         if(frame==0)measuredStart=new Date().time;
         var now:int=getTimer();if(frame>=0&&previousTime)intervals.push(now-previousTime);previousTime=now;
         var p:int=(frame+30)%120;w.gg.setPos(360+p*(LARGE?12:4),640);w.gg.setVisPos();w.cam.calc(w.gg);w.loc.lighting();w.loc.lighting2();
         var order:Array=(frame&1)?[1,0]:[0,1];
         for each(var index:int in order){
            var m:*=mods[index];
            for each(var other:* in mods)if(other.fogVis)other.fogVis.visible=false;
            var start:int=getTimer();m.frameCount++;m.onFrameInner();var elapsed:int=getTimer()-start;
            if(frame>=0)times[index].push(elapsed);
            start=getTimer();canvas.fillRect(canvas.rect,0xffffff);canvas.draw(m.fogVis,new Matrix(1,0,0,1,LARGE?w.cam.vx:-120,LARGE?w.cam.vy:-240),null,null,null,true);
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
         w.loc.units=nativeUnits;timer.stop();canvas.dispose();trace("FRAME COMPLETE");NativeApplication.nativeApplication.exit(0);
      }
      private function equal(a:BitmapData,b:BitmapData):Boolean{var d:Object=a.compare(b),ok:Boolean=d is uint&&uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;}
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
         var mat:Matrix=new Matrix(1,0,0,1,LARGE?w.cam.vx:-120,LARGE?w.cam.vy:-240);
         a.fogVis.visible=true;b.fogVis.visible=true;ca.fillRect(ca.rect,0xffffff);cb.fillRect(cb.rect,0xffffff);ca.draw(a.fogVis,mat,null,null,null,true);cb.draw(b.fogVis,mat,null,null,null,true);
         ok=equal(ca,cb);ca.dispose();cb.dispose();if(!ok)throw new Error("composited fog mismatch");
         result.checks.push({caseIndex:caseIndex,frame:frame,exact:true});
         trace("PASS exact native frame "+caseIndex+"/"+frame);
      }
   }
}
