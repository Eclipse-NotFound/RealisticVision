"""Freeze rejected D49 evidence and only our state/index changes."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys,time
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/fog-setters-output';GAME=MOD.parents[1];DEST=MOD/'knowledge/experiments/fog-setters-d49-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('eb5095a')
assert not git('diff','--cached','--name-only').strip()
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f','../../pfe.swf':'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7'}
assert all(sha(MOD/p)==h for p,h in expected.items())
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry,Registration
active=[r for r in Registry().status() if r['state'] in ('running','waiting','needs-check')]
assert not [r for r in active if 'RealisticVision' in r['owner']]
older={r['id'] for r in active};deadline=time.monotonic()+900
if older:print('Allow earlier registered tests before archive IO: '+','.join(sorted(older)),flush=True)
while older:
 older={r['id'] for r in Registry().status() if r['id'] in older and r['state'] in ('running','waiting','needs-check')}
 if not older:break
 assert time.monotonic()<deadline,'Archive deferred; no IO performed';time.sleep(5)
with Registration(owner='RealisticVision / D49 证据收尾',purpose='非游戏；归档和索引字节核对',run_dir=OUT,evidence=DEST/'archive.json',wait=900) as rec:
 assert not DEST.exists();DEST.mkdir(parents=True)
 reject=OUT/'candidates/guard/not-adopted.json';assert not reject.exists()
 reject.write_text(json.dumps({'adopted':False,'reason':'414 pixel checks passed; complete same-process combat has no consistent improvement in either mode.','formalUnchanged':expected},indent=2)+'\n',encoding='utf-8')
 pins={}
 for top in ['local-01','native-01','combat-01','profile-01','candidates','group-steps']:
  folder=OUT/top
  if top.endswith('01'):
   assert json.loads((folder/'last-run.json').read_text())['exit']==0
   assert not(folder/'test.xml').exists()
  for p in folder.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(folder)
   keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png') or p.name=='not-adopted.json'
   if keep:
    q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
 shutil.copyfile(OUT/'inputs.json',DEST/'inputs.json');pins['inputs.json']=sha(DEST/'inputs.json')
 (DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
 receipt={'formalUnchanged':expected,'checks':414,'combatPairedIntervals':2148,'adopted':False,'activeOwnedGameTests':0,'profile':'D44 nested diagnostic only; not performance acceptance'}
 (DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');pins['finish.json']=sha(DEST/'finish.json')
 (DEST/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 head='> 2026-10-25 **D49结束，正式仍D44**：雾层同值setter跳过通过414项严格画面检查；完整战斗current61.47→61.77ms、classic65.70→66.44ms，>100ms未降，不采用。原始D44嵌套热点：current fillFogCache4.56ms，classic classicLogicRegion3.46ms，滤镜树0.02–0.04ms；不能相加或当性能验收。下一步检查classic原始插值工作图复用，仍只按旧查询范围发布，不扩大fogCache范围。所有本轮AIR已退出；详见[报告](../knowledge/experiments/2026-10-25-fog-setters.md)，证据fog-setters-d49-20261025。'
 stop='- D49已结束，无RV测试占用；guard无收益不采用。基线仍准确D44。下一步先核对classicLogicRegion的重复raw/visibility/wall插值：私有工作图可扩大预计算，但fogCache只能按旧查询确切范围发布，避免D40显示副作用；current另看fillFogCache。D49profile含计时插桩，仅定位。CS请求后续窗口，已停止追加游戏，归档等待既有测试。下方为历史停点。'
 journal='''## 2026-10-25 — D49同值雾设置无整体收益，热点收窄

- 独立D44候选只跳过同值显示setter，保留实际状态读取/恢复及常亮临时解罩。120帧整雾+230墙体+64原生整雾严格相同，原生捕获前不扩大classic查询。
- 完整14入口组合与额外RV子域、原生六敌、两模式12窗共2148有效间隔。current61.47→61.77ms、classic65.70→66.44ms，>100ms5→7/15→16，无收益，未采用/未部署。
- 原始D44另做两窗嵌套热点：current fillFogCache4.56ms，classic classicLogicRegion3.46ms；滤镜树约0.02–0.04ms。插桩数据不能相加或与干净轮拼接。下一步核对classic私有插值工作图复用，保留原发布查询范围。
- 正式638E/config5136/rootA796不变，4项authority外部WIP保留；所有AIR/描述符退出，无出站消息。D48收尾提交eb5095a并补台账。D49报告knowledge/experiments/2026-10-25-fog-setters.md，证据fog-setters-d49-20261025，目标未完成。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
 for name in ['MEMORY.md','journal.md']:
  base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
  def transform(s):
   if name=='journal.md':return journal+s
   at=s.index('> 2026-10-25 **D48');s=s[:at]+head+'\n\n'+s[at:]
   pos=s.index('\n\n',s.index('## 4. 正在进行与停点'))+2;return s[:pos]+stop+'\n\n'+s[pos:]
  (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
 for p in (MOD/'build/fog-setters').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 subprocess.run(['git','add','--','.gitignore','build/fog-setters','knowledge/experiments/2026-10-25-fog-setters.md'],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',str(DEST)],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  digest=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=MOD,input=(owned/name).read_bytes()).decode().strip();subprocess.run(['git','update-index','--cacheinfo','100644,'+digest+',state/'+name],cwd=MOD,check=True)
 for rel,h in pins.items():assert hashlib.sha256(git('show',':'+(DEST/rel).relative_to(MOD).as_posix())).hexdigest()==h,rel
 assert sorted(line.split() for line in git('diff','--numstat').decode().splitlines())==sorted([['24','0','src/RVAuthorityView.as'],['2','0','state/MEMORY.md'],['4','0','state/journal.md'],['15','0','tests/authority/AuthorityViewChecks.as']])
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print(json.dumps(receipt,ensure_ascii=False),flush=True);rec.outcome='passed';rec.note='仅归档核验，不是新增游戏测试；候选不采用'
