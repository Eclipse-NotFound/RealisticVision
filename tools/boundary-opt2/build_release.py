"""Build the production candidate from the verified v0.34.7 frozen lineage.

The development tree stays untouched: cs-window and clip-hyst ports are both
still pending there; the reviewed sources remain in
build/boundary-opt2-20261104/production/src.
"""
import shutil
from run import MOD, OUT, prepare, r

prepare()
dest=OUT/'production';assert not dest.exists()
shutil.copytree(OUT/'clip-pad/src',dest/'src')
path=dest/'src/RealisticVisionMod.as'
source=path.read_text('utf8')
old='private static const VERSION:String = "v0.34.7-clip-hyst";'
assert source.count(old)==1
source=source.replace(old,'private static const VERSION:String = "v0.34.8-clip-pad";')
path.write_text(source,'utf8')
r.runner.compile(path,dest/'RealisticVisionMod.swf',[path.parent],stubs=True)
r.save(dest/'build.json',{'version':'v0.34.8-clip-pad','swf':r.sha(dest/'RealisticVisionMod.swf'),
    'source':{p.relative_to(dest/'src').as_posix():r.sha(p) for p in (dest/'src').rglob('*.as')},
    'candidate':'clip-pad','exact':'pad-exact-01','native':['pad-perf-01','pad-perf-02'],
    'control':'pad-aa-01'})
print('Production',r.sha(dest/'RealisticVisionMod.swf'))
