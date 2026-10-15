package {
   import flash.display.Sprite;
   import flash.desktop.NativeApplication;
   import flash.filesystem.*;
   import modlocales.vision.RVLocale;
   public class SettingsChecks extends Sprite {
      private var passed:int=0,failed:int=0;
      public function SettingsChecks(){try{run();}catch(e:Error){failed++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("SETTINGS COMPLETE passed="+passed+" failures="+failed);NativeApplication.nativeApplication.exit(failed?1:0);}
      private function check(v:Boolean,s:String):void{if(v)passed++;else failed++;trace((v?"PASS ":"FAIL ")+s);}
      private function run():void {
         var m:RealisticVisionMod=new RealisticVisionMod(),item:Object;
         for each(var row:Object in m.buildMswItems())if(row.key=="wallbright")item=row;
         check(item!=null&&item.kind=="check"&&item.def===true&&item.get()===true,"settings exposes a default-on checkbox");
         check(RVLocale.translate(item.label,"en")!=item.label&&RVLocale.translate(item.label,"ru")!=item.label,"new setting is translated to English and Russian");
         check(RVLocale.translate(item.hint,"en")!=item.hint&&RVLocale.translate(item.hint,"ru")!=item.hint,"setting explanation is translated");
         m.cfgMode="classic";m.cfgDim=.45;var seen:Array=m.explored;
         item.set(false);check(item.get()===false&&m.cfgMode=="classic"&&m.cfgDim==.45&&m.explored===seen,"toggle is independent of mode, memory brightness and exploration");
         var next:RealisticVisionMod=new RealisticVisionMod();next.loadConfig();
         check(next.cfgWallBright===false&&next.cfgMode=="classic"&&next.cfgDim==.45,"OFF persists with existing configuration values");
         item.set(true);next=new RealisticVisionMod();next.loadConfig();check(next.cfgWallBright===true,"ON persists and reloads");
         var file:File=new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt"),stream:FileStream=new FileStream();
         stream.open(file,FileMode.WRITE);stream.writeUTFBytes("mode=current\ndim=0.35\n");stream.close();
         next=new RealisticVisionMod();next.loadConfig();check(next.cfgWallBright===true,"old configs without the key keep the default");
         stream.open(file,FileMode.WRITE);stream.writeUTFBytes("wallbright=invalid\n");stream.close();
         next=new RealisticVisionMod();next.loadConfig();check(next.cfgWallBright===true,"invalid config values cannot silently disable the option");
      }
   }
}
