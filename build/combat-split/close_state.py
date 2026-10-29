"""Stage D58-owned records, retaining existing authority changes."""
from pathlib import Path
import ast,hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-split-output'
DEST=MOD/'knowledge/experiments/combat-split-d58-20261029'
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('d29db85')
assert not git('diff','--cached','--name-only').strip()
finish=json.loads((DEST/'finish.json').read_text());assert finish['allOwnedRunsFinished'] and not finish['deployed']
header=(OUT/'memory-entry.txt').read_text().strip()
journal=(OUT/'journal-entry.txt').read_text().strip()+'\n\n'
assert header.startswith('> 2026-10-29 **D58') and journal.startswith('## 2026-10-29 — D58')
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode();live=(MOD/'state'/name).read_text()
 def transform(text):
  if name=='journal.md':return journal+text
  pos=text.index('\n\n')+2;text=text[:pos]+header+'\n\n'+text[pos:]
  marker='## 4. 正在进行与停点\n\n';assert marker in text
  return text.replace(marker,marker+'- D58已结束，正式仍D56；拆分分配、帧率校准、小数位移及支持区缓存的证据/否决理由见顶部报告。没有合格部署候选。后续只选独立变量验证，不把少扫描等同整帧提升。\n\n',1)
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n')
 (MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
for p in (MOD/'build/combat-split').glob('*.py'):ast.parse(p.read_text())
pins=json.loads((DEST/'archive.json').read_text())
for rel,h in pins.items():assert hashlib.sha256((DEST/rel).read_bytes()).hexdigest()==h,rel
git('add','--','.gitignore','build/combat-split','knowledge/experiments/2026-10-29-combat-split.md')
git('add','-f','--',str(DEST))
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(owned/name).read_bytes()).decode().strip()
 git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()}
assert actual==expected,actual
git('diff','--cached','--check')
prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in pins)+'\n').encode());offset=0
for rel in pins:
 end=raw.index(b'\n',offset);h=raw[offset:end].split();assert h[1]==b'blob';size=int(h[2])
 data=raw[end+1:end+size+1];offset=end+size+2;assert hashlib.sha256(data).hexdigest()==pins[rel],rel
assert offset==len(raw)
print(json.dumps({'stagedArchiveFiles':len(pins),'externalChangesPreserved':actual,'deployed':False}))
