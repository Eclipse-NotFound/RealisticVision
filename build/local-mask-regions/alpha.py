"""Independent candidate: compare only alpha for exact one-source coverage."""
from pathlib import Path
import shutil,json,hashlib
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/local-mask-regions-output'
target=OUT/'alpha-candidate/src';assert not target.exists();shutil.copytree(OUT/'baseline/src',target)
p=target/'RVWallSurface.as';s=p.read_text('utf8')
old='            if(!full)contourScratch.fillRect(contourScratch.rect,0);'
new='''            if(full){
               // One untransformed source covers every destination pixel. The
               // contour consumes alpha only; RGB changes cannot affect it.
               var onlyAlpha:BitmapData=patch.next;
               onlyAlpha.copyChannel(plan[0].data,plan[0].region,origin,BitmapDataChannel.ALPHA,BitmapDataChannel.ALPHA);
               var alphaDelta:Object=onlyAlpha.compare(patch.alpha);
               // A later composed/drawn source must refresh the RGB snapshot even
               // if it happens to equal a snapshot from before this fast path.
               patch.pixelsValid=false;
               if(!(alphaDelta is uint&&uint(alphaDelta)==0)){
                  var alphaSwap:BitmapData=patch.alpha;patch.alpha=onlyAlpha;patch.next=alphaSwap;
                  contourDirty=true;patch.runs=null;
                  if(alphaDelta is BitmapData)BitmapData(alphaDelta).dispose();
               }
               // ALPHA_ONLY_HIT
               continue;
            }
            if(!full)contourScratch.fillRect(contourScratch.rect,0);'''
assert s.count(old)==1;s=s.replace(old,new)
old='         var delta:Object=contourScratch.compare(patch.pixels);'
assert s.count(old)==1;s=s.replace(old,'         var delta:Object=patch.pixelsValid===false?null:contourScratch.compare(patch.pixels);')
old='         var swap:BitmapData=patch.pixels;patch.pixels=contourScratch;patch.scratch=swap;'
assert s.count(old)==1;s=s.replace(old,old+'patch.pixelsValid=true;')
p.write_text(s,'utf8',newline='\n')
(OUT/'alpha-candidate/sources.json').write_text(json.dumps({q.relative_to(target).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in target.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
print('Created independent alpha-only candidate')
