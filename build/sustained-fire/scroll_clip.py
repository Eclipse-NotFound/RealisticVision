"""Alternative: clip the existing mask rather than redraw its bitmap fill."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];BASE=MOD/'build/combat-render-output/production-final2/src';OUT=MOD/'build/sustained-fire-output/candidates/scroll/src';assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
needle='         if(shape.parent!==visual.parent)visual.parent.addChild(shape);'
assert s.count(needle)==1
extra='''         var clip:Rectangle=null;
         if(this.cfgMode=="current" && !drawDark && !this.worldVisualHasFilters(visual)){
            var left:Number=Math.max(0,x0-1)*Tile.tileX,top:Number=Math.max(0,y0-1)*Tile.tileY;
            clip=new Rectangle(left,top,Math.min(this.spaceX,x1+2)*Tile.tileX-left,Math.min(this.spaceY,y1+2)*Tile.tileY-top); // D54_TRAILING
         }
         if((clip==null)!=(record.clip==null) || (clip!=null && (record.clip==null || !clip.equals(record.clip)))){
            shape.scrollRect=clip;record.clip=clip;
            shape.x=clip==null?0:clip.x;shape.y=clip==null?0:clip.y;
         }
'''
shutil.copytree(BASE,OUT);(OUT/'RealisticVisionMod.as').write_text(s.replace(needle,extra+needle),encoding='utf-8',newline='\n')
