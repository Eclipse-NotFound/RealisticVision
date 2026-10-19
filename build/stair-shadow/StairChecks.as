package {
   import flash.display.*;
   import flash.geom.*;
   import flash.desktop.NativeApplication;
   /** A native partial tile may remain opaque when a background suffix follows
    * its height marker (C;F). The cut-away air is not a texture notch. */
   public class StairChecks extends Sprite {
      private var failures:int=0,passed:int=0;
      private var surface:RVWallSurface=new RVWallSurface();
      private var fog:Sprite=new Sprite(),base:Sprite=new Sprite(),front:Sprite=new Sprite();
      private var pixels:BitmapData=new BitmapData(400,320,true,0),tiles:Array=[],loc:Object;
      private var bright:Boolean=false,light:Number=1;
      public function StairChecks(){
         try{run();}catch(e:Error){failures++;trace("FAIL "+e+" "+e.getStackTrace());}
         trace("STAIR COMPLETE passed="+passed+" failures="+failures);
         NativeApplication.nativeApplication.exit(failures?1:0);
      }
      private function check(ok:Boolean,label:String):void{if(ok)passed++;else failures++;trace((ok?"PASS ":"FAIL ")+label);}
      private function update(view:Rectangle=null):void{
         var self:StairChecks=this;
         surface.update(fog,base,{visFront:front},loc,view||new Rectangle(0,0,10,8),
            function(x:int,y:int):Boolean{return true;},function(...args):Number{return self.light;},bright);
      }
      private function shot():BitmapData{var b:BitmapData=new BitmapData(400,320,false,0xffffff);b.draw(fog,null,null,null,null,true);return b;}
      private function build(cut:int,opaque:Boolean):void{
         pixels.fillRect(pixels.rect,0);
         for(var y:int=0;y<8;y++)for(var x:int=0;x<10;x++){
            var solid:Boolean=x>=2&&x<=6&&y>=2&&y<=5;
            tiles[x+y*10]={opac:solid?1:0,phis:solid?1:0,front:solid?"C":"",zForm:solid&&y==2?cut:0};
            if(solid){
               if(y==2&&!opaque)tiles[x+y*10].opac=0;
               pixels.fillRect(new Rectangle(x*40,y*40+(y==2?cut*10:0),40,40-(y==2?cut*10:0)),0xffffffff);
            }
         }
         base.graphics.clear();base.graphics.beginFill(0,1-light);base.graphics.drawRect(0,0,400,320);base.graphics.endFill();
      }
      private function run():void{
         var self:StairChecks=this;
         loc={spaceX:10,spaceY:8,getTile:function(x:int,y:int):Object{return self.tiles[x+y*10];}};
         front.addChild(new Bitmap(pixels));fog.addChild(base);
         for each(bright in [false,true])for each(light in [1,.35])for(var cut:int=1;cut<=3;cut++){
            build(cut,true);update();var b:BitmapData=shot();
            var changed:int=0,black:int=0,expected:int=Math.round(255*light);
            // Cut-away air 1px above the physical top must retain original fog,
            // including the 5px bilinear-support halo where the old field is zero.
            for(var y:int=80;y<80+cut*10;y++)for(var x:int=100;x<260;x++){
               var v:int=b.getPixel(x,y)&255;
               if(Math.abs(v-expected)>1)changed++;if(v==0)black++;
            }
            check(changed==0,"cut="+cut+" bright="+bright+" light="+light+" air stays original, changed="+changed+" black="+black);
            check(Math.abs((b.getPixel(180,180)&255)-expected)<=1,"distant inner field not changed by contour correction");b.dispose();
            // A real transparent notch *inside* the physical stair still needs
            // the independent anti-spill correction, also with constant rim OFF.
            base.graphics.beginFill(0);base.graphics.drawRect(140,80+cut*10,10,5);base.graphics.endFill();
            pixels.fillRect(new Rectangle(140,80+cut*10,10,5),0);update();b=shot();
            check(Math.abs((b.getPixel(145,82+cut*10)&255)-expected)<=1,"cut="+cut+" material notch remains repaired");b.dispose();
         }
         bright=false;light=1;build(3,true);update();
         tiles[4+2*10].zForm=1;pixels.fillRect(new Rectangle(160,90,40,20),0xffffffff);update();
         check(surface.heightAt(loc,4,2)==30,"height change detected at fixed camera");
         var first:BitmapData=shot();surface.reset();update();var second:BitmapData=shot(),diff:Object=first.compare(second);
         check(diff is uint&&uint(diff)==0,"incremental height change equals clean rebuild");
         if(diff is BitmapData)BitmapData(diff).dispose();first.dispose();second.dispose();
         build(2,false);update();first=shot();surface.reset();update();second=shot();diff=first.compare(second);
         check(diff is uint&&uint(diff)==0,"native nonblocking stairs keep stable output");
         if(diff is BitmapData)BitmapData(diff).dispose();first.dispose();second.dispose();
         check(tiles[4+2*10].opac==0,"display correction never writes native opacity");
         build(3,true);update(new Rectangle(1,1,8,6));first=shot();
         surface.reset();update();second=shot();
         check(first.getPixel(180,95)==second.getPixel(180,95),"nonzero viewport top preserves physical cut phase");
         first.dispose();second.dispose();
         for each(var zoom:Number in [.75,1.25]){
            var matrix:Matrix=new Matrix(zoom,0,0,zoom,.25,.5);
            first=new BitmapData(520,420,false,0xffffff);first.draw(fog,matrix,null,null,null,true);
            var keep:DisplayObject=base.mask;base.mask=null;
            second=new BitmapData(520,420,false,0xffffff);second.draw(base,matrix,null,null,null,true);base.mask=keep;
            var mismatches:int=0;
            for(var yy:int=int(82*zoom)+1;yy<int(108*zoom);yy++)for(var xx:int=int(100*zoom)+1;xx<int(260*zoom);xx++)
               if(first.getPixel(xx,yy)!=second.getPixel(xx,yy))mismatches++;
            check(mismatches==0,"fractional camera "+zoom+" retains air exactly, changed="+mismatches);
            first.dispose();second.dispose();
         }
         // Native destruction may retain zForm, but opacity/material disappear.
         tiles[4+2*10].opac=0;tiles[4+2*10].phis=0;tiles[4+2*10].front="";
         pixels.fillRect(new Rectangle(160,80,40,40),0);update();first=shot();
         surface.reset();update();second=shot();diff=first.compare(second);
         check(diff is uint&&uint(diff)==0,"destroyed stair with stale zForm equals fresh output");
         if(diff is BitmapData)BitmapData(diff).dispose();first.dispose();second.dispose();
      }
   }
}
