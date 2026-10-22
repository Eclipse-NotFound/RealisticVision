"""Candidate 03: derive support and its complement together, retain exact rectangles."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output'
def transform(s):
 s=s.replace('private var support:Array=[];','private var support:Array=[];\n      private var supportComplement:Array=[];')
 s=s.replace('faces=[];support=[];heights=null;','faces=[];support=[];supportComplement=[];heights=null;')
 s=s.replace('rebuildClip(loc,onClip);','onClip.graphics.copyFrom(baseClip.graphics);')
 start=s.index('         var rectangles:Array=[],previous:Object={};',s.index('private function rebuildClip('))
 end=s.index('         clip.graphics.endFill();',start)
 s=s[:start]+'''         for each(var rect:Rectangle in supportComplement)
            clip.graphics.drawRect(ox+rect.x,oy+rect.y,rect.width,rect.height);
'''+s[end:]
 start=s.index('         support=[];',s.index('private function rebuildSupport('))
 end=s.index('\n      private function plain(',start)
 s=s[:start]+'''         support=[];supportComplement=[];
         var width:int=field.width,height:int=field.height;
         var pixels:Vector.<uint>=field.getVector(field.rect);
         var active:Vector.<int>=new Vector.<int>(width*height,true);
         // Dilate contiguous source runs by the same one-sample square halo.
         for(var y:int=0;y<height;y++){
            var x:int=0,row:int=y*width;
            while(x<width){
               if(!(pixels[row+x]>>>24)){x++;continue;}
               var begin:int=x;while(x<width && pixels[row+x]>>>24)x++;
               var lo:int=Math.max(0,begin-1),hi:int=Math.min(width,x+1);
               for(var yy:int=Math.max(0,y-1);yy<=Math.min(height-1,y+1);yy++)
                  for(var xx:int=lo,base:int=yy*width;xx<hi;xx++)active[base+xx]=1;
            }
         }
         // Emit the same maximal support rectangles and their positive
         // complement in one pass. Both masks share this geometry.
         var previous:Object={},outsidePrevious:Object={};
         for(y=0;y<height;y++){
            var current:Object={},outsideCurrent:Object={};x=0;row=y*width;
            while(x<width){
               var inside:int=active[row+x];begin=x;
               while(x<width && active[row+x]==inside)x++;
               var key:String=begin+":"+x;
               var prior:Object=inside?previous:outsidePrevious;
               var next:Object=inside?current:outsideCurrent;
               var list:Array=inside?support:supportComplement;
               var rect:Rectangle=prior[key] as Rectangle;
               if(rect!=null)rect.height+=STEP;
               else{rect=new Rectangle(begin*STEP,y*STEP,(x-begin)*STEP,STEP);list.push(rect);}
               next[key]=rect;
            }
            previous=current;outsidePrevious=outsideCurrent;
         }
      }
''' + s[end:]
 return s
if __name__=='__main__':
 dest=OUT/'candidate-03/src';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest)
 f=dest/'RVWallSurface.as';f.write_text(transform(f.read_text(encoding='utf-8-sig')),encoding='utf-8',newline='\n')
