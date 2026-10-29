"""Freeze D58 evidence after all owned instances finish; no deployment."""
from pathlib import Path
import gzip,hashlib,json,re,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1]
OUT=MOD/'build/combat-split-output';DEST=MOD/'knowledge/experiments/combat-split-d58-20261029'
OLD='bd64b5bbfe5a07a0b5bff38e4c344652e1df526cfd5c308d63b607123ce4a9ad'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*a):return subprocess.run(['git',*a],cwd=MOD,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('d29db85')
assert not git('diff','--cached','--name-only').strip()
assert sha(MOD/'release/RealisticVisionMod.swf')==OLD
assert sha(MOD/'release/config.txt')=='5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'
assert not git('diff','--','src/RealisticVisionMod.as','release').strip()
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry
assert not [v for v in Registry().status() if v['owner'].startswith('RealisticVision / D58') and v['state'] in ('waiting','running','needs-check')]
runs=sorted(p for p in OUT.iterdir() if p.is_dir() and re.match(r'^\d\d-',p.name))
assert not any((p/'test.xml').exists() for p in runs)
decision=json.loads((OUT/'decision.json').read_text());assert decision['deployed'] is False
summary={}
for p in runs:
 row={}
 for name in ['validation.json','analysis.json','environment.json']:
  if (p/name).exists():row[name]=json.loads((p/name).read_text())
 result=p/'evidence/result.json'
 if result.exists():
  data=json.loads(result.read_text());cs=data.get('cases',[])
  row['windowCount']=len(cs);row['completeIntervals']=sum(sum('nextInterval' in f for f in c['frames']) for c in cs)
  row['samplePlayerShotsLowerBound']=sum(c.get('samplePlayerShotsLowerBound',0) for c in cs)
  row['sampleEnemyShotsLowerBound']=sum(c.get('sampleNativeEnemyShotsLowerBound',0)+c.get('sampleForcedEnemyShots',0) for c in cs)
  row['nativeMenuClosed']=data.get('nativeMenuClosed')
  row['windows']=[{k:c.get(k) for k in ['mode','variant','actualStageRate','windowActive','retained','samplePlayerShotsLowerBound','sampleNativeEnemyShotsLowerBound','sampleForcedEnemyShots']} for c in cs]
 log=(p/'result.txt').read_text(errors='replace') if (p/'result.txt').exists() else ''
 if 'SUPPORT ' in log:row['support']=json.loads(re.search(r'SUPPORT (\{[^\n]+\})',log)[1])
 if 'FRACTION HITS ' in log:row['fractionHits']=int(re.search(r'FRACTION HITS (\d+)',log)[1])
 summary[p.name]=row
assert not DEST.exists();DEST.mkdir(parents=True)
objects={};mapping={};pins={};compressed={}
def copy(p,rel):
 q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[rel]=sha(q);return rel
for parent in runs+[OUT/'baseline',OUT/'candidates',OUT/'native-source']:
 for p in parent.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(parent);original=p.relative_to(OUT).as_posix()
  if any(x in rel.parts for x in ['storage','Local Store','player-seed','player-evidence']):continue
  keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ['.json','.log','.txt','.png']
  keep=keep or 'evidence' in rel.parts and p.suffix in ['.json','.png']
  binary=p.name in ['rv.swf','candidate.swf','vector.swf','EffectLoadChecks.swf','CombatRenderProbeMod.swf']
  if not(keep or binary):continue
  if p.suffix in ['.as','.swf']:
   key=(sha(p),p.suffix)
   if key not in objects:objects[key]=copy(p,'objects/'+key[0]+p.suffix)
   mapping[original]={'sha256':key[0],'stored':objects[key]}
  elif p.suffix=='.json' and p.stat().st_size>100000:
   stored=original+'.gz';q=DEST/stored;q.parent.mkdir(parents=True,exist_ok=True)
   q.write_bytes(gzip.compress(p.read_bytes(),compresslevel=9,mtime=0));pins[stored]=sha(q)
   assert gzip.decompress(q.read_bytes())==p.read_bytes()
   compressed[original]={'stored':stored,'originalSha256':sha(p),'storedSha256':sha(q)}
  else:copy(p,original)
for name in ['frozen.json','job-query.json','decision.json']:
 if (OUT/name).exists():copy(OUT/name,name)
save(DEST/'object-map.json',mapping);pins['object-map.json']=sha(DEST/'object-map.json')
save(DEST/'compressed-map.json',compressed);pins['compressed-map.json']=sha(DEST/'compressed-map.json')
finish={**decision,'installedSha256':OLD,'runs':summary,'allOwnedRunsFinished':True}
save(DEST/'finish.json',finish);pins['finish.json']=sha(DEST/'finish.json')
(DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
save(DEST/'archive.json',pins)
print(json.dumps({'runs':len(runs),'files':len(pins),'bytes':sum((DEST/p).stat().st_size for p in pins),'installedUnchanged':True}))
