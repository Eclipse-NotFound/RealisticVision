"""Freeze this audit's evidence, excluding saves, media duplicates and other mods."""
from pathlib import Path
import gzip,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combo-audit-output'
DEST=MOD/'knowledge/experiments/combo-audit-20261101'
assert not DEST.exists(), 'Evidence is immutable; use a new revision'
DEST.mkdir()
origins={}
def cp(p,rel):
    q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True)
    raw=p.read_bytes();data=raw
    if p.suffix in ('.as','.json','.log'):
        data=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        if p.suffix=='.as':data=b'\n'.join(line.rstrip() for line in data.split(b'\n'))
    q.write_bytes(data)
    origins[str(rel).replace('\\','/')]={'source':str(p),'originalSHA256':hashlib.sha256(raw).hexdigest(),'textWhitespaceNormalized':raw!=data}
for name in ['inputs.json','summary.json','native-source/checked.json']:cp(OUT/name,name)
for version in ['baseline','candidate']:
    for p in (OUT/version/'src').rglob('*.as'):cp(p,Path('production-source')/version/p.relative_to(OUT/version/'src'))
for folder in sorted(OUT.glob('[0-9][0-9]-*')):
    for name in ['build.json','before.json','after.json','environment.json','analysis.json','last-run.json','resource-policy.json','running.json','CombatRenderProbeMod.as','air-output.log']:
        p=folder/name
        if p.exists():cp(p,Path(folder.name)/name)
    p=folder/'evidence/result.json'
    if p.exists():
        q=DEST/folder.name/'result.json.gz';q.parent.mkdir(exist_ok=True)
        q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    for p in (folder/'evidence').glob('audit-*.png'):cp(p,Path(folder.name)/p.name)
cp(OUT/'01-large-pair/evidence/scene-0.png','01-large-pair/scene-0.png')
failures={'02-small-pair-checks':'All six timed windows finished; post-timing PNG write used app: resource path and failed. Preserved, corrected and checked in 04/08.',
          '06-audit-only':'Host changed while queued; reuse fingerprint guard stopped before AIR launch.',
          '07-large-fog':'Host changed while queued; native-loop fingerprint guard stopped before compile/AIR. 08/09 explicitly reuse frozen private host.'}
(DEST/'failures.json').write_text(json.dumps(failures,indent=2)+'\n',encoding='utf-8',newline='\n')
(DEST/'origins.json').write_text(json.dumps(origins,indent=2)+'\n',encoding='utf-8',newline='\n')
manifest={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print(len(manifest),'files',sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()),'bytes')
