package {
   import flash.display.*;
   import flash.events.*;
   import flash.net.URLRequest;
   import flash.system.*;
   import flash.utils.*;
   import flash.geom.*;
   import flash.filesystem.*;
   import flash.desktop.NativeApplication;

   public class WallSurfaceProbe extends Sprite {
      private static const ROCK:Boolean=CONFIG::rockFixture;
      private static const BENCH:Boolean=CONFIG::wallBench;
      private static var probe:WallSurfaceProbe;
      public static function init(main:*):void { probe=new WallSurfaceProbe(main); }
      private var host:*;
      private var worldClass:Class;
      private var classes:Object={};
      private var loaders:Array=[];
      private var timer:Timer=new Timer(200);
      private var phase:int=0,ticks:int=0,settled:int=0;
      private var result:Object={checks:[],states:[],timings:[]};
      private var captureState:Object;
      private var benchState:Object;
      public function WallSurfaceProbe(main:*=null) {
         if(main==null)return;
         host=main;worldClass=main.loaderInfo.applicationDomain.getDefinition("fe.World") as Class;
         for each(var name:String in ["baseline","candidate"])load(name);
         timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
      }
      private function load(name:String):void {
         var loader:Loader=new Loader();loaders.push(loader);
         var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));ctx.allowCodeImport=true;
         loader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {
            classes[name]=loader.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod");
         });
         loader.load(new URLRequest("app:/"+name+".swf"),ctx);
      }
      private function check(ok:Boolean,name:String):void {
         result.checks.push({ok:ok,name:name});trace((ok?"PASS ":"FAIL ")+name);
         if(!ok)throw new Error(name);
      }
      private function save(name:String,data:*):void {
         var directory:String=File.applicationDirectory.nativePath.replace(/\\/g,"/");
         if(directory.indexOf("/RealisticVision/build/wall-options-output/")<0)throw new Error("Unexpected probe output root");
         // app: resources are read-only; this explicit native file URL stays in
         // the owned test directory, with no dependency on APPDATA permissions.
         var target:File=new File(directory+"/evidence/"+name),stream:FileStream=new FileStream();
         stream.open(target,FileMode.WRITE);
         if(data is ByteArray)stream.writeBytes(data);else stream.writeUTFBytes(String(data));
         stream.close();trace("FILE "+name);
      }
      private function emit(name:String,b:BitmapData):void {save(name+".png",b.encode(b.rect,new PNGEncoderOptions()));b.dispose();}
      private function shot(display:DisplayObject,width:int,height:int,matrix:Matrix=null):BitmapData {
         var b:BitmapData=new BitmapData(width,height,false,0xffffff);b.draw(display,matrix,null,null,null,true);return b;
      }
      private function tick(e:Event):void {
         try {
            if(++ticks>300)throw new Error("timeout phase="+phase);
            var w:*=worldClass["w"];
            if(!classes.baseline||!classes.candidate||!w||!w.allLandsLoaded||!w.landData)return;
            if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
            if(phase==0){w.mm.active=false;w.newGame(-1,"LP",null);phase=1;trace("SURFACE GAME newGame");return;}
            if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.game.curLandId){w.pers.healAll();w.game.beginMission("rbl");phase=2;return;}
            if(phase==2&&w.loc&&w.loc.active&&w.game.curLandId=="rbl"&&w.land.act.id=="rbl"){
               w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw new Error("training entry failed");
               w.gg.setPos(1080,640);phase=3;return;
            }
            if(phase==3&&w.loc&&w.loc.active&&w.land.locX==1&&w.land.locY==0){
               if(++settled<15)return;
               phase=4;w.mm.active=true;timer.delay=10;
            }
            if(phase==4){
               // Return to AIR between steps: a whole six-case experiment in a
               // single event can hit the runtime's long-script watchdog.
               if(!(BENCH?bench(w):capture(w)))return;
               timer.stop();save("result.json",JSON.stringify(result));
               trace("SURFACE GAME COMPLETE checks="+result.checks.length);NativeApplication.nativeApplication.exit(0);
            }
         }catch(error:Error){timer.stop();trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);try{save("result.json",JSON.stringify(result));}catch(writeError:Error){trace("FAIL evidence write "+writeError);}NativeApplication.nativeApplication.exit(1);}
      }
      private function lightState(loc:*):String {
         var a:Array=[];for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
            var t:*=loc.getTile(x,y);a.push([t.visi,t.t_visi]);
         }return JSON.stringify(a);
      }
      private function capture(w:*):Boolean {
         var loc:*=w.loc;w.black=true;loc.black=true;loc.base=false;
         var width:int=loc.spaceX*40,height:int=loc.spaceY*40;
         if(captureState==null){
         if(ROCK){
            // Native stone material, unchanged training geometry, one partial tile.
            // This is a controlled material fixture, not the user's exact save.
            for(var ry:int=0;ry<loc.spaceY;ry++)for(var rx:int=0;rx<loc.spaceX;rx++)
               if(loc.getTile(rx,ry).opac>=1)loc.getTile(rx,ry).front="G";
            check(loc.getTile(23,10).opac>=1,"rock fixture partial wall exists");
            loc.getTile(23,10).zForm=2;w.grafon.drawLoc(loc);
         }
         result.fixture=ROCK?"native-stone-training-partial-wall":"native-metal-training";
         captureState={original:JSON.parse(lightState(loc)),variant:0,mode:0,step:0,references:{}};
         emit("terrain",shot(w.grafon.visFront,width,height));
         // Preserve foreground alpha separately for quantitative leak checks.
         var alpha:BitmapData=new BitmapData(width,height,true,0);alpha.draw(w.grafon.visFront);emit("terrain-alpha",alpha);
         w.cam.setLoc(loc);w.cam.setZoom();w.cam.calc(w.gg);
         return false;
         }
         var route:Array=[[1080,640],[480,640],[240,640],[240,920],[240,640],[480,640]];
         var variant:String=["baseline","off","on"][captureState.variant];
         var mode:String=["classic","current"][captureState.mode];
         var step:int=captureState.step,previous:*=captureState.previous,m:*=captureState.m;
         var original:Array=captureState.original,references:Object=captureState.references;
         if(step==0){
               if(previous){previous.restoreAll(w,loc);if(previous.fogVis)previous.fogVis.visible=false;}
               for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
                  loc.getTile(x,y).visi=original[x+y*loc.spaceX][0];loc.getTile(x,y).t_visi=original[x+y*loc.spaceX][1];
               }
               var cls:Class=classes[variant=="baseline"?"baseline":"candidate"];m=new cls();
               if(variant!="baseline")m.cfgWallBright=variant=="on";
               m.cfgMode=mode;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,loc);
               captureState.m=m;
         }
                  var routeStart:int=getTimer();
                  trace("ROUTE START "+variant+" "+mode+" "+step);
                  w.gg.setPos(route[step][0],route[step][1]);w.gg.setVisPos();
                  w.cam.calc(w.gg);
                  for(var lf:int=0;lf<24;lf++){loc.lighting();loc.lighting2();}
                  var before:String=lightState(loc);
                  for(var f:int=0;f<24;f++){m.frameCount++;m.onFrameInner();}
                  check(lightState(loc)==before,variant+" "+mode+" route "+step+" native light unchanged");
                  var enemies:Array=[];
                  for each(var unit:* in loc.units)if(unit!==loc.gg && unit.fraction>0 && unit.fraction<100)
                     enemies.push([unit.id,m.enemyState(loc,unit)]);
                  var state:Object={variant:variant,mode:mode,step:step,eye:[m.eyeX,m.eyeY],fov:m.fov,explored:m.explored,seen:m.seenSub,enemies:enemies};
                  var identity:String=JSON.stringify({eye:state.eye,fov:state.fov,explored:state.explored,seen:state.seen,enemies:enemies});
                  var key:String=mode+"-"+step;
                  if(variant=="baseline")references[key]=identity;
                  else check(identity==references[key],mode+" route "+step+" FOV/exploration/enemy visibility identical to installed lineage");
                  trace("ROUTE UPDATE "+variant+" "+mode+" "+step+" ms="+(getTimer()-routeStart));
                  if(step==3||step==5){
                  var tag:String=(step==3?"lower":"upper")+"-"+mode;
                  emit(variant+"-"+tag,shot(w.grafon.visual,width,height));
                  emit(variant+"-"+tag+"-fog",shot(m.fogVis,width,height));
                  emit(variant+"-"+tag+"-stage",shot(host.stage,host.stage.stageWidth,host.stage.stageHeight));
                  if(variant=="off"){
                     var beforeToggle:String=JSON.stringify({fov:m.fov,explored:m.explored,seen:m.seenSub,light:lightState(loc)});
                     m.cfgWallBright=true;m.updateWallSurface(w,loc);m.cfgWallBright=false;m.updateWallSurface(w,loc);
                     check(beforeToggle==JSON.stringify({fov:m.fov,explored:m.explored,seen:m.seenSub,light:lightState(loc)}),mode+" "+tag+" live toggle leaves game and sight state unchanged");
                  }
                  if(variant=="on"){
                     m.fogVis.visible=false;w.grafon.setLight();w.grafon.visLight.visible=true;
                     emit("native-"+tag,shot(w.grafon.visual,width,height));
                     emit("native-"+tag+"-fog",shot(w.grafon.visLight,width,height,w.grafon.visLight.transform.matrix));
                     w.grafon.visLight.visible=false;m.fogVis.visible=true;
                  }
                  state.tiles=[];
                  for(y=0;y<loc.spaceY;y++)for(x=0;x<loc.spaceX;x++){
                     var t:*=loc.getTile(x,y);state.tiles.push({x:x,y:y,opac:t.opac,zForm:t.zForm,visi:t.visi,explored:m.memoryExplored(x+y*loc.spaceX)});
                  }
                  // Identity was compared immediately above. Persist per-position
                  // tile values, not aliases of the arrays mutated by later steps.
                  delete state.fov;delete state.explored;delete state.seen;result.states.push(state);
                  }
         if(++captureState.step==route.length){
            captureState.previous=m;captureState.step=0;
            if(++captureState.mode==2){captureState.mode=0;++captureState.variant;}
         }
         return captureState.variant==3;
      }

      private function bench(w:*):Boolean {
         var loc:*=w.loc;w.black=true;loc.black=true;loc.base=false;
         // Isolate rendering costs and alternate A/B order per frame. No PNG
         // encoding, native physics or competing enemy display writers in timing.
         if(benchState==null){
            benchState={savedUnits:loc.units,previous:[],canvas:new BitmapData(loc.spaceX*40,loc.spaceY*40,false,0xffffff),mode:0,variant:0,frame:0};
            loc.units=[];
         }
         var mode:String=["classic","current"][benchState.mode];
         var variant:String,m:*,f:int;
         if(benchState.variant<3){
            if(benchState.variant==0){
               for each(var old:* in benchState.previous)old.fogVis.visible=false;
               benchState.mods={};benchState.times={baseline:[],off:[],on:[]};benchState.draws={baseline:[],off:[],on:[]};
            }
            variant=["baseline","off","on"][benchState.variant];
               var cls:Class=classes[variant=="baseline"?"baseline":"candidate"];var m:*=new cls();
               if(variant!="baseline")m.cfgWallBright=variant=="on";
               m.cfgMode=mode;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,loc);
               for each(var position:Array in [[1080,640],[480,640],[240,640],[240,920],[480,640]]){
                  w.gg.setPos(position[0],position[1]);
                  for(f=0;f<30;f++){loc.lighting();loc.lighting2();m.frameCount++;m.onFrameInner();}
               }
               benchState.mods[variant]=m;benchState.previous.push(m);++benchState.variant;
               trace("BENCH WARM "+mode+" "+variant);return false;
         }
               f=benchState.frame;
               w.gg.setPos(480+(f%90)*4,640);
               var order:Array=[["baseline","off","on"],["off","on","baseline"],["on","baseline","off"]][f%3];
               for each(variant in order){
                  m=benchState.mods[variant];var start:int=getTimer();m.frameCount++;m.onFrameInner();benchState.times[variant].push(getTimer()-start);
                  start=getTimer();benchState.canvas.fillRect(benchState.canvas.rect,0xffffff);benchState.canvas.draw(m.fogVis,null,null,null,null,true);benchState.draws[variant].push(getTimer()-start);
               }
         if(++benchState.frame<120)return false;
         for each(variant in ["baseline","off","on"]){
            var measurement:Object={variant:variant,mode:mode,updates:benchState.times[variant],composition:benchState.draws[variant]};
            m=benchState.mods[variant];
            if("wallSurface" in m && "profile" in m.wallSurface)measurement.profile=m.wallSurface.profile;
            result.timings.push(measurement);
         }
         trace("BENCH MODE COMPLETE "+mode);benchState.frame=0;benchState.variant=0;
         if(++benchState.mode<2)return false;
         loc.units=benchState.savedUnits;benchState.canvas.dispose();result.fixture="paired-native-training-render-only";
         check(true,"paired rendering benchmark completed without screenshots in timing");
         return true;
      }
   }
}
