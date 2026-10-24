package {
 import flash.display.*;
 import flash.events.*;
 import flash.filesystem.*;
 import flash.net.URLRequest;
 import flash.system.*;
 import flash.geom.*;
 import flash.utils.*;
 import flash.desktop.NativeApplication;
 public class CombatRenderProbeMod extends Sprite {
  private static const SAMPLE_COUNT=90;
  private static const LARGE=false;
  private static var instance:CombatRenderProbeMod;
  public static function init(main:*):void {instance=new CombatRenderProbeMod(main);}
  private var host:*,wc:Class,rvClass:Class,loader:Loader=new Loader(),timer:Timer=new Timer(150);
  private var phase:int=0,ticks:int=0,settle:int=0,index:int=0,age:int=0,last:int=0;
  private var plan:Array=[],crowd:Array=[],restore:Array=[],row:Object,rv:*,floor:Number,low:Number,high:Number;
  private var result:Object={cases:[],checks:[]},shots:Dictionary=new Dictionary(true);
  public function CombatRenderProbeMod(main:* = null) {
   if(main==null)return;host=main;wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   loader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {rvClass=loader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
   var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));ctx.allowCodeImport=true;loader.load(new URLRequest('app:/rv.swf'),ctx);
   for each(var n:int in [0,1,6]) for each(var mode:String in ['current','classic']) for each(var variant:String in ['off','normal','nomask','nodraw','nomask','normal','off'])plan.push({n:n,mode:mode,variant:variant});
   timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function save():void {
   var p:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(p.indexOf('/RealisticVision/build/combat-render-output/')<0)throw new Error('wrong output root');
   var fs:FileStream=new FileStream();fs.open(new File(p+'/evidence/result.json'),FileMode.WRITE);fs.writeUTFBytes(JSON.stringify(result));fs.close();
  }
  private function fail(e:Error):void {timer.stop();host.stage.removeEventListener(Event.ENTER_FRAME,step);result.error=e.toString();trace('FAIL '+e+' '+e.getStackTrace());save();NativeApplication.nativeApplication.exit(1);}
  private function tick(e:Event):void {
   try {
    var w:*=wc['w'];if(++ticks>1200)throw new Error('boot timeout '+phase);
    if(!rvClass||!w||!w.allLandsLoaded||!w.landData)return;if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
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
     result.scene={large:LARGE,size:[w.loc.spaceX,w.loc.spaceY],nativeUnits:w.loc.units.length,platform:[low,high,floor],fps:host.stage.frameRate};
     timer.stop();start(w);host.stage.addEventListener(Event.ENTER_FRAME,step,false,-10000);
    }
   }catch(e:Error){fail(e);}
  }
  private function undo():void {
   for each(var r:Object in restore){var v:DisplayObject=r.v;v.visible=r.visible;v.cacheAsBitmap=r.cache;v.mask=r.mask;if(r.mask)r.mask.visible=r.maskVisible;}
   restore=[];
  }
  private function start(w:*):void {
   undo();if(rv){rv.restoreAll(w,w.loc);if(rv.fogVis&&rv.fogVis.parent)rv.fogVis.parent.removeChild(rv.fogVis);}
   var p:Object=plan[index];
   while(crowd.length<p.n){
    var cls:Class=host.loaderInfo.applicationDomain.getDefinition('fe.unit.UnitMerc') as Class;var u:*=new cls('1',10,null,{weap:'smg10'});
    u.putLoc(w.loc,low+210+crowd.length*55,floor-1);u.invulner=true;w.loc.addObj(u);w.loc.units.push(u);u.step();crowd.push(u);
   }
   rv=new rvClass();rv.cfgDim=.6;rv.cfgSoftCurrent=25;rv.cfgMode=p.mode;rv.cfgEnabled=p.variant!='off';rv.cfgWallBright=false;rv.mswRegistered=true;rv.cfgBaseRooms={};rv.resetRoom(w,w.loc);
   age=0;last=0;row={crowd:p.n,mode:p.mode,variant:p.variant,intervals:[],updates:[],diagnosticMs:[],masks:[],memory:[],positions:[],units:w.loc.units.length,maxObjects:0,maxProjectiles:0,attacks:0};
   trace('D44 START '+index+' '+JSON.stringify(p));
  }
  private function alter(v:DisplayObject,seen:Dictionary,kind:String):int {
   if(v==null||v.parent==null||seen[v])return 0;seen[v]=true;var mask:DisplayObject=v.mask;
   if(kind=='nomask'&&mask==null)return 0;
   restore.push({v:v,visible:v.visible,cache:v.cacheAsBitmap,mask:mask,maskVisible:mask?mask.visible:false});
   if(kind=='nomask'){v.mask=null;v.cacheAsBitmap=false;mask.visible=false;}else v.visible=false;
   return mask?1:0;
  }
  private function step(e:Event):void {
   try {
    var w:*=wc['w'];if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
    var now:int=getTimer();if(age>=30&&last)row.intervals.push(now-last);last=now;
    undo();w.ctr.clearAll();w.gg.ggControl=true;
    var t:int=getTimer();rv.frameCount++;rv.onFrameInner();var ms:int=getTimer()-t;
    t=getTimer();var masks:int=0,seen:Dictionary=new Dictionary(true),kind:String=row.variant;
    if(kind=='nomask'||kind=='nodraw'){
     for each(var unit:* in w.loc.units){
      if(unit===w.gg)continue;masks+=alter(unit.vis,seen,kind);masks+=alter(unit.hpbar,seen,kind);
      for each(var child:* in unit.childObjs)if(child.vis)masks+=alter(child.vis,seen,kind);
     }
    }
    var obj:*=w.loc.firstObj,count:int=0,projectiles:int=0;
    while(obj&&count++<5000){
     var name:String=getQualifiedClassName(obj);
     if(name.indexOf('Bullet')>=0)projectiles++;
     if((kind=='nomask'||kind=='nodraw')&&(name.indexOf('Bullet')>=0||name=='fe.graph::Part')&&obj.vis)masks+=alter(obj.vis,seen,kind);
     obj=obj.nobj;
    }
    for each(var layer:DisplayObjectContainer in w.grafon.visObjs)for(var i:int=layer.numChildren-1;i>=0;i--){
     var visual:DisplayObject=layer.getChildAt(i);
     if(kind=='nomask'||kind=='nodraw'){if(getQualifiedClassName(visual).indexOf('visualGrifArm')==0)masks+=alter(visual,seen,kind);}
     else if(visual.mask)masks++;
    }
    if(age>=30){row.updates.push(ms);row.diagnosticMs.push(getTimer()-t);row.masks.push(masks);row.memory.push(System.totalMemory);row.positions.push([w.gg.X,w.gg.Y]);}
    row.maxObjects=Math.max(count,row.maxObjects);row.maxProjectiles=Math.max(projectiles,row.maxProjectiles);
    for each(var fighter:* in crowd){fighter.setCel(w.gg);if(age%6==0)fighter.currentWeapon.attack();var weapon:*=fighter.currentWeapon;if(weapon.t_attack>int(shots[weapon]))row.attacks++;shots[weapon]=weapon.t_attack;}
    if(++age<30+SAMPLE_COUNT)return;
    result.cases.push(row);save();trace('D44 END '+index+' '+row.variant+' shots='+row.attacks+' bullets='+row.maxProjectiles);
    if(++index<plan.length){start(w);return;}
    undo();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D44 COMPLETE');NativeApplication.nativeApplication.exit(0);
   }catch(error:Error){fail(error);}
  }
 }
}
