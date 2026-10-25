"""D51: prove empty ray rectangles from the unchanged opacity snapshot."""
from pathlib import Path
import hashlib, json, shutil

HERE=Path(__file__).resolve().parent; MOD=HERE.parents[1]
OUT=MOD/'build/ray-clearance-output'; BASE=MOD/'build/combat-render-output/production-final2/src'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE/'RealisticVisionMod.as')=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
target=OUT/'candidate-v2/src'; assert not target.exists(); shutil.copytree(BASE,target)
p=target/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
def patch(old,new):
 global s
 assert s.count(old)==1,(s.count(old),old)
 s=s.replace(old,new)
patch('      private var rayOpac:Vector.<Number>;', '''      private var rayOpac:Vector.<Number>;
      private var rayClearCounts:Vector.<int>;
      private var rayClearReady:Boolean=false;''')
patch('         this.rayLoc = null;', '         this.rayLoc = null;this.rayClearCounts=null;this.rayClearReady=false;')
patch('            this.rayOpac = new Vector.<Number>(this.spaceX*this.spaceY,true);',
      '            this.rayOpac = new Vector.<Number>(this.spaceX*this.spaceY,true);\n            this.rayClearCounts=null;this.rayClearReady=false;')
patch('if(ray[index] !== opacity) { ray[index] = opacity; changed = true; }',
      'if(ray[index] !== opacity) { this.rayClearReady=false;ray[index] = opacity; changed = true; }')
patch('if(this.rayOpac[i]!==opacity) { this.rayOpac[i]=opacity; changed=true; }',
      'if(this.rayOpac[i]!==opacity) { this.rayClearReady=false;this.rayOpac[i]=opacity; changed=true; }')
patch('               return this.scenePrepareOcclusionFast(loc,sceneSpace,changed);', '''            {
               changed=this.scenePrepareOcclusionFast(loc,sceneSpace,changed);
               this.prepareClearRect();
               return changed;
            }''')
marker='''         return changed;
      }

      private function computeFov'''
patch(marker,'''         this.prepareClearRect();
         return changed;
      }

      /** Conservative proof only: a zero rectangle contains no positive or
       * non-finite opacity. Its old ray traversal therefore returns exactly 1.
       * Invalidate before any snapshot write, so interrupted refreshes cannot
       * leave a valid summary of partially updated data. */
      private function prepareClearRect():void
      {
         if(this.rayClearReady) return;
         var stride:int=this.rayWidth+1;
         var length:int=stride*(this.rayHeight+1);
         if(this.rayClearCounts==null || this.rayClearCounts.length!=length)
            this.rayClearCounts=new Vector.<int>(length,true);
         var counts:Vector.<int>=this.rayClearCounts;
         for(var y:int=0;y<this.rayHeight;y++)
         {
            var sum:int=0,source:int=y*this.rayWidth,dest:int=(y+1)*stride+1,above:int=y*stride+1;
            for(var x:int=0;x<this.rayWidth;x++,source++,dest++,above++)
            {
               var opacity:Number=this.rayOpac[source];
               if(opacity>0 || !isFinite(opacity))sum++;
               counts[dest]=counts[above]+sum;
            }
         }
         this.rayClearReady=true;
      }

      private function computeFov''')
patch('''         var c0x:int = Math.floor(ex / Tile.tileX);
         var c0y:int = Math.floor(ey / Tile.tileY);''', '''         var originX:Number=Math.floor(ex / Tile.tileX),originY:Number=Math.floor(ey / Tile.tileY);
         var c0x:int = originX;
         var c0y:int = originY;''')
patch('''         var stepX:int;
         var stepY:int;''','''         if(cached && this.rayClearReady && this.rayClearCounts!=null
            && Tile.tileX>0 && Tile.tileY>0 && originX==c0x && originY==c0y
            && Math.floor(cx/Tile.tileX)==tx && Math.floor(cy/Tile.tileY)==ty)
         {
            var left:int=c0x<tx?c0x:tx,right:int=(c0x>tx?c0x:tx)+1;
            var top:int=c0y<ty?c0y:ty,bottom:int=(c0y>ty?c0y:ty)+1;
            var stride:int=this.rayWidth+1;
            if(this.rayClearCounts[bottom*stride+right]-this.rayClearCounts[top*stride+right]
               -this.rayClearCounts[bottom*stride+left]+this.rayClearCounts[top*stride+left]==0)
               return 1;
         }
         var stepX:int;
         var stepY:int;''')
p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'inputs-v2.json').write_text(json.dumps({'base':{p.relative_to(BASE).as_posix():sha(p) for p in BASE.rglob('*.as')},
 'candidate':{p.relative_to(target).as_posix():sha(p) for p in target.rglob('*.as')},
 'no_timing':True,'baseline':'D44 only; D50 remains separate and pending performance'},indent=2)+'\n',encoding='utf-8')
print('D51 independent candidate frozen; production unchanged')
