package {
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
  private static const EXPERIMENT=false;
  private static const CONTROLLED=false;
  private static const PROFILE=false;
  private static const SPLIT=false;
  private static var instance:CombatRenderProbeMod;
  public static function init(main:*):void {instance=new CombatRenderProbeMod(main);}
  private var host:*,wc:Class,rvClass:Class,candidateClass:Class,loader:Loader=new Loader(),candidateLoader:Loader=new Loader(),timer:Timer=new Timer(150);
  private var phase:int=0,ticks:int=0,settle:int=0,index:int=0,age:int=0,last:int=0;
  private var plan:Array=[],crowd:Array=[],restore:Array=[],row:Object,rv:*,floor:Number,low:Number,high:Number;
  private var result:Object={cases:[],checks:[]},shots:Dictionary=new Dictionary(true),previousFrame:Object=null,sceneLoc:*;
  private var mouseOriginal:Dictionary=new Dictionary(true);
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
   }
   for each(var variant:String in ['normal','nomouse','nodraw','noeffects','noeffects','nodraw','nomouse','normal'])plan.push({n:0,mode:'current',variant:variant});
   timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function save():void {
   var p:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(p.indexOf('/RealisticVision/build/solo-fire-output/')<0)throw new Error('wrong output root');
   var fs:FileStream=new FileStream();fs.open(new File(p+'/evidence/result.json'),FileMode.WRITE);fs.writeUTFBytes(JSON.stringify(result));fs.close();
  }
  private function fail(e:Error):void {timer.stop();host.stage.removeEventListener(Event.ENTER_FRAME,step);result.error=e.toString();trace('FAIL '+e+' '+e.getStackTrace());save();NativeApplication.nativeApplication.exit(1);}
  private function tick(e:Event):void {
   try {
    SoundMixer.soundTransform=new SoundTransform(0);var w:*=wc['w'];if(++ticks>1200)throw new Error('boot timeout '+phase);
    if(!rvClass||(EXPERIMENT&&!candidateClass)||!w||!w.allLandsLoaded||!w.landData)return;if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
    if(phase==0){w.mm.active=false;w.newGame(-1,'LP',null);phase=1;return;}
    if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.game.curLandId){
     if(LARGE){var c:*=host.getChildByName('ContinuousSceneCarrier');if(!c||!c.sceneAPI.ready||w.t_exit!=0||!w.game.lands.continuous_scene)return;}
     w.pers.healAll();w.game.beginMission(LARGE?'continuous_scene':'rbl');phase=2;return;
    }
    if(phase==2&&w.loc&&w.loc.active&&w.t_exit==0&&w.game.curLandId==(LARGE?'continuous_scene':'rbl')&&w.land.act.id==w.game.curLandId){
     if(!LARGE){w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw new Error('training entry');w.gg.setPos(480,640);}phase=3;return;
    }
    if(phase==3&&w.loc&&w.loc.active&&(LARGE||(w.land.locX==1&&w.land.locY==0))){
     if(++settle<15)return;
     var found:Boolean=false;
     for(var fy:int=6;fy<w.loc.spaceY-2&&!found;fy++){
      var begin:int=-1;
      for(var fx:int=2;fx<w.loc.spaceX-2;fx++){
       var tile:*=w.loc.getTile(fx,fy);var clear:Boolean=tile.opac>=1&&int(tile.zForm)==0;
       for(var ay:int=1;ay<=3&&clear;ay++)if(w.loc.getTile(fx,fy-ay).opac>=1)clear=false;
       if(clear){if(begin<0)begin=fx;}else begin=-1;
       if(begin>=0&&fx-begin>=15){low=(begin+2)*40;high=(fx-1)*40;floor=fy*40;found=true;break;}
      }
     }
     if(!found)throw new Error('native platform not found');
     w.black=true;w.loc.black=true;w.loc.base=false;w.godMode=true;w.gg.invulner=false;
     w.gg.setPos(low+80,floor-1);w.gg.setVisPos();w.ctr.clearAll();w.gg.ggControl=true;
     result.scene={large:LARGE,controlled:CONTROLLED,size:[w.loc.spaceX,w.loc.spaceY],nativeUnits:w.loc.units.length,platform:[low,high,floor],fps:host.stage.frameRate};
     var weapons:Class=host.loaderInfo.applicationDomain.getDefinition('fe.weapon.Weapon') as Class;
     w.gg.invent.weapons['lmg']=weapons['create'](w.gg,'lmg');w.gg.changeWeapon('lmg',true);
     if(!w.gg.currentWeapon||w.gg.currentWeapon.id!='lmg')throw new Error('LMG equip failed');
     w.gg.currentWeapon.lvl=1;w.gg.currentWeapon.perslvl=0;w.gg.currentWeapon.hold=100000;w.gg.currentWeapon.hp=100000;
     result.weapon='lmg';result.audioVolume=SoundMixer.soundTransform.volume;
     sceneLoc=w.loc;timer.stop();start(w);host.stage.addEventListener(Event.ENTER_FRAME,step,false,-10000);
    }
   }catch(e:Error){fail(e);}
  }
  private function undo():void {
   for each(var r:Object in restore){var v:DisplayObject=r.v;if(r.layer){v.visible=r.visible;continue;}v.cacheAsBitmap=r.cache;v.mask=r.mask;if(r.mask)r.mask.visible=r.maskVisible;}
   restore=[];
  }
  private function start(w:*):void {
   for(var mouseObject:Object in mouseOriginal){var mouseFlags:Object=mouseOriginal[mouseObject];InteractiveObject(mouseObject).mouseEnabled=mouseFlags.enabled;if(mouseObject is DisplayObjectContainer)DisplayObjectContainer(mouseObject).mouseChildren=mouseFlags.children;}
   mouseOriginal=new Dictionary(true);
   undo();if(rv){rv.restoreAll(w,w.loc);if(rv.fogVis&&rv.fogVis.parent)rv.fogVis.parent.removeChild(rv.fogVis);}
   var p:Object=plan[index];
   while(crowd.length<p.n){
    var cls:Class=host.loaderInfo.applicationDomain.getDefinition('fe.unit.UnitMerc') as Class;var u:*=new cls('1',10,null,{weap:'smg10'});
    u.putLoc(w.loc,low+210+crowd.length*55,floor-1);u.invulner=true;w.loc.addObj(u);w.loc.units.push(u);u.step();crowd.push(u);
   }
   var clsRV:Class=p.variant=='candidate'?candidateClass:rvClass;
   rv=new clsRV();rv.cfgDim=.6;rv.cfgSoftCurrent=25;rv.cfgMode=p.mode;rv.cfgEnabled=p.variant.indexOf('off')!=0;rv.d53SkipEffects=p.variant=='noeffects';rv.cfgWallBright=false;rv.mswRegistered=true;rv.cfgBaseRooms={};rv.resetRoom(w,w.loc);
   
   rv.profile={};rv.calls={};age=0;last=0;previousFrame=null;row={crowd:p.n,mode:p.mode,variant:p.variant,warmup:WARMUP_COUNT,sampleFrames:SAMPLE_COUNT,intervals:[],updates:[],diagnosticMs:[],masks:[],memory:[],positions:[],frames:[],units:w.loc.units.length,maxObjects:0,maxProjectiles:0,maxParticles:0,attacks:0};
   trace('D53 START '+index+' '+JSON.stringify(p));
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
    var now:int=getTimer();if(previousFrame)previousFrame.nextInterval=now-last;
    if(age>=WARMUP_COUNT&&last)row.intervals.push(now-last);last=now;
    undo();w.ctr.clearAll();w.gg.ggControl=true;
    if(CONTROLLED){
     // Reproducible rendering stimulus only: real AI, weapons and projectiles
     // still advance, but knockback/flight cannot change the next test's view.
     w.gg.setPos(low+80+60*Math.sin(age/15),floor-1);w.gg.setVisPos();
     for(var fighterIndex:int=0;fighterIndex<crowd.length;fighterIndex++){
      var fixedFighter:*=crowd[fighterIndex];fixedFighter.setPos(low+210+fighterIndex*55,floor-1);fixedFighter.setVisPos();
     }
    }
    var memStart:Number=System.totalMemory;
    if(PROFILE&&age==WARMUP_COUNT){rv.profile={};rv.calls={};}
    var t:int=getTimer();rv.frameCount++;rv.onFrameInner();var ms:int=getTimer()-t;
    t=getTimer();var masks:int=0,seen:Dictionary=new Dictionary(true),owned:Dictionary=new Dictionary(true),kind:String=row.variant;
    if(kind=='nodraw'){
     var rec:Object;
     for each(rec in rv.unitVis){if(rec.m2)owned[rec.m2]=true;if(rec.m3)owned[rec.m3]=true;}
     for each(rec in rv.weaponVisuals)if(rec.shape)owned[rec.shape]=true;
     for each(rec in rv.worldVisuals)if(rec.shape)owned[rec.shape]=true;
     if(false)for each(var unit:* in w.loc.units){
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
      if(kind=='nodraw')masks+=alter(obj.vis,seen,owned);
      if(kind=='nomouse')noMouse(obj.vis);
     }
     obj=obj.nobj;
    }
    for each(var layer:DisplayObjectContainer in w.grafon.visObjs){
     for(var i:int=layer.numChildren-1;i>=0;i--){
      var visual:DisplayObject=layer.getChildAt(i);
      if(false){if(getQualifiedClassName(visual).indexOf('visualGrifArm')==0)masks+=alter(visual,seen,owned);}
      else if(visual.mask)masks++;
     }
     // Unit.step reads its own vis.visible to decide whether to emit movement
     // particles. Hide the parent object layers, never change child visibility.
     // This diagnostic also hides player/props; it measures object-layer cost,
     // not enemy-only cost, and needs the zero-enemy control to interpret.
     if(kind=='noobjects'){restore.push({v:layer,layer:true,visible:layer.visible});layer.visible=false;}
    }
    previousFrame={age:age,rv:ms,diagnosticMs:getTimer()-t,worldPass:rv.worldPass,objects:count,projectiles:projectiles,particles:particles,masks:masks,memoryBefore:memStart,memoryAfter:System.totalMemory};
    if(age>=WARMUP_COUNT){row.updates.push(ms);row.diagnosticMs.push(previousFrame.diagnosticMs);row.masks.push(masks);row.memory.push(System.totalMemory);row.positions.push([w.gg.X,w.gg.Y]);row.frames.push(previousFrame);}
    row.maxObjects=Math.max(count,row.maxObjects);row.maxProjectiles=Math.max(projectiles,row.maxProjectiles);row.maxParticles=Math.max(particles,row.maxParticles);
    w.gg.celX=low+1000;w.gg.celY=floor-60;w.gg.storona=1;
    var gun:*=w.gg.currentWeapon;gun.rot=0;gun.hold=100000;gun.hp=100000;
    var prior:int=gun.t_attack;if(row.variant.indexOf('idle')<0){gun.attack();if(gun.t_attack>prior)row.attacks++;}

    if(age==60 && row.variant.indexOf('idle')<0 && row.attacks==0)throw new Error('LMG did not fire; check player skill');
    if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;
    // Sample cache sizes outside the timed frame sequence. Pixel bytes exclude
    // Flash's own render caches; never label this as total application memory.
    var retained:Object={rasters:0,rawPixels:0,softPixels:0,previousPixels:0,visuals:0,worldPass:rv.worldPass};
    for each(var raster:Object in rv.worldMasks){
     retained.rasters++;
     if(raster.m2d)retained.rawPixels+=BitmapData(raster.m2d).width*BitmapData(raster.m2d).height;
     if(raster.m2e)retained.softPixels+=BitmapData(raster.m2e).width*BitmapData(raster.m2e).height;
     if(raster.maskInput)retained.previousPixels+=BitmapData(raster.maskInput).width*BitmapData(raster.maskInput).height;
    }
    retained.emptyVisuals=0;retained.extraEmptyVisuals=0;
    for(var visualKey:Object in rv.worldVisuals){
     retained.visuals++;var worldRecord:Object=rv.worldVisuals[visualKey];
     if(worldRecord.dark){retained.emptyVisuals++;if(!worldRecord.raster.fullyDark)retained.extraEmptyVisuals++;}
    }
    row.retained=retained;
    // Endpoint inventory only: distinguish actual attached masks and duplicate
    // layer references from the cheap per-frame raw loop count.
    var uniqueLayers:Dictionary=new Dictionary(true),uniqueVisuals:Dictionary=new Dictionary(true),rvMasks:Dictionary=new Dictionary(true);
    for each(var maskRecord:Object in rv.unitVis){if(maskRecord.m2)rvMasks[maskRecord.m2]=true;if(maskRecord.m3)rvMasks[maskRecord.m3]=true;}
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
    row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);save();trace('D53 END '+index+' '+row.variant+' shots='+row.attacks+' bullets='+row.maxProjectiles);
    if(++index<plan.length){start(w);return;}
    undo();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D53 COMPLETE');NativeApplication.nativeApplication.exit(0);
   }catch(error:Error){fail(error);}
  }
 }
}
