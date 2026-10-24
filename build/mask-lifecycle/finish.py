"""Freeze D46 evidence and update only this task's state, preserving other WIP."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-lifecycle-output';GAME=MOD.parents[1]
DEST=MOD/'knowledge/experiments/mask-lifecycle-d46-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('43e7121')
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f','../../pfe.swf':'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7'}
assert all(sha(MOD/p)==h for p,h in expected.items()),'Formal installation drift'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registry
rows=Registry().status()
active=[r for r in rows if r['state'] in ('waiting','running','needs-check')]
assert not [r for r in active if 'RealisticVision' in r['owner']],'Owned testing still active'
assert not DEST.exists(),'Do not overwrite archive'
DEST.mkdir(parents=True)
paths=[OUT/'inputs.json']
for name in ['release-observe-01','carry-pixels-01','carry-native-01','carry-controlled-01']:
 folder=OUT/name;assert json.loads((folder/'last-run.json').read_text())['exit']==0
 assert not (folder/'test.xml').exists(),name
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png'):paths.append(p)
for folder in [OUT/'candidates',OUT/'group-steps']:
 paths += [p for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.json','.log')]
pins={}
for p in paths:
 rel=p.relative_to(OUT);target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);pins[rel.as_posix()]=sha(target)
attributes=DEST/'.gitattributes';attributes.write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(attributes)
receipt={'formalUnchanged':expected,'activeOwnedTests':0,'activeOthers':[{k:r.get(k) for k in ('id','owner','state')} for r in active],'archivedFiles':len(pins),'adopted':False}
(DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['finish.json']=sha(DEST/'finish.json')
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
head='> 2026-10-25 **D46结束，正式仍D44**：清理观察四窗2156配对帧，28个实际释放帧41–93ms，505ms峰值发生时没有释放，不支持集中释放主因，未做分帧释放。相同输入分类复用carry通过361+888检查、阳性40453次，但12战斗窗整体无稳定收益（current63.75→63.52ms、classic60.23→61.89ms），未采用。所有本轮AIR和队列结束，不再追加争占测试。下一步区分RV调用外的宿主/绘制/调度开销，避免继续只减局部CPU。详见[报告](../knowledge/experiments/2026-10-25-mask-lifecycle.md)，证据mask-lifecycle-d46-20261025；目标尚未解决。'
stop='- D46已结束，当前无RV测试或队列，carry不采用，安装仍D44。下一步区分完整帧中RV调用以外的成本，并量化动态遮罩绘制/分配；集中清理已有反证，不重复D45/D46失败候选。保持画质和刷新率。下方均为历史停点。'
journal='''## 2026-10-25 — D46清理反证与分类复用候选未采用

- 基于准确D44源，清理观察四窗2156配对帧：28个实际释放帧均低于100ms，单次75–202栅格、约52–135万像素；505ms等峰值没有当帧释放。暂停分帧释放方向，不把相关性或内存下降一概当GC。
- carry只复用已有完整输入相等分支的明暗分类，361严格图像/阳性及888原生检查通过，复用40453次；完整14项组合12战斗窗验证真实开火与源指纹。current63.75→63.52ms但>100次数8→12；classic60.23→61.89ms且尾部不利。没有稳定整体收益，不采用、不部署。
- 正式RV638E…3710、config5136…A3C7F、rootA796…238B7不变；未改主源码、玩家存储或其它模组。所有本轮AIR退出、描述符及共享登记清理；当前批后没有追加测试，无出站协调消息。
- 下一步区分RV调用外的宿主/绘制/调度开销，再确定改动；整体目标未完成。报告knowledge/experiments/2026-10-25-mask-lifecycle.md，冻结证据mask-lifecycle-d46-20261025，工具build/mask-lifecycle。D45报告已追加全局台账。

'''
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
 def transform(s):
  if name=='journal.md':return journal+s
  at=s.index('> 2026-10-25 **D45');s=s[:at]+head+'\n\n'+s[at:]
  at=s.index('## 4. 正在进行与停点');pos=s.index('\n\n',at)+2
  return s[:pos]+stop+'\n\n'+s[pos:]
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n')
 (MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
print(json.dumps(receipt,ensure_ascii=False))
