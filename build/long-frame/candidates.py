"""D39: retain exact wall contour work when a camera cache translates."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/long-frame-output'
if __name__=='__main__':
 dst=OUT/'candidate-01/src';assert not dst.exists();shutil.copytree(OUT/'candidate-00/src',dst)
 p=dst/'RVWallSurface.as';s=p.read_text(encoding='utf-8-sig')
 s=s.replace('var reset:Boolean = owner !== loc', '''var oldHeights:Vector.<int>=heights;
         var oldLeft:int=left,oldTop:int=top,oldCols:int=cols,oldRows:int=rows;
         var terrainChanged:Boolean=owner!==loc;
         var reset:Boolean = owner !== loc''')
 s=s.replace('contourDirty=contourLayoutDirty=true;\n         }\n         // One-cell', '''// Keep patches in the same world location when the viewport origin
            // changes. Cached runs are local coordinates, so translate those too.
            var dx:int=(oldLeft-left)*CELL,dy:int=(oldTop-top)*CELL;
            if(!terrainChanged && (dx!=0 || dy!=0))for each(var movedPatch:Object in contourPieces){
               movedPatch.rect.offset(dx,dy);
               var movedRuns:Vector.<int>=movedPatch.runs as Vector.<int>;
               if(movedRuns!=null)for(var ri:int=0;ri<movedRuns.length;ri+=5){movedRuns[ri]+=dx;movedRuns[ri+1]+=dy;}
            }
            contourDirty=contourLayoutDirty=true;
         }
         // One-cell''')
 s=s.replace('if(heights[index]!=h){shapeDirty=true;heights[index]=h;}', '''if(reset){
               if(oldHeights!=null && x>=oldLeft-1 && x<=oldLeft+oldCols && y>=oldTop-1 && y<=oldTop+oldRows
                  && oldHeights[x-oldLeft+1+(y-oldTop+1)*(oldCols+2)]!=h)terrainChanged=true;
            }else if(heights[index]!=h)terrainChanged=true;
            if(heights[index]!=h){shapeDirty=true;heights[index]=h;}''')
 s=s.replace('contourGeometryVersion++;\n            // Drop', 'if(terrainChanged)contourGeometryVersion++;\n            // Drop')
 s=s.replace('for each(var stalePatch:Object in contourPieces)stalePatch.runs=null;', 'if(terrainChanged)for each(var stalePatch:Object in contourPieces)stalePatch.runs=null;')
 p.write_text(s,encoding='utf-8',newline='\n')

def bright_guard():
 dst=OUT/'candidate-02/src';assert not dst.exists();shutil.copytree(OUT/'candidate-01/src',dst)
 p=dst/'RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=s.replace('var terrainChanged:Boolean=owner!==loc;', 'var terrainChanged:Boolean=owner!==loc || (alwaysBright && bounds!=null && !bounds.equals(view));')
 p.write_text(s,encoding='utf-8',newline='\n')

def sample_kernel():
 dst=OUT/'candidate-03/src';assert not dst.exists();shutil.copytree(OUT/'candidate-02/src',dst)
 p=dst/'RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=s.replace('private var sampleStarts:', '''// Faces always lie on the 5px sampling grid. The same two kernels
      // are reused at every face, preserving the original rounding exactly.
      private var kernelOffsets:Array=[];
      private var kernelAlphas:Array=[];
      private var sampleStarts:''')
 s=s.replace('wallPixels.mouseEnabled=wallPixels.mouseChildren=false;', '''wallPixels.mouseEnabled=wallPixels.mouseChildren=false;
         for each(var sign:int in [1,-1]){
            var offsets:Vector.<int>=new Vector.<int>(),alphas:Vector.<int>=new Vector.<int>();
            var low:int=Math.floor(-(sign>0?FRINGE:DEPTH)/STEP),high:int=Math.ceil((sign>0?DEPTH:FRINGE)/STEP);
            for(var q:int=low;q<high;q++){
               var distance:Number=(q+0.5)*STEP*sign;
               if(distance < -FRINGE || distance>=DEPTH)continue;
               var alpha:int=distance<=BRIGHT?255:Math.round(255*(DEPTH-distance)/(DEPTH-BRIGHT));
               if(distance<0)alpha=Math.round(alpha*Math.min(1,(distance+FRINGE)/STEP));
               offsets.push(q);alphas.push(alpha);
            }
            kernelOffsets.push(offsets);kernelAlphas.push(alphas);
         }''')
 start=s.index('         sampleStarts=new Vector.<int>();',s.index('private function rebuildSamples'))
 end=s.index('\n      }',start)
 s=s[:start]+'''         var faceCount:int=faces.length/5,capacity:int=faceCount*Vector.<int>(kernelOffsets[0]).length;
         sampleStarts=new Vector.<int>(faceCount+1);samplePixels=new Vector.<int>(capacity);sampleAlphas=new Vector.<int>(capacity);
         sampleCells=new Vector.<int>();floorValues=new Vector.<uint>(field.width*field.height,true);
         var registered:Vector.<Boolean>=new Vector.<Boolean>(floorValues.length,true);
         var write:int=0,width:int=field.width,height:int=field.height;
         for(var i:int=0;i<faces.length;i+=5){
            sampleStarts[int(i/5)]=write;
            var wx:Number=faces[i],wy:Number=faces[i+1],dir:int=faces[i+2];
            var vertical:Boolean=dir>=2,k:int=(dir==0||dir==2)?0:1;
            var offsets:Vector.<int>=kernelOffsets[k],alphas:Vector.<int>=kernelAlphas[k];
            var along:int=Math.floor(((vertical?wy:wx)-(vertical?top:left)*CELL)/STEP);
            var edge:int=((vertical?wx:wy)-(vertical?left:top)*CELL)/STEP;
            for(var q:int=0;q<offsets.length;q++){
               var across:int=edge+offsets[q];
               var px:int=vertical?across:along,py:int=vertical?along:across;
               if(px<0||py<0||px>=width||py>=height)continue;
               var cell:int=px+py*width;
               samplePixels[write]=cell;sampleAlphas[write]=alphas[q];write++;
               if(!registered[cell]){registered[cell]=true;sampleCells.push(cell);}
            }
         }
         sampleStarts[faceCount]=write;samplePixels.length=sampleAlphas.length=write;'''+s[end:]
 p.write_text(s,encoding='utf-8',newline='\n')

def durable_invalidation():
 dst=OUT/'candidate-04/src';assert not dst.exists();shutil.copytree(OUT/'candidate-03/src',dst)
 p=dst/'RVWallSurface.as';s=p.read_text(encoding='utf-8')
 s=s.replace('private var shapeDirty:Boolean = true;', 'private var shapeDirty:Boolean = true;\n      private var terrainDirty:Boolean = true;')
 s=s.replace('var terrainChanged:Boolean=owner!==loc', 'var terrainChanged:Boolean=terrainDirty || owner!==loc')
 s=s.replace('var reset:Boolean = owner !== loc', 'terrainDirty=terrainChanged;\n         var reset:Boolean = owner !== loc')
 s=s.replace(')]!=h)terrainChanged=true;', ')]!=h)terrainDirty=terrainChanged=true;')
 s=s.replace('else if(heights[index]!=h)terrainChanged=true;', 'else if(heights[index]!=h)terrainDirty=terrainChanged=true;')
 s=s.replace('shapeDirty=false;', 'shapeDirty=terrainDirty=false;')
 s=s.replace('owner=null;bounds=null;shapeDirty=fieldShapeDirty=lightDirty=true;', 'owner=null;bounds=null;terrainDirty=shapeDirty=fieldShapeDirty=lightDirty=true;')
 p.write_text(s,encoding='utf-8',newline='\n')
