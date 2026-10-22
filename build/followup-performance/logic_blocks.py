"""Candidate 01: materialize canonical classic tiles in small reusable blocks."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output'
def transform(s):
 start=s.index('      private function classicLogicRegion(');end=s.index('      private function releaseClassicLogic(',start)
 part=s[start:end]
 marker='         if(fresh)\n         {\n'
 assert part.count(marker)==1
 part=part.replace(marker,marker+'''            // Adjacent masks share canonical samples. Batch a small tile block
            // without changing the samples, support gutter, or queried sight.
            var bx:int=Math.max(0,int(bounds.x/4)*4),by:int=Math.max(0,int(bounds.y/4)*4);
            var br:int=Math.min(this.spaceX,Math.ceil(bounds.right/4)*4);
            var bb:int=Math.min(this.spaceY,Math.ceil(bounds.bottom/4)*4);
            bounds=new Rectangle(bx,by,br-bx,bb-by);
            region=new Rectangle(FOG_PAD+bx*FOG_SUB,FOG_PAD+by*FOG_SUB,bounds.width*FOG_SUB,bounds.height*FOG_SUB);
''',1)
 return s[:start]+part+s[end:]
if __name__=='__main__':
 dest=OUT/'candidate-01/src';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest)
 f=dest/'RealisticVisionMod.as';f.write_text(transform(f.read_text(encoding='utf-8-sig')),encoding='utf-8',newline='\n')
