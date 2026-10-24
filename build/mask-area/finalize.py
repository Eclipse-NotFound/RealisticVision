"""Finish the D45 record without folding the separate authority WIP into it."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
DEST=MOD/'knowledge/experiments/mask-area-d45-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((DEST/'archive.json').read_text())
for path,digest in pins.items():assert sha(DEST/path)==digest,path
for parent in [OUT/'candidates',OUT/'group-steps']:
 for source in parent.rglob('*'):
  if not source.is_file() or source.suffix not in ('.as','.json','.log'):continue
  rel=source.relative_to(OUT);target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert sha(target)==sha(source),rel
  else:shutil.copyfile(source,target)
  pins[rel.as_posix()]=sha(target)
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
new_head='> 2026-10-25 **D45结束，三候选均未采用，正式仍D44**：tileclip有19像素差异；precise及cacheoff严格图像通过，但完整战斗性能未达标。四轮64窗包含40窗受限分组诊断，不能算生产验收；源指纹、实际14项加载与真实开火已核对。cacheoff的classic均值66.81→76.15ms、>100ms次数20→58，拒绝部署。旧mask计数含Shape反向链接，已纠正。两簇长停顿从60帧清理点开始，仍只是关联；下一步测释放数量/像素量。所有本轮AIR和队列结束。详见[报告](../knowledge/experiments/2026-10-25-mask-area.md)，工具build/mask-area，冻结证据knowledge/experiments/mask-area-d45-20261025。'
new_stop='- D45已结束，三候选不采用，当前没有RV测试或队列。下一步基于D44准确源验证集中释放与长帧的关联，再决定是否分帧释放；不降低画质/刷新率，不重跑覆盖D45已结束目录。目标尚未解决。下方为历史停点。'
new_journal='''## 2026-10-25 — D45动态遮罩候选与诊断纠正（结束，未部署）

- 保持D44准确安装638E…3710，主源码和配置未改。tileclip严格图像失败；precise和cacheoff图像通过但整帧不利，三者不采用。
- precise 360+888及361阳性组通过；cacheoff 361+888组通过、实际关闭缓存19182次。cacheoff完整战斗current均值67.65→64.39ms但峰值158→254ms，classic66.81→76.15ms、>100ms次数20→58。
- 四轮64战斗窗的源指纹、14项实际加载、真实开火均通过；两轮分组共40窗仅为受限诊断。首轮逐帧拆装有干扰，第二轮接入点抑制仍改变缓存策略/可见工作量，不能直接作独占成本。旧mask计数含Shape互指，实际目标计数已补充。
- 两簇长停顿与60次清理点重合，其它长帧不重合；下一步记录释放数量/像素量再验证分帧释放，尚未实现。所有本轮AIR退出、描述符和登记清理，无出站协调消息。目标继续。
- 报告knowledge/experiments/2026-10-25-mask-area.md；原始日志、失败图、准确候选源及指纹已归档于mask-area-d45-20261025。保留外部authority四项WIP，不部署失败候选。

'''
for root in [MOD/'state',OUT/'owned-state']:
 p=root/'MEMORY.md';s=p.read_text(encoding='utf-8');old=next(x for x in s.splitlines() if x.startswith('> 2026-10-25 **D45'))
 s=s.replace(old,new_head,1)
 old=next(x for x in s.splitlines() if x.startswith('- D45尚有'))
 p.write_text(s.replace(old,new_stop,1),encoding='utf-8',newline='\n')
 p=root/'journal.md';s=p.read_text(encoding='utf-8');start=s.index('## 2026-10-25 — D45');end=s.index('## 2026-10-25 — D44',start)
 p.write_text(s[:start]+new_journal+s[end:],encoding='utf-8',newline='\n')
report=MOD/'knowledge/experiments/2026-10-25-mask-area.md';s=report.read_text(encoding='utf-8')
s=s.replace('仍需整帧收益判断。','整帧结果不利，见下，不采用。').replace('4. cacheoff待测：','4. cacheoff：').replace('其收益和滤镜/生命周期安全性独立验证，不因推理合理直接采用。','其滤镜/生命周期图像检查通过，整帧结果不利，见下，不采用。')
s=s.replace('分组诊断将分别撤下','分组诊断分别撤下').replace('下一轮split-controlled-02','第二轮split-controlled-02')
s+='\n收尾只读核对：正式RV仍638E2D40…FE343710、config仍5136EE19…79A3C7F、根pfe仍A7968271…A238B7；本轮没有替换它们。\n'
report.write_text(s,encoding='utf-8',newline='\n')
p=MOD/'build/mask-area/README.md';s=p.read_text(encoding='utf-8');start=s.index('当前结果：');end=s.index('\n\n`cacheoff.py`',start)
s=s[:start]+'当前结果：三候选均未采用，安装仍D44。tileclip像素失败；precise及cacheoff通过图像但完整战斗不利。两轮分组共40窗有明确归因限制；所有步骤已结束，禁止覆盖原结果重跑。下一步另建实验验证旧遮罩释放与长帧的关联。完整说明见`knowledge/experiments/2026-10-25-mask-area.md`（相对模组根）。'+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
print('D45 finalized, archived',len(pins),'files')
