package {
 import flash.display.*;
 import flash.geom.*;
 import flash.filters.*;
 import flash.desktop.NativeApplication;
 public class MaskBatchChecks extends Sprite {
  public function MaskBatchChecks(){
   try {
    var m:RealisticVisionMod=new RealisticVisionMod(),count:int=0,seed:uint=1234567;
    for(var run:int=0;run<65;run++) {
     var w:int=run==0?256:8+(run%7)*8,h:int=run==0?256:8+(run%9)*8;
     var eligible:BitmapData=new BitmapData(w,h,true,0),soft:BitmapData=eligible.clone(),reference:BitmapData;
     for(var y:int=0;y<h;y++) for(var x:int=0;x<w;x++) {
      seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;
      eligible.setPixel32(x,y,(seed&3)==0?0:0xffffffff);
      soft.setPixel32(x,y,run==0?uint((x<<24)|0xffffff):eligible.getPixel32(x,y));
     }
     if(run>0)soft.applyFilter(eligible,eligible.rect,new Point(),new BlurFilter(run%9,run%11,1+run%3));
     reference=soft.clone();
     var ev:Vector.<uint>=eligible.getVector(eligible.rect),sv:Vector.<uint>=reference.getVector(reference.rect);
     for(var i:int=0;i<sv.length;i++){var a:int=ev[i]==0?0:Math.max(0,2*(sv[i]>>>24)-255);sv[i]=a==0?0:uint((a<<24)|0xffffff);}
     reference.setVector(reference.rect,sv);m.finishCurrentMask(eligible,soft);
     var delta:Object=reference.compare(soft);if(!(delta is uint&&uint(delta)==0))throw new Error("batch mismatch "+run);
     count++;eligible.dispose();soft.dispose();reference.dispose();
    }
    trace("PASS all alpha values and 64 blurred fields exact");trace("BATCH COMPLETE "+count);NativeApplication.nativeApplication.exit(0);
   }catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
  }
 }
}
