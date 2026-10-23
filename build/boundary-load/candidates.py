"""Create immutable candidates from D41's frozen baseline."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/boundary-load-output'
if __name__=='__main__':
 target=OUT/'candidate-02/src';assert not target.exists();shutil.copytree(OUT/'candidate-01/src',target)
 p=target/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
 old='''         var tx:int,ty:int;
         for(ty=bounds.y;ty<bounds.bottom && !fresh;ty++) for(tx=bounds.x;tx<bounds.right;tx++)
            if(!this.classicLogicTiles[tx+ty*this.spaceX]){fresh=true;break;}
'''
 new='''         var tx:int,ty:int;
         var freshLeft:int=this.spaceX,freshTop:int=this.spaceY,freshRight:int=0,freshBottom:int=0;
         for(ty=bounds.y;ty<bounds.bottom;ty++) for(tx=bounds.x;tx<bounds.right;tx++)
            if(!this.classicLogicTiles[tx+ty*this.spaceX]){
               fresh=true;
               if(tx<freshLeft)freshLeft=tx;if(ty<freshTop)freshTop=ty;
               if(tx+1>freshRight)freshRight=tx+1;if(ty+1>freshBottom)freshBottom=ty+1;
            }
'''
 assert s.count(old)==1;s=s.replace(old,new)
 for a,b in [('int(bounds.x/4)','int(freshLeft/4)'),('int(bounds.y/4)','int(freshTop/4)'),('Math.ceil(bounds.right/4)','Math.ceil(freshRight/4)'),('Math.ceil(bounds.bottom/4)','Math.ceil(freshBottom/4)')]:
  assert s.count(a)==1;s=s.replace(a,b)
 old='''         }
         this.fogCache.copyPixels(this.classicLogicCache,region,new Point(region.x,region.y));
      }
'''
 new='''            // Only the newly materialized rectangle needs publishing. Every
            // previously valid tile was already copied in this field generation.
            this.fogCache.copyPixels(this.classicLogicCache,region,new Point(region.x,region.y));
         }
      }
'''
 assert s.count(old)==1;s=s.replace(old,new)
 p.write_text(s,encoding='utf-8',newline='\n')
