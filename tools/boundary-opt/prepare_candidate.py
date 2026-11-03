"""C4-exact: specialize the existing cached DDA without changing ray semantics."""
from pathlib import Path
import argparse
import difflib, shutil
from run import OUT, prepare

prepare()
p=argparse.ArgumentParser();p.add_argument('--zero',action='store_true');args=p.parse_args()
target = OUT/('dda-zero' if args.zero else 'dda-local')/'src'
assert not target.exists(), 'Keep candidate snapshots immutable'
shutil.copytree(OUT/'baseline/src', target)
path = target/'RealisticVisionMod.as'
before = path.read_text('utf8')
start = before.index('         while(c1x != tx || c1y != ty)', before.index('private function castRay('))
end = before.index('         op = cached ? this.rayOpac[tx+ty*this.rayWidth]', start)
original = before[start:end]
uncached = original.replace('cached ? this.rayOpac[c1x+c1y*this.rayWidth] : ', '')
fast = original.replace('            if(tMaxX < tMaxY)', '            if(tMaxX < tMaxY)')
fast = fast.replace('               c1x += stepX;', '               c1x += stepX;\n               cell += stepX;')
fast = fast.replace('               c1y += stepY;', '               c1y += stepY;\n               cell += rowStep;')
fast = fast.replace('cached ? this.rayOpac[c1x+c1y*this.rayWidth] : this.tileOpac(loc,loc.getTile(c1x,c1y))', 'opacity[cell]')
if args.zero:
    fast = fast.replace('            op = opacity[cell];',
        '            op = opacity[cell];\n            if(op == 0) continue; // Empty cells do not alter light or leakage.')
def indent(s):
    return '\n'.join('   '+line if line else line for line in s.split('\n'))
replacement = '''         // Batch rays share an immutable opacity snapshot. Resolve that path once,
         // then advance its flat index with the DDA instead of reading members
         // and multiplying by the row width at every crossed cell.
         // Keep tie ordering, the 400-step guard and the second target sample.
         if(cached)
         {
            var opacity:Vector.<Number> = this.rayOpac;
            var rowStep:int = stepY * this.rayWidth;
            var cell:int = c0x + c0y * this.rayWidth;
'''+indent(fast)+'''         }
         else
         {
'''+indent(uncached)+'''         }
'''
after = before[:start]+replacement+before[end:]
path.write_text(after,'utf8')
patch = ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
    fromfile='a/RealisticVisionMod.as',tofile='b/RealisticVisionMod.as'))
(Path(__file__).parent/'production.patch').write_text(patch,'utf8')
print(target)
