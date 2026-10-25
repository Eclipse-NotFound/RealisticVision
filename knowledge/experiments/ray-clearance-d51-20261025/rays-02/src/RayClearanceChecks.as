package {
 import flash.display.Sprite;
 import flash.desktop.NativeApplication;
 import fe.loc.Tile;
 public class RayClearanceChecks extends Sprite {
  private var checks:int=0,failed:int=0,seed:uint=0x51a73b9;
  private var comparisons:int=0,fast:int=0,oldSteps:Number=0,newSteps:Number=0;
  public function RayClearanceChecks(){
   try {run();}catch(e:Error){failed++;trace("FAIL unexpected "+e+" "+e.getStackTrace());}
   trace("RAY COMPLETE "+JSON.stringify({passed:checks,failed:failed,comparisons:comparisons,fastHits:fast,oldSteps:oldSteps,newSteps:newSteps,performanceEvidence:false}));
   NativeApplication.nativeApplication.exit(failed?1:0);
  }
  private function check(ok:Boolean,label:String):void{if(!ok){failed++;if(failed<20)trace("FAIL "+label);}else checks++;}
  private function rnd(n:int):int{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return int(seed%n);}
  private function same(a:Number,b:Number):Boolean{return a===b || isNaN(a)&&isNaN(b);}
  private function model(cls:Class,loc:RayTestLocation):*{var m:*=new cls();m.cfgMode="current";m.spaceX=loc.spaceX;m.spaceY=loc.spaceY;m.curLoc=loc;return m;}
  private function prepare(a:*,b:*,loc:RayTestLocation):void{
   check(a.prepareOcclusion(loc)===b.prepareOcclusion(loc),"same invalidation");
   check(b.rayClearReady,"summary ready after complete scan");
   for(var i:int=0;i<a.rayOpac.length;i++)check(same(a.rayOpac[i],b.rayOpac[i]),"same opacity "+i);
  }
  private function ray(a:*,b:*,loc:RayTestLocation,ex:Number,ey:Number,cx:Number,cy:Number,tx:int,ty:int,batch:Boolean=true):void{
   a.rayBatch=b.rayBatch=batch;
   var av:Number,bv:Number,ae:int=0,be:int=0;
   try{av=a.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(ea:Error){ae=ea.errorID;}
   try{bv=b.castRay(loc,ex,ey,cx,cy,tx,ty);}catch(eb:Error){be=eb.errorID;}
   comparisons++;check(ae===be && (ae!=0 || same(av,bv)),"ray "+comparisons+" "+av+"/"+bv+" errors "+ae+"/"+be);
  }
  private function run():void{
   for each(var size:Array in [[24,18],[48,25],[49,25],[48,26],[192,75]]){
    Tile.tileX=40;Tile.tileY=size[0]==49?30:40;
    var loc:RayTestLocation=new RayTestLocation(size[0],size[1]);
    var a:*=model(BaselineVision,loc),b:*=model(RealisticVisionMod,loc);
    for(var scene:int=0;scene<6;scene++){
     loc.opacWater=scene==3?.4:0;
     for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
      var t:Tile=loc.space[x][y];t.opac=0;t.water=0;
      var roll:int=rnd(100);
      if(scene==1 && roll<5)t.opac=1;
      if(scene==2 && roll<9)t.opac=[.05,.3,.8][roll%3];
      if(scene==3){if(roll<15)t.water=1;if(roll>95)t.opac=.2;}
      if(scene==4 && roll<7)t.opac=[NaN,Number.POSITIVE_INFINITY,Number.NEGATIVE_INFINITY,-.3,1][roll%5];
      if(scene==5 && x==int(loc.spaceX/2))t.opac=y%5==0?.3:1;
     }
     prepare(a,b,loc);
     for(var n:int=0;n<700;n++){
      var sx:int=rnd(loc.spaceX),sy:int=rnd(loc.spaceY),tx:int=rnd(loc.spaceX),ty:int=rnd(loc.spaceY);
      var offsets:Array=[0,.001,.5,.999];var ox:Number=offsets[n%4],oy:Number=offsets[int(n/4)%4];
      ray(a,b,loc,(sx+ox)*Tile.tileX,(sy+oy)*Tile.tileY,(tx+.5)*Tile.tileX,(ty+.5)*Tile.tileY,tx,ty,n%19!=0);
     }
     // Same-cell, boundary, unbatched and deliberately inconsistent requests
     // must still agree with the original public function behavior.
     ray(a,b,loc,80,80,80,80,2,int(80/Tile.tileY));
     ray(a,b,loc,-1,40,100,100,2,int(100/Tile.tileY));
     ray(a,b,loc,80,80,100,100,3,3);
     ray(a,b,loc,NaN,80,100,100,2,int(100/Tile.tileY));
    }
    fast+=b.d51Fast;oldSteps+=a.d51Steps;newSteps+=b.d51Steps;
    trace("SIZE "+size+" fast="+b.d51Fast+" steps="+a.d51Steps+"/"+b.d51Steps);
   }
   Tile.tileX=Tile.tileY=40;
   loc=new RayTestLocation(24,18);a=model(BaselineVision,loc);b=model(RealisticVisionMod,loc);prepare(a,b,loc);
   check(b.rayClearCounts[b.rayClearCounts.length-1]==0,"open map summary");
   loc.space[1][0].opac=1;loc.failAt=2;
   var threw:int=0;try{a.prepareOcclusion(loc);}catch(ea:Error){threw++;}
   try{b.prepareOcclusion(loc);}catch(eb:Error){threw++;}
   check(threw==2 && !b.rayClearReady,"interrupted scan invalidates summary before write");
   ray(a,b,loc,20,20,100,20,2,0);
   loc.failAt=-1;prepare(a,b,loc);ray(a,b,loc,20,20,100,20,2,0);
   loc.space[1][0].opac=0;prepare(a,b,loc);ray(a,b,loc,20,20,100,20,2,0);
   // Equal vector lengths with a different stride cannot retain old row/column
   // padding. This caught a flaw in the untested first source draft.
   for each(size in [[24,18],[18,24],[24,18]]){
    loc=new RayTestLocation(size[0],size[1]);loc.space[3][3].opac=1;
    a.spaceX=b.spaceX=loc.spaceX;a.spaceY=b.spaceY=loc.spaceY;a.curLoc=b.curLoc=loc;
    prepare(a,b,loc);ray(a,b,loc,20,20,340,340,8,8);ray(a,b,loc,20,20,340,20,8,0);
   }
   check(fast>0,"shortcut exercised");check(newSteps<oldSteps,"fewer original traversal steps; not a timing claim");
  }
 }
}
