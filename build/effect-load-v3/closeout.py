"""Stage only D43; retain external authority edits."""
import hashlib,json,subprocess
import package as p
MOD,OUT=p.MOD,p.OUT;ARCHIVE='knowledge/experiments/effect-load-v0339-20261024'
def git(*args,**kwargs):return subprocess.check_output(['git',*args],cwd=MOD,**kwargs)
def main():
 paths=['.gitignore','src/RealisticVisionMod.as','decisions/decisions.md','build/effect-load','build/effect-load-v2','build/effect-load-v3','knowledge/experiments/2026-10-24-effect-load.md',ARCHIVE]
 subprocess.run(['git','add','--',*paths],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',ARCHIVE],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  data=(OUT/'owned-state'/name).read_bytes();assert b'\r' not in data
  oid=git('hash-object','-w','--stdin',input=data).decode().strip()
  subprocess.run(['git','update-index','--cacheinfo','100644',oid,'state/'+name],cwd=MOD,check=True)
 pins=json.loads((MOD/ARCHIVE/'archive.json').read_text())
 for rel,digest in pins.items():
  assert hashlib.sha256((MOD/ARCHIVE/rel).read_bytes()).hexdigest()==digest
  assert hashlib.sha256(git('show',':'+ARCHIVE+'/'+rel)).hexdigest()==digest,rel
 assert not git('diff','--cached','--name-only','--','src/RVAuthorityView.as','tests/authority/AuthorityViewChecks.as').strip()
 remaining=git('diff','--numstat').decode().splitlines()
 assert set(remaining)=={'24\t0\tsrc/RVAuthorityView.as','2\t0\tstate/MEMORY.md','4\t0\tstate/journal.md','15\t0\ttests/authority/AuthorityViewChecks.as'},remaining
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print('D43 stage/archive hashes verified',len(pins))
if __name__=='__main__':main()
