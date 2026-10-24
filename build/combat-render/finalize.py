"""Stage owned D44 changes and verify raw evidence without staging outside WIP."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-render-output'
def git(*args,input=None):
    p=subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True)
    if p.returncode:
        (OUT/'staging-check.txt').write_bytes(p.stdout+p.stderr)
        raise RuntimeError((p.stdout+p.stderr).decode('utf-8',errors='replace')[-3000:])
    return p.stdout
receipt=json.loads((OUT/'deployment/receipt.json').read_text());assert receipt['result']=='PASS'
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()==receipt['new']
assert git('rev-parse','HEAD').decode().startswith('39ed9b6'),'HEAD changed; review concurrent work'
paths=['build/combat-render','src/RealisticVisionMod.as','decisions/decisions.md',
       'knowledge/experiments/2026-10-25-combat-render-attribution.md','knowledge/experiments/combat-render-d44-20261025',
       'state/deployment-v03310-2026-10-25.md']
git('add','--',*paths)
for name in ['MEMORY.md','journal.md']:
    data=(OUT/'owned-state'/name).read_bytes()
    oid=git('hash-object','-w','--stdin',input=data).decode().strip()
    git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
staged=git('diff','--cached','--name-only','-z').decode().split('\0')
assert 'src/RVAuthorityView.as' not in staged and 'tests/authority/AuthorityViewChecks.as' not in staged
pins=json.loads((MOD/'knowledge/experiments/combat-render-d44-20261025/archive.json').read_text())
raw_paths=['knowledge/experiments/combat-render-d44-20261025/'+p for p in pins]
# Runtime binaries keep the repository's existing ignore policy. Raw evidence
# logs are intentionally pinned and must not vanish because *.log is ignored.
git('add','-f','--pathspec-from-file=-','--pathspec-file-nul',input=('\0'.join(raw_paths)+'\0').encode())
queries=[':knowledge/experiments/combat-render-d44-20261025/'+p for p in pins]
raw=git('cat-file','--batch',input=('\n'.join(queries)+'\n').encode());offset=0
for path,digest in pins.items():
    end=raw.index(b'\n',offset);header=raw[offset:end].decode().split();assert header[1]=='blob',path
    size=int(header[2]);data=raw[end+1:end+1+size];offset=end+size+2
    assert hashlib.sha256(data).hexdigest()==digest,'Indexed raw bytes differ: '+path
assert offset==len(raw)
git('diff','--cached','--check')
remaining=git('diff','--numstat').decode().splitlines()
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in remaining}
assert actual==expected,actual
print('Staged owned files:',len([p for p in staged if p]))
print('Raw archive byte hashes verified:',len(pins))
print('Outside WIP remains exactly 24/2/4/15 added lines')
