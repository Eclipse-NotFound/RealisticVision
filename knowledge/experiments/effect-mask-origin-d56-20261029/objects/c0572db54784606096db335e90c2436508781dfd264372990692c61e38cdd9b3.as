package {
 import flash.display.*;import flash.events.*;import flash.utils.*;
 import flash.media.*;import flash.filesystem.*;import flash.desktop.NativeApplication;
 public class ProductionSmokeMod extends Sprite {
  private static var instance:ProductionSmokeMod;
  public static function init(main:*):void {instance=new ProductionSmokeMod(main);}
  private var host:*,wc:Class,timer:Timer=new Timer(150),phase:int=0,ticks:int=0,frame:int=0,shots:int=0,before:int=0,maxParticles:int=0,maskedParticles:int=0;
  private var version:String="v0.33.11-effect-clip";
  public function ProductionSmokeMod(main:* = null){
   if(!main)return;host=main;wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   SoundMixer.soundTransform=new SoundTransform(0);timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function readLog():String {
   var file:File=File.applicationStorageDirectory.resolvePath('RVision.log');if(!file.exists)return '';
   var stream:FileStream=new FileStream();stream.open(file,FileMode.READ);var s:String=stream.readUTFBytes(stream.bytesAvailable);stream.close();return s;
  }
  private function fail(e:Error):void {trace('D56 PRODUCTION FAIL '+e+' '+e.getStackTrace());timer.stop();NativeApplication.nativeApplication.exit(1);}
  private function tick(e:Event):void {try{
   SoundMixer.soundTransform=new SoundTransform(0);var w:*=wc['w'];if(++ticks>600)throw new Error('native boot timeout '+phase);
   if(!w||!w.allLandsLoaded||!w.landData)return;if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   if(phase==0){if(readLog().indexOf('init ok '+version)<0)return;w.mm.active=false;w.newGame(0);phase=1;return;}
   if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.allStat==1){w.pers.healAll();w.game.beginMission('random_mane');phase=2;return;}
   if(phase==2&&w.loc&&w.loc.active&&w.game.curLandId=='random_mane'&&w.land.act.id=='random_mane'&&w.t_exit==0){w.land.gotoXY(1,3);phase=3;return;}
   if(phase==3&&w.gg&&w.loc&&w.loc.active&&w.t_exit==0){
    if(!w.gg.currentWeapon||w.gg.currentWeapon.id!='lmg')w.gg.changeWeapon('lmg',true);
    if(!w.gg.currentWeapon||w.gg.currentWeapon.id!='lmg')throw new Error('native LMG missing');
    w.godMode=true;w.gg.invulner=false;w.ctr.clearAll();w.gg.ggControl=true;host.stage.nativeWindow.visible=true;
    timer.stop();host.stage.addEventListener(Event.ENTER_FRAME,input,false,50);host.stage.addEventListener(Event.ENTER_FRAME,step,false,-10000);
   }
  }catch(err:Error){fail(err);}}
  private function input(e:Event):void {try{
   var w:*=wc['w'];w.ctr.clearAll();w.gg.ggControl=true;w.gg.setPos(1000,959);w.gg.dx=w.gg.dy=0;w.gg.setVisPos();
   var gun:*=w.gg.currentWeapon;gun.hold=gun.holder;before=gun.kol_shoot;
   w.ctr.keyAttack=true;var aimX:Number=220,aimY:Number=w.gg.Y-250+220*Math.sin(frame/25);
   w.cam.celX=aimX*w.cam.scaleV+w.cam.vx;w.cam.celY=aimY*w.cam.scaleV+w.cam.vy;w.celX=aimX;w.celY=aimY;
  }catch(err:Error){fail(err);}}
  private function step(e:Event):void {try{
   var w:*=wc['w'];shots+=Math.max(0,int(w.gg.currentWeapon.kol_shoot)-before);
   var obj:*=w.loc.firstObj,count:int=0,guard:int=0;while(obj&&guard++<5000){if(getQualifiedClassName(obj)=='fe.graph::Part'){count++;if(obj.vis&&obj.vis.mask)maskedParticles++;}obj=obj.nobj;}maxParticles=Math.max(maxParticles,count);
   if(++frame<240)return;
   var log:String=readLog();if(shots<20||maxParticles<5||maskedParticles==0)throw new Error('native firing/visibility path absent');
   if(log.indexOf('init ok '+version)<0||log.indexOf('ModSettings settings registered')<0||log.indexOf('tick 181')<0||/ERROR|register failed|#1009|#1069/.test(log))throw new Error('production runtime error '+log);
   var result:Object={version:version,frames:frame,shots:shots,maxParticles:maxParticles,maskedParticleSamples:maskedParticles,windowVisible:host.stage.nativeWindow.visible,audioVolume:SoundMixer.soundTransform.volume,screen:[host.stage.stageWidth,host.stage.stageHeight]};
   var root:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(root.indexOf('/RealisticVision/build/effect-mask-origin-output/')<0)throw new Error('wrong output');
   var out:FileStream=new FileStream();out.open(new File(root+'/evidence/production.json'),FileMode.WRITE);out.writeUTFBytes(JSON.stringify(result));out.close();
   trace('D56 PRODUCTION COMPLETE '+JSON.stringify(result));NativeApplication.nativeApplication.exit(0);
  }catch(err:Error){fail(err);}}
 }
}
