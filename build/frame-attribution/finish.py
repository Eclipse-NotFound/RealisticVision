"""Archive D47 exact evidence, preserving independently owned working changes."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/frame-attribution-output';GAME=MOD.parents[1]
DEST=MOD/'knowledge/experiments/frame-attribution-d47-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('d5ab035')
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f','../../pfe.swf':'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7'}
assert all(sha(MOD/p)==digest for p,digest in expected.items()),'Installation changed'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry
active=[r for r in Registry().status() if r['state'] in ('waiting','running','needs-check')]
assert not [r for r in active if 'RealisticVision' in r['owner']],'Owned tests still active'
assert not DEST.exists();DEST.mkdir(parents=True)
paths=[OUT/'asset-deduplication.json',OUT/'knowledge-receipt.json',OUT/'order-reviewed.json']
for name in ['native-timing-01','native-timing-02','cache-inventory-01','identity-pixels-01','identity-native-01','identity-lifecycle-01','identity-combat-01']:
 folder=OUT/name
 assert json.loads((folder/'last-run.json').read_text())['exit']==(1 if name=='native-timing-01' else 0)
 assert not (folder/'test.xml').exists(),name
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png'):paths.append(p)
for name in ['candidates','group-steps','loader-order','native-source']:
 paths.extend(p for p in (OUT/name).rglob('*') if p.is_file() and p.suffix in ('.as','.json','.log'))
pins={}
for p in paths:
 rel=p.relative_to(OUT);target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);pins[rel.as_posix()]=sha(target)
attributes=DEST/'.gitattributes';attributes.write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(attributes)
receipt={'formalUnchanged':expected,'activeOwnedTests':0,'activeOthers':[{k:r.get(k) for k in ('id','owner','state')} for r in active],'archivedFiles':len(pins),'adopted':False,'candidateChecks':1309,'nativeTimingPairedIntervals':2864,'combatPairedIntervals':2148}
(DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['finish.json']=sha(DEST/'finish.json')
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
head='> 2026-10-25 **D47结束，正式仍D44**：2864个完整间隔已区分原生函数/其它监听/RV/剩余，六敌场景RV约13–14ms；318ms峰值发生于关闭RV且无弹体，不能把剩余全部归GPU。恒亮实际范围撤mask候选通过1309项，但12战斗窗current67.69→68.16ms、classic70.75→69.25ms，尾部不一致，无稳定收益，不采用。所有本轮AIR和队列结束；下一步验证相邻动画共用模糊场，先证明局部边界等价。详见[报告](../knowledge/experiments/2026-10-25-frame-attribution.md)，证据frame-attribution-d47-20261025；方法已补KB-000107 r3，目标仍未完成。'
stop='- D47已结束，没有RV运行/排队；identity不采用，安装仍D44。原生包装已确认RV额外开销主要在自身与尚未完全归因的剩余区间。下一步从准确D44源评估相邻动画共用模糊视野场；局部裁切/房间边缘/宽滤镜/cache语义未证明等价前不推进生产。不要重复D45/D46/D47已否定的微优化。下方为历史停点。'
journal='''## 2026-10-25 — D47完整帧归因与恒亮遮罩候选未采用

- 核对准确A796宿主的MainMenu注册/加载顺序，以独立包装直接计时原生函数；2864间隔四段恒等、调用序号及世界步增量通过。首次包外读internal t_save失败，改测试专用同包访问器后另名复验，失败原件保留。剩余区间仍含事件/帧率等待/调度，不称纯GPU；318ms峰值发生在RV关闭且无弹体。
- 两窗隐藏缓存清点只含原生cache=true对象，可操作数量很少。identity保留目标cache、只撤实际全亮范围mask，361严格图像/阳性1767次、888原生、60状态恢复共1309项通过；无原生包装12战斗窗无两模式稳定收益，未采用/未部署。
- 正式RV638E…3710、config5136…A3C7F、rootA796…238B7不变，主源码与四项外部WIP保留。自有已结束D45/D46只读相同媒体硬链接释放645682232B，未删独有证据。所有本轮AIR退出、描述符/登记释放，无出站协调消息。
- 方法经experience-to-knowledge 2026-09-16.1补入KB-000107 r3并回读；报告knowledge/experiments/2026-10-25-frame-attribution.md，证据frame-attribution-d47-20261025，工具build/frame-attribution。下一步验证相邻动画共用模糊场，先核边界等价，再做整体性能；目标未完成。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
 def transform(s):
  if name=='journal.md':return journal+s
  at=s.index('> 2026-10-25 **D46');s=s[:at]+head+'\n\n'+s[at:]
  at=s.index('## 4. 正在进行与停点');pos=s.index('\n\n',at)+2;return s[:pos]+stop+'\n\n'+s[pos:]
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
print(json.dumps(receipt,ensure_ascii=False))
