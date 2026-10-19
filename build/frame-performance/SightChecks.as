package {
   import flash.display.*;
   import flash.desktop.NativeApplication;
   import flash.geom.Rectangle;
   import fe.loc.Location;
   import fe.loc.Tile;
   import fe.unit.Unit;
   public class SightChecks extends Sprite {
      private var failures:int=0,seed:uint=123019,count:int=0;
      public function SightChecks(){try{run();}catch(e:Error){failures++;trace("FAIL "+e+" "+e.getStackTrace());}trace("SIGHT COMPLETE comparisons="+count+" failures="+failures);NativeApplication.nativeApplication.exit(failures?1:0);}
      private function rand():uint{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed;}
      private function run():void{
         Tile.tileX=Tile.tileY=40;
         for each(var dims:Array in [[24,18],[192,75]]){
            var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod(),loc:Location=new Location();loc.spaceX=dims[0];loc.spaceY=dims[1];
            for each(var m:* in [a,b]){m.spaceX=loc.spaceX;m.spaceY=loc.spaceY;m.cfgMode="current";m.fov=new Array(loc.spaceX*loc.spaceY);m.currentSight=new BitmapData(loc.spaceX*8+8,loc.spaceY*8+8,true,0);}
            var u:Unit=new Unit(),bad:int=0;
            for(var step:int=0;step<24;step++){
               var data:BitmapData=a.currentSight;data.fillRect(data.rect,step%3==0?0:0xffffffff);
               for(var r:int=0;r<90;r++)data.fillRect(new Rectangle(rand()%data.width,rand()%data.height,1+rand()%90,1+rand()%70),rand()%2?0:0xffffffff);
               b.currentSight.copyPixels(data,data.rect,data.rect.topLeft);
               for(var i:int=0;i<a.fov.length;i++)a.fov[i]=b.fov[i]=rand()%5==0?0:2;
               a.currentSightData=b.currentSightData=null;
               if(loc.spaceX<48){a.currentSightData=a.currentSight.getVector(data.rect);b.currentSightData=b.currentSight.getVector(data.rect);}
               for(i=0;i<500;i++){
                  u.X=(rand()%(loc.spaceX*40));u.Y=(rand()%(loc.spaceY*40));u.scX=10+rand()%100;u.scY=10+rand()%120;
                  if(a.enemyState(loc,u)!=b.enemyState(loc,u))bad++;
                  // Same data and repeated/shared bounds exercise the cached branch.
                  if(a.enemyState(loc,u)!=b.enemyState(loc,u))bad++;
                  count+=2;
               }
            }
            if(bad)failures++;trace((bad?"FAIL ":"PASS ")+loc.spaceX+"x"+loc.spaceY+" 24000 exact classifications and changed snapshots mismatches="+bad);
            a.currentSight.dispose();b.currentSight.dispose();
         }
      }
   }
}
