from pathlib import Path
import shutil,json,hashlib
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/local-mask-regions-output'
target=OUT/'candidate/src';assert not target.exists()
shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text('utf8')
def once(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new)
def function(name):
 start=s.index('      private function '+name+'(');end=s.index('\n      private function ',start+1)
 return start,end,s[start:end]
def put_function(start,end,text):
 global s
 s=s[:start]+text+s[end:]
once('      private function refreshMask(rec:Object,bb:Array):void', (HERE/'RegionMethods.inc.as').read_text('utf8')+'\n      private function refreshMask(rec:Object,bb:Array):void')
once('         rec.lastBb = sig;','''         rec.lastBb = sig;
         if(this.regionMaskUnchanged(rec,bb,x0,y0,x1,y1)){
            // REGION_HIT: preserve raster identity, sampling and attachment history.
            if(rec.regionUniform===true)rec.coverageFov=this.fovVersion;
            return;
         }
         rec.regionUniform=false;''')
once('               rec.maskValid=false;\n               return;','               rec.maskValid=false;rec.regionReady=true;rec.regionUniform=true;\n               return;')
once('            if(maskDelta is uint && uint(maskDelta) == 0) return;','            if(maskDelta is uint && uint(maskDelta) == 0){rec.regionReady=true;return;}')
once('         rec.maskValid = true;','         rec.maskValid = true;rec.regionReady=true;')
# Current's complete logical-pixel writers.
once('         var wallChanged:Boolean = this.refreshWallField(loc,this.wallGeometryDirty);','         this.ensureRegions(this.currentSight);\n         var wallChanged:Boolean = this.refreshWallField(loc,this.wallGeometryDirty);')
once('         this.currentSight.fillRect(this.currentSightWritten==null?this.currentSight.rect:this.currentSightWritten,0);','         this.ensureRegions(this.currentSight);this.clearRegionsOutside(sceneBounds);\n         this.currentSight.fillRect(this.currentSightWritten==null?this.currentSight.rect:this.currentSightWritten,0);')
bit='if(sy<4)bitsLo|=uint(1)<<(sy*8+sx);else bitsHi|=uint(1)<<((sy-4)*8+sx);'
for name in ['recalcTile','fillLitTile','fillWallTile']:
 start,end,t=function(name)
 brace=t.index('{')+1;t=t[:brace]+'\n         var bitsLo:uint=0,bitsHi:uint=0;'+t[brace:]
 if name=='recalcTile':
  old='''                  if(logicalA < MASK_LIT_A && sdx*sdx+sdy*sdy <= this.locDist2*this.locDist2)
                     this.currentSight.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,0xFFFFFFFF);'''
  assert old in t;t=t.replace(old,old.replace('\n                     this.currentSight','{'+bit+'\n                     this.currentSight')+'}')
 elif name=='fillLitTile':
  t=t.replace('this.currentSight.fillRect(this.fogCellRect,0xFFFFFFFF);','this.currentSight.fillRect(this.fogCellRect,0xFFFFFFFF);this.putRegion(tx,ty,0xFFFFFFFF,0xFFFFFFFF);')
  old='if(Math.round((1-Math.max(logicalF,0.35))*255)<MASK_LIT_A) this.currentSight.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,0xFFFFFFFF);'
  assert old in t;t=t.replace(old,old.replace(') this.currentSight','){'+bit+'this.currentSight')+'}')
 else:
  old='''            if(this.cfgMode == "current" && this.currentSight != null)
               this.currentSight.fillRect(this.fogCellRect,
                  p00 < MASK_LIT_A && this.fov[tx+ty*this.spaceX] != FOV_NONE ? 0xFFFFFFFF : 0);'''
  assert old in t;t=t.replace(old,'''            if(this.cfgMode == "current" && this.currentSight != null){
               var all:uint=p00 < MASK_LIT_A && this.fov[tx+ty*this.spaceX] != FOV_NONE ? 0xFFFFFFFF : 0;
               this.currentSight.fillRect(this.fogCellRect,all);this.putRegion(tx,ty,all,all);
            }''')
  marker='                  this.currentSight.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,'
  assert marker in t;t=t.replace(marker,'                  if(personalA < MASK_LIT_A && this.fov[tx+ty*this.spaceX]!=FOV_NONE){'+bit+'}\n'+marker)
  t=t.replace('         return maskChanged;', '         if(this.cfgMode=="current" && this.currentSight!=null)this.putRegion(tx,ty,bitsLo,bitsHi);\n         return maskChanged;')
 if name!='fillWallTile':
  endbrace=t.rfind('      }');t=t[:endbrace]+'         this.putRegion(tx,ty,bitsLo,bitsHi);\n'+t[endbrace:]
 put_function(start,end,t)
start,end,t=function('fillMemoryTile');brace=t.index('{')+1;t=t[:brace]+'\n         this.putRegion(tx,ty,0,0);'+t[brace:];put_function(start,end,t)
# Room and off transitions must not retain a source identity for a reused bitmap.
for name in ['resetOff','resetRoom']:
 start,end,t=function(name);brace=t.index('{')+1;t=t[:brace]+'\n         this.regionSource=null;this.regionLo=this.regionHi=null;this.regionStamp=this.regionRead=null;'+t[brace:];put_function(start,end,t)
p.write_text(s,'utf8',newline='\n')
(OUT/'candidate/sources.json').write_text(json.dumps({q.relative_to(target).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in target.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
print('Generated exact regional candidate; no production files changed')
