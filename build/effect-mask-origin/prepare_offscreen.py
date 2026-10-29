"""D56: omit independent effect masks only beyond the actual stage viewport."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/offscreen/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
s=s.replace('private var worldPass:int = 0;','private var worldPass:int = 0;\n      private var worldViewports:Dictionary = new Dictionary(true);')
old='''         var bounds:Rectangle=visual.getBounds(visual.parent);
         var x0:int=Math.max(0,Math.floor(bounds.left/Tile.tileX));'''
new='''         var bounds:Rectangle=visual.getBounds(visual.parent);
         var viewport:Rectangle=this.worldViewport(visual.parent);
         if(viewport!=null && !viewport.intersects(bounds) && !this.worldVisualHasFilters(visual))
         {
            // D56_OFFSCREEN: native animation/lifetime/input continue unchanged.
            if(record!=null)this.releaseWorldVisual(visual,record);
            return;
         }
         var x0:int=Math.max(0,Math.floor(bounds.left/Tile.tileX));'''
assert s.count(old)==1;s=s.replace(old,new)
marker='      private function worldVisualHasFilters(visual:DisplayObject):Boolean'
helper='''      // A conservative parent-space box enclosing the stage plus AA margin.
      // Parent transforms and filters are rechecked every synchronous world pass.
      private function worldViewport(parent:DisplayObjectContainer):Rectangle
      {
         var stage:Stage=parent.stage;
         if(stage==null || stage.scaleMode!="noScale" || stage.align!="TL")return null;
         var entry:Object=this.worldViewports[parent];
         if(entry==null){entry={pass:-1,rect:null};this.worldViewports[parent]=entry;}
         if(entry.pass!=this.worldPass){
            entry.pass=this.worldPass;entry.rect=null;
            for(var ancestor:DisplayObject=parent;ancestor!=null;ancestor=ancestor.parent)
               if(ancestor.filters.length>0)return null;
            var matrix:Matrix=parent.transform.concatenatedMatrix;
            var det:Number=matrix.a*matrix.d-matrix.b*matrix.c;
            if(!isFinite(det) || Math.abs(det)<0.000001)return null;
            matrix.invert();
            var left:Number=Number.POSITIVE_INFINITY,top:Number=left;
            var right:Number=Number.NEGATIVE_INFINITY,bottom:Number=right;
            for(var corner:int=0;corner<4;corner++){
               var x:Number=corner&1?stage.stageWidth+2:-2;
               var y:Number=corner&2?stage.stageHeight+2:-2;
               var px:Number=matrix.a*x+matrix.c*y+matrix.tx;
               var py:Number=matrix.b*x+matrix.d*y+matrix.ty;
               left=Math.min(left,px);right=Math.max(right,px);
               top=Math.min(top,py);bottom=Math.max(bottom,py);
            }
            if(isFinite(left) && isFinite(top) && isFinite(right) && isFinite(bottom))
               entry.rect=new Rectangle(left,top,right-left,bottom-top);
         }
         return entry.rect as Rectangle;
      }

'''
assert s.count(marker)==1;s=s.replace(marker,helper+marker)
s=s.replace('this.worldMasks={};this.worldPass=0;','this.worldMasks={};this.worldPass=0;this.worldViewports=new Dictionary(true);')
p.write_text(s,encoding='utf-8',newline='\n')
