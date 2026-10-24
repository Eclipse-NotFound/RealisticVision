package {
 import flash.display.*;import flash.geom.*;import flash.filters.GlowFilter;import flash.desktop.NativeApplication;
 import fe.World;import fe.loc.Tile;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class IdentityLifecycleChecks extends Sprite {
  private var m:RealisticVisionMod=new RealisticVisionMod(),w:World,loc:MotionLocation,layer:Sprite=new Sprite(),passed:int=0;
  public function IdentityLifecycleChecks(){try{
   Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   w=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];addChild(layer);
   m.mswRegistered=true;m.resetRoom(w,loc);m.onFrameInner();if(!m.currentSight)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
   for each(var mode:String in ['current','classic'])for each(var cache:Boolean in [false,true]){
    m.cfgMode=mode;field(2);var v:Sprite=new Sprite();v.graphics.beginFill(0xff8844);v.graphics.drawRect(-4,-2,8,4);v.graphics.endFill();v.cacheAsBitmap=cache;v.y=200.7;layer.addChild(v);
    var found:Boolean=false;
    for(var x:int=10;x<880;x++){v.x=x+.3;m.applyWorldVisual(v);if(m.worldVisuals[v]&&m.worldVisuals[v].identity===true){found=true;break;}}
    check(found,'identity positive '+mode+'/'+cache);
    var rec:Object=m.worldVisuals[v];check(v.mask==null&&rec.shape.parent==null&&v.cacheAsBitmap,'identity retains raster cache');
    m.restoreWorldVisuals();check(v.mask==null&&v.cacheAsBitmap===cache&&m.worldVisuals[v]==null,'restore original cache preference');
    m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true,'identity reentry');
    v.filters=[new GlowFilter(0xffffff,1,20,20)];m.applyWorldVisual(v);check(m.worldVisuals[v].identity===false&&v.mask===m.worldVisuals[v].shape,'new root filter restores mask');
    v.filters=[];m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true,'remove root filter returns identity');
    var child:Sprite=new Sprite();child.filters=[new GlowFilter(0xffffff,1,20,20)];v.addChild(child);m.applyWorldVisual(v);check(m.worldVisuals[v].identity===false&&v.mask===m.worldVisuals[v].shape,'nested filter retains mask');v.removeChild(child);
    m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true,'identity after child removal');
    field(0);m.applyWorldVisual(v);check(m.worldVisuals[v]==null&&v.mask==null&&v.cacheAsBitmap===cache,'whole cell fully lit releases identity');
    field(2);m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true,'identity after field change');
    field(1);m.applyWorldVisual(v);check(m.worldVisuals[v].identity===false&&v.mask===m.worldVisuals[v].shape,'dark reentry attaches mask');
    field(2);m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true&&v.mask==null,'dark to identity removes mask');
    var external:Shape=new Shape();external.graphics.beginFill(0);external.graphics.drawRect(0,0,960,720);external.graphics.endFill();layer.addChild(external);v.mask=external;v.cacheAsBitmap=true;m.applyWorldVisual(v);
    check(v.mask===external&&v.cacheAsBitmap&&m.worldVisuals[v]==null,'third party mask and cache retained');
    v.mask=null;v.cacheAsBitmap=cache;layer.removeChild(external);m.applyWorldVisual(v);check(m.worldVisuals[v].identity===true,'identity after third party releases');
    m.resetRoom(w,loc);check(v.mask==null&&v.cacheAsBitmap===cache&&m.worldVisuals[v]==null,'room reset restores identity');layer.removeChild(v);
   }
   trace('LIFECYCLE COMPLETE passed='+passed);NativeApplication.nativeApplication.exit(0);
  }catch(e:Error){trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function field(state:int):void {
   m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,state==1?0:0xffffffff);m.fogCache.fillRect(m.fogCache.rect,state==1?0xff000000:0);
   if(state==2)for(var x:int=20;x<m.currentSight.width;x+=35){m.currentSight.fillRect(new Rectangle(x,0,17,m.currentSight.height),0);m.fogCache.fillRect(new Rectangle(x,0,17,m.fogCache.height),0xff000000);}
   m.currentSightData=null;m.classifiedSight=null;m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=4;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=4;m.fovVersion++;m.worldPass++;
  }
  private function check(ok:Boolean,label:String):void{if(!ok)throw new Error(label);passed++;trace('PASS '+label);}
 }
}
