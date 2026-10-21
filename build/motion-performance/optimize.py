"""D33 trial: preserve contour runs exactly, cache unchanged patch runs."""
from pathlib import Path
import argparse,shutil
import run

def prepare(no_cache=False,packed=False):
    source=run.OUT/'baseline/src/RVWallSurface.as'
    s=source.read_text(encoding='utf-8-sig')
    s=s.replace('      private var seen:Vector.<int>', '      private var contourGeometryVersion:uint = 0;\n      private var seen:Vector.<int>')
    s=s.replace('         if(shapeDirty) {\n            fieldShapeDirty=true;', '         if(shapeDirty) {\n            contourGeometryVersion++;\n            fieldShapeDirty=true;')
    s=s.replace('swap=patch.alpha;patch.alpha=nextAlpha;patch.next=swap;contourDirty=true;', 'swap=patch.alpha;patch.alpha=nextAlpha;patch.next=swap;contourDirty=true;patch.runs=null;')
    begin=s.index('            var pixels:Vector.<uint>=patch.alpha.getVector(patch.alpha.rect),w:int=patch.alpha.width;')
    end=s.index('            for each(rect in rectangles){',begin)
    s=s[:begin]+'''            // A patch's material alpha and tile heights fully determine its
            // contour. Exploration can change the surrounding support without
            // changing this patch; keep exactly the same maximal row runs.
            var rectangles:Array=patch.runs as Array;
            var rect:Object;
            if(rectangles==null || patch.geometryVersion!=contourGeometryVersion){
               rectangles=[];
               var pixels:Vector.<uint>=patch.alpha.getVector(patch.alpha.rect);
               var w:int=patch.alpha.width, ax:int=area.x, right:int=area.right;
               var previous:Object={},row:int=0;
               for(var y:int=area.top;y<area.bottom;y++,row+=w){
                  var current:Object={},start:int=ax,x:int=ax,role:int=-1;
                  var tileEnd:int=ax,tileRole:int=2;
                  var tileRow:int=(int(y/CELL)+1)*(cols+2),subY:int=y%CELL;
                  for(var offset:int=0;x<right;x++,offset++){
                     if(x>=tileEnd){
                        var tileX:int=int(x/CELL);
                        tileEnd=(tileX+1)*CELL;
                        var h:int=heights[tileX+1+tileRow];
                        tileRole=h>0 && subY>=CELL-h?0:2;
                     }
                     var nextRole:int=(pixels[row+offset]>>>24)>0?1:tileRole;
                     if(nextRole!=role){
                        if(role>=0){
                           var key:String=start+":"+x+":"+role;
                           rect=previous[key];
                           if(rect!=null)rect.h++;
                           else{rect={x:start,y:y,w:x-start,h:1,role:role};rectangles.push(rect);}
                           current[key]=rect;
                        }
                        start=x;role=nextRole;
                     }
                  }
                  key=start+":"+x+":"+role;rect=previous[key];
                  if(rect!=null)rect.h++;
                  else{rect={x:start,y:y,w:x-start,h:1,role:role};rectangles.push(rect);}
                  current[key]=rect;
                  previous=current;
               }
               patch.runs=rectangles;patch.geometryVersion=contourGeometryVersion;
            }
''' + s[end:]
    assert s.count('contourGeometryVersion++;')==1
    if no_cache:
        s=s.replace('      private var contourGeometryVersion:uint = 0;\n','')
        s=s.replace('            contourGeometryVersion++;\n','')
        s=s.replace(';patch.runs=null;',';')
        s=s.replace('            var rectangles:Array=patch.runs as Array;','            var rectangles:Array=null;')
        s=s.replace('if(rectangles==null || patch.geometryVersion!=contourGeometryVersion){','if(rectangles==null){')
        s=s.replace('               patch.runs=rectangles;patch.geometryVersion=contourGeometryVersion;\n','')
        s=s.replace('''            // A patch's material alpha and tile heights fully determine its
            // contour. Exploration can change the surrounding support without
            // changing this patch; keep exactly the same maximal row runs.''','''            // Scan alpha linearly and read tile height only at cell boundaries.
            // Emit the same maximal runs as contourRole, without retaining
            // another copy of the rectangle graph between rebuilds.''')
    if packed:
        begin=s.index('      private function buildContourClip(');end=s.index('      private function contourRole(',begin)
        part=s[begin:end]
        part=part.replace('var rectangles:Array=patch.runs as Array;','var rectangles:Vector.<int>=patch.runs as Vector.<int>;')
        part=part.replace('var rect:Object;','var rectangleIndex:int;')
        part=part.replace('rectangles=[];','rectangles=new Vector.<int>();')
        part=part.replace('''                           rect=previous[key];
                           if(rect!=null)rect.h++;
                           else{rect={x:start,y:y,w:x-start,h:1,role:role};rectangles.push(rect);}
                           current[key]=rect;''','''                           rectangleIndex=int(previous[key])-1;
                           if(rectangleIndex>=0)rectangles[rectangleIndex+3]++;
                           else{rectangleIndex=rectangles.length;rectangles.push(start,y,x-start,1,role);}
                           current[key]=rectangleIndex+1;''')
        part=part.replace('''                  key=start+":"+x+":"+role;rect=previous[key];
                  if(rect!=null)rect.h++;
                  else{rect={x:start,y:y,w:x-start,h:1,role:role};rectangles.push(rect);}
                  current[key]=rect;''','''                  key=start+":"+x+":"+role;rectangleIndex=int(previous[key])-1;
                  if(rectangleIndex>=0)rectangles[rectangleIndex+3]++;
                  else{rectangleIndex=rectangles.length;rectangles.push(start,y,x-start,1,role);}
                  current[key]=rectangleIndex+1;''')
        part=part.replace('''            for each(rect in rectangles){
               var shape:Shape=rect.role==0?airClip:baseClip;
               shape.graphics.drawRect(left*CELL+rect.x,top*CELL+rect.y,rect.w,rect.h);
               if(rect.role!=0){shape=rect.role==1?solidClip:onClip;shape.graphics.drawRect(left*CELL+rect.x,top*CELL+rect.y,rect.w,rect.h);}
            }''','''            for(rectangleIndex=0;rectangleIndex<rectangles.length;rectangleIndex+=5){
               role=rectangles[rectangleIndex+4];
               var shape:Shape=role==0?airClip:baseClip;
               var drawX:int=left*CELL+rectangles[rectangleIndex],drawY:int=top*CELL+rectangles[rectangleIndex+1];
               var drawWidth:int=rectangles[rectangleIndex+2],drawHeight:int=rectangles[rectangleIndex+3];
               shape.graphics.drawRect(drawX,drawY,drawWidth,drawHeight);
               if(role!=0){shape=role==1?solidClip:onClip;shape.graphics.drawRect(drawX,drawY,drawWidth,drawHeight);}
            }''')
        assert 'rect.' not in part
        s=s[:begin]+part+s[end:]
        s=s.replace('            contourGeometryVersion++;','''            contourGeometryVersion++;
            // Drop obsolete runs before rebuilding geometry. Packed integers
            // avoid keeping thousands of rectangle objects alive in the cache.
            for each(var stalePatch:Object in contourPieces)stalePatch.runs=null;''')
    (run.OUT/'candidate/src/RVWallSurface.as').write_text(s,encoding='utf-8')
    p=run.OUT/'baseline/src/RealisticVisionMod.as'
    s=p.read_text(encoding='utf-8-sig')
    marker='''            for(var sy:int = 0; sy < FOG_SUB; sy++) for(var sx:int = 0; sx < FOG_SUB; sx++)
            {
               var fx:Number = (sx+0.5)/FOG_SUB, fy:Number = (sy+0.5)/FOG_SUB;'''
    assert s.count(marker)==1
    s=s.replace(marker,'''            // fogBmp already contains fogRaw's integer red channel here.
            // When every correction is zero, the old 64-pixel loop merely
            // writes those same bytes back. Keep the exact existing image.
            var noCorrection:Boolean=d00==0 && d10==0 && d01==0 && d11==0;
            if(noCorrection){
               for(q=0;q<FOG_SUB;q++){
                  if((west && westCurve[q]!=0) || (east && eastCurve[q]!=0)
                     || (north && northCurve[q]!=0) || (south && southCurve[q]!=0)){
                     noCorrection=false;break;
                  }
               }
               if(noCorrection)continue;
            }
'''+marker)
    (run.OUT/'candidate/src/RealisticVisionMod.as').write_text(s,encoding='utf-8')
    print('Prepared contour candidate; no_cache='+str(no_cache)+' packed='+str(packed)+'; installed package unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--no-cache',action='store_true');p.add_argument('--packed',action='store_true');a=p.parse_args()
    if a.no_cache and not (run.OUT/'cached-candidate').exists():shutil.copytree(run.OUT/'candidate',run.OUT/'cached-candidate')
    if a.packed and not (run.OUT/'scan-candidate').exists():shutil.copytree(run.OUT/'candidate',run.OUT/'scan-candidate')
    prepare(a.no_cache,a.packed)
