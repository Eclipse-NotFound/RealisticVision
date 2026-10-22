"""Avoid rebuilding identical wall support; compare final shape, not FOV guesses."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var field:BitmapData;','private var field:BitmapData;\n      private var nextShape:BitmapData;\n      private var contourFieldVersion:int=-1;')
 s=s.replace('field=new BitmapData(cols*CELL/STEP,rows*CELL/STEP,true,0);','field=new BitmapData(cols*CELL/STEP,rows*CELL/STEP,true,0);\n               if(nextShape!=null)nextShape.dispose();nextShape=field.clone();')
 s=s.replace('            contourGeometryVersion++;','            contourGeometryVersion++;contourDirty=true;')
 s=s.replace('var value8:int=Math.round(alpha*intensity/255);','var value8:int=alpha==255?intensity:Math.round(alpha*intensity/255);')
 s=s.replace('            if(fieldChanged){\n               field.setVector(field.rect,shapeValues);','''            var supportChanged:Boolean=reset;
            if(fieldChanged){
               nextShape.setVector(nextShape.rect,shapeValues);
               var shapeDifference:Object=nextShape.compare(field);
               supportChanged=supportChanged || !(shapeDifference is uint && uint(shapeDifference)==0);
               if(shapeDifference is BitmapData)BitmapData(shapeDifference).dispose();
               field.copyPixels(nextShape,nextShape.rect,origin);''')
 old='if(fieldChanged){rebuildSupport();contourDirty=contourLayoutDirty=true;if(alwaysBright){rebuildPieces();rebuildClip(loc);}}'
 new='if(fieldChanged && supportChanged){rebuildSupport();contourDirty=contourLayoutDirty=true;if(alwaysBright){rebuildPieces();rebuildClip(loc);}}'
 assert old in s;s=s.replace(old,new)
 s=s.replace('if(field!=null)field.dispose();field=null;','if(field!=null)field.dispose();field=null;\n         if(nextShape!=null)nextShape.dispose();nextShape=null;contourFieldVersion=-1;')
 s=s.replace('contourDirty=true;\n         }\n         if(contourLayoutDirty)', 'contourDirty=true;contourFieldVersion=-1;\n         }\n         if(contourLayoutDirty)')
 s=s.replace('         contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);','''         if(contourFieldVersion!=fieldUpdates){
            contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);
            contourFieldVersion=fieldUpdates;
         }''')
 return s
if __name__=='__main__':
 dest=OUT/'candidate-02/src';assert not dest.exists();shutil.copytree(OUT/'candidate-01/src',dest)
 p=dest/'RVWallSurface.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
