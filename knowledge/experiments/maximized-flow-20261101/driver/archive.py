"""Archive this experiment's compact evidence after all runs finish."""
from pathlib import Path
import hashlib,json,gzip
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
OUT=MOD/'build/maximized-flow-output'
DEST=MOD/'knowledge/experiments/maximized-flow-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not DEST.exists(),'Do not overwrite frozen evidence'
DEST.mkdir();origins={}
def keep(source,relative,compress=False):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
    data=source.read_bytes();normalized=not compress and source.suffix!='.png'
    if normalized:data=('\n'.join(line.rstrip() for line in data.decode('utf-8-sig').splitlines()).rstrip()+'\n').encode('utf-8')
    target.write_bytes(gzip.compress(data,mtime=0) if compress else data)
    origins[str(relative)]={'source':str(source),'sourceSha256':sha(source),'gzip':compress,'normalizedText':normalized}
keep(OUT/'inputs.json',Path('initial-inputs.json'))
keep(OUT/'native-source/checked.json',Path('native-checked.json'))
for name in ['baseline','floor-candidate','merged-candidate','candidate']:
    source=OUT/name
    for p in (source/'src').rglob('*.as'):keep(p,Path('sources')/name/(p.relative_to(source).as_posix()+'.gz'),True)
    if (source/'change.json').exists():keep(source/'change.json',Path('sources')/name/'change.json')
for folder in sorted(OUT.iterdir()):
    if not (folder/'build.json').exists():continue
    for rel in ['analysis.json','summary.json','interpretation.json','pixel-difference.json','build.json','environment.json','before.json','after.json','resource-policy.json','running.json','last-run.json','test.xml','selection.json','air-output.log','CombatRenderProbeMod.as']:
        p=folder/rel
        if p.exists():keep(p,Path(folder.name)/rel)
    for rel in ['evidence/result.json','cpu-samples.json']:
        if (folder/rel).exists():keep(folder/rel,Path(folder.name)/(rel+'.gz'),True)
    for p in (folder/'evidence').glob('*.png'):keep(p,Path(folder.name)/'evidence'/p.name)
    for variant in ['rv-src','candidate-src']:
        for p in (folder/variant).rglob('*.as'):keep(p,Path(folder.name)/variant/(p.relative_to(folder/variant).as_posix()+'.gz'),True)
for p in HERE.iterdir():
    if p.suffix in ['.py','.as','.md']:keep(p,Path('driver')/p.name)
(DEST/'origins.json').write_text(json.dumps(origins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(DEST/'.gitattributes').write_text('* -text\n',encoding='utf-8',newline='\n')
(DEST/'manifest.json').write_text(json.dumps({p.relative_to(DEST).as_posix():sha(p) for p in sorted(DEST.rglob('*')) if p.is_file()},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Archived',len(origins),'inputs; bytes',sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()))
