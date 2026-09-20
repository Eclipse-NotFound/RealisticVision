package {
  import flash.display.*;
  import flash.geom.*;
  import flash.utils.*;
  public class MotionCapture {
    public static function run(w:*,modClass:Class,stageFPS:Number,capture:Boolean=true):void {
      var loc:*=w.loc;w.black=true;loc.black=true;loc.base=false;w.gg.setPos(480,640);
      var m:*=new modClass();m.mswRegistered=true;m.cfgMode="current";
      var nativeBefore:Array=[],tiles:Array=[];
      for(var y:int=0;y<loc.spaceY;y++)for(var x:int=0;x<loc.spaceX;x++){
        var t:*=loc.getTile(x,y);nativeBefore.push([t.visi,t.t_visi]);tiles.push({x:x,y:y,opac:t.opac,phis:t.phis,water:t.water,visi:t.visi});
      }
      for(var warm:int=0;warm<40;warm++){m.frameCount++;m.onFrameInner();}
      var frames:Array=[],captures:Array=[],last:BitmapData=m.fogBmp.clone(),frozen:int=0,maxFrozen:int=0,updates:int=0;
      for(var f:int=0;f<90;f++){
        w.gg.setPos(480+4*(f+1),640);var oldV:int=m.fovVersion;
        m.motionPerf={};m.motionRays=0;m.motionTiles=0;
        var start:int=getTimer();m.frameCount++;m.onFrameInner();var cost:int=getTimer()-start;
        var diff:Object=m.fogBmp.compare(last),same:Boolean=diff is uint && uint(diff)==0;
        if(diff is BitmapData)BitmapData(diff).dispose();last.dispose();last=m.fogBmp.clone();
        if(same)frozen++;else{maxFrozen=Math.max(maxFrozen,frozen);frozen=0;updates++;}
        frames.push({f:f,x:w.gg.X,eye:m.eyeX,ms:cost,recomputed:m.fovVersion!=oldV,changed:!same,pending:m.fogBlurPending,perf:m.motionPerf,rays:m.motionRays,tiles:m.motionTiles});
        if(capture && f<24){var b:BitmapData=new BitmapData(loc.spaceX*40,loc.spaceY*40,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);captures.push(b);}
      }
      var mutations:int=0;
      for(y=0;y<loc.spaceY;y++)for(x=0;x<loc.spaceX;x++){
        t=loc.getTile(x,y);var old:Array=nativeBefore[x+y*loc.spaceX];if(t.visi!==old[0]||t.t_visi!==old[1])mutations++;
      }
      if(mutations)throw Error("native brightness changed "+mutations);
      trace("MOTION_GAME "+(maxFrozen>1?"RED":"GREEN")+" frozen="+maxFrozen+" updates="+updates+"/90 stageFPS="+stageFPS+" room="+loc.spaceX+"x"+loc.spaceY+" mutations="+mutations);
      trace("DATA "+JSON.stringify({frames:frames,maxFrozen:maxFrozen,updates:updates,worldStep:4,stageFPS:stageFPS,width:loc.spaceX,height:loc.spaceY,room:loc.id,tiles:tiles,dist1:loc.lDist1,dist2:loc.lDist2,mutations:mutations}));
      for(f=0;f<captures.length;f++){emit("frame-"+(f<10?"0":"")+f,captures[f]);captures[f].dispose();}
      last.dispose();m.restoreAll(w,loc);
      if(m.fogVis.parent)m.fogVis.parent.removeChild(m.fogVis);
      trace("MOTION_GAME COMPLETE");
    }
    private static function emit(name:String,b:BitmapData):void {
      var a:ByteArray=b.encode(b.rect,new PNGEncoderOptions()),parts:Array=[],table:Array=[];
      for(var i:int=0;i<256;i++)table[i]=(i<16?"0":"")+i.toString(16);
      for(i=0;i<a.length;i++)parts.push(table[a[i]]);
      trace("PNG "+name+" "+parts.join(""));
    }
  }
}
