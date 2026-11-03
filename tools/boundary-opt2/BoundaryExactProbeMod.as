package {
  import flash.display.*; import flash.events.*; import flash.filesystem.*;
  import flash.system.*; import flash.net.URLRequest; import flash.geom.*;
  import flash.utils.*; import flash.media.*; import flash.desktop.NativeApplication;
  /** Exact values, pixels and enemy-state behaviour for the clip-mask round. */
  public class BoundaryExactProbeMod extends Sprite {
   private static var instance:BoundaryExactProbeMod;
   public static function init(main:*):void{instance=new BoundaryExactProbeMod(main);}
   private var host:*,wc:Class,classes:Object={},loaders:Array=[],timer:Timer=new Timer(150);
   private var ticks:int=0,phase:int=0,settle:int=0,seed:uint=0x5162b391;
   private var result:Object={checks:0,rays:0,matchingRayErrors:0,fields:0,pixels:0,
     dynFrames:0,dynDiffs:0,dynAdded:0,dynLost:0,dynAddedDark:0,statPixels:0,statNonempty:0,
     calib:{},oscillate:{},hystChecks:0};
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
    if(p.indexOf('/RealisticVision/build/boundary-opt2-20261104/')<0)throw new Error('wrong output');
    var f:FileStream=new FileStream();try{f.open(new File(p+'/evidence/result.json'),FileMode.WRITE);f.writeUTFBytes(JSON.stringify(result));}finally{f.close();}
   }
   private function fail(e:Error):void{timer.stop();result.error=String(e);save();trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
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
    if(phase==1&&w.gg&&w.loc&&w.loc.active&&w.allStat==1&&w.game.curLandId){
     if(w.game.curLandId!='rbl'){w.pers.healAll();w.game.beginMission('rbl');}
     phase=2;return;
    }
    if(phase==2&&w.loc&&w.loc.active&&w.game.curLandId=='rbl'&&w.land.act.id=='rbl'&&w.t_exit==0){
     w.gg.setPos(w.loc.limX-60,600);if(w.land.gotoLoc(2)==null)throw new Error('training entry');w.gg.setPos(480,640);phase=3;return;
    }
    if(phase==3&&w.loc&&w.loc.active&&w.land.locX==1&&w.land.locY==0&&w.allStat==1){
     if(++settle<15)return;timer.stop();w.black=true;w.loc.black=true;w.loc.base=false;
     run(w);save();trace('BOUNDARY EXACT COMPLETE '+JSON.stringify(result));NativeApplication.nativeApplication.exit(0);
    }
   }catch(err:Error){fail(err);}}
   private function make(n:String,w:*):*{var c:Class=classes[n],m:*=new c();m.loadConfig();m.cfgEnabled=true;m.cfgBaseRooms={};m.mswRegistered=true;m.resetRoom(w,w.loc);return m;}
   private function ray(a:*,b:*,loc:*,ex:Number,ey:Number,cx:Number,cy:Number):void{
    var tx:int=Math.floor(cx/40),ty:int=Math.floor(cy/40);
    var av:Number,bv:Number,ae:String='',be:String='';
    try{av=a.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(ea:Error){ae=String(ea);}
    try{bv=b.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(eb:Error){be=String(eb);}
    check(ae==be&&(ae!=''||av===bv),'ray '+[ex,ey,cx,cy,av,bv,ae,be]);
    if(ae!='')result.matchingRayErrors++;result.rays++;
   }
   /** Full RV update at a fixed eye so hideEnemies classification runs. */
   private function stepRV(m:*,w:*,loc:*):void{
    m.frameCount++;m.prepareOcclusion(loc);m.computeFov(loc,true);m.fovVersion++;m.fogDirty=true;
    m.applyVision(w,loc,true,true);m.hideEnemies(w,loc,true);
   }
   private function stateOf(m:*,dummy:*):int{
    var rec:Object=m.unitVis[dummy];return rec==null?-1:int(rec.state);
   }
   private function run(w:*):void{
    var a:*=make('baseline',w),b:*=make('candidate',w),m:*,x:int,y:int,i:int,f:int;
    var cells:Vector.<Number>=new Vector.<Number>(64*48,true);
    for each(m in [a,b]){m.rayBatch=true;m.rayLoc=null;m.rayWidth=64;m.rayHeight=48;m.rayOpac=cells;}
    // Ray regression only: this round does not touch castRay, sampled coverage.
    for(f=0;f<2;f++){
     for(i=0;i<cells.length;i++)cells[i]=f==0?0:(rand()<.09?[0,.15,.5,1][int(rand()*4)]:0);
     for(i=0;i<4000;i++){
      var ex:Number=rand()*2559,ey:Number=rand()*1919,cx:Number=rand()*2559,cy:Number=rand()*1919;
      if(i%7==0)cx=ex;if(i%11==0)cy=ey;
      if(i%13==0){ex=int(ex/40)*40;ey=int(ey/40)*40;cx=int(cx/40)*40;cy=int(cy/40)*40;}
      ray(a,b,null,ex,ey,cx,cy);
     }
    }
    for each(m in [a,b]){m.rayBatch=false;}
    // Native geometry, deterministic eye sweeps and live opacity changes.
    var layers:Array=[new Sprite(),new Sprite()];
    var dyn:Array=[new Sprite(),new Sprite()],stat:Array=[new Sprite(),new Sprite()];
    for(i=0;i<2;i++){layers[i].addChild(dyn[i]);layers[i].addChild(stat[i]);host.stage.addChild(layers[i]);}
    var oldx:Number=w.gg.X,oldy:Number=w.gg.Y,oldscale:Number=w.gg.vis.scaleX;
    var tile:*=w.loc.getTile(12,14),oldop:Number=tile.opac;
    var view:Rectangle=new Rectangle(0,0,1000,800);
    for each(var mode:String in ['current','classic'])for each(var sub:int in [4,8]){
     for each(m in [a,b]){m.restoreAll(w,w.loc);m.cfgMode=mode;m.fogSub=sub;m.cfgFogQuality=sub==4?0:1;m.applyVisionScale();m.resetRoom(w,w.loc);}
     for(f=0;f<24;f++){
      w.gg.setPos(360+f*7.25,640);w.gg.vis.scaleX=oldscale*(f%6<3?1:-1);w.gg.setVisPos();
      tile.opac=[oldop,0,.5,1][int(f/6)];
      for(i=0;i<2;i++){
       m=i==0?a:b;m.frameCount++;m.prepareOcclusion(w.loc);m.computeFov(w.loc);m.fovVersion++;m.fogDirty=true;
       if(mode=='current')m.applyVision(w,w.loc,true,true);else m.applyVisionClassic(w,w.loc,true);
       var vd:Sprite=dyn[i];vd.graphics.clear();vd.graphics.beginFill(0xffffff);vd.graphics.drawRect(-40-f*3,-4,100+f*3,8);vd.graphics.endFill();vd.x=530+f*3;vd.y=620;
       m.applyWorldVisual(vd,true);   // projectile semantics (C-Bul-1)
       var vs:Sprite=stat[i];vs.graphics.clear();vs.graphics.beginFill(0xffffff);vs.graphics.drawRect(-40-f*3,-4,100+f*3,8);vs.graphics.endFill();vs.x=530+f*3+120;vs.y=620;
       m.applyWorldVisual(vs,false);  // enemy-weapon semantics, must stay identical
      }
      check(JSON.stringify(a.fov)==JSON.stringify(b.fov),'FOV '+mode+'/'+sub+'/'+f);
      check(JSON.stringify(a.seenSub)==JSON.stringify(b.seenSub),'exploration '+mode+'/'+sub+'/'+f);
      if(mode=='current'){same(a.fogCache,b.fogCache,'fog');same(a.currentSight,b.currentSight,'sight');}
      var ia:BitmapData=new BitmapData(1000,800,true,0),ib:BitmapData=new BitmapData(1000,800,true,0);
      ia.draw(layers[0]);ib.draw(layers[1]);
      var va:Vector.<uint>=ia.getVector(view),vb:Vector.<uint>=ib.getVector(view);
      var addedDark:int=0,lost:int=0,added:int=0,diffPix:int=0;
      for(i=0;i<va.length;i++){
       var sa:uint=va[i]>>>24,sb:uint=vb[i]>>>24;
       if(sa==sb)continue;
       diffPix++;
       if(sb==0)lost++;
       else{added++;if(sa==0)addedDark++;}
      }
      // C-Bul-1: clip semantics may only widen the transition band of the
      // dynamic visual and never hide a pixel the alpha mask revealed.
      check(lost==0,'dyn lost pixels '+mode+'/'+sub+'/'+f+' '+lost);
      check(addedDark==0,'dyn added outside band '+mode+'/'+sub+'/'+f+' '+addedDark);
      if(diffPix>0)result.dynFrames++;
      result.dynDiffs+=diffPix;result.dynAdded+=added;result.dynLost+=lost;result.dynAddedDark+=addedDark;
      ia.dispose();ib.dispose();result.fields++;
     }
    }
    // C-Bul-2 invariant: narrowing the support padding must not change any
    // pixel of the projectile path (the clip boundary follows the mask alpha
    // inside the bounding box, which the padding does not touch).
    check(result.dynFrames==0&&result.dynAdded==0&&result.dynLost==0,'clip path pixels identical');
    // Positive control: the world rasters themselves must have shrunk.
    var areaA:int=0,areaB:int=0;
    for each(var rkA:Object in a.worldMasks) if(rkA.m2e)areaA+=rkA.m2e.width*rkA.m2e.height;
    for each(var rkB:Object in b.worldMasks) if(rkB.m2e)areaB+=rkB.m2e.width*rkB.m2e.height;
    check(areaB<areaA,'pad narrowed rasters '+areaA+'->'+areaB);
    result.padArea={baseline:areaA,candidate:areaB};
    // Strict comparison for the static (non-projectile) visual: hide the
    // dynamic sprites so both layers contain only the static consumer.
    dyn[0].visible=false;dyn[1].visible=false;
    for(f=0;f<6;f++){
     w.gg.setPos(360+f*29,640);w.gg.setVisPos();
     for(i=0;i<2;i++){
      m=i==0?a:b;m.frameCount++;m.prepareOcclusion(w.loc);m.computeFov(w.loc);m.fovVersion++;m.fogDirty=true;
      m.applyVision(w,w.loc,true,true);
      var vs2:Sprite=stat[i];vs2.graphics.clear();vs2.graphics.beginFill(0xffffff);vs2.graphics.drawRect(-60,-6,140,12);vs2.graphics.endFill();vs2.x=560+f*24;vs2.y=620;
      m.applyWorldVisual(vs2,false);
     }
     var ja:BitmapData=new BitmapData(1000,800,true,0),jb:BitmapData=new BitmapData(1000,800,true,0);
     ja.draw(layers[0]);jb.draw(layers[1]);same(ja,jb,'static consumer '+f);
     if(!ja.getColorBoundsRect(0xff000000,0,false).isEmpty())result.statNonempty++;
     ja.dispose();jb.dispose();
    }
    check(result.statNonempty>0,'static content exercised');
    tile.opac=oldop;w.gg.vis.scaleX=oldscale;
    for each(m in [a,b])m.restoreAll(w,w.loc);
    for each(var layer:Sprite in layers)host.stage.removeChild(layer);
    enemyHysteresis(w,a,b,oldx,oldy);
   }
   /** Find the nearest lit/dark tile boundary from the vision field. */
   private function findEdge(m:*,w:*,loc:*):Array{
    m.frameCount++;m.prepareOcclusion(loc);m.computeFov(loc,true);m.fovVersion++;m.fogDirty=true;
    m.applyVision(w,loc,true,true);
    var fov:*=m.fov,sx:int=m.spaceX,sy:int=m.spaceY;
    var px:Number=w.gg.X,py:Number=w.gg.Y;
    var best:Array=null,bestD:Number=1e9;
    var dirs:Array=[[1,0],[-1,0],[0,1],[0,-1]];
    for(var ty:int=2;ty<sy-2;ty++)for(var tx:int=2;tx<sx-2;tx++){
     if(fov[tx+ty*sx]==0)continue;
     for(var di:int=0;di<4;di++){
      var nx:int=tx+dirs[di][0],ny:int=ty+dirs[di][1];
      if(fov[nx+ny*sx]!=0)continue;
      var wx:Number=(tx+0.5)*40,wy:Number=(ty+0.5)*40;
      var vx:Number=wx+dirs[di][0]*40,vy:Number=wy+dirs[di][1]*40;
      var cx:Number=(wx+vx)*0.5,cy:Number=(wy+vy)*0.5;
      var d:Number=Math.sqrt((cx-px)*(cx-px)+(cy-py)*(cy-py));
      if(d>120&&d<bestD){bestD=d;best=[cx,cy,dirs[di][0],dirs[di][1]];}
     }
    }
    return best;
   }
   /** C-Ene-1: oscillate a dummy across a real vision edge. */
   private function enemyHysteresis(w:*,a:*,b:*,oldx:Number,oldy:Number):void{
    var loc:*=w.loc,dummy:*;
    for each(var un:* in loc.units)if(un.id=='training'){dummy=un;break;}
    check(dummy!=null,'training dummy present');
    var home:*=dummy.X,homeY:*=dummy.Y;
    w.gg.setPos(480,640);w.gg.setVisPos();w.godMode=true;w.gg.invulner=true;
    // The field-comparison loop above leaves cfgMode at its last iteration
    // (classic). The missing middle band only exists on the current in-room
    // path, which is also the user's actual configuration: restore it.
    for each(var m0:* in [a,b]){m0.cfgMode='current';m0.fogSub=4;m0.cfgFogQuality=0;m0.applyVisionScale();m0.resetRoom(w,loc);}
    var edge:Array=findEdge(a,w,loc);
    check(edge!=null,'vision edge found');
    var cx:Number=edge[0],cy:Number=edge[1],dx:Number=edge[2],dy:Number=edge[3];
    trace('DIAG edge '+cx+','+cy+' dir '+dx+','+dy+' mode='+a.cfgMode+' enemyFast='+a.cfgEnemyFast+' sightData='+(a.currentSightData==null?'null':a.currentSightData.length));
    // Sweep across the edge to record both sides, then oscillate on it.
    var calibA:Array=[],calibB:Array=[],i:int,off:Number;
    for(off=-100;off<=100;off+=4){
     dummy.setPos(cx+dx*off,cy+dy*off);
     stepRV(a,w,loc);stepRV(b,w,loc);
     calibA.push(stateOf(a,dummy));calibB.push(stateOf(b,dummy));
     if(off==0){
      var bbA:Array=a.unitBBox(loc,dummy);
      trace('DIAG off0 bb='+bbA+' fovN='+a.bboxFovCount(bbA)+'/'+a.bboxTotal(bbA)+' direct='+a.enemyState(loc,dummy)+' recA='+stateOf(a,dummy)+' recB='+stateOf(b,dummy));
     }
    }
    result.calib={center:[cx,cy],dir:[dx,dy],offsetFrom:-100,step:4,baseline:calibA,candidate:calibB};
    check(calibA.indexOf(1)>=0,'lit side visible');
    // Crossing evidence: baseline drops out of 1 and the candidate enters the
    // partial band (or reaches hidden on a sufficiently deep sweep).
    check(calibA.indexOf(1)!=calibA.length-1,'edge crossed by baseline');
    check(calibB.indexOf(2)>=0||calibB.indexOf(0)>=0,'edge crossed by candidate');
    // Oscillate across the 0.8 gate; baseline flips 0<->1 directly, candidate
    // never does (hysteresis forces the partial band between the extremes).
    var amp:int=10,tries:int=0,seqA:Array=[],seqB:Array=[],directA:int=0,directB:int=0;
    while(tries<4){
     seqA=[];seqB=[];directA=0;directB=0;
     for(i=0;i<40;i++){
      var s:Number=amp*Math.sin(i*Math.PI/5);
      dummy.setPos(cx+dx*s,cy+dy*s);
      stepRV(a,w,loc);stepRV(b,w,loc);
      seqA.push(stateOf(a,dummy));seqB.push(stateOf(b,dummy));
     }
     for(i=0;i<39;i++){
      if(seqA[i]+seqA[i+1]==1)directA++;
      if(seqB[i]+seqB[i+1]==1)directB++;
     }
     if(directA>=3)break;
     amp*=2;tries++;
    }
    result.oscillate={center:[cx,cy],dir:[dx,dy],amp:amp,baseline:seqA,candidate:seqB,directA:directA,directB:directB};
    // Since v0.34.7 the baseline itself carries the hysteresis: both variants
    // must stay free of direct 0<->1 flips, and the partial band is still used.
    check(directA==0&&directB==0,'no direct 0<->1 flip ('+directA+'/'+directB+')');
    check(calibA.indexOf(2)>=0&&calibB.indexOf(2)>=0,'partial band used on both sides');
    result.hystChecks=2;
    dummy.setPos(home,homeY);
    w.gg.setPos(oldx,oldy);w.gg.setVisPos();
   }
  }
}
