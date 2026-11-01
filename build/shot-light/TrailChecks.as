package {
 import flash.display.*;import flash.geom.*;import flash.utils.getTimer;import flash.filesystem.*;import flash.desktop.NativeApplication;
 public class TrailChecks extends Sprite {
  private var a:BaselineTrail=new BaselineTrail(),b:CandidateTrail=new CandidateTrail();
  private var seed:uint=123456789,passed:int=0,rayChecks:int=0,pixelChecks:int=0,limitedCases:int=0;
  private function rnd():Number {seed=uint(seed*1664525+1013904223);return seed/4294967296;}
  private function check(ok:Boolean,label:String):void {if(!ok)throw new Error(label);passed++;}
  private function room(kind:int):Object {
   var w:int=64,h:int=48,space:Array=[];
   for(var x:int=0;x<w;x++){space[x]=[];for(var y:int=0;y<h;y++){
    var op:Number=kind==0?0:kind==1?((x%7==0&&y%5!=0)?1:0):[0,0,.2,.49,.5,.98,.99,1][int(rnd()*8)];
    space[x][y]={opac:op};
   }}
   return {spaceX:w,spaceY:h,space:space};
  }
  public function TrailChecks(){try{
   var scratch:BitmapData=new BitmapData(4,4,false,0);
   for(var kind:int=0;kind<3;kind++){
    var loc:Object=room(kind);a.render(scratch,new Rectangle(0,0,48,48),12,loc,[]);b.render(scratch,new Rectangle(0,0,48,48),12,loc,[]);
    for(var n:int=0;n<30000;n++){
     var cx:int=int(rnd()*66)-1,cy:int=int(rnd()*50)-1,sx:Number=cx*40+rnd()*40,sy:Number=cy*40+rnd()*40;
     var ex:Number=sx+(rnd()-.5)*360,ey:Number=sy+(rnd()-.5)*360,flavor:int=n%8;
     if(flavor==1){ex=cx*40+rnd()*40;ey=cy*40+rnd()*40;}
     if(flavor==2){ex=(cx+(n%2?1:-1))*40+rnd()*40;ey=cy*40+rnd()*40;}
     if(flavor==3){ex=cx*40+rnd()*40;ey=(cy+(n%2?1:-1))*40+rnd()*40;}
     if(flavor==4){sx=cx*40;sy=cy*40;ex=sx+(rnd()-.5)*80;ey=sy+(rnd()-.5)*80;}
     if(flavor==5){ex=Math.floor(ex/40)*40;ey=Math.floor(ey/40)*40;}
     if(flavor==6){sx=cx*40+20;sy=cy*40+20;ex=sx+40;ey=sy+40+[0,.000001,-.000001,.00004,-.00004][n%5];}
     if(flavor==7){ex=(cx+1)*40+[0,1e-8,-1e-8][n%3];ey=cy*40+[0,1e-8,-1e-8][n%3];}
     var av:Boolean=a.visible(loc,sx,sy,ex,ey),bv:Boolean=b.visible(loc,sx,sy,ex,ey);
     if(av!=bv)throw new Error("ray "+JSON.stringify({kind:kind,n:n,start:[sx,sy],end:[ex,ey],old:av,candidate:bv}));
     rayChecks++;
    }
   }
   scratch.dispose();
   for(var f:int=0;f<180;f++){
    loc=room(f%3);
    var width:int=f%15==0?384:[48,96,128][f%3],height:int=f%15==0?160:[40,72,96][f%3],cell:int=[12,5,17][int(f/3)%3];
    var bounds:Rectangle=new Rectangle((f%5)*40+[0,.3,-.3][f%3],(f%7)*40+[0,.7,-.7][f%3],width*cell,height*cell);
    var lights:Array=makeLights(f,bounds);
    var first:BitmapData=new BitmapData(width,height,false,0x182839+(f%20)*0x020101);
    var second:BitmapData=first.clone();
    if(f==90){a.epoch=b.epoch=0xffffffff;}
    a.render(first,bounds,cell,loc,lights);b.render(second,bounds,cell,loc,lights);
    var d:Object=first.compare(second);
    if(!(d is uint&&uint(d)==0)){save(first,"baseline");save(second,"candidate");throw new Error("pixel f="+f+" diff="+String(BitmapData(d).getColorBoundsRect(0xffffffff,0,false)));}
    pixelChecks++;check(a.visits==b.visits&&a.rays==b.rays&&a.painted==b.painted&&a.limited==b.limited,"budget and sample counts f="+f);
    if(a.limited)limitedCases++;
    first.dispose();second.dispose();
    if(f%20==0){a.clear();b.clear();check(b.rayTerrain==null,"room reference released");}
   }
   check(b.fastSame>100&&b.fastAdjacent>100,"short paths exercised");check(limitedCases>0,"budget exercised");
   trace("TRAIL CHECKS "+JSON.stringify({passed:passed,rays:rayChecks,pixels:pixelChecks,limited:limitedCases,same:b.fastSame,adjacent:b.fastAdjacent}));
   benchmark();
   trace("TRAIL COMPLETE");NativeApplication.nativeApplication.exit(0);
  }catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
  private function makeLights(f:int,bounds:Rectangle):Array {
   var lights:Array=[],count:int=f%15==0?30:[4,24,96][f%3];
   for(var k:int=0;k<count;k++){
    var segments:Array=[],n:int=f%15==0?4:1+k%4;
    for(var j:int=0;j<n;j++){
     var ax:Number=bounds.x+rnd()*bounds.width,ay:Number=bounds.y+rnd()*bounds.height;
     var bx:Number=ax+(rnd()-.5)*800,by:Number=ay+(rnd()-.5)*500,radius:Number=[3,12,24,48,90,120][(k+j)%6];
     if(f%15==0){ax=bounds.x;bx=bounds.right;ay=by=bounds.y+bounds.height*(k%6)/6;radius=120;}
     if(k==0&&f%9==0)radius=[0,-1,121,NaN,Infinity][f%5];
     if(k==1&&f%11==0)bx=NaN;
     segments.push({ax:ax,ay:ay,bx:bx,by:by,width:radius,tail:[0,.1,.45,.8][j%4],head:[1,.4,.8][k%3]});
    }
    lights.push({trail:segments,color:uint(rnd()*0xffffff),power:[0,.001,.01,.4,1,3][k%6]});
   }
   return lights;
  }
  private function benchmark():void {
   var loc:Object=room(0),bounds:Rectangle=new Rectangle(120,80,1536,1152),target:BitmapData=new BitmapData(128,96,false,0x202020);
   var all:Array=[];for(var i:int=0;i<24;i++)all.push(makeLights(i,bounds));
   var rows:Array=[];
   for each(var which:int in [0,1,1,0]){
    var object:*=which?b:a;
    for(i=0;i<24;i++)object.render(target,bounds,12,loc,all[i]);
    var started:int=getTimer();
    for(i=0;i<240;i++)object.render(target,bounds,12,loc,all[i%24]);
    rows.push({candidate:which==1,totalMs:getTimer()-started,iterations:240});
   }
   trace("TRAIL BENCH "+JSON.stringify(rows));target.dispose();
  }
  private function save(bd:BitmapData,name:String):void {
   var root:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');
   if(root.indexOf('/RealisticVision/build/shot-light-output/')<0)throw new Error("wrong output");
   var fs:FileStream=new FileStream();try{fs.open(new File(root+'/evidence/'+name+'.png'),FileMode.WRITE);fs.writeBytes(bd.encode(bd.rect,new PNGEncoderOptions()));}finally{fs.close();}
  }
 }
}
