from pathlib import Path
import shutil
OUT=Path(__file__).resolve().parents[2]/'build/boundary-load-output'
if __name__=='__main__':
 dst=OUT/'candidate-03/src';assert not dst.exists();shutil.copytree(OUT/'candidate-02/src',dst)
 p=dst/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 edits=[
 ('private var currentSight:BitmapData;','private var currentSight:BitmapData;\n      private var currentSightWritten:Rectangle;'),
 ('this.currentSightData = null;','this.currentSightData = null;\n         this.currentSightWritten = null;'),
 ('this.currentSight = new BitmapData(this.fogCache.width,this.fogCache.height,true,0);','this.currentSight = new BitmapData(this.fogCache.width,this.fogCache.height,true,0);\n            this.currentSightWritten = null;'),
 ('var maskChanged:Boolean = false;\n            for each(var wi:int', 'var maskChanged:Boolean = false;\n            // Static native lighting can rewrite wall samples outside the view.\n            this.currentSightWritten = null;\n            for each(var wi:int'),
 ('this.currentSight.fillRect(this.currentSight.rect,0);','''// Every write in this pass lies in sceneBounds. Clear the previous
         // write extent, including camera jumps; all other pixels remain zero.
         // Room/allocation/static-wall changes invalidate the extent above.
         this.currentSight.fillRect(this.currentSightWritten==null?this.currentSight.rect:this.currentSightWritten,0);
         this.currentSightWritten=new Rectangle(FOG_PAD+sceneBounds.x*FOG_SUB,FOG_PAD+sceneBounds.y*FOG_SUB,
            sceneBounds.width*FOG_SUB,sceneBounds.height*FOG_SUB);''')]
 for old,new in edits:
  assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
 p.write_text(s,encoding='utf-8',newline='\n')
