"""Build the production candidate from the verified v0.34.4 lineage, not WIP HEAD."""
import difflib, shutil
from run import HERE, MOD, OUT, prepare, r

prepare()
dest=OUT/'production';assert not dest.exists()
shutil.copytree(OUT/'dda-zero/src',dest/'src')
path=dest/'src/RealisticVisionMod.as'
source=path.read_text('utf8')
old='private static const VERSION:String = "v0.34.4-door-smooth";'
assert source.count(old)==1
source=source.replace(old,'private static const VERSION:String = "v0.34.5-ray-loop";')
path.write_text(source,'utf8')
r.runner.compile(path,dest/'RealisticVisionMod.swf',[path.parent],stubs=True)
baseline=(OUT/'baseline/src/RealisticVisionMod.as').read_text('utf8')
(HERE/'production.patch').write_text(''.join(difflib.unified_diff(
    baseline.splitlines(True),source.splitlines(True),fromfile='a/RealisticVisionMod.as',
    tofile='b/RealisticVisionMod.as',n=0)),'utf8')
# Carry only the reviewed method into the development tree; preserve its
# unrelated authority work and its separate version/production lineage.
start='   private function castRay(';end='      private function tileOpac('
old_method=baseline[baseline.index(start):baseline.index(end)]
new_method=source[source.index(start):source.index(end)]
working=MOD/'src/RealisticVisionMod.as';raw=working.read_bytes()
text=raw.decode('utf-8-sig').replace('\r\n','\n')
assert text.count(old_method)==1,'Development method changed concurrently'
text=text.replace(old_method,new_method)
if b'\r\n' in raw:text=text.replace('\n','\r\n')
working.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf8'))
r.save(dest/'build.json',{'version':'v0.34.5-ray-loop','swf':r.sha(dest/'RealisticVisionMod.swf'),
    'source':{p.relative_to(dest/'src').as_posix():r.sha(p) for p in (dest/'src').glob('*.as')},
    'candidate':'dda-zero','exact':'zero-exact-02','native':['zero-perf-01','zero-perf-02'],
    'control':'aa-perf-01'})
print('Production',r.sha(dest/'RealisticVisionMod.swf'))
