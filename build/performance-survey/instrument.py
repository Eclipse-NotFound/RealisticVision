"""Diagnostic counters only. No skipped work, visibility or production changes."""
def replace_once(s, old, new):
    assert s.count(old) == 1, (old, s.count(old))
    return s.replace(old, new)


def instrument(s):
    pos = s.index('{', s.index('public class')) + 1
    s = s[:pos] + '''
 public var survey:Object={};
 public var surveySeen:Dictionary=new Dictionary(true),surveyTypes:Dictionary=new Dictionary(true);
 public var surveySource:int=0;
 public function surveyHit(key:String,amount:Number=1):void {survey[key]=Number(survey[key]||0)+amount;}
 public function surveyVisual(v:DisplayObject):void {
   surveyHit("visualCalls");surveyHit("source"+surveySource);
   if(surveySeen[v]===worldPass)surveyHit("duplicateVisualCalls");else surveyHit("uniqueVisualCalls");
   surveySeen[v]=worldPass;
   var cls:Object=Object(v).constructor;
   var kind:String=surveyTypes[cls];
   if(kind==null){kind=getQualifiedClassName(v);surveyTypes[cls]=kind;}
   surveyHit("type:"+kind);
 }
''' + s[pos:]
    changes = [
        ('this.worldPass++;', 'this.worldPass++;this.surveySource=0;'),
        ('if(w.grafon != null) for(var layerIndex:', 'this.surveySource=1;\n          if(w.grafon != null) for(var layerIndex:'),
        ('// A fully visible body can carry a long gun beyond its own bounds.', 'this.surveySource=2;\n          // A fully visible body can carry a long gun beyond its own bounds.'),
        ('public function applyWorldVisual(visual:DisplayObject):void\n      {', 'public function applyWorldVisual(visual:DisplayObject):void\n      {\n          this.surveyVisual(visual);'),
        ('bounds=record.lastBounds;', 'this.surveyHit("boundsReuse");bounds=record.lastBounds;'),
        ('bounds=visual.getBounds(visual.parent);', 'this.surveyHit("boundsRead");bounds=visual.getBounds(visual.parent);'),
        ('if(raster==null){raster={worldRaster:true,', 'if(raster==null){this.surveyHit("worldRasterNew");raster={worldRaster:true,'),
        ('if(raster.coverageFov!==this.fovVersion)\n         {', 'if(raster.coverageFov!==this.fovVersion)\n         {\n             this.surveyHit("coverageRead");'),
        ('if(raster.fullyLit)\n         {', 'if(raster.fullyLit)\n         {\n             this.surveyHit("fullyLitReturn");'),
        ('var drawDark:Boolean=raster.fullyDark;', 'var drawDark:Boolean=raster.fullyDark;this.surveyHit(drawDark?"wholeDark":"mixed");'),
        ('record={shape:new Shape(),baseMask:', 'this.surveyHit("visualRecordNew");record={shape:new Shape(),baseMask:'),
        ('screenMatrix = this.matrixCacheValue;', 'this.surveyHit("matrixReuse");screenMatrix = this.matrixCacheValue;'),
        ('screenMatrix = visual.parent.transform.concatenatedMatrix;', 'this.surveyHit("matrixRead");screenMatrix = visual.parent.transform.concatenatedMatrix;'),
        ('var drawX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;', '''
          if(!drawDark){
             this.surveyHit("mixedDraw");
             this.surveyHit("boundsArea",Math.max(0,bounds.width*bounds.height));
             this.surveyHit("fullMaskArea",BitmapData(raster.m2e).width*BitmapData(raster.m2e).height*25);
             if(screenMatrix.a!=1||screenMatrix.d!=1||screenMatrix.b!=0||screenMatrix.c!=0)this.surveyHit("nonUnitTransform");
             else if(screenMatrix.tx!=Math.floor(screenMatrix.tx)||screenMatrix.ty!=Math.floor(screenMatrix.ty))this.surveyHit("fractionalParent");
             else this.surveyHit("unitIntegerParent");
          }
          var drawX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;'''),
        ('var clipChanged:Boolean=', 'if(drawClip!=null)this.surveyHit("cropUsed");\n          var clipChanged:Boolean='),
        ('if(visual.mask===shape)visual.mask=null;', 'if(visual.mask===shape){this.surveyHit("maskDetach");visual.mask=null;}'),
        ('if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;\n         if(visual.mask!==shape)visual.mask=shape;', 'if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;\n         if(visual.mask!==shape){this.surveyHit("maskAttach");visual.mask=shape;}'),
        ('public function worldVisualHasFilters(visual:DisplayObject):Boolean\n      {', 'public function worldVisualHasFilters(visual:DisplayObject):Boolean\n      {\n          this.surveyHit("filterNodesRead");'),
        ('this.disposeWorldMask(raster);delete this.worldMasks[key];', 'this.surveyHit("worldRasterEvict");this.disposeWorldMask(raster);delete this.worldMasks[key];'),
        ('public function refreshMask(rec:Object,bb:Array):void\n      {', 'public function refreshMask(rec:Object,bb:Array):void\n      {\n          this.surveyHit(rec.worldRaster===true?"worldRefreshCalls":"unitRefreshCalls");'),
        ('if(rec.lastFov == this.fovVersion && rec.lastBb == sig)\n         {', 'if(rec.lastFov == this.fovVersion && rec.lastBb == sig)\n         {\n             this.surveyHit("sameVersionReturn");'),
        ('rec.lastFov = this.fovVersion;', 'this.surveyHit("refreshWork");rec.lastFov = this.fovVersion;'),
        ('bd = new BitmapData(totx,toty,true,0);', 'this.surveyHit("rawAllocation");this.surveyHit("rawAllocatedPixels",totx*toty);bd = new BitmapData(totx,toty,true,0);'),
        ('var maskDelta:Object = bd.compare(previousInput);', 'this.surveyHit("inputCompare");this.surveyHit("inputComparePixels",bd.width*bd.height);var maskDelta:Object = bd.compare(previousInput);'),
        ('if(maskDelta is uint && uint(maskDelta) == 0) return;', 'if(maskDelta is uint && uint(maskDelta) == 0){this.surveyHit("inputUnchanged");return;}this.surveyHit("inputChanged");'),
        ('bdb.applyFilter(bd,bd.rect,this.fogPoint,blur);', 'this.surveyHit("maskBlur");this.surveyHit("maskBlurPixels",bd.width*bd.height);bdb.applyFilter(bd,bd.rect,this.fogPoint,blur);'),
        ('if(dark || uniformLit){', 'if(dark || uniformLit){this.surveyHit(dark?"uniformDarkReturn":"uniformLitReturn");'),
        ('this.fovVersion++;', None),
    ]
    for old, new in changes:
        if new is not None:
            s = replace_once(s, old, new)
    # All four tile writers are counted; no change to their inputs or outputs.
    for name in ('fillLitTile', 'fillMemoryTile', 'fillWallTile', 'recalcTile'):
        start = s.index('public function '+name+'(')
        pos = s.index('{', start)+1
        s = s[:pos]+'this.surveyHit("'+name+'");'+s[pos:]
    s = replace_once(s, 'this.fogCache.lock();\n            var tx:int;', 'this.surveyHit("fogFillTiles",sceneBounds.width*sceneBounds.height);this.fogCache.lock();\n            var tx:int;')
    return s


def helper(s):
    pos=s.index('{',s.index('public class'))+1
    s=s[:pos]+'\n public var survey:Object={};\n public function surveyHit(k:String,n:Number=1):void{survey[k]=Number(survey[k]||0)+n;}\n'+s[pos:]
    for old,new in [
        ('var requested:int=alwaysBright?1:0;', 'surveyHit("update");var requested:int=alwaysBright?1:0;'),
        ('fieldUpdates++;','surveyHit("fieldChanged");fieldUpdates++;'),
        ('var delta:Object=contourScratch.compare(patch.pixels);','surveyHit("terrainCompare");surveyHit("terrainComparePixels",contourScratch.width*contourScratch.height);var delta:Object=contourScratch.compare(patch.pixels);'),
        ('if(delta is uint&&uint(delta)==0)continue;', 'if(delta is uint&&uint(delta)==0){surveyHit("terrainSame");continue;}surveyHit("terrainChanged");'),
        ('if(contourDirty){buildContourClip(loc);', 'if(contourDirty){surveyHit("contourRebuild");buildContourClip(loc);'),
    ]:
        s=replace_once(s,old,new)
    return s
