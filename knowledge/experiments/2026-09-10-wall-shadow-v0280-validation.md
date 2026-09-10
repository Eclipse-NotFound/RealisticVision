# 2026-09-10 RealisticVision v0.28.0 墙内阴影修复验证

被测技能：remains-auto-testing / remains-mod-build / remains-runtime-debug（生产回归，非技能晋升测试）
技能归属：D:/Program Files/Steam/steamapps/common/Remains/.agents/skills
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

## 结果

> 后续状态：用户随后明确授权部署，v0.28.0已进入正式release并通过启动/入口检查，详见末尾“部署补记”。以下候选验证及fingerprints.json保留部署前的原始语境。

代码修复完成，**候选 v0.28.0；未部署**。39 项独立渲染断言全部通过；同一套断言在 v0.27.1 / 8748feb 上为 9 通过、30 失败。完整游戏副本在 random_mane / loc0_4（48×25）对两模式各比较 358,400 个墙面像素，最大 RGB 通道差均为 0，游戏 visi/t_visi 改写数均为 0。

可直接打开 [交互对照](wall-shadow-v0280/comparison.html)。源码决定见 ../../decisions/decisions.md 的 D22；复验入口见 ../../build/wall-tests/README.md。

## 用户确认的目标

1. 两模式墙内黑芯、亮面位置和渐变范围均以原版为基准；离开视野后保留层次，只压暗亮面。current / classic 地板雾效各自保留。
2. 原版继续维护亮度记录；模组负责显示和敌人遮挡。地图、传送落点的曾见判定随之恢复原版语义。
3. 本次修复授权不等于覆盖正式运行文件；未改游戏根 SWF、描述符、正式 release 或 config，未访问真实 pfe 存档。

## 环境、输入与证据

- Windows；本机 Flex/AIR SDK：D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；JRE：D:/Program Files/Adobe Animate 2024/jre。
- 宿主：根目录 1.02 pfe.swf 的资源副本；SHA256 为 5300ec4874e0404d298bb58c5d2a7469e82f93b455ad29ad64dd2e29d17241e7，与本轮检查时实际根 SWF 相同。
- 独立渲染：真实 AIR Bitmap.draw。临时源只将 private 改 public，以便调用实际绘制函数；未重写被测函数体。游戏数据以编译存根和 FixtureLocation 提供，故它不是整个游戏行为测试。
- 完整游戏：独立资源根 build/wall-test-output/game，app id rv-wall-game-probe；等 allLandsLoaded 后 newGame(-1)，正常 beginMission 前往 random_mane。使用现有 loader 启动测试引导器，再在游戏类环境中加载候选；不调用候选 startup，直接调用实际绘制函数，检查绘图与原版字段。
- 完整游戏对照固定 cfgFadeStep=0、visCur=1，隔离记忆进度，只验证墙形状。正常记忆衰减由确定性夹具另测。地板画面差异不是墙像素差异。
- [旧版断言](wall-shadow-v0280/baseline-results.txt)、[候选断言](wall-shadow-v0280/candidate-results.txt)、[完整游戏日志](wall-shadow-v0280/game-results.txt) 均来自工具实跑输出。日志的 PNG 编码行转存至交互页面；没有把代理结论当作实测结果。
- [文件指纹](wall-shadow-v0280/fingerprints.json) 包含最终源码、候选 SWF、正式 release/config 和根 SWF。
- 最终构建：build/build_test.bat 返回 0，测试 SWF 17,378 字节；FFDec dumpAS3 仅 RealisticVisionMod，无 fe.* 存根嵌入。测试引导器与公开访问副本未进入该产物。

## 覆盖范围

| 场景 | 结果 |
|---|---|
| 四格厚墙、竖墙、墙角与零行零列边界 | 可见墙最终像素与原版相同 |
| 弱光墙角、弱光来自相邻地板角 | 记忆只压暗；误差≤2/255（取整） |
| current→classic | 不污染原版场，黑芯保留 |
| 原版 retDark | 墙跟随原版实际亮度，不套常亮记忆下限 |
| 站立时原版照明变化 | 墙图即时更新；跨可见阈值的部分单位掩膜缓存同步失效 |
| 墙被破坏、同尺寸房间替换、无墙场景 | 无旧墙遮罩残留 |
| classic 门景 | 只增强显示，不写原版 visi/t_visi |
| 0.8 / 1.25 画面缩放 | 墙内部亮度通过；不是所有边缝/相机位置验收 |
| 完整游戏房间 | 两模式各 358,400 墙像素、最大差0、原版字段改写0 |

性能只做 12×10 控制房间的 120 次渲染更新循环：最终旧版 current 301ms / classic 12ms；候选 current 303ms / classic 38ms。classic 有额外墙图和范围维护开销，平均此次小样本约增加 0.22ms/次；这不是完整游戏帧率，也不足以宣称性能提升或所有房间无回退。

## 已确认原因与修复

1. **四象限不等于双线性。** 原版一格内以自身/E/S/SE四角连续混合；current 先分四块再模糊会改变坡的位置和宽度。5px 重采样后的最终 smoothing 还会将拐点抹圆约2.5px。本次直接保留原版1px/格位图的实际显示，墙与地板使用互补裁剪范围，避免双重叠压。
2. **墙角不只来自墙格。** 只修实体墙角仍不够，邻接地板角的统一 dim 下限也会抬亮墙面。独立墙场所有角都用原版亮度乘记忆衰减，不借地板的统一灰值。
3. **原版亮度曾被模组改写。** current 的0/1赋值和 classic 的 doorBoost 会直接或间接改变原版照明后续结果。删除全部 visi/t_visi 写入，门景移到显示计算。
4. **边缘常量被遗漏。** 原版 Grafon.setLight/Location.lighting 从1起循环；零行零列保持全黑。完整游戏对照实证暴露了旧夹具的边界缺口，源码和参考夹具均已校正。
5. **显示与敌人裁剪缓存需一起更新。** 墙图随原版站立照明更新；墙子格采样跨 MASK_LIT_A 时递增 fovVersion，使部分单位掩膜重建，不重跑整房地板模糊。

