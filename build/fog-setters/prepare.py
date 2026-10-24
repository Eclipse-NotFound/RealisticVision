"""D49: skip equal display assignments; immutable D44 production baseline."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/fog-setters-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE/'RealisticVisionMod.as')=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
target=OUT/'candidates/guard/src';assert not target.exists();shutil.copytree(BASE,target)
p=target/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
begin=s.index('      private function ensureFog(');end=s.index('      private function normalMode(',begin)
block=s[begin:end]
def replace(old,new):
 global block
 assert block.count(old)==1,old
 block=block.replace(old,new)
replace('this.fogBitmap.visible = true;','if(!this.fogBitmap.visible) this.fogBitmap.visible = true;')
replace('this.classicWallShadeBmp.visible = this.cfgMode == "classic";','if(this.classicWallShadeBmp.visible != (this.cfgMode == "classic"))\n            this.classicWallShadeBmp.visible = this.cfgMode == "classic";')
replace('this.wallBmp.mask = null;','if(this.wallBmp.mask != null) this.wallBmp.mask = null;')
replace('this.fogVis.scrollRect = sceneView;','this.setFogCrop(this.fogVis,sceneView);')
replace('this.fogVis.scrollRect = null;','this.setFogCrop(this.fogVis,null);')
replace('this.fogVis.x = sceneView.x; this.fogVis.y = sceneView.y;','if(this.fogVis.x != sceneView.x) this.fogVis.x = sceneView.x;\n            if(this.fogVis.y != sceneView.y) this.fogVis.y = sceneView.y;')
replace('this.fogVis.x = this.fogVis.y = 0;','if(this.fogVis.x != 0) this.fogVis.x = 0;\n            if(this.fogVis.y != 0) this.fogVis.y = 0;')
replace('this.fogShadow.scrollRect = this.fogVis.scrollRect;','this.setFogCrop(this.fogShadow,this.fogVis.scrollRect);')
replace('this.fogShadow.x = this.fogVis.x; this.fogShadow.y = this.fogVis.y;','if(this.fogShadow.x != this.fogVis.x) this.fogShadow.x = this.fogVis.x;\n         if(this.fogShadow.y != this.fogVis.y) this.fogShadow.y = this.fogVis.y;')
replace('this.fogVis.visible = true;','if(!this.fogVis.visible) this.fogVis.visible = true;')
for ct,blend in [('infraCT','multiply'),('defCT','normal')]:
 replace('this.fogShadow.transform.colorTransform = this.'+ct+';','this.setFogColor(this.'+ct+');')
 replace('this.fogShadow.blendMode = "'+blend+'";','if(this.fogShadow.blendMode != "'+blend+'") this.fogShadow.blendMode = "'+blend+'";')
helpers='''      // Compare actual display state so external changes are still repaired.
      private function setFogCrop(node:Sprite, value:Rectangle):void
      {
         var previous:Rectangle=node.scrollRect;
         if(value==null ? previous!=null : previous==null || !previous.equals(value)) node.scrollRect=value;
      }

      private function setFogColor(value:ColorTransform):void
      {
         var previous:ColorTransform=this.fogShadow.transform.colorTransform;
         if(previous.redMultiplier!=value.redMultiplier || previous.greenMultiplier!=value.greenMultiplier
            || previous.blueMultiplier!=value.blueMultiplier || previous.alphaMultiplier!=value.alphaMultiplier
            || previous.redOffset!=value.redOffset || previous.greenOffset!=value.greenOffset
            || previous.blueOffset!=value.blueOffset || previous.alphaOffset!=value.alphaOffset)
            this.fogShadow.transform.colorTransform=value;
      }

'''
s=s[:begin]+helpers+block+s[end:];p.write_text(s,encoding='utf-8',newline='\n')
p=target/'RVWallSurface.as';s=p.read_text(encoding='utf-8')
changes={
 'parent.setChildIndex(wallPixels,parent.numChildren-1);':'if(parent.getChildIndex(wallPixels)!=parent.numChildren-1)parent.setChildIndex(wallPixels,parent.numChildren-1);',
 'wallPixels.visible = true;':'if(!wallPixels.visible)wallPixels.visible = true;',
 'wallPixels.visible=count>0;':'if(wallPixels.visible!=(count>0))wallPixels.visible=count>0;',
 'airPixels.visible=wallPixels.visible;':'if(airPixels.visible!=wallPixels.visible)airPixels.visible=wallPixels.visible;',
 'airPixels.mask=airClip;':'if(airPixels.mask!==airClip)airPixels.mask=airClip;',
 'wallPixels.mask=solidClip;base.mask=onClip;':'if(wallPixels.mask!==solidClip)wallPixels.mask=solidClip;if(base.mask!==onClip)base.mask=onClip;',
 '}else base.mask=baseClip;':'}else if(base.mask!==baseClip)base.mask=baseClip;',
 'airPixels.x=left*CELL;airPixels.y=top*CELL;':'if(airPixels.x!=left*CELL)airPixels.x=left*CELL;if(airPixels.y!=top*CELL)airPixels.y=top*CELL;'
}
for old,new in changes.items():assert s.count(old)==1,old;s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'inputs.json').write_text(json.dumps({'baseline':{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*.as')},'candidate':{str(p.relative_to(target)):sha(p) for p in target.rglob('*.as')},'hypothesis':'Equal scrollRect, mask and color assignments may invalidate fog composition. Strict pixels must hold; adopt only with complete combat improvement.'},indent=2)+'\n',encoding='utf-8')
print('D49 frozen candidate created; no production modification')
