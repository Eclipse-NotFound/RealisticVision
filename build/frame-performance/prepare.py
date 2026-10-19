"""Reproduce the complete D31 candidate from the frozen installed D29 source."""
import shutil
import run,optimize,sparse_sight,view_cache

def prepare():
    source=run.OUT/'baseline/src';target=run.OUT/'candidate/src'
    for p in source.rglob('*.as'):
        q=target/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True)
        if p.name=='RealisticVisionMod.as':
            s=optimize.optimize(p.read_text(encoding='utf-8-sig'))
            s=sparse_sight.optimize(s)
            s=view_cache.optimize(s)
            q.write_text(s,encoding='utf-8')
        else:shutil.copyfile(p,q)

if __name__=='__main__':prepare()
