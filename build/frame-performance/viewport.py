"""Functional viewport comparison with real AIR bitmaps and no native game."""
import argparse,re
import run,view_cache

def build(name):
    folder=run.OUT/name;src=folder/'src'
    run.public_source('frame-04',src)
    original=(run.OUT/'frame-04/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
    (src/'RealisticVisionMod.as').write_text(re.sub(r'\bprivate\b','public',view_cache.optimize(original)),encoding='utf-8')
    (src/'BaselineVision.as').write_text(re.sub(r'\bprivate\b','public',original.replace('RealisticVisionMod','BaselineVision')),encoding='utf-8')
    run.runner.compile(run.HERE/'ViewportChecks.as',folder/'ViewportChecks.swf',[src,run.HERE,run.MOD/'build/stubs'])

def check(name):
    folder=run.OUT/name
    code,log=run.runner.run_air(folder,'ViewportChecks.swf',150)
    (folder/'ViewportChecks.txt').write_text(log,encoding='utf-8');print(log,flush=True)
    assert code==0 and 'VIEWPORT COMPLETE comparisons=192 failures=0' in log

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--name',required=True);a=p.parse_args()
    if a.action=='build':build(a.name)
    else:check(a.name)
