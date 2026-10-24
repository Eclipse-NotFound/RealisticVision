"""Sequential registered checks. Stop on failure, preserve each original run."""
from pathlib import Path
import subprocess, sys, json, hashlib

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
OUT=MOD/'build/effect-load-v3-output'
GAME=MOD.parents[1]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def step(args):
    label=' '.join(args)
    log=OUT/('gate-'+ '-'.join(args).replace('.py','')+'.log')
    assert not log.exists(), str(log)
    print('GATE START '+label, flush=True)
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run([sys.executable,'-X','utf8',str(HERE/args[0]),*args[1:]],cwd=MOD,stdout=stream,stderr=stream)
    if result.returncode:
        print(log.read_text(encoding='utf-8')[-4000:],flush=True)
        raise SystemExit(result.returncode)
    print('GATE PASS '+label,flush=True)

if __name__=='__main__':
    assert (OUT/'native-04/build.json').exists()
    pins=json.loads((OUT/'native-03/supplemental-inputs.json').read_text())
    for rel,d in pins['files'].items():
        assert digest(GAME/rel)==d and digest(OUT/'native-04'/rel)==d,rel
    (OUT/'native-04/supplemental-inputs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
    steps=[['native.py','run','native-04','--lean','--samples','120'],
           ['review.py','--perf-only','native-03','native-04']]
    if '--functional' in sys.argv:
        steps=[['bench.py','run','candidate-03'],['bench.py','run','edges-01'],
               ['functional.py','build','functional-02'],['functional.py','run','functional-02'],
               ['measure.py','build','safe-01-parent','--candidate','candidate','--verify','--wide'],
               ['measure.py','run','safe-01-parent'],['package.py','build'],['package.py','check'],
               ['review.py','native-03','native-04']]
    for args in steps: step(args)
