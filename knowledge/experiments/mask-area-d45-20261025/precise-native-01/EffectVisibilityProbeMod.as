package {
import flash.filters.GlowFilter;
   import flash.display.*;
   import flash.events.*;
   import flash.net.URLRequest;
   import flash.system.*;
   import flash.utils.*;
   import flash.geom.*;
   import flash.filesystem.*;
   import flash.desktop.NativeApplication;

   public class EffectVisibilityProbeMod extends Sprite {
      private static const LARGE:Boolean=CONFIG::largeScene;
      private static const VERIFY:Boolean=CONFIG::verifyPixels;
      private static const LIVE:Boolean=CONFIG::liveFrames;
      private static var instance:EffectVisibilityProbeMod;
      public static function init(main:*):void {instance=new EffectVisibilityProbeMod(main);}
      private var host:*, worldClass:Class, classes:Object={},loaders:Array=[];
      private var timer:Timer=new Timer(150),phase:int=0,ticks:int=0,settled:int=0;
      private var cases:Array=[{mode:"current",dense:false,bright:false},{mode:"current",dense:true,bright:false},{mode:"classic",dense:true,bright:false},{mode:"current",dense:true,bright:true}];
      private var caseIndex:int=0,frame:int=-30,mods:Array=[],times:Array=[],draws:Array=[],previousTime:int=0,intervals:Array=[];
      private var nativeUnits:Array,testUnits:Array=[],canvas:BitmapData;
      private var result:Object={cases:[],checks:[]};
      private var liveOrder:Array=["baseline","candidate","candidate","baseline","off"],liveIndex:int=0,liveAge:int=0,liveLast:int=0,liveMod:*,liveRow:Object;
      public function EffectVisibilityProbeMod(main:*=null){
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
         if(path.indexOf("/RealisticVision/build/mask-area-output/")<0)throw new Error("wrong output root");
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
               inspectEffects(w);return;makeUnits(w);canvas=new BitmapData(1280,720,false,0xffffff);
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
      private function inspectEffects(w:*):void {
         var domain:ApplicationDomain=host.loaderInfo.applicationDomain;
         var uc:Class=domain.getDefinition("fe.unit.UnitMerc") as Class;
         var u:*=new uc("1",10,null,{weap:"smg10"});
         u.putLoc(w.loc,600,640);w.loc.addObj(u);w.loc.units.push(u);u.step();u.setVisPos();u.currentWeapon.step();
         // An exempt neighbour defeats the legacy proximity guess without changing the mercenary.
         var friendClass:Class=domain.getDefinition("fe.unit.Unit") as Class,friend:*=new friendClass();
         friend.X=600;friend.Y=610;friend.npc=true;w.loc.units.push(friend);
         var arm:DisplayObject;
         for(var i:int=0;i<w.grafon.visObjs[2].numChildren;i++){
            var c:DisplayObject=w.grafon.visObjs[2].getChildAt(i);
            if(getQualifiedClassName(c).indexOf("visualGrifArm")==0)arm=c;
         }
         check("native mercenary arm found",arm!=null);
         var visuals:Array=[{kind:"merc-arm",vis:arm},{kind:"merc-weapon",vis:u.currentWeapon.vis}];
         var bulletClass:Class=domain.getDefinition("fe.weapon.Bullet") as Class;
         for each(var type:String in ["visualBullet","visbullaser"]){
            var vc:Class=domain.getDefinition(type) as Class,b:*=new bulletClass(w.gg,600,600,vc);
            b.vis.visible=true;b.vis.scaleX=2;visuals.push({kind:type,vis:b.vis,obj:b});
         }
         var ec:Class=domain.getDefinition("fe.graph.Emitter") as Class;
         for each(var effect:String in ["iskr_bul","iskr","expl","gilza"]){
            var p:*=ec.arr[effect].cast(w.loc,600,600,{kol:1});
            check("native emitter "+effect,p&&p.vis);p.step();visuals.push({kind:effect,vis:p.vis,obj:p});
         }
         result.rows=[];
         for each(var mode:String in ["current","classic"])for each(var name:String in ["baseline","candidate"]){
            var cls:Class=classes[name],m:*=new cls();m.cfgMode=mode;m.cfgDim=.6;m.cfgEnabled=true;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,w.loc);
            w.gg.setPos(480,640);w.gg.setVisPos();m.frameCount++;m.onFrameInner();
            if(m.currentSight==null)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
            for(i=0;i<m.fov.length;i++)m.fov[i]=0;
            m.currentSight.fillRect(m.currentSight.rect,0);m.currentSightData=null;m.classifiedSight=null;m.sightClasses=null;m.fovVersion++;
            m.fogCache.fillRect(m.fogCache.rect,0xff000000);
            // Freeze the canonical classic logical raster for an exact visibility fixture.
            m.classicLogicCache=null;
            for(var f:int=0;f<4;f++){
               m.frameCount=f;m.hideEnemies(w,w.loc,f==0);
               for each(var row:Object in visuals){
                  var n:int=effectPixels(row.vis);
                  result.rows.push({mode:mode,variant:name,frame:f,kind:row.kind,pixels:n,mask:row.vis.mask!=null,visible:row.vis.visible});
                  if(name=="baseline"&&row.kind!="merc-weapon")check("baseline dark "+mode+" "+row.kind+" "+f,n==0);
                  if(name=="candidate"&&("worldVisuals" in m))check("fixed dark "+mode+" "+row.kind+" "+f,n==0);
               }
            }
            m.restoreAll(w,w.loc);if(m.fogVis)m.fogVis.visible=false;
            if(name=="candidate"&&("worldVisuals" in m)){
               for each(var state:String in ["light","partial","light","dark","light"]){
                  for(i=0;i<m.fov.length;i++)m.fov[i]=state=="dark"?0:1;
                  m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,state=="dark"?0:0xffffffff);m.fogCache.fillRect(m.fogCache.rect,state=="dark"?0xff000000:0);
                  if(state=="partial"){
                     m.currentSight.fillRect(new Rectangle(4+120,0,m.currentSight.width-124,m.currentSight.height),0);
                     m.fogCache.fillRect(new Rectangle(4+120,0,m.fogCache.width-124,m.fogCache.height),0xff000000);
                  }
                  m.currentSightData=null;m.classifiedSight=null;m.fovVersion++;
                  // Capture original visible material before applying the new world masks.
                  var originals:Array=[];
                  for each(row in visuals){row.vis.visible=true;originals.push(effectImage(row.vis));}
                  m.hideEnemies(w,w.loc,true);
                  for(i=0;i<visuals.length;i++){
                     row=visuals[i];var out:BitmapData=effectImage(row.vis),ref:BitmapData=originals[i];
                     if(state=="light")check("visible pixel identity "+mode+" "+row.kind,equal(out,ref));
                     if(state=="dark")check("reentry dark "+mode+" "+row.kind,out.getColorBoundsRect(0xff000000,0,false).isEmpty());
                     if(state=="partial"&&row.kind!="merc-weapon"){
                        var right:BitmapData=new BitmapData(140,240,true,0);right.copyPixels(out,new Rectangle(260,0,140,240),new Point());
                        check("partial hidden side "+mode+" "+row.kind,right.getColorBoundsRect(0xff000000,0,false).isEmpty());right.dispose();
                     }
                     if(state=="partial"){var fs:FileStream=new FileStream();fs.open(new File(File.applicationDirectory.nativePath+"/evidence/"+mode+"-"+row.kind+".png"),FileMode.WRITE);fs.writeBytes(out.encode(out.rect,new PNGEncoderOptions()));fs.close();}
                     ref.dispose();out.dispose();
                  }
                  m.restoreAll(w,w.loc);
                  for each(row in visuals)check("restored native mask "+mode+" "+row.kind,row.vis.mask==null);
               }
               // A native long gun can extend beyond the body classification.
               // Keep the body fully lit while its actual muzzle points into dark space.
               var wp:*=u.currentWeapon,oldWX:Number=wp.X,oldWY:Number=wp.Y;
               var bb:Array=m.unitBBox(w.loc,u),edge:Number=(bb[2]+1)*40;
               for(i=0;i<m.fov.length;i++)m.fov[i]=1;
               m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,0xffffffff);m.fogCache.fillRect(m.fogCache.rect,0);
               m.currentSight.fillRect(new Rectangle(4+edge/5,0,m.currentSight.width-4-edge/5,m.currentSight.height),0);
               m.fogCache.fillRect(new Rectangle(4+edge/5,0,m.fogCache.width-4-edge/5,m.fogCache.height),0xff000000);
               m.currentSightData=m.currentSight.getVector(m.currentSight.rect);m.classifiedSight=null;m.fovVersion++;
               wp.X=edge+80;wp.Y=600;wp.animate();wp.vis.visible=true;
               check("long weapon native positive "+mode,effectPixels(wp.vis)>0);
               m.hideEnemies(w,w.loc,true);
               check("body classification unchanged "+mode,m.enemyState(w.loc,u)==1);
               check("long weapon outside body hidden "+mode,effectPixels(wp.vis)==0);
               m.restoreAll(w,w.loc);wp.X=oldWX;wp.Y=oldWY;wp.animate();
               // New particle animation steps may set visible=true again. The
               // spatial mask must remain effective without suppressing step().
               for(i=0;i<m.fov.length;i++)m.fov[i]=0;
               m.currentSight.fillRect(m.currentSight.rect,0);m.currentSightData=null;m.fogCache.fillRect(m.fogCache.rect,0xff000000);m.fovVersion++;
               for(var age:int=0;age<8;age++){
                  var particle:*=ec.arr["iskr_bul"].cast(w.loc,600,600,{kol:1});particle.vis.visible=false;particle.step();
                  m.hideEnemies(w,w.loc,false);check("native particle animation cannot reveal "+mode+" "+age,effectPixels(particle.vis)==0);
               }
               m.restoreAll(w,w.loc);

               arm.visible=false;m.hideEnemies(w,w.loc,true);m.restoreAll(w,w.loc);check("native dead arm preserved "+mode,!arm.visible);arm.visible=true;
               m.hideEnemies(w,w.loc,true);var prior:*=visuals[2].vis,priorMask:*=prior.mask;
               prior.parent.removeChild(prior);m.hideEnemies(w,w.loc,false);check("removed effect released "+mode,prior.mask==null&&(priorMask==null||priorMask.parent==null));w.grafon.visObjs[2].addChild(prior);
               m.hideEnemies(w,w.loc,false);m.resetRoom(w,w.loc);check("room reset releases effects "+mode,prior.mask==null&&arm.mask==null);
            }
         }
         // Same animation frame and visibility field, whole native effect parent.
         // Restoring each version prevents its mask from contaminating the next.
         var filtersIdentity:Array=[],supportHits:int=0;
         for each(var originalRow:Object in visuals)filtersIdentity.push(originalRow.vis.filters);
         for each(var identityMode:String in ["current","classic"]){
            var references:Array=[];
            for(var ageIdentity:int=0;ageIdentity<12;ageIdentity++){
               var filterIndex:int=0;
               for each(var visualRow:Object in visuals){
                  visualRow.vis.visible=true;
                  visualRow.vis.filters=(filtersIdentity[filterIndex++] as Array).concat(ageIdentity%3==0?[new GlowFilter(0xff44aa,1,20,20,2,1)]:[]);
                  if(visualRow.vis is MovieClip)MovieClip(visualRow.vis).nextFrame();
               }
               for each(var identityName:String in ["baseline","candidate"]){
                  var identityClass:Class=classes[identityName],identity:*=new identityClass();
                  identity.cfgMode=identityMode;identity.cfgEnabled=true;identity.cfgDim=.6;identity.mswRegistered=true;identity.cfgBaseRooms={};identity.resetRoom(w,w.loc);identity.onFrameInner();
                  if(identity.currentSight==null)identity.currentSight=new BitmapData(identity.fogCache.width,identity.fogCache.height,true,0);
                  identity.classicLogicCache=null;identity.currentSight.fillRect(identity.currentSight.rect,0xffffffff);identity.fogCache.fillRect(identity.fogCache.rect,0);
                  var cutoff:int=90+ageIdentity*5;
                  identity.currentSight.fillRect(new Rectangle(cutoff,0,identity.currentSight.width-cutoff,identity.currentSight.height),0);
                  identity.fogCache.fillRect(new Rectangle(cutoff,0,identity.fogCache.width-cutoff,identity.fogCache.height),0xff000000);
                  identity.currentSightData=null;identity.classifiedSight=null;identity.fovVersion++;
                  for(var repeatIdentity:int=0;repeatIdentity<3;repeatIdentity++){
                     identity.hideEnemies(w,w.loc,true);
                     if(identityName=="candidate" && ("worldVisualHasFilters" in identity))for each(var supportRecord:Object in identity.worldVisuals)
                        if(supportRecord.dark && !supportRecord.raster.fullyDark)supportHits++;
                     for(var visualIndex:int=0;visualIndex<visuals.length;visualIndex++){
                        var captured:BitmapData=effectImage(visuals[visualIndex].vis),referenceIndex:int=repeatIdentity*visuals.length+visualIndex;
                        if(identityName=="baseline")references[referenceIndex]=captured;
                        else {check("exact native repeated mask "+identityMode+" "+ageIdentity+" "+repeatIdentity+" "+visuals[visualIndex].kind,equal(captured,references[referenceIndex]));captured.dispose();BitmapData(references[referenceIndex]).dispose();}
                     }
                  }
                  identity.restoreAll(w,w.loc);if(identity.fogVis)identity.fogVis.visible=false;
               }
            }
         }
         for(var filterRestore:int=0;filterRestore<visuals.length;filterRestore++)visuals[filterRestore].vis.filters=filtersIdentity[filterRestore];
         if("worldVisualHasFilters" in identity)check("transparent-support shortcut actually exercised",supportHits>0);

         save();trace("D42 EFFECT "+JSON.stringify(result));timer.stop();trace("FRAME COMPLETE");NativeApplication.nativeApplication.exit(0);
      }
      private function check(label:String,ok:Boolean):void {result.checks.push({label:label,pass:ok});trace((ok?"PASS ":"FAIL ")+label);if(!ok)throw new Error(label);}
      private function effectPixels(visual:DisplayObject):int {
         var bitmap:BitmapData=effectImage(visual);
         var values:Vector.<uint>=bitmap.getVector(bitmap.rect),count:int=0;for each(var pixel:uint in values)if(pixel>>>24)count++;
         bitmap.dispose();return count;
      }
      private function effectImage(visual:DisplayObject):BitmapData {
         var layer:DisplayObjectContainer=visual.parent,states:Array=[],i:int;
         for(i=0;i<layer.numChildren;i++){var c:DisplayObject=layer.getChildAt(i);states.push([c,c.visible]);if(c!==visual&&c!==visual.mask)c.visible=false;}
         var bitmap:BitmapData=new BitmapData(400,240,true,0);bitmap.draw(layer,new Matrix(1,0,0,1,-400,-480),null,null,null,true);
         for each(var pair:Array in states)pair[0].visible=pair[1];
         return bitmap;
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
         var c:Object=cases[caseIndex],entry:Object={spec:c,updates:times,draws:draws,pairedIntervals:intervals,stages:[],helper:[],counts:[],helperCounts:[]};
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
