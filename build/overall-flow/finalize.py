"""Archive D40 attempted optimizations without promoting an unproven release."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import package as p
OUT,MOD=p.OUT,p.MOD
ARCHIVE='overall-flow-20261023';REPORT='2026-10-23-overall-flow.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def triple(a):return '/'.join(str(a[k]) for k in ['mean','p95','max'])
def main():
 proof=read('verified.json');perf=read('performance.json');manifest=read('production/manifest.json');decision=read('decision.json')
 assert proof['status']=='FUNCTIONAL_PASS_RELEASE_HELD' and decision['deployed'] is False
 assert sha(MOD/'release/RealisticVisionMod.swf')==read('inputs.json')['installed']
 archive=MOD/'knowledge/experiments'/ARCHIVE;archive.mkdir(exist_ok=False)
 files=[]
 for folder in OUT.iterdir():
  if not folder.is_dir() or folder.name in ['owned-state']:continue
  # Retain evidence and exact source/probe snapshots, not duplicate runtimes.
  for f in folder.rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   rel=f.relative_to(folder)
   if f.suffix in ['.json','.log','.png'] and not any(x in rel.parts for x in ['mods','data','Rooms']):files.append(f)
   elif f.suffix=='.as' and (rel.parts[0]=='src' or len(rel.parts)==1):files.append(f)
   elif f.name=='classes.txt':files.append(f)
 files += [f for f in OUT.iterdir() if f.is_file() and f.suffix in ['.json','.txt']]
 files=sorted(set(files))
 for f in files:
  dst=archive/f.relative_to(OUT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst);assert sha(dst)==sha(f)
 (archive/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8',newline='\n')
 (archive/'archive.json').write_text(json.dumps({f.relative_to(OUT).as_posix():sha(f) for f in files},indent=2)+'\n',encoding='utf-8',newline='\n')
 paired=[]
 for c in perf['paired']:
  a,b=c['updates'];paired.append(f"| {c['spec']['mode']} / {c['spec']['dim']} | {triple(a)} | {triple(b)} |")
 full=[]
 for label,key in [('原生跑动正序','native'),('原生跑动反序、低监测','reverse'),('脚本镜头扫动','sweep')]:
  for c in perf[key]:full.append(f"| {label} | {c['mode']} / {c['variant']} | {triple(c['interval'])} | {c['interval']['over50']}/{c['interval']['n']} | {triple(c['rv'])} |")
 report=f'''被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-mod-memory
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-23 整体流畅度与其他长帧：候选未发布

用户要求继续改善整体流畅度并定位其他长帧。本轮从D39准确生产源试验六种候选。**正式安装仍为v0.33.6-long-frame，83D8E590…205C7E65。未修改src或release，未部署v0.33.7候选。**

{decision['reason']}

## 候选与取舍

| 候选 | 处理 | 结论 |
|---|---|---|
| 01 | 跳过相同mask/层级/变换写入，未变场不重复paletteMap | 四组局部计时变化不稳定，没有选择 |
| 02 | 单前景路径直接复制alpha，免RGB比较 | 未稳定变快，部分变慢；未选择 |
| 03 | 在02基础上加入精确数值查表 | 组合没有稳定收益；未证明查表单独无效 |
| 04、06 | 雾层只显示视口小位图；06延后到单位遮罩之后快照 | 严格父层画面首组175126像素不同，最大19/255；修正取图顺序后仍失败，淘汰，不放宽容差 |
| 05 | classic将探索淡入更新和逐格准备合并，同一Tile读取三次减为一次 | 96组严格图像与36设置通过，局部CPU有小幅下降；整体收益未稳定，保留候选，未发布 |

05不改current算法，不改分辨率、刷新频率、视距、原生visi/t_visi、AI、地图和传送规则；helper与D39完全一致。墙芯/阶梯/防溢出/武器遮蔽/常亮开关保留。构建基于准确六类生产快照，不包含authority开发。候选包{manifest['bytes']}B，SHA `{manifest['swf']}`，版本字符串{p.VERSION}只是未发布候选。

## 严格正确性与取图纠正

`safe-classic-parent`64组覆盖两模式、亮度0/.35/.6/1、柔化0/40、视距.5/1/3、常亮和缩放；`safe-shared-parent`32组补默认设置和动态共享探索。每组比较最终父层像素、场、探索/淡入状态与敌人分类/遮罩，无像素容差。准确生产字节两进程36项设置/改键/保存通过，合计132项/组；原生24窗活动断言单列，不将历史D39的414项重复计数。

发现用于诊断的classicLogicRegion整房查询会更新显示墙影，故`safe-`驱动在此查询之前抓取实际完成画面。旧抓图结果保留为过程证据；局部小位图方案在纠正后仍失败，不能宣称只是测试误报。未执行的helper扩展不计入检查。

## 同输入局部CPU

192×75大场景、96人工单位，同进程交错，每版本每组120样本，不加函数分段计时。单位ms，均值/P95/最大；只能评价RV更新，不能换算FPS。current代码未改，其波动不是收益。

| 模式 / 记忆亮度 | D39更新 | 候选05更新 |
|---|---|---|
{chr(10).join(paired)}

此前分段诊断中prepareClassicCells 80次总耗时241→205ms、253→207ms；完整classic路径989→892ms、988→911ms。该数字来自插桩轮，不能与无插桩轮拼接。局部最大值有下降也有上升，未声称消灭峰值。

## 原生跑动、射击与完整间隔

两轮各12窗，每窗240记录帧，末帧没有下一次起点，排除后每模式/版本478个间隔。首次放置于已检查的平台，随后仅方向键/跑动控制；不逐帧传送或设镜头。每窗检查贴地≥220帧、距离≥300px、至少一次折返，持续原生开火及弹体存在。完整组合14入口requested/ok一致，版本输入有指纹约束。

正序为off/A/B/B/A/off，反序为off/B/A/A/B/off；反序还降低了环境观察开销，因此两轮不作“监测方式单变量因果”比较。世界和NPC持续演进，攻击次数与对象数量不会完全一致；即使反序结果更好，也不能覆盖正序的不利结果。off是同完整模组组合关闭RV，**不是纯净原版**。

| 场景 | 模式 / 版本 | 完整间隔均值/P95/最大ms | >50ms | RV更新均值/P95/最大ms |
|---|---|---|---|---|
{chr(10).join(full)}

## 其他长帧边界

- 原生跑动正序classic候选出现847ms间隔：本次RV22ms，其余825ms；对应后续early→live约799ms。玩家贴地、镜头缓存没有变化，155单位、433对象、1弹体。它不是D39已修的镜头跨缓存集中重建；尚不能归因到具体宿主函数、其他回调或调度。
- 同一轮D39 classic的166/164ms间隔内，RV分别115/121ms，System.totalMemory减少约76/82MiB。这只支持内存回收相关线索，不能证明GC是唯一原因；没有强制GC或降低刷新频率来掩盖问题。
- 单独显示排除试验仍运行D39计算，只隐藏最终雾层，出现885ms间隔、RV26ms、其余859ms，说明雾层绘制不足以解释所有峰值。这个改变了视觉的诊断从未发布。
- 外部CPU诊断`system-battle`本身每次采样最高263ms，且采样起点与实际CPU读取时间不重合。原`system-analysis.json`把差值当帧内CPU上界的说法无效，由`system-analysis-corrected.json`明确纠正；该轮不作发布性能验收，也不据此认定GPU/GC/缺页原因。反序改为运行中只读自己进程及内存，保留采样耗时；共享登记仍负责测试排他。

原生时间戳使用同一个监听器连续起点差，RV绝对起止逐行校验。剩余时间包含其他脚本、绘制与系统调度，不能称为GPU。环境采样未见并行AIR/JVM仅是采样边界内结论；反序运行中没有全面枚举其他进程，不声称全机无干扰。

## 发布状态与接续

本轮没有安全地证明两种模式整体已接近原版，也没有完成其他长帧根因的函数级定位。正式D39和四项外部authority WIP保持原样；未生成新的部署备份或修改玩家配置。candidate05保留供后续合并；发布器拒绝`FUNCTIONAL_PASS_RELEASE_HELD`状态，不能把132项功能通过当性能发布通过。

后续若继续，应围绕已记录的early→live长停顿进一步分离原生主循环与其他回调，并用低开销采样复核；不要重复试验已失败的alpha/局部位图方案，也不要把脚本传送当真实跑动。协作消息仅向用户已授权的RConnect会话发送，未新增委托。全部测试用唯一AIR ID、独立存储、隐藏私有桌面和共享登记，结束后自有进程退出。

证据：[performance.json]({ARCHIVE}/performance.json)、[verified.json]({ARCHIVE}/verified.json)、[决策]({ARCHIVE}/decision.json)。
'''
 (MOD/'knowledge/experiments'/REPORT).write_text(report,encoding='utf-8',newline='\n')
 summary=f'> 2026-10-23 **D40整体性能试验完成，未发布**：六候选中05 classic合并逐格扫描通过96组严格图像与36设置；局部CPU略降，24原生跑动射击窗整体收益未稳定。正式仍D39 83D8…205C7E65，src/release未改。847ms长帧中RV22ms；另有内存下降相关峰值，根因未完全定位。外部高频监测证据标无效性能验收。[报告](../knowledge/experiments/{REPORT})；候选/数据build/overall-flow-output，勿据功能通过自动部署。\n\n'
 journal=f'## 2026-10-23 — D40整体流畅度试验，候选未发布\n\n- 六候选筛选：无效写入跳过、直接alpha、组合查表无稳定收益；局部显示位图严格画面失败。05 classic单次扫描通过132项/组，但两轮24原生跑动射击窗未确立稳定整帧收益，保持D39正式安装。\n- 长帧：正序847ms中RV22ms、其余825ms；D39另有115/121ms RV峰值伴内存下降，仅相关性。纠正CPU采样上界及诊断取图副作用，不归因所有峰值于GPU/GC。\n- 无src/release变更、无新委托，四项authority WIP保留；报告与接续见[证据](../knowledge/experiments/{REPORT})。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name in ['MEMORY.md','journal.md']:
  head=subprocess.check_output(['git','show','HEAD:state/'+name],cwd=MOD).decode('utf-8');work=(MOD/'state'/name).read_text(encoding='utf-8-sig')
  def change(s):
   if name=='journal.md':return journal+s
   return s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+summary,1).replace('## 4. 正在进行与停点\n\n','## 4. 正在进行与停点\n\n- D40已结束并保留候选，不自动重跑/部署；正式仍D39。后续针对原生跑动的非RV长停顿作低开销归因，详见顶部报告；不可把局部CPU下降当整体成功。\n\n',1)
  (owned/name).write_text(change(head),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(change(work),encoding='utf-8',newline='\n')
 with (MOD/'decisions/decisions.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f'\n## D40：整体收益未稳定，保留D39安装\n\n六候选实测后只保留05 classic单次扫描作为未发布候选。96严格图像、36设置通过不等于性能发布通过；24原生控制窗口仍有不利结果和长帧。禁止以降低画质/刷新或只选有利轮次证明成功。证据、未确证原因和接续见[报告](../knowledge/experiments/{REPORT})。\n')
 print('D40 archived',len(files),'files; release unchanged; own-only state snapshots ready')
if __name__=='__main__':main()
