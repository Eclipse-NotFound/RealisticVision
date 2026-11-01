package {
 import flash.display.*;import flash.geom.*;import flash.filesystem.*;import flash.desktop.NativeApplication;
 public class GeometryChecks extends Sprite {
  private var seed:uint=34567891;
  private function rnd():Number{seed=uint(seed*1664525+1013904223);return seed/4294967296;}
  private function room(kind:int):Object{
   var space:Array=[];
   for(var x:int=0;x<64;x++){space[x]=[];for(var y:int=0;y<48;y++)space[x][y]={opac:kind==0?0:kind==1?(y>=24?1:0):[0,0,.2,.49,.5,.98,.99,1][int(rnd()*8)]};}
   return {space:space,spaceX:64,spaceY:48};
  }
  public function GeometryChecks(){try{
   var old:BaselineFan=new BaselineFan(),candidate:CandidateFan=new CandidateFan(),entry:Object={};
   var checks:int=0,mutations:int=0,resets:int=0,loc:Object;
   for(var f:int=0;f<900;f++){
    if(f%300==0){loc=room(int(f/300));old.loc=candidate.loc=loc;}
    if(f%30==0){loc.space[24][22].opac=loc.space[24][22].opac?0:1;mutations++;}
    var radius:Number=[1,12,44.5,85,180,360,440][int(f/20)%7];
    var light:Object={x:880+(f%20)*3.75,y:920+(f%100>=80?.125*(f%10):0),radius:radius,angle:[0,.41,-Math.PI,Math.PI/2][int(f/20)%4],
       cone:[Math.PI*2,Math.PI*.58,Math.PI,Math.PI*2-.005,Math.PI*2-.011][int(f/20)%5],transient:int(f/20)%2==0};
    if(f%101==0){light.x=-.01;light.y=0;}
    var previous:BitmapData=entry.data,expected:BitmapData=old.makeLight(light),actual:BitmapData=candidate.makeLight(light,entry);
    if(previous && previous!==actual)previous.dispose();entry.data=actual;
    var difference:Object=expected.compare(actual);
    if(!(difference is uint&&uint(difference)==0)){save(expected,"baseline");save(actual,"candidate");throw new Error("geometry image f="+f+" "+JSON.stringify(light));}
    expected.dispose();checks++;
    if(f%37==0){entry.data.dispose();entry={};resets++;}
   }
   if(candidate.reuses<50)throw new Error("insufficient reuse "+candidate.reuses);
   if(entry.data)entry.data.dispose();
   trace("GEOMETRY CHECKS "+JSON.stringify({pixels:checks,reuses:candidate.reuses,terrainMutations:mutations,cacheResets:resets}));
   trace("GEOMETRY COMPLETE");NativeApplication.nativeApplication.exit(0);
  }catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function save(data:BitmapData,name:String):void{
   var root:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');
   if(root.indexOf('/RealisticVision/build/shot-light-output/')<0)throw new Error("wrong output");
   var fs:FileStream=new FileStream();try{fs.open(new File(root+'/evidence/'+name+'.png'),FileMode.WRITE);fs.writeBytes(data.encode(data.rect,new PNGEncoderOptions()));}finally{fs.close();}
  }
 }
}
