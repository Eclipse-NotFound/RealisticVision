package {
 import flash.display.*; import flash.events.*; import flash.filesystem.*;
 import flash.system.*; import flash.net.URLRequest; import flash.geom.*;
 import flash.utils.*; import flash.media.*; import flash.desktop.NativeApplication;
 public class BoundaryPerfProbeMod extends Sprite {
  private static const PROFILE:Boolean=true;
  private static const PAIRED:Boolean=false;
  private static const REVERSE:Boolean=false;
  private static const MOVING:Boolean=false;
  private static const WARM:int=60,N:int=180;
  private static var instance:BoundaryPerfProbeMod;
  public static function init(main:*):void {instance=new BoundaryPerfProbeMod(main);}
  private var host:*,wc:Class,classes:Object={},loaders:Array=[],timer:Timer=new Timer(150);
  private var phase:int=0,ticks:int=0,settle:int=0,index:int=0,age:int=0,last:int=0;
  private var plan:Array=[],result:Object={cases:[]},row:Object,rv:*,loc:*,shotBefore:int=0;
  public function BoundaryPerfProbeMod(main:*=null){
   if(!main)return;host=main;SoundMixer.soundTransform=new SoundTransform(0);
   wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   for each(var n:String in ['baseline','candidate'])load(n);
   var scenes:Array=['idle-fixed','fire-fixed','idle-move','fire-move'];
   if(MOVING)scenes=['idle-move','fire-move'];
   if(REVERSE)scenes.reverse();
   for each(var s:String in scenes){
    var order:Array=PAIRED?(REVERSE?['candidate','baseline','baseline','candidate']:['baseline','candidate','candidate','baseline']):['baseline','candidate'];
    for each(var v:String in order)plan.push({scenario:s,variant:v});
   }
   timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function load(n:String):void{
   var l:Loader=new Loader();loaders.push(l);var c:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));c.allowCodeImport=true;
   l.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void{classes[n]=l.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod');});
   l.load(new URLRequest('app:/'+n+'.swf'),c);
  }
  private function save():void{
   var p:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');
   if(p.indexOf('/RealisticVision/build/boundary-opt-20261103/')<0)throw new Error('wrong output');
   var f:FileStream=new FileStream();try{f.open(new File(p+'/evidence/result.json'),FileMode.WRITE);f.writeUTFBytes(JSON.stringify(result));}finally{f.close();}
  }
  private function fail(e:Error):void{timer.stop();host.stage.removeEventListener(Event.ENTER_FRAME,input);host.stage.removeEventListener(Event.ENTER_FRAME,step);result.error=String(e);save();trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
  private function tick(e:Event):void{try{
   if(++ticks>800)throw new Error('boot timeout '+phase);var w:*=wc['w'];
   if(!classes.baseline||!classes.candidate||!w||!w.landData||!w.allLandsLoaded)return;
   if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   if(phase==0){w.mm.mainMenuOff();w.newGame(-1,'LP',null);phase=1;return;}
   if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.game.curLandId&&w.allStat==1){
    if(w.game.curLandId!='rbl'){w.pers.healAll();w.game.beginMission('rbl');}
    phase=2;return;
   }
   if(phase==2&&w.loc&&w.loc.active&&w.game.curLandId=='rbl'&&w.land.act.id=='rbl'&&w.t_exit==0){
    w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw new Error('training entry');w.gg.setPos(480,640);phase=3;return;
   }
   if(phase==3&&w.loc&&w.loc.active&&w.land.locX==1&&w.land.locY==0&&w.allStat==1){
    if(++settle<15)return;timer.stop();loc=w.loc;w.black=true;loc.black=true;loc.base=false;w.godMode=true;w.gg.invulner=true;
    var gunClass:Class=host.loaderInfo.applicationDomain.getDefinition('fe.weapon.Weapon') as Class;
    w.gg.invent.weapons['lmg']=gunClass['create'](w.gg,'lmg');w.gg.changeWeapon('lmg',true);
    if(!w.gg.currentWeapon||w.gg.currentWeapon.id!='lmg')throw new Error('LMG missing');
    w.gg.currentWeapon.lvl=1;w.gg.currentWeapon.perslvl=0;
    result.scene={land:w.game.curLandId,loc:loc.id,size:[loc.spaceX,loc.spaceY],units:loc.units.length,fps:host.stage.frameRate,zoom:w.cam.scaleV};
    start(w);host.stage.addEventListener(Event.ENTER_FRAME,input,false,50);host.stage.addEventListener(Event.ENTER_FRAME,step,false,-10000);
   }
  }catch(err:Error){fail(err);}}
  private function start(w:*):void{
   if(rv){rv.restoreAll(w,loc);if(rv.fogVis&&rv.fogVis.parent)rv.fogVis.parent.removeChild(rv.fogVis);}
   var spec:Object=plan[index],c:Class=classes[spec.variant];rv=new c();rv.loadConfig();
   rv.cfgEnabled=true;rv.cfgBaseRooms={};rv.mswRegistered=true;rv.cfgAutoTest=PROFILE;rv.resetRoom(w,loc);
   // Equal firing phase and full durability prevent random jams from changing work.
   var gun:*=w.gg.currentWeapon;gun.jammed=false;gun.hp=gun.maxhp;
   gun.t_attack=gun.t_reload=gun.t_shoot=gun.t_prep=gun.t_auto=gun.kol_shoot=0;
   gun.deviation=0;w.gg.mazil=0;
   age=0;last=0;
   row={scenario:spec.scenario,variant:spec.variant,intervals:[],updates:[],positions:[],shotsLower:0,activeFrames:0,maxObjects:0,maxProjectiles:0,maxPartial:0,
    config:{mode:rv.cfgMode,fogSub:rv.fogSub,dim:rv.cfgDim,door:rv.cfgDoorDim,soft:rv.cfgSoftCurrent,motion:rv.cfgMotionStep,maskBlur:rv.maskBlurCurrent.blurX,fx:rv.cfgFxQuality,enemy:rv.cfgEnemyFast,testEnabled:true}};
   trace('BOUNDARY START '+index+' '+spec.scenario+' '+spec.variant+' '+JSON.stringify(row.config));
  }
  private function input(e:Event):void{try{
   if(!host.stage.nativeWindow.active)host.stage.nativeWindow.activate();var w:*=wc['w'];
   w.ctr.clearAll();w.gg.ggControl=true;w.gg.setPos(480+(row.scenario.indexOf('move')>=0?Math.abs((age%120)-60)*4:0),640);
   w.gg.dx=w.gg.dy=0;w.gg.setVisPos();w.cam.calc(w.gg);
   w.ctr.keyAttack=row.scenario.indexOf('fire')==0;
   w.celX=1400;w.celY=580;w.cam.celX=w.celX*w.cam.scaleV+w.cam.vx;w.cam.celY=w.celY*w.cam.scaleV+w.cam.vy;
   var g:*=w.gg.currentWeapon;g.hold=g.holder;g.hp=g.maxhp;shotBefore=int(g.kol_shoot);
  }catch(err:Error){fail(err);}}
  private function step(e:Event):void{try{
   var w:*=wc['w'];if(w.loc!==loc||w.mm.active||w.allStat!=1)throw new Error('scene changed');
   if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   var now:int=getTimer();if(age>WARM)row.intervals.push(now-last);last=now;
   if(age==WARM&&PROFILE){rv.profile={};rv.calls={};rv.audit={};rv.atFovM=rv.atFovH=rv.atFovF=0;}
   var t:int=getTimer();rv.frameCount++;rv.onFrameInner();var ms:int=getTimer()-t;
   if(age>=WARM){
    row.updates.push(ms);if(host.stage.nativeWindow.active)row.activeFrames++;
    var eye:Point=rv.playerVisionEye(w.gg);row.positions.push([w.gg.X,w.gg.Y,eye.x,eye.y]);
    row.shotsLower+=Math.max(0,int(w.gg.currentWeapon.kol_shoot)-shotBefore);
    var obj:*=loc.firstObj,total:int=0,bullets:int=0;while(obj&&total<5000){total++;if(getQualifiedClassName(obj).indexOf('Bullet')>=0)bullets++;obj=obj.nobj;}
    row.maxObjects=Math.max(row.maxObjects,total);row.maxProjectiles=Math.max(row.maxProjectiles,bullets);
    var part:int=0;for each(var rec:Object in rv.unitVis)if(rec.state==2)part++;row.maxPartial=Math.max(row.maxPartial,part);
   }
   if(++age<WARM+N)return;
   if(row.scenario.indexOf('fire')==0&&row.shotsLower<10)throw new Error('fire did not occur '+row.shotsLower);
   if(PROFILE){row.profile=rv.profile;row.calls=rv.calls;row.audit=rv.audit;row.fovReasons={m:rv.atFovM,h:rv.atFovH,f:rv.atFovF};}
   result.cases.push(row);save();trace('BOUNDARY END '+index);
   if(++index<plan.length){start(w);return;}
   host.stage.removeEventListener(Event.ENTER_FRAME,input);host.stage.removeEventListener(Event.ENTER_FRAME,step);
   trace('BOUNDARY PERF COMPLETE');NativeApplication.nativeApplication.exit(0);
  }catch(err:Error){fail(err);}}
 }
}
