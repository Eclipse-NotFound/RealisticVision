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
         if(directory.indexOf("/RealisticVision/build/wall-surface-output/")<0)throw new Error("Unexpected probe output root");
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
               phase=4;timer.stop();w.mm.active=true;if(BENCH)bench(w);else capture(w);save("result.json",JSON.stringify(result));
               trace("SURFACE GAME COMPLETE checks="+result.checks.length);NativeApplication.nativeApplication.exit(0);
            }
         }catch(error:Error){timer.stop();trace("FAIL "+error+" "+error.getStackTrace());result.error=String(error);try{save("result.json",JSON.stringify(result));}catch(writeError:Error){trace("FAIL evidence write "+writeError);}NativeApplication.nativeApplication.exit(1);}
      }
      private function lightState(loc:*):String {
         var a:Array=[];for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
            var t:*=loc.getTile(x,y);a.push([t.visi,t.t_visi]);
         }return JSON.stringify(a);
      }
      private function capture(w:*):void {
         var loc:*=w.loc;w.black=true;loc.black=true;loc.base=false;
         if(ROCK){
            // Native stone material, unchanged training geometry, one partial tile.
            // This is a controlled material fixture, not the user's exact save.
            for(var ry:int=0;ry<loc.spaceY;ry++)for(var rx:int=0;rx<loc.spaceX;rx++)
               if(loc.getTile(rx,ry).opac>=1)loc.getTile(rx,ry).front="G";
            check(loc.getTile(23,10).opac>=1,"rock fixture partial wall exists");
            loc.getTile(23,10).zForm=2;w.grafon.drawLoc(loc);
         }
         result.fixture=ROCK?"native-stone-training-partial-wall":"native-metal-training";
         var width:int=loc.spaceX*40,height:int=loc.spaceY*40;
         var original:Array=JSON.parse(lightState(loc)) as Array;
         var route:Array=[[1080,640],[480,640],[240,640],[240,920],[240,640],[480,640]];
         var previous:*,m:*,references:Object={};
         emit("terrain",shot(w.grafon.visFront,width,height));
         // Preserve foreground alpha separately for quantitative leak checks.
         var alpha:BitmapData=new BitmapData(width,height,true,0);alpha.draw(w.grafon.visFront);emit("terrain-alpha",alpha);
         for each(var variant:String in ["baseline","candidate"]){
            for each(var mode:String in ["classic","current"]){
               if(previous){previous.restoreAll(w,loc);if(previous.fogVis)previous.fogVis.visible=false;}
               for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
                  loc.getTile(x,y).visi=original[x+y*loc.spaceX][0];loc.getTile(x,y).t_visi=original[x+y*loc.spaceX][1];
               }
               var cls:Class=classes[variant];m=new cls();m.cfgMode=mode;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,loc);
               for(var step:int=0;step<route.length;step++){
                  w.gg.setPos(route[step][0],route[step][1]);w.gg.setVisPos();
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
                  if(step!=3&&step!=5)continue;
                  var tag:String=(step==3?"lower":"upper")+"-"+mode;
                  emit(variant+"-"+tag,shot(w.grafon.visual,width,height));
                  emit(variant+"-"+tag+"-fog",shot(m.fogVis,width,height));
                  if(variant=="candidate"){
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
               // End-to-end fixed input replay includes wall-mask composition,
               // but excludes scene drawing/PNG I/O. This is not combat FPS.
               var times:Array=[],drawTimes:Array=[];
               var canvas:BitmapData=new BitmapData(width,height,false,0xffffff);
               for(f=0;f<60;f++){
                  w.gg.setPos(480+f*4,640);var start:int=getTimer();m.frameCount++;m.onFrameInner();times.push(getTimer()-start);
                  start=getTimer();canvas.fillRect(canvas.rect,0xffffff);canvas.draw(m.fogVis,null,null,null,null,true);drawTimes.push(getTimer()-start);
               }canvas.dispose();result.timings.push({variant:variant,mode:mode,updates:times,composition:drawTimes});
               previous=m;
            }
         }
      }

      private function bench(w:*):void {
         var loc:*=w.loc;w.black=true;loc.black=true;loc.base=false;
         // Isolate rendering costs and alternate A/B order per frame. No PNG
         // encoding, native physics or competing enemy display writers in timing.
         var savedUnits:*=loc.units;loc.units=[];
         var previous:Array=[];
         var canvas:BitmapData=new BitmapData(loc.spaceX*40,loc.spaceY*40,false,0xffffff);
         for each(var mode:String in ["classic","current"]){
            for each(var old:* in previous)old.fogVis.visible=false;
            var mods:Object={},times:Object={baseline:[],candidate:[]},draws:Object={baseline:[],candidate:[]};
            for each(var variant:String in ["baseline","candidate"]){
               var cls:Class=classes[variant];var m:*=new cls();m.cfgMode=mode;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,loc);
               for each(var position:Array in [[1080,640],[480,640],[240,640],[240,920],[480,640]]){
                  w.gg.setPos(position[0],position[1]);
                  for(var f:int=0;f<30;f++){loc.lighting();loc.lighting2();m.frameCount++;m.onFrameInner();}
               }
               mods[variant]=m;previous.push(m);
            }
            for(f=0;f<120;f++){
               w.gg.setPos(480+(f%90)*4,640);
               var order:Array=f%2?["candidate","baseline"]:["baseline","candidate"];
               for each(variant in order){
                  m=mods[variant];var start:int=getTimer();m.frameCount++;m.onFrameInner();times[variant].push(getTimer()-start);
                  start=getTimer();canvas.fillRect(canvas.rect,0xffffff);canvas.draw(m.fogVis,null,null,null,null,true);draws[variant].push(getTimer()-start);
               }
            }
            for each(variant in ["baseline","candidate"])result.timings.push({variant:variant,mode:mode,updates:times[variant],composition:draws[variant]});
         }
         loc.units=savedUnits;canvas.dispose();result.fixture="paired-native-training-render-only";
         check(true,"paired rendering benchmark completed without screenshots in timing");
      }
   }
}
