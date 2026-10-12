package {
   import flash.display.Sprite;
   import flash.desktop.NativeApplication;
   import flash.filesystem.File;
   import flash.filesystem.FileMode;
   import flash.filesystem.FileStream;
   public final class AuthorityViewChecks extends Sprite {
      private var results:Array=[];
      public function AuthorityViewChecks() {
         try {run();}catch(error:*){results.push({ok:false,name:String(error)});}
         var failed:int=0;for each(var r:Object in results)if(!r.ok)++failed;
         var stream:FileStream=new FileStream();stream.open(new File(File.applicationDirectory.nativePath).resolvePath("authority-checks.json"),FileMode.WRITE);
         stream.writeUTFBytes(JSON.stringify({passed:results.length-failed,failed:failed,results:results}));stream.close();
         NativeApplication.nativeApplication.exit(failed==0?0:1);
      }
      private function check(value:Boolean,name:String):void {results.push({ok:value,name:name});}
      private function run():void {
         var view:RVAuthorityView=new RVAuthorityView(),body:Sprite=new Sprite(),nativeMask:Sprite=new Sprite();
         body.visible=false;view.write(body,"visible",true,true);
         check(body.visible,"unattached path retains original visible assignment");
         view.publish(this);var entry:Object=(getChildByName("RVAuthorityViewAPI") as RVAuthorityCarrier).authorityAPI;
         check(entry.attach({version:2,session:"test",role:"host"})==null,"reject incompatible interface");
         var lease:Object=entry.attach({version:1,session:"test",role:"host"});
         check(lease!=null && lease.version===1,"B attaches through separate carrier");
         check(entry.attach({version:1,session:"other",role:"join"})==null,"reject second owner");
         body.visible=false;view.write(body,"visible",true,true);
         check(!body.visible,"reveal preserves native hidden pose");lease.prepare();
         body.visible=true;view.write(body,"visible",false);
         check(!body.visible,"RV applies local occlusion");lease.prepare();
         check(body.visible,"native step sees pre-view visibility");
         var entity:Object={prior:3};view.write(entity,"prior",0);lease.prepare();
         check(entity.prior===3,"restore native priority rather than assumed one");
         view.write(entity,"prior",0);entity.prior=7;lease.prepare();
         check(entity.prior===7,"preserve intervening native priority change");
         var localMask:Sprite=new Sprite();addChild(body);addChild(nativeMask);addChild(localMask);
         body.mask=nativeMask;body.cacheAsBitmap=true;
         view.write(body,"mask",localMask);view.write(body,"cacheAsBitmap",true);lease.prepare();
         check(body.mask===nativeMask && body.cacheAsBitmap,"restore original native mask and cache");
         check(localMask.parent==null && nativeMask.parent===this,"remove only RV mask from display tree");
         body.visible=true;view.remember(body,"visible");body.visible=false;view.changed(body,"visible");lease.prepare();
         check(body.visible,"record delegated native visDetails changes");
         body.visible=true;view.write(body,"visible",false);lease.detach();
         check(body.visible && !view.active,"detach restores pending local view");
         var stale:Boolean=false;try{lease.prepare();}catch(expected:*){stale=true;}
         check(stale,"old lease cannot act after detach");
         var next:Object=entry.attach({version:1,session:"test2",role:"join"});lease.detach();
         check(next.inspect().active,"old detach cannot revoke new owner");next.detach();
      }
   }
}
