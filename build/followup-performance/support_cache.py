"""Candidate 02: preserve support/contour when the occupied field is identical."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output'
def transform(s):
 s=s.replace('private var field:BitmapData;','private var field:BitmapData;\n      private var supportShape:Vector.<uint>;')
 s=s.replace('         if(shapeDirty) {','         var geometryChanged:Boolean=shapeDirty;\n         if(shapeDirty) {',1)
 marker='            if(fieldChanged){\n               field.setVector(field.rect,shapeValues);'
 assert marker in s
 s=s.replace(marker,'''            var supportChanged:Boolean=reset || geometryChanged || supportShape==null;
            if(fieldChanged){
               if(!supportChanged)for(c=0;c<sampleCells.length;c++){
                  var sampleCell:int=sampleCells[c];
                  if(Boolean(shapeValues[sampleCell]>>>24)!=Boolean(supportShape[sampleCell]>>>24)){supportChanged=true;break;}
               }
               supportShape=shapeValues;
               field.setVector(field.rect,shapeValues);''',1)
 s=s.replace('if(fieldChanged){rebuildSupport();','if(fieldChanged && supportChanged){rebuildSupport();',1)
 s=s.replace('if(field!=null)field.dispose();field=null;','if(field!=null)field.dispose();field=null;supportShape=null;',1)
 return s
if __name__=='__main__':
 dest=OUT/'candidate-02/src';assert not dest.exists();shutil.copytree(OUT/'candidate-00/src',dest)
 f=dest/'RVWallSurface.as';f.write_text(transform(f.read_text(encoding='utf-8-sig')),encoding='utf-8',newline='\n')
