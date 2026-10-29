"""Stage D57 ownership only; preserve the four pre-existing authority edits."""
from pathlib import Path
import ast,hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/enemy-combat-output'
DEST=MOD/'knowledge/experiments/enemy-combat-d57-20261029'
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('ee2c1a7')
assert not git('diff','--cached','--name-only').strip()
finish=json.loads((DEST/'finish.json').read_text());assert finish['allOwnedRunsFinished'] and not finish['deployed']
header='> 2026-10-29 **D57六敌交战调查结束，未采用/未部署，正式仍D56**：身体裁切1531项、alpha裁切722项+原生60帧、减少临时对象723项均有功能证据，但整帧收益不稳定或回退。纠正菜单显示层残留、原生后固定狮鹫姿态及kol_shoot计数；纠正后68窗11692完整间隔（含内存归因）。长帧分布原生/RV/其它监听/绘制后等待；部分内存骤降不证明全由RV分配。22个实验均结束，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-29-enemy-combat.md)；工具build/enemy-combat，经验KB-000123 r4。'
journal='''## 2026-10-29 — D57六敌交战与长帧归因，三候选未采用

- 用户确认扫射已缓解、与敌人交战仍卡。以正式D56准确生产源做六狮鹫SMG加玩家LMG、最大化私有桌面测试，不动玩家存档/进程和正式release。
- 修正旧驱动active=false仍保留菜单显示层的问题，11起mainMenuOff；12起原生更新前固定敌人位置，确保手臂/身体同步，并将kol_shoot正差值记为采样期下界。旧D54–D56同轮相对观察保留，正常显示状态的表述受此纠正限制。
- 身体/血条/武器裁切最终1531项、alpha内容裁切722项及原生60帧、无用m3/首像素判定723项均通过功能检查；完整交战或反向复测无稳定收益。最后current首轮62.28→51.88ms、反向55.05→58.43ms；classic两轮回退，全部拒绝合并/部署。
- 纠正后68窗11692完整间隔，采样玩家开火下界5670、敌人12505；19是内存归因而非性能验收。RV计算内出现55–68MiB下降的长帧，但全局回收来源未定；后续RENDER至native区间不是GPU独占。动态特效占hideEnemies大部分局部CPU，身体/武器计算小，不将其外推成全部渲染成本。
- 正式仍BD64B5BB…CE4A9AD，主src和release不改；22个实验含编译失败/像素反例已全部退出。约22MB去重/压缩证据不含玩家种子；四项authority WIP保留。报告knowledge/experiments/2026-10-29-enemy-combat.md，方法纠正回流KB-000123 r4。
- 下一步优先细分原生更新和绘制后等待，寻找可重复的单一长帧条件；必要时拆分m3/首像素两项测量，不把分配减少等同流畅度，不重跑已否决的整套候选。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode();live=(MOD/'state'/name).read_text()
 def transform(text):
  if name=='journal.md':return journal+text
  pos=text.index('\n\n')+2;text=text[:pos]+header+'\n\n'+text[pos:]
  old='- 当前安装D56 v0.33.11-effect-clip，BD64B5BB…CE4A9AD；准确生产源build/effect-mask-origin-output/production/src，排除authority。current轻机枪持续扫射已改善，classic保持旧路径；仍有长帧和相对关闭RV的差距，详见顶部D56报告。'
  new=old+' D57六敌交战三候选均未获稳定整帧收益，未发布；纠正后的显示/姿态/计数边界与长帧分段见顶部D57报告。'
  assert old in text;text=text.replace(old,new)
  marker='## 4. 正在进行与停点\n\n';assert marker in text
  return text.replace(marker,marker+'- D57已结束并释放全部测试登记，正式仍D56。下一步定位原生更新/绘制后等待的具体长帧触发，暂不复用被否决候选。独立生产源与authority开发线继续隔离；下方保留历史停点。\n\n',1)
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
for p in (MOD/'build/enemy-combat').glob('*.py'):ast.parse(p.read_text())
pins=json.loads((DEST/'archive.json').read_text())
for rel,h in pins.items():assert hashlib.sha256((DEST/rel).read_bytes()).hexdigest()==h,rel
git('add','--','.gitignore','build/enemy-combat','knowledge/experiments/2026-10-29-enemy-combat.md')
git('add','-f','--',str(DEST))
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(owned/name).read_bytes()).decode().strip();git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()};assert actual==expected,actual
git('diff','--cached','--check')
prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in pins)+'\n').encode());offset=0
for rel in pins:
 end=raw.index(b'\n',offset);h=raw[offset:end].split();assert h[1]==b'blob';size=int(h[2]);data=raw[end+1:end+size+1];offset=end+size+2;assert hashlib.sha256(data).hexdigest()==pins[rel],rel
assert offset==len(raw)
print(json.dumps({'stagedArchiveFiles':len(pins),'externalChangesPreserved':actual,'deployed':False}))
