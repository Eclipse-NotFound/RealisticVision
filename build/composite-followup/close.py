"""Stage only this investigation, retaining other chats' uncommitted state."""
from pathlib import Path
import ast, hashlib, json, sqlite3, subprocess
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/composite-followup-output'
def git(*args,data=None):return subprocess.check_output(['git',*args],cwd=MOD,input=data)
assert git('rev-parse','HEAD').decode().startswith('0e8fd0c')
assert not git('diff','--cached','--name-only').strip()
db=sqlite3.connect('file:'+str(GAME/'shared-knowledge/knowledge-validation/coordination/test-runs.sqlite3').replace('\\','/')+'?mode=ro',uri=True)
rows=[json.loads(x[0]) for x in db.execute('select payload from runs')];db.close()
mine=[r for r in rows if r['owner']=='RealisticVision / 阴影交叉归因']
assert len(mine)>=2 and not [r for r in mine if r['state'] in ('waiting','running')]
for p in HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
evidence=MOD/'knowledge/experiments/composite-followup-20261101'
for rel,digest in json.loads((evidence/'manifest.json').read_text()).items():assert hashlib.sha256((evidence/rel).read_bytes()).hexdigest()==digest,rel
memory=(OUT/'memory-entry.txt').read_text(encoding='utf-8').strip()
journal=(OUT/'journal-entry.txt').read_text(encoding='utf-8').strip()+'\n\n'
owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
for rel,block in [('state/MEMORY.md',memory),('state/journal.md',journal)]:
    p=MOD/rel;before=p.read_bytes();working=before.decode('utf-8-sig');base=git('show','HEAD:'+rel).decode('utf-8-sig')
    def add(s):
        if rel.endswith('MEMORY.md'):
            first,sep,rest=s.partition('\n');return first+'\n\n'+block+'\n\n'+rest.lstrip('\n')
        return block+s
    (owned/(p.name+'.before')).write_bytes(before)
    assert p.read_bytes()==before
    p.write_text(add(working),encoding='utf-8',newline='\n')
    blob=git('hash-object','-w','--stdin',data=add(base).encode()).decode().strip()
    git('update-index','--cacheinfo','100644,'+blob+','+rel)
git('add','.gitignore','build/composite-followup','knowledge/experiments/2026-11-01-composite-followup.md','knowledge/experiments/composite-followup-20261101')
logs=[p.relative_to(MOD).as_posix() for p in evidence.glob('*/air-output.log')]
if logs:git('add','-f','--',*logs)
git('diff','--cached','--check')
print('Owned investigation staged; external work remains unstaged')
