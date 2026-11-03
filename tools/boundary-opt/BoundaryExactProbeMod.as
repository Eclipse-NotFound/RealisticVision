package {
 import flash.display.*; import flash.events.*; import flash.filesystem.*;
 import flash.system.*; import flash.net.URLRequest; import flash.geom.*;
 import flash.utils.*; import flash.media.*; import flash.desktop.NativeApplication;
 /** Exact values and pixels, separate from native frame timing. */
 public class BoundaryExactProbeMod extends Sprite {
  private static var instance:BoundaryExactProbeMod;
  public static function init(main:*):void{instance=new BoundaryExactProbeMod(main);}
  private var host:*,wc:Class,classes:Object={},loaders:Array=[],timer:Timer=new Timer(150);
  private var ticks:int=0,phase:int=0,settle:int=0,seed:uint=0x5162b391;
  private var result:Object={checks:0,rays:0,matchingRayErrors:0,fields:0,pixels:0,masked:0,nonempty:0,rayTiming:[]};
  public function BoundaryExactProbeMod(main:*=null){
   if(!main)return;host=main;SoundMixer.soundTransform=new SoundTransform(0);
   wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;
   for each(var n:String in ['baseline','candidate'])load(n);
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
  private function check(ok:Boolean,n:String):void{result.checks++;if(!ok)throw new Error(n);}
  private function same(a:BitmapData,b:BitmapData,n:String):void{
   check(a!=null&&b!=null,n+' exists');var diff:*=a.compare(b);
   if(diff is BitmapData){diff.dispose();throw new Error(n+' pixels differ');}
   check(Number(diff)==0,n+' dimensions and pixels');result.pixels+=a.width*a.height;
  }
  private function rand():Number{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return Number(seed)/4294967296;}
  private function tick(e:Event):void{try{
   if(++ticks>700)throw new Error('boot timeout');var w:*=wc['w'];
   if(!classes.baseline||!classes.candidate||!w||!w.landData||!w.allLandsLoaded)return;
   if(w.verror&&w.verror.visible)throw new Error(w.verror.txt.text);
   if(phase==0){w.mm.mainMenuOff();w.newGame(-1,'LP',null);phase=1;return;}
   if(w.gg&&w.loc&&w.loc.active&&w.allStat==1&&++settle>15){
    timer.stop();w.mm.active=true;w.black=true;w.loc.black=true;w.loc.base=false;
    run(w);save();trace('BOUNDARY EXACT COMPLETE '+JSON.stringify(result));NativeApplication.nativeApplication.exit(0);
   }
  }catch(err:Error){timer.stop();result.error=String(err);save();trace('FAIL '+err+' '+err.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function make(n:String,w:*):*{var c:Class=classes[n],m:*=new c();m.loadConfig();m.cfgEnabled=true;m.cfgBaseRooms={};m.mswRegistered=true;m.resetRoom(w,w.loc);return m;}
  private function ray(a:*,b:*,loc:*,ex:Number,ey:Number,cx:Number,cy:Number):void{
   var tx:int=Math.floor(cx/40),ty:int=Math.floor(cy/40);
   var av:Number,bv:Number,ae:String='',be:String='';
   try{av=a.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(ea:Error){ae=String(ea);}
   try{bv=b.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(eb:Error){be=String(eb);}
   check(ae==be&&(ae!=''||av===bv),'ray '+[ex,ey,cx,cy,av,bv,ae,be]);
   if(ae!='')result.matchingRayErrors++;result.rays++;
  }
  private function run(w:*):void{
   var a:*=make('baseline',w),b:*=make('candidate',w),m:*,x:int,y:int,i:int,f:int;
   var cells:Vector.<Number>=new Vector.<Number>(64*48,true);
   for each(m in [a,b]){m.rayBatch=true;m.rayLoc=null;m.rayWidth=64;m.rayHeight=48;m.rayOpac=cells;}
   // Open space, partial opacity, opaque cells and mixed materials. Grid lines,
   // axis-aligned rays, diagonal ties, same-tile rays and exact corner targets.
   for(f=0;f<4;f++){
    for(i=0;i<cells.length;i++)cells[i]=f==0?0:(rand()<.09?[0,.15,.5,1][int(rand()*4)]:0);
    for(i=0;i<16000;i++){
     var ex:Number=rand()*2559,ey:Number=rand()*1919,cx:Number=rand()*2559,cy:Number=rand()*1919;
     if(i%7==0)cx=ex;if(i%11==0)cy=ey;
     if(i%13==0){ex=int(ex/40)*40;ey=int(ey/40)*40;cx=int(cx/40)*40;cy=int(cy/40)*40;}
     ray(a,b,null,ex,ey,cx,cy);
    }
   }
   var wide:Vector.<Number>=new Vector.<Number>(1024*2,true);
   for each(m in [a,b]){m.rayWidth=1024;m.rayHeight=2;m.rayOpac=wide;}
   for(i=0;i<100;i++){wide[700]=i%2?.5:0;ray(a,b,null,20,20,28020+i,20);}
   // Exercise the uncached fallback and compare it with the cached path too.
   for each(m in [a,b]){m.prepareOcclusion(w.loc);m.rayBatch=false;}
   for(i=0;i<1500;i++){
    ex=rand()*(w.loc.spaceX*40-1);ey=rand()*(w.loc.spaceY*40-1);
    cx=rand()*(w.loc.spaceX*40-1);cy=rand()*(w.loc.spaceY*40-1);
    ray(a,b,w.loc,ex,ey,cx,cy);
    a.rayBatch=false;b.rayBatch=true;ray(a,b,w.loc,ex,ey,cx,cy);b.rayBatch=false;
   }
   // Native geometry, deterministic eye sweeps and live opacity changes.
   // Pure output fields are compared before display filtering; separate bound
   // consumers below also check the final filtered pixels across transitions.
   var layers:Array=[new Sprite(),new Sprite()],visuals:Array=[new Sprite(),new Sprite()];
   for(i=0;i<2;i++){layers[i].addChild(visuals[i]);host.stage.addChild(layers[i]);}
   var oldx:Number=w.gg.X,oldy:Number=w.gg.Y,oldscale:Number=w.gg.vis.scaleX;
   var tile:*=w.loc.getTile(12,14),oldop:Number=tile.opac;
   for each(var mode:String in ['current','classic'])for each(var sub:int in [4,8]){
    for each(m in [a,b]){m.restoreAll(w,w.loc);m.cfgMode=mode;m.fogSub=sub;m.cfgFogQuality=sub==4?0:1;m.applyVisionScale();m.resetRoom(w,w.loc);}
    for(f=0;f<24;f++){
     w.gg.setPos(360+f*7.25,640);w.gg.vis.scaleX=oldscale*(f%6<3?1:-1);w.gg.setVisPos();
     tile.opac=[oldop,0,.5,1][int(f/6)];
     for(i=0;i<2;i++){
      m=i==0?a:b;m.frameCount++;m.prepareOcclusion(w.loc);m.computeFov(w.loc);m.fovVersion++;m.fogDirty=true;
      if(mode=='current')m.applyVision(w,w.loc,true,true);else m.applyVisionClassic(w,w.loc,true);
      var v:Sprite=visuals[i];v.graphics.clear();v.graphics.beginFill(0xffffff);v.graphics.drawRect(-40-f*3,-4,100+f*3,8);v.graphics.endFill();v.x=530+f*3;v.y=620;
      m.applyWorldVisual(v,true);
      if(v.mask!=null)result.masked++;
     }
     check(JSON.stringify(a.fov)==JSON.stringify(b.fov),'FOV '+mode+'/'+sub+'/'+f);
     check(JSON.stringify(a.seenSub)==JSON.stringify(b.seenSub),'exploration '+mode+'/'+sub+'/'+f);
     if(mode=='current'){same(a.fogCache,b.fogCache,'fog');same(a.currentSight,b.currentSight,'sight');}
     var ia:BitmapData=new BitmapData(1000,800,true,0),ib:BitmapData=new BitmapData(1000,800,true,0);
     ia.draw(layers[0]);ib.draw(layers[1]);same(ia,ib,'continuous consumer');
     if(!ia.getColorBoundsRect(0xff000000,0,false).isEmpty())result.nonempty++;
     ia.dispose();ib.dispose();result.fields++;
    }
   }
   check(result.masked>0&&result.nonempty>0,'continuous mask and visible pixels exercised');
   tile.opac=oldop;w.gg.vis.scaleX=oldscale;w.gg.setPos(oldx,oldy);w.gg.setVisPos();
   for each(m in [a,b])m.restoreAll(w,w.loc);for each(var layer:Sprite in layers)host.stage.removeChild(layer);
   // Identical deterministic native-ray batches, ABBA repeated. These numbers
   // measure ray execution only, never complete game FPS.
   var points:Array=[];seed=0x51a9b432;
   for(i=0;i<12000;i++)points.push([rand()*1900,rand()*980,rand()*1900,rand()*980]);
   for each(m in [a,b]){m.prepareOcclusion(w.loc);m.rayBatch=true;}
   var sum:Number=0;
   for(var pass:int=0;pass<12;pass++){
    var slot:int=[0,1,1,0][pass%4];m=slot==0?a:b;var start:int=getTimer();
    for each(var p:Array in points)sum+=m.castRay(w.loc,p[0],p[1],p[2],p[3],int(p[2]/40),int(p[3]/40));
    result.rayTiming.push({variant:slot==0?'baseline':'candidate',ms:getTimer()-start});
   }
   result.checksum=sum;
  }
 }
}
