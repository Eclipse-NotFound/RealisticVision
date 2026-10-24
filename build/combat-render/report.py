"""Append measured D44 results without erasing the earlier paused investigation."""
from pathlib import Path
import json
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-render-output';REPORT=MOD/'knowledge/experiments/2026-10-25-combat-render-attribution.md'
data=json.loads((OUT/'performance.json').read_text())
lines=['## 恢复测试后的实证（2026-10-25）','',
'用户明确“可进行测试”后，提升权限预检无其它AIR/Java、可用内存6.18GiB，保留原暂停标记并从新目录运行。使用独立AIR应用ID、隐藏桌面、共享登记；HighQoS仅用于自建测试进程，未修改玩家启动策略。普通训练房独立组原有7单位，完整组合原有14单位；6是额外生成的原生雇佣兵，并非场内总单位数。', '',
'所有整帧统计都将本帧RV调用与下一次同一监听器到达间隔配对，排除每窗末帧。每种条件两窗往返；原生AI、武器和弹体继续执行。固定路线另限制玩家和测试敌人位置以减少击退/飞行带来的视角差异，它是受控刺激，不能冒称原生自由游玩。不同进程的绝对耗时不直接比较。', '',
'### 归因与候选选择', '',
'small-02共42窗：无新增敌人时两模式接近33ms；六敌普通遮罩约42–60ms，仅撤掉RV自己拥有的动态遮罩回到约33ms。隐藏对象父层也接近33ms；未改子对象visible，保留原生粒子生成逻辑。撤罩/隐藏仅供归因，未进入候选。', '',
'- guard：只在值或对象身份变化时设置mask/cacheAsBitmap，原位图、几何和采样不变。独立房间有效；完整组合自由战斗的current出现不利结果，已保留，不据单轮好数据发布。',
'- bitmap：直接缩放原遮罩位图；首个混合明暗帧（f=120）不满足严格像素一致，停止，未跑性能或发布。',
'- trim：缩小无滤镜对象周围遮罩矩形；同样在f=120失败，停止，未发布。',
'- support：保留guard，仍使用原遮罩绘图。只在对象覆盖格及双线性相邻样本全部透明、对象和所有子对象都无滤镜时，使用空几何遮罩并恢复原缓存状态；不改visible/alpha/动画。其它情况完整保留原路径，不裁短非透明掩膜。', '',
'### 整帧结果', '',
'单位ms；P95表示95%的采样不超过此值。“>100”为超过100ms的次数。表内每行仅代表该轮同进程结果；保留最大值，不因平均改善宣称所有长帧解决。', '',
'| 轮次 | 模式 | 条件 | 帧数 | 均值 | P95 | 最大 | >100 | RV更新均值 |',
'|---|---|---|---:|---:|---:|---:|---:|---:|']
insert=lines.index('### 整帧结果')
lines[insert:insert]=[
'- support2：与support画面规则相同；复用一个同步临时矩形，用整数边界代替两个临时矩形，先检查透明度，再按需读取原生滤镜列表。360组图像及888原生检查通过。固定路线current仍有539ms峰值，未隐去或归为已解决。',
'- bindings：在support2上补齐clearMask的空mask/false缓存，以及身体、血条、武器相同visible值的重复设置保护；不跳过原生状态检查、动画、采样或更新帧。',
'- tileclip：进一步检验保留原始瓦片采样格的缩小矩形，与此前trim的任意整数裁切分开；其图像结果独立判断，未通过就不采用。', '']
for run in ['guard-01','guard-full-02','guard-controlled-03','support-controlled-01','support-free-02','support2-controlled-01','support2-free-01','bindings-controlled-01','bindings-free-01']:
 if run not in data:continue
 for mode in ['current','classic']:
  for variant,label in [('off','关闭RV'),('normal','正式D43'),('candidate','候选')]:
   g=data[run]['groups']['6/'+mode+'/'+variant];v=g['frame']
   lines.append(f"| {run} | {mode} | {label} | {v['n']} | {v['mean']:.2f} | {v['p95']} | {v['max']} | {v['>100']} | {g['rv']['mean']:.2f} |")
lines += ['', '固定路线采样前预热210帧、采样180帧，跨过240/300/360次缓存清理扫描；早前150帧短窗排除第180次处置的结论仅适用于旧短窗。自由战斗不同窗口的射击量和镜头仍会变化，原始记录含实际弹体/粒子数及位置，不以名义开火次数替代真实工作量。', '', '### 视觉、机制及工具验证', '']
for name in ['pixels-01','native-pixels-02','support-pixels-01','support-native-01','support-native-04','support2-pixels-01','support2-native-01','bindings-pixels-01','bindings-native-01','tileclip-pixels-01']:
 p=OUT/name/'validation.json'
 if p.exists():
  v=json.loads(p.read_text());lines.append(f"- {name}：{'通过' if v['pass'] else '未通过'}，{v['checks']}项/组。")
