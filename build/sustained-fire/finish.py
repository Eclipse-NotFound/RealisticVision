"""D54 evidence and state checkpoint. No deployment; exclude private save data."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/sustained-fire-output'
DEST=MOD/'knowledge/experiments/sustained-fire-d54-20261028'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('5ae5443')
assert not git('diff','--cached','--name-only').strip()
formal={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'}
assert all(sha(MOD/p)==h for p,h in formal.items())
assert not git('diff','--','src/RealisticVisionMod.as').strip()
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registry
assert not [r for r in Registry().status() if r['owner'].startswith('RealisticVision / D54') and r['state'] in ('waiting','running','needs-check')]
runs=[p for p in OUT.iterdir() if p.is_dir() and p.name.rsplit('-',1)[-1].isdigit()]
counts={};scene_checks={}
for folder in runs:
 assert not (folder/'test.xml').exists(),folder
 if (folder/'build.json').exists():
  for rel,h in json.loads((folder/'build.json').read_text()).get('files',{}).items():assert sha(folder/rel)==h,(folder.name,rel)
 if (folder/'analysis.json').exists():
  data=json.loads((folder/'evidence/result.json').read_text());cs=data.get('cases',[])
  counts[folder.name]={'windows':len(cs),'intervals':sum(sum('nextInterval' in f for f in c['frames']) for c in cs),'shots':sum(c['attacks'] for c in cs),'windowVisible':data.get('windowVisible'),'scene':data.get('scene'),'environment':json.loads((folder/'environment.json').read_text())}
 if (folder/'validation.json').exists():scene_checks[folder.name]=json.loads((folder/'validation.json').read_text())
assert scene_checks['integer-v2-pixels-25']['checks']==721
assert scene_checks['integer-v2-native-26']['checks']==888
assert scene_checks['pixel-cache-pixels-29']['checks']==721
assert not scene_checks['direct-v2-pixels-32']['passed']
assert counts['visible-split-28']['intervals']==1432 and counts['visible-split-28']['shots']==1055
for name in ['trailing-present-16','integer-present-20','integer-v2-present-27','visible-split-28','pixel-cache-present-30']:
 assert counts[name]['windowVisible'] is True and counts[name]['environment']['performanceEligible']
assert not DEST.exists();DEST.mkdir(parents=True);pins={}
for folder in runs+[OUT/'candidates',OUT/'baseline',OUT/'production']:
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  # Never include app Local Store, player-seed, private frame logs or native media.
  if any(v in rel.parts for v in ('storage','Local Store','player-seed','player-evidence')):continue
  keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt')
  keep=keep or 'evidence' in rel.parts and p.suffix in ('.json','.png')
  keep=keep or p.name in ('rv.swf','baseline.swf','candidate.swf','EffectLoadChecks.swf','CombatRenderProbeMod.swf','EffectVisibilityProbeMod.swf','CandidateOptionsProbe.swf')
  keep=keep or folder.name=='production' and p.name=='RealisticVisionMod.swf'
  if keep:
   q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
receipt={'formalUnchanged':formal,'adopted':False,'deployed':False,'resolved':False,'allOwnedRunsFinished':True,'timingRuns':counts,'visualChecks':scene_checks,'rootHostSha256':sha(GAME/'pfe.swf'),'boundary':'Different processes regenerated random layouts; compare conditions within each process only. Private-desktop visible is not foreground human verification.'}
(DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');pins['finish.json']=sha(DEST/'finish.json')
(DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
(DEST/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
header='> 2026-10-28 **D54最大化持续扫射已复现额外成本，未修复/未部署，正式仍D44**：用户已确认正式启动器、current、轻机枪整个持续扫射、最大化窗口。只读存档副本+原生keyAttack、容量内补弹、单人固定位置，独立私有桌面实际visible=true。28拆分正常53.96/禁鼠标54.17/计算后撤罩48.51/跳过特效46.11ms，支持动态特效绘制线索；撤罩不是修复。integer-v2通过721+888严格检查但27整帧回退；预绘共享通过721但整体收益不稳定，直接Bitmap两版f121差异，均不采用。候选v0.33.11-trailing-cache未部署，不能安装。主src/release不变，自有AIR全退出，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-sustained-fire.md)，工具build/sustained-fire。'
journal='''## 2026-10-28 — D54正式存档、最大化窗口持续轻机枪调查

- 用户补全正式启动器/current/持续扫射/最大化条件。复制自动存档到独立ID，经原生输入实际开火；随机地图重新生成，不称精确现场回放。修正直接loadGame、超容量补弹、误读未发布FA字段、窗口visible未生效及测试舞台缩放等失真，失败全部保留。
- 右下裁切、整数裁切及预绘共享路径有严格画面通过，但实际显示窗整帧收益不稳定。integer-v2的721+888通过不能替代性能；27 current55.58→57.26ms且长帧更多，拒绝部署。tight/grid/cell/scroll/direct位图失败均淘汰。未采用的v0.33.11-trailing-cache包没有门禁通过记录。
- 28最大化显示窗8窗1432间隔/1055次开火：正常53.96、禁鼠标54.17、计算后撤罩48.51、跳过特效46.11ms。支持动态遮罩绘制方向，不把差值独占归GPU，也不通过撤罩或删动画修复。当前仍未达到接近原版流畅度。
- 正式638E/config5136和主源码不变，用户存档/游戏未写或终止，全部自有AIR/描述符/登记已结束。归档sustained-fire-d54-20261028，不包含私有种子/原始帧记录。接续建议同一原生动画/位置/视野的绘制回放，尚未实现；仍需真实射击终验。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
 def transform(s):
  if name=='journal.md':return journal+s
  pos=s.index('\n\n')+2;s=s[:pos]+header+'\n\n'+s[pos:]
  old='- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。D50/D51已恢复独立战斗复验，未证实稳定整帧收益，未采用；正式安装未改，详见顶部D52报告。'
  new='- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。最新D54已匹配正式入口、存档轻机枪和最大化窗口，确认持续特效遮罩额外成本，但候选均未形成可靠修复，未采用/部署；详见顶部D54报告。'
  assert old in s;s=s.replace(old,new)
  marker='## 4. 正在进行与停点\n\n';assert marker in s
  s=s.replace(marker,marker+'- D54：正式最大化窗口持续射击问题仍未解决；无需再问启动入口/武器/是否持续/窗口状态。所有本轮测试已结束，勿安装忽略目录production的未采用v0.33.11。优先区分同输入绘制成本，保留原生开枪实测作验收；下方是历史停点。\n\n',1)
  return s
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
for p in (MOD/'build/sustained-fire').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
git('add','--','.gitignore','build/sustained-fire','knowledge/experiments/2026-10-28-sustained-fire.md')
git('add','-f','--',str(DEST))
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(owned/name).read_bytes()).decode().strip();git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()}
assert actual==expected,actual
paths=list(pins);prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in paths)+'\n').encode());offset=0
for rel in paths:
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob'
 size=int(header[2]);data=raw[end+1:end+1+size];offset=end+size+2
 assert hashlib.sha256(data).hexdigest()==pins[rel],rel
assert offset==len(raw)
git('diff','--cached','--check')
print(json.dumps({'files':len(pins),'bytes':sum((DEST/p).stat().st_size for p in pins),'formalUnchanged':True,'resolved':False,'deployed':False,'timingRuns':list(counts)},ensure_ascii=False))
