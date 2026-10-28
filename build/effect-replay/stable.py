"""D55 stable mask support prototype. Exact D44 source; no visual simplification."""
from pathlib import Path
import shutil,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-replay-output/candidates/stable/src'
BASE=MOD/'build/combat-render-output/production-final2/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
start=s.index('      private function applyWorldVisual(visual:');end=s.index('      private function worldVisualHasFilters(',start)
p=s[start:end]
old='''         var key:String=x0+","+y0+","+x1+","+y1;'''
new='''         var mx0:int=x0,my0:int=y0,mx1:int=x1,my1:int=y1;
         // Retain an existing full mask while motion remains inside its blur
         // support. Do not change native visual bounds or skip any field update.
         if(this.cfgMode=="current" && record!=null && record.stableBb!=null && this.worldParentPixelAligned(visual.parent) && !this.worldVisualHasFilters(visual)){
            var oldBb:Array=record.stableBb;
            var marginX:int=Math.ceil((this.maskBlurCurrent.blurX*this.maskBlurCurrent.quality/2+2)/MASK_SUB);
            var marginY:int=Math.ceil((this.maskBlurCurrent.blurY*this.maskBlurCurrent.quality/2+2)/MASK_SUB);
            if(marginX<=MASK_PAD_X && marginY<=MASK_PAD_BOTTOM
               && x0>=oldBb[0]-MASK_PAD_X+marginX && x1<=oldBb[2]+MASK_PAD_X-marginX
               && y0>=oldBb[1]-MASK_PAD_TOP+marginY && y1<=oldBb[3]+MASK_PAD_BOTTOM-marginY){
               mx0=oldBb[0];my0=oldBb[1];mx1=oldBb[2];my1=oldBb[3];
               // D55_STABLE
            }
         }
         var key:String=mx0+","+my0+","+mx1+","+my1;'''
assert p.count(old)==1;p=p.replace(old,new)
p=p.replace('this.refreshMask(raster,[x0,y0,x1,y1]);','this.refreshMask(raster,[mx0,my0,mx1,my1]);')
p=p.replace('if(raster.coverageFov!==this.fovVersion)','var coverage:String=x0+","+y0+","+x1+","+y1;\n         if(raster.coverageFov!==this.fovVersion || raster.coverageBb!==coverage)')
p=p.replace('Math.max(0,x0-MASK_PAD_X)','Math.max(0,mx0-MASK_PAD_X)').replace('Math.max(0,y0-MASK_PAD_TOP)','Math.max(0,my0-MASK_PAD_TOP)')
p=p.replace('raster.coverageFov=this.fovVersion;','raster.coverageFov=this.fovVersion;raster.coverageBb=coverage;')
p=p.replace('record.pass=this.worldPass;','record.pass=this.worldPass;record.stableBb=[mx0,my0,mx1,my1];')
s=s[:start]+p+s[end:]
reference=(MOD/'build/sustained-fire-output/candidates/integer-v2/src/RealisticVisionMod.as').read_text()
helper=reference[reference.index('      // All calls in one world pass are synchronous.'):reference.index('      private function worldVisualHasFilters(')]
s=s.replace('      private function worldVisualHasFilters(',helper+'      private function worldVisualHasFilters(',1)
s=s.replace('private var worldMasks:Object = {};','private var worldMasks:Object = {};\n      private var worldPixelLattice:Dictionary = new Dictionary(true);')
s=s.replace('this.worldMasks={};this.worldPass=0;','this.worldMasks={};this.worldPass=0;this.worldPixelLattice=new Dictionary(true);')
shutil.copytree(BASE,OUT);(OUT/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
# Rebind known fixtures only; never regenerate the D54 directory.
t=(MOD/'build/sustained-fire/check.py').read_text().replace('D54','D55').replace('sustained-fire-output','effect-replay-output')
a=t.index(" src=folder/'src'");b=t.index('\n p=src/',a)
t=t[:a]+" src=folder/'src';r.public(OUT/'candidates/stable/src',src)"+t[b:]
t=t.replace('// D55_TRAILING','// D55_STABLE').replace("if any(k in sys.argv for k in ['--integer'", "if any(k in sys.argv for k in ['--stable','--integer'")
(MOD/'build/effect-replay/check.py').write_text(t,encoding='utf-8',newline='\n')
