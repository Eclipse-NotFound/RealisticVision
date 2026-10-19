package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   import fe.World;
   import fe.loc.Tile;
   import fe.unit.Unit;
   import fe.unit.UnitPlayer;
   import fe.graph.Grafon;

   public class MaskChecks extends Sprite {
      private var passed:int=0,failed:int=0,seed:uint=0x1D302610;
      private var old:BaselineVision=new BaselineVision(),candidate:RealisticVisionMod=new RealisticVisionMod();
      private var w:World,loc:MotionLocation;
      public function MaskChecks(){
         try{run();}catch(e:Error){failed++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("MASK COMPLETE passed="+passed+" failed="+failed);NativeApplication.nativeApplication.exit(failed?1:0);
      }
      private function check(ok:Boolean,label:String):void{if(ok)passed++;else failed++;trace((ok?"PASS ":"FAIL ")+label);}
      private function same(a:BitmapData,b:BitmapData):Boolean{
         var d:Object=a.compare(b),ok:Boolean=d is uint&&uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;
      }
      private function random():uint{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed;}
      private function init():void{
         Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
         w=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new Grafon();w.grafon.visual=new Sprite();
         w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
         for each(var m:* in [old,candidate]){m.mswRegistered=true;m.resetRoom(w,loc);}
      }
      private function unit():Unit{var u:Unit=new Unit();u.X=650;u.Y=440;u.scX=80;u.scY=80;u.vis=new MovieClip();u.hpbar=new Sprite();return u;}
      private function run():void{
         init();var bad:int=0,k:int,m:*,a:Object,b:Object;
         // Exercise complete per-frame call site, motion and live geometry changes.
         for each(var mode:String in ["current","classic"]){
            for each(m in [old,candidate]){m.cfgMode=mode;m.resetRoom(w,loc);}
            for(k=0;k<80;k++){
               loc.gg.X=180+k*3.25;loc.gg.Y=500-(k%11);
               if(k==25)loc.getTile(10,7).opac=0;
               if(k==42)loc.getTile(6,8).opac=.3;
               if(k==55){loc.getTile(7,9).water=1;loc.opacWater=.45;}
               for each(m in [old,candidate]){m.frameCount++;m.onFrameInner();}
               if(!same(old.fogCache,candidate.fogCache)||!same(old.fogBmp,candidate.fogBmp)||!same(old.wallRaw,candidate.wallRaw))bad++;
               if(mode=="current"&&!same(old.currentSight,candidate.currentSight))bad++;
               if(JSON.stringify([old.fov,old.explored,old.seenSub])!=JSON.stringify([candidate.fov,candidate.explored,candidate.seenSub]))bad++;
            }
            check(bad==0,mode+" 80 moving frames: exact fog, wall, sight, exploration, stationary geometry updates");
         }
         var u:Unit=unit(),v:Unit=unit(),blur:Number;
         for each(mode in ["classic","current"]){
            for each(m in [old,candidate]){m.cfgMode=mode;m.resetRoom(w,loc);m.onFrameInner();}
            for each(blur in [0,1,2,4,6,9]){
               bad=0;
               for(k=0;k<24;k++){
                  var pixels:Vector.<uint>=new Vector.<uint>(old.fogCache.width*old.fogCache.height,true);
                  var eligible:Vector.<uint>=new Vector.<uint>(pixels.length,true);
                  for(var i:int=0;i<pixels.length;i++){pixels[i]=random();eligible[i]=(random()%7<4)?0xFFFFFFFF:0;}
                  for each(m in [old,candidate]){
                     m.fogCache.setVector(m.fogCache.rect,pixels);m.currentSight.setVector(m.currentSight.rect,eligible);
                     m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;
                     m.fovVersion++;
                  }
                  u.X=v.X=30+(k*37)%850;u.Y=v.Y=50+(k*19)%650;u.scX=v.scX=18+k*2;u.scY=v.scY=24+k;
                  old.applyMask(w,u,old.unitBBox(loc,u));candidate.applyMask(w,v,candidate.unitBBox(loc,v));
                  a=old.unitVis[u];b=candidate.unitVis[v];
                  if(!same(a.m2d,b.m2d)||!same(a.m2e,b.m2e))bad++;
                  // Unchanged input with a new FOV version must reuse pixels
                  // while still restoring detached display masks.
                  old.clearMask(u);candidate.clearMask(v);old.fovVersion++;candidate.fovVersion++;
                  old.applyMask(w,u,old.unitBBox(loc,u));candidate.applyMask(w,v,candidate.unitBBox(loc,v));
                  if(!same(a.m2d,b.m2d)||!same(a.m2e,b.m2e)||v.vis.mask!==b.m2||b.m2.parent==null)bad++;
               }
               check(bad==0,mode+" blur="+blur+" 24 random full-alpha fields, edge sizes and exact masks");
            }
         }
         old.cfgMode=candidate.cfgMode="current";bad=0;
         for(var alpha:int=0;alpha<256;alpha++)for each(var tracking:Boolean in [false,true]){
            for each(m in [old,candidate]){
               m.sharedLight=null;for(i=0;i<m.wallA.length;i++){m.wallA[i]=alpha;m.fov[i]=(alpha%3);}
               m.fogCache.fillRect(m.fogCache.rect,0x7f000000);m.currentSight.fillRect(m.currentSight.rect,0xffffffff);
            }
            var ar:Boolean=old.fillWallTile(10,7,tracking),br:Boolean=candidate.fillWallTile(10,7,tracking);
            if(ar!=br||!same(old.fogCache,candidate.fogCache)||!same(old.currentSight,candidate.currentSight))bad++;
         }
         check(bad==0,"512 uniform wall corner/threshold cases preserve pixels and tracking result");
         old.clearMask(u);candidate.clearMask(v);
         check(u.vis.mask==null&&v.vis.mask==null&&old.unitVis[u].m2.parent==null&&candidate.unitVis[v].m2.parent==null,"mask teardown removes display shapes");
      }
   }
}
