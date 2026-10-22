"""Archive D39 evidence and preserve other authors' state edits."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import package as p
OUT,MOD=p.OUT,p.MOD
ARCHIVE='long-frame-v0336-20261022';REPORT='2026-10-22-long-frame-triggers.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def triple(a):return '/'.join(str(a[k]) for k in ['mean','p95','max']) if a else '—'
def main():
 receipt=read('deployment/receipt.json');proof=read('verified.json');perf=read('performance.json');manifest=read('production/manifest.json')
 assert receipt['result']=='PASS' and receipt['new']==manifest['swf'] and read('development-check/result.json')['compiled']
 archive=MOD/'knowledge/experiments'/ARCHIVE;archive.mkdir(exist_ok=False)
 names=['trace-full-01','trace-order-02','trace-sweep-02','helper-02','helper-03','helper-final','timing-02-visible','timing-03-visible','exact-final-parent','wide-final-parent','timing-final-visible','trace-final','weapon-final','production','deployment','development-check']
 files=[]
 for name in names:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   if f.suffix in ['.json','.log','.png'] or (f.suffix=='.txt' and f.name in ['classes.txt','formal-runtime.txt','formal-output.txt','analysis.txt']):files.append(f)
 files += [OUT/x for x in ['inputs.json','selected.json','verified.json','performance.json','development.patch']]
 files += list((OUT/'production/src').rglob('*.as'))
 for name in ['trace-full-01','trace-order-02','trace-sweep-02','trace-final','exact-final-parent','wide-final-parent']:
  files.append(OUT/name/'RecoveryFrameProbeMod.as')
 files.append(OUT/'helper-final/src/EquivalenceChecks.as')
 for f in files:
  dst=archive/f.relative_to(OUT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst);assert sha(dst)==sha(f)
 (archive/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8',newline='\n')
 (archive/'archive.json').write_text(json.dumps({f.relative_to(OUT).as_posix():sha(f) for f in files},indent=2)+'\n',encoding='utf-8',newline='\n')
 paired=[]
 for c in perf['paired']:
  a,b=c['update'];paired.append(f"| {c['case']['mode']} / {c['case']['dim']} | {triple(a)} | {triple(b)} | {100*(a['mean']-b['mean'])/a['mean']:.1f}% |")
 full=[]
 for c in perf['full_combo_sweep']:
  full.append(f"| {c['mode']} / {c['variant']} | {triple(c['interval'])} | {c['interval']['over50']}/{c['interval']['n']} | {triple(c['update'])} | {triple(c['viewChanges'])} |")
 summaries={}
 for mode in ['current','classic']:
  a=next(x for x in perf['full_combo_sweep'] if x['mode']==mode and x['variant']=='baseline');b=next(x for x in perf['full_combo_sweep'] if x['mode']==mode and x['variant']=='candidate')
  summaries[mode]=f"{mode}跨缓存帧RV均值{a['viewChanges']['mean']}→{b['viewChanges']['mean']}ms，完整间隔均值{a['interval']['mean']}→{b['interval']['mean']}ms、P95{a['interval']['p95']}→{b['interval']['p95']}ms、最大{a['interval']['max']}→{b['interval']['max']}ms"
 report=f'''被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-22 偶发长帧的触发情景与局部修复

用户要求定位偶发卡顿和长帧并尝试解决。准确基线为D38 v0.33.5、6593EE35…8FD6EC06的六类生产源。本轮选择candidate-04，部署{p.VERSION}；不发布独立authority开发内容。

## 已定位与仍未知

- **镜头跨墙面缓存边界**：192×75大场景，视口左右扫动，helper bounds改变时整片rebuildFaces/rebuildSamples/rebuildSupport/updateContour重建。首次完整组合的current共15个重建帧，RV更新平均52.2ms、最大97ms；classic平均63.8ms、最大166ms。普通不驱动移动窗口的RV更新明显更低。该驱动每步18px位移并调用cam.calc，用于触发边界，并非实际物理跑步录像。
- **轮廓重复作废与分配**：原实现把视口平移也当全新地形，清掉所有patch.runs，再按相对视口坐标找材质块；重叠世界区域也重复扫描像素、分配缓存。第二轮off/A/B/B/A/off完整组合对照，candidate-02把重建帧的RV更新均值current58.93→37.03ms、classic57.87→36.47ms，轮廓生成均值9.8→1.67、10.03→1.93ms，支持该触发链。两版本各模式30个重建帧；是诊断插桩结果，不能和最终无插桩数字拼成更优收益。
- **持续交战并非每次都由RV长更新触发**：首轮完整组合的窄幅移动加原生射击窗口，RV更新current最大23ms、classic最大35ms；关闭RV也有长帧。不能把全部卡顿归因于本模组，更不能把帧间隔剩余部分直接叫GPU耗时。
- **内存回收线索未确证**：首轮current sweep一个非重建帧RV85ms、helper.updateContour72ms，同期System.totalMemory减少约71MiB。只证明时间相关，未强制GC、未证明停顿唯一由GC造成。本轮通过减少重建和分配降低触发压力，不声明解决所有回收停顿。

## 实现与边界

`RVWallSurface.update`区分真实地形变化和缓存视口平移：重叠世界区域保留材质块及轮廓行段，把局部坐标作整数平移。每帧仍读取墙高和材质像素；任何重叠区的墙高变化都会作废轮廓，alpha变化仍即时重建。中途读取失败的脏标记保留到成功重建，避免下一帧漏掉破墙。

`rebuildSamples`将每个面反复计算的两种5px采样模板预先计算，按上限预分配样本向量。沿用同一取整与衰减公式；230组检查同时比较采样表和最终像素。常亮开启路径保留原有视口重建行为，避免改变它的全分辨率中间图对齐；采样模板优化两种开关都使用。

没有降低分辨率、刷新频率、视距；没有改变主渲染/FOV/设置/共享探索/武器遮罩代码，主类仅版本号变化。原生visi/t_visi、AI、地图和传送判定不改。候选01在常亮路径的共享Rectangle引用风险在正式验收前以02隔离；03加入采样模板，04补异常扫描持久失效。01不作为完整候选发布。

## 计时探针纠正

trace-full-01最初假定EXIT_FRAME只在整帧末尾出现。trace-order-02绝对事件序列实际观察到同一ENTER周期多个EXIT，且既有liveStep之前也有EXIT；旧toExit/tail行对应错误。**旧trace-analysis.json的host/tail归因不得使用**；原始文件保留，trace-analysis-v2.json明确标为无效阶段映射，只保留直接包围RV函数的计时作初步定位。

后续V2改为同一个liveStep连续起点差，记录绝对liveStart/rvStart/rvEnd并逐行核对；末帧没有下一起点，排除。outsideRV包含驱动设置位置与cam.calc、其他脚本、绘制及系统调度，不能再细分归因。未用错误EXIT映射评价修复收益。

## 最终正确性

本轮最终{proof['checks']}项/组：helper230（包括连续视口平移/缩放、墙高/alpha变化、常亮开关、异常中断后重试及严格采样表），父层显示96，真实原生childObjs武器52，准确生产字节设置36。96组图像与D38逐像素相等，覆盖两模式、常亮、记忆亮度0/.35/.6/1、柔化0/40、视距.5/1/3和多种缩放。保留原父子层级取图，无像素容差；不等于全部GPU/DPI组合认证。

旧D35武器泄露反例仍为正例，最终候选泄露为0。FOV和共享探索相关算法本轮无代码差异，复用D38历史证据而不虚增检查数。所有最终源码与生产快照比对；六类不含fe.*存根或authority。

## 最终同输入性能

192×75、96人工单位，每版每组120样本，同进程轮换，无分段插桩、无取图。单位ms，均值/P95/最大；这是模组更新CPU时间，不能换算完整FPS。独立软件draw数据完整保存于performance.json。

| 模式 / 记忆亮度 | D38更新 | D39更新 | 更新均值减少 |
|---|---|---|---|
{chr(10).join(paired)}

## 最终完整组合长帧

同进程每模式off/A/B/B/A/off，场景内原生NPC持续运行，左右扫动；每窗300样本，末帧排除后每版本/模式598个间隔。每组所选14入口requested/ok逐项核对，RV由隔离探针加载，避免正式入口双跑。无函数分段插桩，仅同样的外层计时及状态记录。off指相同完整组合关闭RV显示，不是纯净原版。世界持续演进，窗口不是确定性因果性能试验，不外推联机FPS。

| 模式 / 版本 | 整体间隔均值/P95/最大 | >50ms帧 | RV更新均值/P95/最大 | 跨视口缓存帧RV均值/P95/最大 |
|---|---|---|---|---|
{chr(10).join(full)}

{summaries['current']}；{summaries['classic']}。整体帧间隔没有稳定改善，classic本轮平均及P95略变差，current最大间隔也未降低。这些是持续演进窗口的观察，不能证明修改导致了剩余整体波动；同样不能用局部下降宣称全部卡顿已解。

本轮结论限于减少已确认的缓存边界集中重建。其他长帧仍在，不能承诺两模式所有战斗都已接近原版流畅度。完整样本、峰值、加载清单和内存/进程采样见[performance.json]({ARCHIVE}/performance.json)。环境秒级采样只能排除所采到的其他AIR/JVM，不能排除所有短进程和系统抖动。

## 部署与回退

准确包{manifest['bytes']}B，SHA256 `{receipt['new']}`。共享占用内核对根application.xml→pfe.swf及loader，再备份D38并只替换RV。正式路径独立init、ModSettings注册、tick1/181/361通过；保护文件和真实用户配置指纹未变，自己的实例和描述符退出清理。用户保存并正常重启游戏生效。

回退文件：`{receipt['backup']}`，SHA `{receipt['old']}`。仅将其替换回`release/RealisticVisionMod.swf`再正常重启；不要回滚宿主或其他模组。部署与源码提交分开记录，所有四项外部authority WIP保留。

测试使用唯一AIR应用ID、独立存储与私有桌面，全部按共享登记排队。经验检索partial，KB-000056已回读；来源缺失不解释成全库无经验。CS同任务对照结果属于协作线索，未混入本报告实测数字；未新增委托。
'''
 (MOD/'knowledge/experiments'/REPORT).write_text(report,encoding='utf-8',newline='\n')
 summary=f'> 2026-10-22 **D39 v0.33.6已部署**：定位镜头跨墙面缓存边界的集中重建；复用重叠世界区域轮廓、预计算精确采样模板并保留异常失效。414项/组、96组严格图像及完整组合12窗通过；准确包{receipt["new"][:8]}…{receipt["new"][-8:]}（{manifest["bytes"]}B），正式init/注册/tick1/181/361通过。仍有非RV长更新的长帧，不声称全部卡顿消除；[报告](../knowledge/experiments/{REPORT})。生产源build/long-frame-output/production/src，无authority；D38备份见部署回执。\n\n'
 journal=f'## 2026-10-22 — D39偶发长帧归因与缓存重建优化\n\n- 定位：快速镜头跨helper缓存边界时，整片轮廓与样本重复生成。重叠世界块复用和预计算模板减少此类开销；真实地形/材质仍每帧检查。\n- 验证：414项/组、96组父层像素严格相等，12完整组合扫动窗口。EXIT_FRAME旧阶段计时被实证否定，旧结果保留并标无效；最终同监听器连续时间戳核对。长帧仍有外部/未知成分，见[报告](../knowledge/experiments/{REPORT})。\n- 部署：{p.VERSION}，{receipt["new"]}，{manifest["bytes"]}B；正式init/注册/tick1/181/361通过。D38备份{receipt["backup"]}；只改RV，四项外部WIP保留。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name in ['MEMORY.md','journal.md']:
  head=subprocess.check_output(['git','show','HEAD:state/'+name],cwd=MOD).decode('utf-8');work=(MOD/'state'/name).read_text(encoding='utf-8-sig')
  def change(s):
   if name=='journal.md':return journal+s
   s=s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+summary,1)
   s=s.replace('- 当前安装D38 v0.33.5（6593EE35…8FD6EC06）；精确采样复用与墙面行段优化。准确源build/followup-performance-output/production/src和knowledge/experiments/followup-performance-v0335-20261022/production/src，不从含authority的HEAD整包部署。','- 当前安装D39 v0.33.6；镜头跨墙面缓存边界复用、采样模板优化。准确源build/long-frame-output/production/src；不从含authority的HEAD整包部署。')
   s=s.replace('## 4. 正在进行与停点\n\n','## 4. 正在进行与停点\n\n- D39已部署并完成归档；测试退出。已减少缓存边界重建开销，剩余偶发长帧需另行针对驱动、宿主计算或绘制取证；不使用旧EXIT_FRAME分段归因。\n\n',1)
   return s
  (owned/name).write_text(change(head),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(change(work),encoding='utf-8',newline='\n')
 decision=MOD/'decisions/decisions.md'
 with decision.open('a',encoding='utf-8',newline='\n') as f:f.write(f'\n## D39：镜头平移保留世界轮廓，采样模板预计算\n\n先按长帧触发情景定位，再优化跨视口缓存边界的重复生成。真实墙高、材质alpha及失败重试仍及时作废，常亮开启保留原全分辨率路径。未降低画质或更新频率。414项/组与严格图像通过；完整组合仍有长帧，不归因所有峰值于GC或GPU。已部署{p.VERSION}；证据及回退见[报告](../knowledge/experiments/{REPORT})。\n')
 print('D39 archived',len(files),'files; state own-only snapshots saved')
if __name__=='__main__':main()