主要原版依据：fe.graph.Grafon 构造器与 setLight；fe.loc.Location.lighting / lighting2；fe.loc.Tile.updVisi。源码首选 game-reference/decompiled/1.02/src102/scripts。

## 过程概要（非逐字）

- 先读取截图、历史回滚和现行函数；按 grilling 将原版管线事实交由只读子代理核对，主线搭建实际渲染夹具。两项视觉/机制取舍均由用户确认。
- 原始旧版最小复现5项失败，修复后扩大为39项；独立复核进一步指出邻接地板角、5px二次平滑和缓存同步问题，均补入实际输出检查。
- 完整游戏引导首次把 MainFE 当普通子 SWF 加载，构造器 stage 为 null；改为副本已有 loader 启动探针。随后仅等 landData 开档过早，在 Land.prepareRooms 报空值；增加 allLandsLoaded 门控后正常入场。均为测试引导问题，未当作模组故障。
- 第一次完整游戏可见基地对照暴露原版零行/列边界差异；修正后在实际黑暗房间通过。
- 本轮不把旧截图的像素裁剪当作当前源码的通过证据；以相同输入的实际 AIR 与同帧完整游戏截图交叉验证。

## 经验归属与限制

- 原版位移/smoothing 的已有证据：[已落盘→classic-v5-original-pipeline.md]；其“四象限”文字过粗，本轮不能照字面实现。
- 子 SWF 构造阶段 stage 为空、开档需等 allLandsLoaded：[未落盘] 建议由运行时/自动化知识库维护会话核对，属测试引导入口约束；本轮报告记录单次观察，不自动改正式技能。
- 旧资料“磁盘存档保存 visi”经原版保存链核对不成立：同实例切房重用 Tile 会保留，磁盘读档重建 Tile 不直接恢复该字段。[未落盘] 建议公共知识库核对冲突；本次不以错误记忆播种。
- 代理只读核对 / 候选审查是事实与设计反馈，最终结论以源代码和实跑结果为依据；跨会话独立验证次数未取得。
- 尚未验证：长期游玩、所有光源/墙装饰/相机边缝、真实敌人战斗、快捷键、六模组共同运行、正式路径重启冒烟。
- 本轮修改仅在 RealisticVision 模组目录；测试程序已结束。测试存储独立，正式存档未动。资源副本留在明确的忽略目录供复验。

## 本次产物与读侧事项

- v0.28.0 源码、构建产物、build/wall-tests 下的复验程序。
- 本报告、交互页面、真实断言输出与文件指纹。
- D22 与 state/MEMORY.md、journal.md 的当前状态。
- 读侧只需核对引导约束和旧知识冲突，不据本轮生产回归宣称技能晋升。部署后仍需用户目检墙边衔接及整体观感。

## 部署补记（2026-09-10）

用户明确要求“部署”后，按发布门禁复用已验证候选（源码提交35ecef6），先备份v0.27.1再替换正式release。没有修改根pfe.swf、正式application.xml、config或其他模组文件。未重新生成部署前指纹或候选渲染证据。

- 正式产物：release/RealisticVisionMod.swf，17,378字节，SHA256 `57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0`。
- 回滚文件：build/release_backup_v0271_before_v0280_20260910.swf，SHA256 `9423F7D727191C0F090EDD0C2E50D43339643F70F69E9D0F05C33114AE86A56D`。覆盖正式release同名文件并重启即可回到v0.27.1。
- 冒烟入口：根目录临时描述符仅将app id改为`rv-deploy-smoke-v0280-20260910-213116`，content仍为`pfe.swf`，applicationDirectory仍是实际游戏目录。用正常现有loader加载真实release；没有换测试引导器、没有调用候选公开访问副本。
- 通过证据：六个loader均`init returned`；RV日志含`init ok v0.28.0 enabled=true`、持续tick、`msw settings registered`。6次定向F12键事件的调用栈均进入`cycleMode`。14项部署断言为true，详见[部署断言](wall-shadow-v0280/deployment-checks.json)、[RV原始日志](wall-shadow-v0280/deployment-runtime.txt)、[loader原始输出](wall-shadow-v0280/deployment-loader.txt)。
- 既有故障复现：6次F12各触发一次`saveConfig`的`SecurityError:fileWriteResource`，与此前记录的配置写回问题一致；异常在保存函数内捕获，没有新增RV异常，config哈希未变。此次只确认按键处理路径响应，未修设置持久化。
- 验收边界：主菜单启动和入口响应通过；隐藏窗口截图不可用，未用于证明模式画面切换。没有在此次部署冒烟中开档、进入战斗或验收六模组玩法。墙渲染结论仍来自上文的39项独立AIR断言及完整游戏副本像素比较；整体衔接待用户目检。
- 清理：仅结束自有测试进程并移除临时描述符；测试存储使用独立app id，真实pfe存档未操作。原始输出副本保留在本模组目录，正式游戏下次启动加载v0.28.0。

发布门禁第1–3项沿用未改动候选的构建/版本/渲染结果；第4项由用户“部署”授权；第5项无需改loader，根SWF哈希未变；第6–9项备份、替换、启动和回滚路径见上；第10–12项同步更新MEMORY/journal并提交模组仓库。本模组无独立changelog。