lines += ['- support密集图像包含100/500个移动对象、六档柔化、明暗切换、房间边界以及0.5/0.75/1/1.5/2倍取图；整图严格相同。原生对照覆盖独立手臂、武器、弹体、激光、火花、爆炸和弹壳。新增滤镜切换对照及“透明区域分支实际触发”断言。',
'- native-pixels-01在所有断言后因继承的输出目录检查失败，整体不算通过；native-pixels-02修正后完成。support-native-02缺滤镜导入导致夹具编译失败；03误用Array构造造成嵌套滤镜数组（#2005）；04改用as Array并完成。均保留原始失败，没有改候选来迁就测试。',
'- bitmap候选生成器最初对两个类型声明误要求单次匹配，启动游戏前中止；修正计数后才执行像素检查。',
'- 共享登记存在等待者非FIFO获取占用的现象。本侧让已较早登记的指定测试完成后再加入，并在一次真实占用内顺序编译/测试；未修改公共登记器、未结束其它会话进程。',
'- 一次向既有RConnect对话的协调消息被自动审批拒绝，理由为无法确认此前授权覆盖该对话编号；消息未发送，未绕行，后续使用共享登记。', '', '### 更新函数归因（不用于性能验收）', '',
'guard-profile-01在固定路线下记录嵌套函数计时。current：applyVision约4.98ms（其中fillFogCache3.38）、updateWallSurface2.45、hideEnemies5.13（其中applyWorldVisuals3.87）。classic：applyVisionClassic3.00、updateWallSurface2.76、hideEnemies6.38（其中applyWorldVisuals4.36）。嵌套项不能相加；计时插桩本身有开销，没有混入正式性能对照或生产包。', '', '### 发布状态', '']
receipt=OUT/'deployment/receipt.json'
if receipt.exists():
 r=json.loads(receipt.read_text());lines += [f"正式路径结果：{r['result']}；{r['version']}，SHA256 {r['new']}，46110B。备份：{r['backup']}。正式init、设置注册及tick1/181/361与保护文件指纹见receipt。",
 '准确包含6类、两进程36设置检查通过；加上360严格图像与888原生检查共1284项/组，完整组合24窗另计。bindings固定路线与自由战斗四组平均帧耗时减少约16%–19%，P95及超过100ms的次数均下降。自由战斗current69.50→56.43ms、classic65.17→53.58ms，仍高于同场关闭RV的42.50/39.66ms；不宣称接近原版或全部长帧已解决。',
 '开发线直套生产差分在git apply --check阶段因既有authority包装而失败，未写源码。随后保留active authority每次记录，仅在inactive路径应用同值保护；开发线单独编译通过，未发布authority类或验证其新运行行为。正式包始终使用production-final2准确源。',
 '本地保护曾拦截混合“写源码审查记录+读取SWF指纹”的命令，整条未执行；拆为独立记录和只读指纹后通过，没有关闭护栏。tileclip排队进程在任何构建/AIR启动前由本侧核对后停止；只准备原型，未采用。',
 '长帧原始记录见outliers.json。support2的539ms峰值中RV调用13ms、帧间内存增加约0.51MiB，不能据此断定GC，也不能将其余间隔归为非RV（包含最终绘制）。最终bindings两轮候选没有>200ms帧，但仍有>100ms帧；未排除任何不利样本。',
 '回退仅恢复本轮BF4A单文件备份并核对SHA256，保留其它模组与宿主；正常重启生效。回执与步骤见state/deployment-v03310-2026-10-25.md。']
else:lines += ['截至此记录，正式仍v0.33.9-effect-load（BF4AC9CD…3AFEF），尚未部署。本轮候选不等于全部流畅度目标已达成；保留完整组合、长帧和原版关闭对照。']
text=REPORT.read_text(encoding='utf-8');text=text.split('## 恢复测试后的实证（2026-10-25）')[0].rstrip()+'\n\n'+'\n'.join(lines)+'\n'
if receipt.exists():
 text=text.replace('被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build','被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching')
 text=text.replace('2026-10-25；用户已明确“可进行测试”，现已恢复并取得下述新证据。目标未完成，正式D43仍不变。早前暂停经过保留为历史记录。','2026-10-25；用户恢复测试后，bindings通过图像/原生/设置检查与两轮完整战斗对照，已部署v0.33.10。四组均值降低约16%–19%，仍未达到关闭RV的流畅度，目标未全部完成。早前暂停与失败候选保留为历史记录。')
REPORT.write_text(text,encoding='utf-8',newline='\n')
print('D44 report refreshed')
