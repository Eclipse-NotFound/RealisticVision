package {
 import flash.display.*;import flash.geom.*;import flash.desktop.NativeApplication;
 import fe.World;import fe.graph.Grafon;import fe.unit.Pers;import fe.loc.Tile;
 public class FogChecks extends Sprite {
  private var passed:int=0,a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod();
  public function FogChecks(){try{run();trace('FOG COMPLETE passed='+passed);NativeApplication.nativeApplication.exit(0);}catch(e:Error){trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function world():World {var w:World=new World();w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.pers=new Pers();w.cam={vx:0,vy:0,scaleV:1,screenX:640,screenY:400};return w;}
  private function draw(m:*,w:World):BitmapData {
   var out:BitmapData=new BitmapData(640,400,false,0xabcde1),node:Sprite=m.fogVis,old:DisplayObjectContainer=node.parent,slot:int=old.getChildIndex(node),wrap:Sprite=new Sprite();wrap.addChild(node);
   try{out.draw(wrap,new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,w.cam.vx,w.cam.vy),null,null,null,true);}finally{old.addChildAt(node,slot);}return out;
  }
  private function run():void {
   Tile.tileX=Tile.tileY=40;var wa:World=world(),wb:World=world();
   for(var f:int=0;f<120;f++){
    var wide:Boolean=int(f/30)%2==1;
    for each(var m:* in [a,b]){
     var w:World=m===a?wa:wb;World.w=w;
     m.spaceX=wide?72:20;m.spaceY=wide?40:12;m.cfgMode=int(f/10)%2?'classic':'current';
     w.pers.infravis=int(f/5)%2;w.cam.scaleV=[.5,1,1.25][int(f/4)%3];w.cam.vx=-40*int(f/3);w.cam.vy=-40*int(f/7);
     if(m.fogVis&&f%4==1){
      m.fogVis.visible=false;m.fogBitmap.visible=false;m.fogVis.scrollRect=new Rectangle(17,19,211,113);m.fogShadow.scrollRect=null;
      m.fogVis.x=19;m.fogShadow.y=21;m.fogShadow.transform.colorTransform=new ColorTransform(.5,.6,.7,.8,1,2,3,4);m.fogShadow.blendMode='add';m.wallBmp.mask=new Shape();
     }
     m.ensureFog(w);
     m.fogBmp.fillRect(m.fogBmp.rect,0x68335577);m.wallRaw.fillRect(m.wallRaw.rect,0x93554422);m.classicWallShade.fillRect(m.classicWallShade.rect,0x49271144);
     m.floorClip.graphics.clear();m.floorClip.graphics.beginFill(0xffffff);m.floorClip.graphics.drawRect(0,0,m.spaceX*40,m.spaceY*40);m.floorClip.graphics.endFill();
     m.wallClip.graphics.clear();m.wallClip.graphics.beginFill(0xffffff);m.wallClip.graphics.drawRect(100,60,400,180);m.wallClip.graphics.endFill();
     if(!m.fogVis.visible||!m.fogBitmap.visible||m.wallBmp.mask!=null||m.fogShadow.blendMode!=(w.pers.infravis?'multiply':'normal'))throw new Error('property recovery '+f);
    }
    var ca:BitmapData=draw(a,wa),cb:BitmapData=draw(b,wb),delta:Object=ca.compare(cb);
    if(!(delta is uint&&uint(delta)==0))throw new Error('exact full fog '+f);
    passed++;ca.dispose();cb.dispose();
   }
  }
 }
}
