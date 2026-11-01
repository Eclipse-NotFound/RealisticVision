package {
 import flash.display.*;
 import flash.events.*;
 import flash.filesystem.*;
 import flash.system.*;
 import flash.net.URLRequest;
 import flash.geom.*;
 import flash.utils.*;
 import flash.media.*;
 import flash.desktop.NativeApplication;
 public class EyeBoundaryProbeMod extends Sprite {
  private static var instance:EyeBoundaryProbeMod;
  public static function init(main:*):void {instance=new EyeBoundaryProbeMod(main);}
  private var host:*,wc:Class,classes:Object={},loaders:Array=[],timer:Timer=new Timer(150),ticks:int=0,phase:int=0,settled:int=0;
  private var result:Object={checks:[],eyes:[],bullets:[]};
  public function EyeBoundaryProbeMod(main:*=null){
   if(!main)return;host=main;SoundMixer.soundTransform=new SoundTransform(0);
   wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   for each(var n:String in ['baseline','candidate'])load(n);
   timer.addEventListener(TimerEvent.TIMER,tick);timer.start();
  }
  private function load(n:String):void {
   var l:Loader=new Loader();loaders.push(l);var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));ctx.allowCodeImport=true;
   l.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void{classes[n]=l.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod');});
   l.load(new URLRequest('app:/'+n+'.swf'),ctx);
  }
  private function save(n:String,v:*):void {
   var p:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(p.indexOf('/RealisticVision/build/eye-boundary-output/')<0)throw new Error('wrong output');
   var f:FileStream=new FileStream();try{f.open(new File(p+'/evidence/'+n),FileMode.WRITE);if(v is ByteArray)f.writeBytes(v);else f.writeUTFBytes(JSON.stringify(v));}finally{f.close();}
  }
  private function check(ok:Boolean,n:String):void {result.checks.push({ok:ok,name:n});trace((ok?'PASS ':'FAIL ')+n);if(!ok)throw new Error(n);}
  private function png(n:String,b:BitmapData):void{save(n+'.png',b.encode(b.rect,new PNGEncoderOptions()));}
  private function tick(e:Event):void {try{
   if(++ticks>700)throw new Error('timeout');var w:*=wc['w'];
   if(!classes.baseline||!classes.candidate||!w||!w.landData||!w.allLandsLoaded)return;
   if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   if(phase==0){w.mm.mainMenuOff();w.newGame(-1,'LP',null);phase=1;return;}
   if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.game.curLandId){
    if(w.allStat!=1||++settled<12)return;
    timer.stop();w.mm.active=true;w.black=true;w.loc.base=false;w.loc.black=true;w.gg.setVisPos();
    run(w);save('result.json',result);trace('BOUNDARY COMPLETE');NativeApplication.nativeApplication.exit(0);
   }
  }catch(err:Error){timer.stop();result.error=String(err);trace('FAIL '+err+' '+err.getStackTrace());save('result.json',result);NativeApplication.nativeApplication.exit(1);}}
  private function make(n:String,w:*):* {var c:Class=classes[n],m:*=new c();m.cfgMode='current';m.cfgBaseRooms={};m.mswRegistered=true;m.applyVisionScale();m.resetRoom(w,w.loc);return m;}
  private function run(w:*):void {
   var a:*=make('baseline',w),b:*=make('candidate',w),gg:*=w.gg;
   var v:MovieClip=gg.vis;v.osn.gotoAndStop('stay');v.osn.body.gotoAndStop(1);var eye:DisplayObject=v.osn.body.head.morda.eye;
   check(eye!=null,'native player eye exists');
   var originalScale:Number=v.scaleX,originalRot:Number=v.osn.body.head.morda.rotation;
   for each(var facing:int in [-1,1])for each(var tilt:int in [-30,0,45]){
    v.scaleX=Math.abs(originalScale)*facing;v.osn.body.head.morda.rotation=tilt;
    var r:Rectangle=eye.getBounds(v.parent),expected:Point=new Point((r.left+r.right)/2,(r.top+r.bottom)/2);
    var p:Point=b.playerVisionEye(gg);b.computeFov(w.loc);
    check(Point.distance(p,expected)<.2,'eye matches displayed geometry '+facing+'/'+tilt);
    check(Point.distance(new Point(b.eyeX,b.eyeY),expected)<.2,'ray origin matches eye '+facing+'/'+tilt);
    var old:Point=new Point(gg.X,gg.Y-gg.scY*.75);
    result.eyes.push({facing:facing,tilt:tilt,eye:[p.x,p.y],old:[old.x,old.y],offset:Point.distance(p,old)});
    var image:BitmapData=new BitmapData(320,300,false,0x404040),mat:Matrix=new Matrix(2,0,0,2,160-gg.X*2,250-gg.Y*2);
    image.draw(v.parent,mat);var marks:Shape=new Shape();marks.graphics.lineStyle(1,0x00ff00);marks.graphics.drawCircle(160+(p.x-gg.X)*2,250+(p.y-gg.Y)*2,5);marks.graphics.lineStyle(1,0xff0000);marks.graphics.drawCircle(160+(old.x-gg.X)*2,250+(old.y-gg.Y)*2,5);image.draw(marks);png('eye-'+facing+'-'+tilt,image);image.dispose();
   }
   v.osn.body.head.morda.rotation=originalRot;v.scaleX=originalScale;
   b.frameCount=11;b.onFrameInner();var gen:int=b.fovVersion;
   v.scaleX=-originalScale;b.frameCount++;b.onFrameInner();
   check(b.fovVersion>gen,'stationary facing change refreshes FOV');
   v.scaleX=originalScale;
   v.osn.visible=false;var fallback:Point=b.playerVisionEye(gg);
   check(fallback.x==gg.X&&fallback.y==gg.Y-gg.scY*.75,'hidden pony timeline falls back safely');v.osn.visible=true;
   b.restoreAll(w,w.loc);
   // Real Bullet instances pass through production dispatch; a bright strip
   // makes surviving pixels measurable independently of textured scenery.
   var cls:Class=host.loaderInfo.applicationDomain.getDefinition('fe.weapon.Bullet') as Class;
   var bullet:*=new cls(gg,0,0,null,false);var originalFirst:*=w.loc.firstObj;
   var layer:Sprite=new Sprite();host.stage.addChild(layer);
   var sprite:MovieClip=new MovieClip();sprite.graphics.beginFill(0xffffff);sprite.graphics.drawRect(-100,-2,100,4);sprite.graphics.endFill();layer.addChild(sprite);bullet.vis=sprite;bullet.nobj=null;w.loc.firstObj=bullet;
   for each(var mode:String in ['current','classic'])for each(var sub:int in [4,8]){
    for each(var m:* in [a,b]){m.cfgMode=mode;m.cfgFogQuality=sub==4?0:1;m.fogSub=sub;m.applyVisionScale();m.resetRoom(w,w.loc);m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);m.currentSight.fillRect(new Rectangle(0,0,4+300*sub/40,m.currentSight.height),0xffffffff);m.fogCache.fillRect(m.fogCache.rect,0xff000000);m.fogCache.fillRect(new Rectangle(0,0,4+300*sub/40,m.fogCache.height),0);m.classicLogicCache=null;m.fovVersion++;}
    for each(var x:int in [270,310,340,450,280]){
     b.restoreAll(w,w.loc);sprite.x=x;sprite.y=240;
     a.applyWorldVisuals(w,w.loc);var before:BitmapData=new BitmapData(500,300,true,0);before.draw(layer);a.restoreAll(w,w.loc);
     b.applyWorldVisuals(w,w.loc);var after:BitmapData=new BitmapData(500,300,true,0);after.draw(layer);
     var litBefore:int=count(before,200,290),litAfter:int=count(after,200,290),dark:int=count(after,350,490);
     result.bullets.push({mode:mode,sub:sub,x:x,litBefore:litBefore,litAfter:litAfter,dark:dark});
     if(x==310||x==340){check(litBefore==0,'old tracer disappears early '+mode+'/'+sub+'/'+x);check(litAfter>100,'candidate keeps visible tracer '+mode+'/'+sub+'/'+x);}
     check(dark==0,'candidate does not reveal dark projectile '+mode+'/'+sub+'/'+x);
     if(x==310){png('bullet-before-'+mode+'-'+sub,before);png('bullet-after-'+mode+'-'+sub,after);}
     before.dispose();after.dispose();
    }
    b.restoreAll(w,w.loc);a.restoreAll(w,w.loc);
   }
   // Keep each consumer bound across transitions; include child geometry changes
   // without moving its parent (lasers resize this way in the native game).
   b.cfgMode='current';b.fogSub=4;b.applyVisionScale();b.resetRoom(w,w.loc);
   b.currentSight=new BitmapData(b.fogCache.width,b.fogCache.height,true,0);
   b.currentSight.fillRect(new Rectangle(0,0,34,b.currentSight.height),0xffffffff);b.fovVersion++;
   for each(var quality:int in [0,1])for each(var type:String in ['Bullet','SmartBullet','PhisBullet']){
    b.restoreAll(w,w.loc);var bc:Class=host.loaderInfo.applicationDomain.getDefinition('fe.weapon.'+type) as Class;
    var item:*=type=='PhisBullet'?new bc(gg,0,0,null):new bc(gg,0,0,null,false);
    item.vis=sprite;item.nobj=null;w.loc.firstObj=item;b.cfgFxQuality=quality;
    for(var f:int=0;f<60;f++){
     sprite.graphics.clear();sprite.graphics.beginFill(0xffffff);sprite.graphics.drawRect(f%2==0?-40:-120,-2,f%2==0?40:120,4);sprite.graphics.endFill();
     sprite.x=340;sprite.y=240;b.frameCount++;b.applyWorldVisuals(w,w.loc);
     var continuous:BitmapData=new BitmapData(500,300,true,0);continuous.draw(layer);
     check(f%2==0?count(continuous,200,290)==0:count(continuous,200,290)>100,'continuous resizing '+type+'/'+quality+'/'+f);
     check(count(continuous,350,490)==0,'continuous dark side '+type+'/'+quality+'/'+f);continuous.dispose();
    }
   }
   b.restoreAll(w,w.loc);w.loc.firstObj=originalFirst;host.stage.removeChild(layer);
  }
  private function count(b:BitmapData,x0:int,x1:int):int {var n:int=0;for(var y:int=235;y<245;y++)for(var x:int=x0;x<x1;x++)if((b.getPixel32(x,y)>>>24)>20)n++;return n;}
 }
}
