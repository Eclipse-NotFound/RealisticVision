from pathlib import Path
import re,json
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/overall-flow/measure.py').read_text(encoding='utf-8').replace('overall-flow-output','boundary-load-output')
s=s[:s.rindex("\nif __name__=='__main__':")]
exec(compile(s,str(HERE/'measure.py'),'exec'),globals())
base_build=build
def build(name,candidate,verify=False,profile=False,live=False,native=False,wide=False):
 previous=inv.r.runner.compile
 def compile_probe(entry,*args,**kwargs):
  if 'stress' in name and entry.name=='RecoveryFrameProbeMod.as':
   text=entry.read_text(encoding='utf-8');cases=[]
   for mode in ['classic','current']:
    for count,speed in [(0,36),(24,36),(96,0),(96,4),(96,36)]:cases.append({'mode':mode,'dense':count>0,'bright':False,'dim':.35,'count':count,'speed':speed})
   text=re.sub(r'private var cases:Array=.*?;', 'private var cases:Array='+json.dumps(cases)+';',text,count=1)
   text=text.replace('w.loc.units=c.dense?testUnits:[]','w.loc.units=testUnits.slice(0,c.count)')
   text=text.replace('u.vis.visible=c.dense','u.vis.visible=testUnits.indexOf(u)<c.count')
   text=text.replace('360+p*(LARGE?12:4)','360+(p*cases[caseIndex].speed)%1440')
   text=text.replace('if(++frame<120)','if(++frame<80)')
   entry.write_text(text,encoding='utf-8',newline='\n')
  if 'extent' in name and entry.name=='RecoveryFrameProbeMod.as':
   text=entry.read_text(encoding='utf-8')
   text=re.sub(r'private var cases:Array=.*?;', 'private var cases:Array=[{mode:"current",dense:true,bright:false,dim:.35}];',text,count=1)
   text=text.replace('if(++frame<120)','if(++frame<32)')
   text=text.replace('if(VERIFY&&frame>=0&&frame%15==0)verify(w);','if(VERIFY&&frame>=0&&frame%15==0){verify(w);verifyExtent(w);}')
   marker='      private function verify(w:*):void{'
   probe='''      private function verifyExtent(w:*):void {
         var a:*=mods[0],b:*=mods[1],view:Rectangle=b.scenePaintBounds(),wi:int=-1;
         for each(var n:int in b.wallTiles)if(n%b.spaceX>view.right+4 && n%b.spaceX<b.spaceX-2 && int(n/b.spaceX)>1 && int(n/b.spaceX)<b.spaceY-2){wi=n;break;}
         if(wi<0)throw new Error("offscreen wall fixture missing");
         var tx:int=wi%b.spaceX,ty:int=int(wi/b.spaceX),saved:Array=[],savedState:Array=[];
         for(var y:int=ty;y<=ty+1;y++)for(var x:int=tx;x<=tx+1;x++){var tile:*=w.loc.getTile(x,y);saved.push([tile,tile.visi]);tile.visi=1;}
         try {
            for each(var m:* in mods){
               savedState.push([m,wi,m.fov[wi]]);m.fov[wi]=1;
               for(y=ty;y<=ty+1;y++)for(x=tx;x<=tx+1;x++){n=x+y*m.spaceX;savedState.push([m,n,null,m.memCur[n]]);m.memCur[n]=0;}
               m.wallGeometryDirty=true;m.applyVision(w,w.loc,false,true);
            }
            var pixelX:int=4+tx*8,pixelY:int=4+ty*8;
            if(a.currentSight.getPixel32(pixelX,pixelY)==0 || b.currentSightWritten!=null)throw new Error("static offscreen write not exercised");
            if(!equal(a.currentSight,b.currentSight))throw new Error("static wall sight mismatch");
            for each(m in mods)m.fillFogCache(w.loc);
            if(!equal(a.currentSight,b.currentSight) || b.currentSight.getPixel32(pixelX,pixelY)!=0)throw new Error("stale offscreen sight after clear");
            result.checks.push({frame:frame,exact:true,kind:"offscreen lighting invalidates and clears"});
            trace("PASS offscreen sight extent "+frame);
         } finally {for each(var item:Array in saved)item[0].visi=item[1];for each(item in savedState){if(item.length==3)item[0].fov[item[1]]=item[2];else item[0].memCur[item[1]]=item[3];}for each(m in mods)m.lastGX=-99999;}
      }
'''
   assert text.count(marker)==1;text=text.replace(marker,probe+marker);entry.write_text(text,encoding='utf-8',newline='\n')
  return previous(entry,*args,**kwargs)
 inv.r.runner.compile=compile_probe
 try:return base_build(name,candidate,verify,profile,live,native,wide)
 finally:inv.r.runner.compile=previous
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run']);a.add_argument('name');a.add_argument('--candidate',default='candidate-00');a.add_argument('--profile',action='store_true');a.add_argument('--verify',action='store_true');a.add_argument('--wide',action='store_true');x=a.parse_args()
 build(x.name,x.candidate,x.verify,x.profile,False,False,x.wide) if x.action=='build' else run(x.name)
