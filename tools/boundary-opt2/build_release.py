"""Build the production candidate from the verified cs-window frozen lineage.

The development tree stays untouched this round: the cs-window session has
not ported its own edits back yet, so splicing these edits into a v0.34.5
tree would fork it further and collide with their future port. The reviewed
sources remain in build/boundary-opt2-20261104/production/src.
"""
import shutil
from run import MOD, OUT, prepare, r

prepare()
dest=OUT/'production';assert not dest.exists()
shutil.copytree(OUT/'clip-hyst/src',dest/'src')
path=dest/'src/RealisticVisionMod.as'
source=path.read_text('utf8')
old='private static const VERSION:String = "v0.34.6-cs-window";'
assert source.count(old)==1
source=source.replace(old,'private static const VERSION:String = "v0.34.7-clip-hyst";')
path.write_text(source,'utf8')
r.runner.compile(path,dest/'RealisticVisionMod.swf',[path.parent],stubs=True)
r.save(dest/'build.json',{'version':'v0.34.7-clip-hyst','swf':r.sha(dest/'RealisticVisionMod.swf'),
    'source':{p.relative_to(dest/'src').as_posix():r.sha(p) for p in (dest/'src').rglob('*.as')},
    'candidate':'clip-hyst','exact':'clip-exact-01','native':['clip-perf-01','clip-perf-02'],
    'control':'aa-perf-01'})
print('Production',r.sha(dest/'RealisticVisionMod.swf'))
