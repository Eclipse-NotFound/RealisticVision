package {
 import flash.display.Sprite;
 import flash.events.*;
 import flash.utils.Timer;
 import flash.media.*;
 import flash.desktop.NativeApplication;
 public class SmokeProbeMod extends Sprite {
  private static var instance:SmokeProbeMod;
  public static function init(main:*):void{instance=new SmokeProbeMod(main);}
  private var wc:Class,t:Timer=new Timer(100),ticks:int=0,age:int=0,started:Boolean=false;
  public function SmokeProbeMod(main:*=null){if(!main)return;SoundMixer.soundTransform=new SoundTransform(0);wc=main.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;t.addEventListener(TimerEvent.TIMER,step);t.start();}
  private function step(e:Event):void{try{
   if(++ticks>900)throw new Error('timeout');var w:*=wc['w'];if(!w||!w.allLandsLoaded||!w.landData)return;
   if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   if(!started){w.mm.mainMenuOff();w.newGame(-1,'LP',null);started=true;return;}
   if(!w.gg||!w.loc||!w.loc.active||w.allStat!=1)return;
   w.loc.base=false;w.loc.black=true;w.black=true;
   // Let the installed production listener process normal game frames.
   if(++age>=75){trace('PRODUCTION SMOKE COMPLETE native active frames='+age);t.stop();NativeApplication.nativeApplication.exit(0);}
  }catch(err:Error){trace('FAIL '+err+' '+err.getStackTrace());t.stop();NativeApplication.nativeApplication.exit(1);}}
 }
}
