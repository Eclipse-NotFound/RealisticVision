package {
 import fe.NativeTimingAccess;
 import flash.display.*;
 import flash.media.SoundMixer;
 import flash.media.SoundTransform;
 import flash.events.*;
 import flash.filesystem.*;
 import flash.net.URLRequest;
 import flash.system.*;
 import flash.geom.*;
 import flash.utils.*;
 import flash.desktop.NativeApplication;
 public class CombatRenderProbeMod extends Sprite {
  private static const SAMPLE_COUNT=180;
  private static const WARMUP_COUNT=90;
  private static const LARGE=false;
  private static const EXPERIMENT=true;
  private static const CONTROLLED=false;
  private static const PROFILE=false;
  private static const SPLIT=false;
  private static const VISUAL=false;
  private static const SWEEP=true;
  private static const SOLO=true;
  private static const SHOW_WINDOW=true;
  private static var instance:CombatRenderProbeMod;
  public static function init(main:*):void {instance=new CombatRenderProbeMod(main);}
  private var nativeStep:Function,nativeStart:int=0,nativeEnd:int=0,nativeSerial:int=0,lastNativeSerial:int=0;
  private var host:*,wc:Class,rvClass:Class,candidateClass:Class,vectorClass:Class,vectorLoader:Loader=new Loader(),loader:Loader=new Loader(),candidateLoader:Loader=new Loader(),timer:Timer=new Timer(150);
  private var phase:int=0,ticks:int=0,settle:int=0,index:int=0,age:int=0,last:int=0;
  private var plan:Array=[],crowd:Array=[],restore:Array=[],row:Object,rv:*,floor:Number,low:Number,high:Number;
  private var result:Object={cases:[],checks:[]},shots:Dictionary=new Dictionary(true),previousFrame:Object=null,sceneLoc:*;
  private var mouseOriginal:Dictionary=new Dictionary(true);
  private var shotBefore:int=0,triggerNow:Boolean=false;
  private var marks:Array=[0,0,0,0,0,0],gunHp:Number=0;
  private function installMarks():void {
   var priorities:Array=[101,99,2,-1,-99,-101];
   for(var i:int=0;i<priorities.length;i++)installMark(i,int(priorities[i]));
  }
  private function installMark(i:int,priority:int):void {host.stage.addEventListener(Event.ENTER_FRAME,function(e:Event):void{marks[i]=getTimer();},false,priority);}
  private function noMouse(v:DisplayObject):void {
   if(v is InteractiveObject && mouseOriginal[v]===undefined){
    var interactive:InteractiveObject=v as InteractiveObject;
    mouseOriginal[v]={enabled:interactive.mouseEnabled,children:v is DisplayObjectContainer?DisplayObjectContainer(v).mouseChildren:false};
    interactive.mouseEnabled=false;if(v is DisplayObjectContainer)DisplayObjectContainer(v).mouseChildren=false;
   }
  }
  public function CombatRenderProbeMod(main:* = null) {
   if(main==null)return;SoundMixer.soundTransform=new SoundTransform(0);host=main;wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   loader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {rvClass=loader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
   var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));ctx.allowCodeImport=true;loader.load(new URLRequest('app:/rv.swf'),ctx);
   if(EXPERIMENT){
    candidateLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {candidateClass=candidateLoader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
    var candidateCtx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));candidateCtx.allowCodeImport=true;candidateLoader.load(new URLRequest('app:/candidate.swf'),candidateCtx);
    vectorLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {vectorClass=vectorLoader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
    var vectorCtx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));vectorCtx.allowCodeImport=true;vectorLoader.load(new URLRequest('app:/vector.swf'),vectorCtx);
   }
   for each(var mode:String in ['current','classic'])for each(var variant:String in ['off','normal','candidate','candidate','normal','off'])plan.push({n:6,mode:mode,variant:variant});
   timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function save():void {
   var p:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(p.indexOf('/RealisticVision/build/combat-split-output/')<0)throw new Error('wrong output root');
   var fs:FileStream=new FileStream();fs.open(new File(p+'/evidence/result.json'),FileMode.WRITE);fs.writeUTFBytes(JSON.stringify(result));fs.close();
  }
  private function fail(e:Error):void {timer.stop();host.stage.removeEventListener(Event.ENTER_FRAME,step);result.error=e.toString();trace('FAIL '+e+' '+e.getStackTrace());save();NativeApplication.nativeApplication.exit(1);}
  private function tick(e:Event):void {
   try {
    SoundMixer.soundTransform=new SoundTransform(0);var w:*=wc['w'];if(++ticks>1200)throw new Error('boot timeout '+phase);
    if(!rvClass||(EXPERIMENT&&(!candidateClass||!vectorClass))||!w||!w.allLandsLoaded||!w.landData)return;if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
    if(phase==0){w.mm.mainMenuOff();result.nativeMenuClosed=true;var saved:*=w.getSave(0);if(!saved||!saved.est)throw new Error('copied autosave missing');w.newGame(0);phase=3;return;}
    if(phase==3&&ticks%20==0)trace('D58 BOOT '+JSON.stringify({gg:w.gg!=null,loc:w.loc!=null,active:w.loc?w.loc.active:null,land:w.game?w.game.curLandId:null,stat:w.allStat,click:w.clickReq,menu:w.mm.active}));
    if(phase==3&&w.gg&&w.loc&&w.loc.active&&w.allStat==1){w.pers.healAll();w.game.beginMission('random_mane');phase=4;return;}
    if(phase==4&&w.loc&&w.loc.active&&w.game.curLandId=='random_mane'&&w.land.act.id=='random_mane'&&w.t_exit==0){w.land.gotoXY(1,3);phase=5;return;}
    if(phase==5&&w.gg&&w.loc&&w.loc.active&&w.t_exit==0){
     if(SOLO&&settle==0){
      result.removedUnits=0;
      for(var ui:int=w.loc.units.length-1;ui>=0;ui--){var removed:*=w.loc.units[ui];if(removed===w.gg)continue;
       for each(var removedChild:* in removed.childObjs)if(removedChild)w.loc.remObj(removedChild);
       w.loc.remObj(removed);w.loc.units.splice(ui,1);result.removedUnits++;
      }
     }
     if(++settle<15)return;
     if(SWEEP){w.gg.setPos(1000,959);w.gg.setVisPos();}
     low=w.gg.X-80;high=w.gg.X+500;floor=w.gg.Y;
     w.godMode=true;w.gg.invulner=false;w.ctr.clearAll();w.gg.ggControl=true;
     result.scene={land:w.game.curLandId,loc:w.loc.id,size:[w.loc.spaceX,w.loc.spaceY],nativeUnits:w.loc.units.length,platform:[low,high,floor],fps:host.stage.frameRate,screen:[host.stage.stageWidth,host.stage.stageHeight],black:w.black,roomBlack:w.loc.black,base:w.loc.base,zoom:w.cam.scaleV};
     if(w.gg.currentWeapon==null||w.gg.currentWeapon.id!='lmg')w.gg.changeWeapon('lmg',true);
     if(!w.gg.currentWeapon||w.gg.currentWeapon.id!='lmg')throw new Error('saved LMG unavailable');
     result.savedGun={lvl:w.gg.currentWeapon.lvl,hold:w.gg.currentWeapon.hold,hp:w.gg.currentWeapon.hp};
     w.gg.currentWeapon.hold=w.gg.currentWeapon.holder;
     result.weapon='lmg';result.audioVolume=SoundMixer.soundTransform.volume;
     if(SHOW_WINDOW)host.stage.nativeWindow.visible=true;
     result.windowVisible=host.stage.nativeWindow.visible;
     nativeStep=w.mm.mainStep as Function;if(nativeStep==null)throw new Error('native mainStep unavailable');
     host.stage.removeEventListener(Event.ENTER_FRAME,nativeStep);host.stage.addEventListener(Event.ENTER_FRAME,nativeFrame,false,1);
     result.nativeTiming={method:'MainMenu.mainStep',priority:1,originalPriority:0,checkedSource:true};
     sceneLoc=w.loc;gunHp=w.gg.currentWeapon.hp;timer.stop();start(w);installMarks();host.stage.addEventListener(Event.ENTER_FRAME,inputFrame,false,50);host.stage.addEventListener(Event.ENTER_FRAME,step,false,-10000);
    }
   }catch(e:Error){fail(e);}
  }
  private function nativeFrame(e:Event):void {nativeStart=getTimer();nativeSerial++;try{nativeStep(e);}finally{nativeEnd=getTimer();}}
  private function inputFrame(e:Event):void {
   var w:*=wc['w'];w.ctr.clearAll();w.gg.ggControl=true;
   if(SOLO){w.gg.setPos(low+80,floor);w.gg.dx=w.gg.dy=0;w.gg.setVisPos();}
    for(var fighterIndex:int=0;fighterIndex<crowd.length;fighterIndex++){
      var fixedFighter:*=crowd[fighterIndex];fixedFighter.setPos(low+210+fighterIndex*55,floor-1);fixedFighter.dx=fixedFighter.dy=0;fixedFighter.setVisPos();
    }
   triggerNow=row.variant.indexOf('idle')<0;
   w.ctr.keyAttack=triggerNow;
   var aimX:Number=SWEEP?low+550:low+1000,aimY:Number=SWEEP?floor-65+80*Math.sin(age/25):floor-60;
   w.cam.celX=aimX*w.cam.scaleV+w.cam.vx;w.cam.celY=aimY*w.cam.scaleV+w.cam.vy;
   w.celX=aimX;w.celY=aimY;
   var gun:*=w.gg.currentWeapon;gun.hold=gun.holder;shotBefore=int(gun.kol_shoot);
  }
  private function undo():void {
   for each(var r:Object in restore){var v:DisplayObject=r.v;if(r.layer){v.visible=r.visible;continue;}v.cacheAsBitmap=r.cache;v.mask=r.mask;if(r.mask)r.mask.visible=r.maskVisible;}
   restore=[];
  }
  private function start(w:*):void {
   w.gg.currentWeapon.hp=gunHp;
   for(var mouseObject:Object in mouseOriginal){var mouseFlags:Object=mouseOriginal[mouseObject];InteractiveObject(mouseObject).mouseEnabled=mouseFlags.enabled;if(mouseObject is DisplayObjectContainer)DisplayObjectContainer(mouseObject).mouseChildren=mouseFlags.children;}
   mouseOriginal=new Dictionary(true);
   undo();if(rv){rv.restoreAll(w,w.loc);if(rv.fogVis&&rv.fogVis.parent)rv.fogVis.parent.removeChild(rv.fogVis);}
   var p:Object=plan[index];
   while(crowd.length<p.n){
    var cls:Class=host.loaderInfo.applicationDomain.getDefinition('fe.unit.UnitMerc') as Class;var u:*=new cls('1',10,null,{weap:'smg10'});
    u.putLoc(w.loc,low+210+crowd.length*55,floor-1);u.invulner=true;w.loc.addObj(u);w.loc.units.push(u);u.step();crowd.push(u);shots[u.currentWeapon]=int(u.currentWeapon.kol_shoot);
   }
   var clsRV:Class=p.variant=='candidate'?candidateClass:p.variant=='vector'?vectorClass:rvClass;
   rv=new clsRV();rv.cfgDim=.6;rv.cfgSoftCurrent=25;rv.cfgMode=p.mode;rv.cfgEnabled=p.variant.indexOf('off')!=0;rv.d53SkipEffects=p.variant=='noeffects';rv.cfgWallBright=false;rv.mswRegistered=true;rv.cfgBaseRooms={};rv.resetRoom(w,w.loc);

   rv.profile={};rv.calls={};age=0;last=0;previousFrame=null;row={crowd:p.n,mode:p.mode,variant:p.variant,warmup:WARMUP_COUNT,sampleFrames:SAMPLE_COUNT,intervals:[],updates:[],diagnosticMs:[],masks:[],memory:[],positions:[],frames:[],allFrames:[],units:w.loc.units.length,maxObjects:0,maxProjectiles:0,maxParticles:0,attacks:0,enemyShots:0,sampleNativeEnemyShotsLowerBound:0,sampleForcedEnemyShots:0,samplePlayerShotsLowerBound:0,maxPartialEnemies:0,enemyMaskRemovals:0,effectMaskRemovals:0};
   trace('D58 START '+index+' '+JSON.stringify(p));
  }
  private function alter(v:DisplayObject,seen:Dictionary,owned:Dictionary):int {
   if(v==null||v.parent==null||seen[v])return 0;seen[v]=true;var mask:DisplayObject=v.mask;
   if(mask==null||!owned[mask])return 0;
   restore.push({v:v,cache:v.cacheAsBitmap,mask:mask,maskVisible:mask.visible});
   v.mask=null;v.cacheAsBitmap=false;mask.visible=false;
   return 1;
  }
  private function step(e:Event):void {
   try {
    var w:*=wc['w'];if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
    if(w.loc!==sceneLoc||w.allStat!=1||w.mm.active)throw new Error('scene/menu/SATS changed during timing');
    var now:int=getTimer();
    if(nativeSerial!=lastNativeSerial+1||nativeStart>nativeEnd||nativeEnd>now)throw new Error('native order');lastNativeSerial=nativeSerial;
    if(previousFrame){
     previousFrame.nextInterval=now-last;previousFrame.nativeNext=nativeEnd-nativeStart;previousFrame.otherHandlersNext=now-nativeEnd;
     previousFrame.afterProbe=nativeStart-previousFrame.probeEnd;previousFrame.probeMs=previousFrame.probeEnd-previousFrame.start;
     previousFrame.worldStepsNext=NativeTimingAccess.tick(w)-previousFrame.nativeTick;
     if(previousFrame.worldStepsNext!=1||previousFrame.afterProbe<0||previousFrame.nativeNext+previousFrame.otherHandlersNext+previousFrame.afterProbe+previousFrame.probeMs!=previousFrame.nextInterval)throw new Error('native partition');
    }
    if(age>=WARMUP_COUNT&&last)row.intervals.push(now-last);last=now;
    undo();w.ctr.clearAll();w.gg.ggControl=true;
    // Controlled trigger requests, not pure autonomous AI. Native smg10 emits
    // on the next Weapon.actions; driver cost is recorded separately from RV.
    // kol_shoot may reset between frames; positive deltas are a lower bound,
    // never advertised as an exact lifetime shot count.
    var driveStart:int=getTimer(),nativeEnemyShotLowerBound:int=0,forcedEnemyShots:int=0;
    for each(var fighter:* in crowd){
     fighter.setCel(w.gg);var enemyGun:*=fighter.currentWeapon;enemyGun.hold=enemyGun.holder;
     var beforeForced:int=int(enemyGun.kol_shoot);
     nativeEnemyShotLowerBound+=Math.max(0,beforeForced-int(shots[enemyGun]));
     if(age%6==0)enemyGun.attack();
     forcedEnemyShots+=Math.max(0,int(enemyGun.kol_shoot)-beforeForced);shots[enemyGun]=int(enemyGun.kol_shoot);
    }
    var driveMs:int=getTimer()-driveStart;
    row.enemyShots+=nativeEnemyShotLowerBound+forcedEnemyShots;
    if(age>=WARMUP_COUNT){row.sampleNativeEnemyShotsLowerBound+=nativeEnemyShotLowerBound;row.sampleForcedEnemyShots+=forcedEnemyShots;}
    var memStart:Number=System.totalMemory;
    if(PROFILE&&age==WARMUP_COUNT){rv.profile={};rv.calls={};}
    var t:int=getTimer();rv.frameCount++;rv.onFrameInner();var ms:int=getTimer()-t;
    t=getTimer();var masks:int=0,seen:Dictionary=new Dictionary(true),owned:Dictionary=new Dictionary(true),kind:String=row.variant;
    if(kind=='enemy-nodraw'||kind=='effect-nodraw'){
     var rec:Object;
     for each(rec in rv.unitVis){if(rec.m2)owned[rec.m2]=true;if(rec.m3)owned[rec.m3]=true;if(rec.bodyDraw)owned[rec.bodyDraw.shape]=true;if(rec.barDraw)owned[rec.barDraw.shape]=true;}
     for each(rec in rv.weaponVisuals)if(rec.shape)owned[rec.shape]=true;
     for each(rec in rv.worldVisuals)if(rec.shape)owned[rec.shape]=true;
     if(kind=='enemy-nodraw')for each(var unit:* in w.loc.units){
      if(unit===w.gg)continue;masks+=alter(unit.vis,seen,owned);masks+=alter(unit.hpbar,seen,owned);
      for each(var child:* in unit.childObjs)if(child.vis)masks+=alter(child.vis,seen,owned);
     }
    }
    var obj:*=w.loc.firstObj,count:int=0,projectiles:int=0,particles:int=0;
    while(obj&&count++<5000){
     var name:String=getQualifiedClassName(obj);
     if(name.indexOf('Bullet')>=0)projectiles++;
     if(name=='fe.graph::Part')particles++;
     if((name.indexOf('Bullet')>=0||name=='fe.graph::Part')&&obj.vis){
      if(kind=='effect-nodraw')masks+=alter(obj.vis,seen,owned);
      if(kind=='nomouse')noMouse(obj.vis);
     }
     obj=obj.nobj;
    }
    for each(var layer:DisplayObjectContainer in w.grafon.visObjs){
     for(var i:int=layer.numChildren-1;i>=0;i--){
      var visual:DisplayObject=layer.getChildAt(i);
      if(kind=='enemy-nodraw'){if(getQualifiedClassName(visual).indexOf('visualGrifArm')==0)masks+=alter(visual,seen,owned);}
      else if(visual.mask)masks++;
     }
     // Unit.step reads its own vis.visible to decide whether to emit movement
     // particles. Hide the parent object layers, never change child visibility.
     // This diagnostic also hides player/props; it measures object-layer cost,
     // not enemy-only cost, and needs the zero-enemy control to interpret.
     if(kind=='noobjects'){restore.push({v:layer,layer:true,visible:layer.visible});layer.visible=false;}
    }
    var partial:int=0;for each(var unitState:Object in rv.unitVis)if(unitState.state==2)partial++;
    row.maxPartialEnemies=Math.max(row.maxPartialEnemies,partial);
    if(kind=='enemy-nodraw')row.enemyMaskRemovals+=masks;
    if(kind=='effect-nodraw')row.effectMaskRemovals+=masks;
    previousFrame={start:now,nativeTick:NativeTimingAccess.tick(w),nativeEnemyShotLowerBound:nativeEnemyShotLowerBound,forcedEnemyShots:forcedEnemyShots,enemyDriveMs:driveMs,partialEnemies:partial,age:age,rv:ms,band100:marks[1]-marks[0],bandNative:marks[3]-marks[2],bandMinus100:marks[5]-marks[4],beforeProbe:now-marks[0],diagnosticMs:getTimer()-t,worldPass:rv.worldPass,objects:count,projectiles:projectiles,particles:particles,masks:masks,memoryBefore:memStart,memoryAfter:System.totalMemory};
    row.allFrames.push(previousFrame);
    if(age>=WARMUP_COUNT){row.updates.push(ms);row.diagnosticMs.push(previousFrame.diagnosticMs);row.masks.push(masks);row.memory.push(System.totalMemory);row.positions.push([w.gg.X,w.gg.Y]);row.frames.push(previousFrame);}
    row.maxObjects=Math.max(count,row.maxObjects);row.maxProjectiles=Math.max(projectiles,row.maxProjectiles);row.maxParticles=Math.max(particles,row.maxParticles);
    var gun:*=w.gg.currentWeapon;var delta:int=Math.max(0,int(gun.kol_shoot)-shotBefore);
    previousFrame.trigger=triggerNow;previousFrame.fired=delta>0;previousFrame.fireTime=0;row.attacks+=delta;if(age>=WARMUP_COUNT)row.samplePlayerShotsLowerBound+=delta;

    if(age==90 && row.variant.indexOf('idle')<0 && row.attacks==0)throw new Error('LMG did not fire; check player skill');
    previousFrame.probeEnd=getTimer();if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;
    if(VISUAL||index==0){var bitmap:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,false,0);bitmap.draw(host.stage);var imageFile:FileStream=new FileStream();imageFile.open(new File(File.applicationDirectory.nativePath+'/evidence/scene-'+index+'.png'),FileMode.WRITE);imageFile.writeBytes(bitmap.encode(bitmap.rect,new PNGEncoderOptions()));imageFile.close();bitmap.dispose();}
    // Sample cache sizes outside the timed frame sequence. Pixel bytes exclude
    // Flash's own render caches; never label this as total application memory.
    var retained:Object={rasters:0,rawPixels:0,softPixels:0,previousPixels:0,unusedBarShapes:0,supportCachedRasters:0,visuals:0,worldPass:rv.worldPass};
    for each(var raster:Object in rv.worldMasks){
     retained.rasters++;if(raster.m3)retained.unusedBarShapes++;
     if(raster.supportEmptyValid === true)retained.supportCachedRasters++;
     if(raster.m2d)retained.rawPixels+=BitmapData(raster.m2d).width*BitmapData(raster.m2d).height;
     if(raster.m2e)retained.softPixels+=BitmapData(raster.m2e).width*BitmapData(raster.m2e).height;
     if(raster.maskInput)retained.previousPixels+=BitmapData(raster.maskInput).width*BitmapData(raster.maskInput).height;
    }
    retained.emptyVisuals=0;retained.extraEmptyVisuals=0;
    for(var visualKey:Object in rv.worldVisuals){
     retained.visuals++;var worldRecord:Object=rv.worldVisuals[visualKey];
     if(worldRecord.dark){retained.emptyVisuals++;if(!worldRecord.raster.fullyDark)retained.extraEmptyVisuals++;}
    }
    retained.optimizedCalls=rv.trailingHits;retained.alphaHits=rv.alphaHits;retained.auxHits=rv.auxHits;retained.vectorHits=rv.vectorHits;retained.fractionHits=rv.fractionHits;row.retained=retained;
    // Endpoint inventory only: distinguish actual attached masks and duplicate
    // layer references from the cheap per-frame raw loop count.
    var uniqueLayers:Dictionary=new Dictionary(true),uniqueVisuals:Dictionary=new Dictionary(true),rvMasks:Dictionary=new Dictionary(true);
    for each(var maskRecord:Object in rv.unitVis){if(maskRecord.m2)rvMasks[maskRecord.m2]=true;if(maskRecord.m3)rvMasks[maskRecord.m3]=true;if(maskRecord.bodyDraw)rvMasks[maskRecord.bodyDraw.shape]=true;if(maskRecord.barDraw)rvMasks[maskRecord.barDraw.shape]=true;}
    for each(maskRecord in rv.weaponVisuals)if(maskRecord.shape)rvMasks[maskRecord.shape]=true;
    for each(maskRecord in rv.worldVisuals)if(maskRecord.shape)rvMasks[maskRecord.shape]=true;
    row.maskInventory={layers:0,duplicateLayers:0,masked:0,visible:0,owned:0,unrecognized:0,maskShapeLinks:0,reciprocalPairs:0,types:{}};
    for each(var maskLayer:DisplayObjectContainer in w.grafon.visObjs){
     if(uniqueLayers[maskLayer]){row.maskInventory.duplicateLayers++;continue;}uniqueLayers[maskLayer]=true;row.maskInventory.layers++;
     for(var mi:int=0;mi<maskLayer.numChildren;mi++){
      var mv:DisplayObject=maskLayer.getChildAt(mi);if(uniqueVisuals[mv]||!mv.mask)continue;uniqueVisuals[mv]=true;
      if(rvMasks[mv]){row.maskInventory.maskShapeLinks++;if(mv.mask.mask===mv)row.maskInventory.reciprocalPairs++;continue;}
      row.maskInventory.masked++;if(mv.visible)row.maskInventory.visible++;if(rvMasks[mv.mask])row.maskInventory.owned++;else row.maskInventory.unrecognized++;
      var mt:String=getQualifiedClassName(mv);row.maskInventory.types[mt]=int(row.maskInventory.types[mt])+1;
     }
    }
    if(PROFILE){row.profile=rv.profile;row.calls=rv.calls;}
    row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);save();trace('D58 END '+index+' '+row.variant+' shots='+row.attacks+' bullets='+row.maxProjectiles);
    if(++index<plan.length){start(w);return;}
    undo();host.stage.removeEventListener(Event.ENTER_FRAME,inputFrame);host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D58 COMPLETE');NativeApplication.nativeApplication.exit(0);
   }catch(error:Error){fail(error);}
  }
 }
}
