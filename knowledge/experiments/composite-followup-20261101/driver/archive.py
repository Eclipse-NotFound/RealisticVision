"""Freeze compact evidence after all requested runs finish; never overwrite."""
from pathlib import Path
import hashlib, json, gzip, shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
OUT=MOD/'build/composite-followup-output'
DEST=MOD/'knowledge/experiments/composite-followup-20261101'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not DEST.exists(), 'Keep frozen evidence immutable'
DEST.mkdir()
origins={}
def keep(source, relative, compress=False):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
    data=source.read_bytes();target.write_bytes(gzip.compress(data,mtime=0) if compress else data)
    origins[str(relative)]={'source':str(source),'sourceSha256':sha(source),'gzip':compress}

keep(OUT/'inputs.json',Path('inputs.json'))
keep(OUT/'native-source/checked.json',Path('native-checked.json'))
for folder in sorted(OUT.iterdir()):
    if not (folder/'analysis.json').exists():continue
    for rel in ['analysis.json','summary.json','pixel-difference.json','build.json','environment.json','before.json','after.json','resource-policy.json','running.json','test.xml','selection.json','air-output.log','CombatRenderProbeMod.as']:
        p=folder/rel
        if p.exists():keep(p,Path(folder.name)/rel)
    for rel in ['evidence/result.json','cpu-samples.json']:
        keep(folder/rel,Path(folder.name)/(rel+'.gz'),True)
    for p in (folder/'evidence').glob('*.png'):keep(p,Path(folder.name)/'evidence'/p.name)
    for p in (folder/'rv-src').rglob('*.as'):keep(p,Path(folder.name)/'rv-src'/(p.relative_to(folder/'rv-src').as_posix()+'.gz'),True)
for p in HERE.iterdir():
    if p.suffix in ['.py','.as','.md']:keep(p,Path('driver')/p.name)
(DEST/'origins.json').write_text(json.dumps(origins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'.gitattributes').write_text('* -text\n',encoding='utf-8')
(DEST/'manifest.json').write_text(json.dumps({p.relative_to(DEST).as_posix():sha(p) for p in sorted(DEST.rglob('*')) if p.is_file()},indent=2)+'\n',encoding='utf-8')
print('Archived',len(origins),'inputs; bytes',sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()))
