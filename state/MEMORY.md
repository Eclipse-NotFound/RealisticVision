# RealisticVision —— 开发记忆入口

> 接手核对：2026-09-10。协议见工作区 GOVERNANCE.md §8；范围见 ../AGENT_SCOPE.md。

## 1. 这个模组是什么

视野系统模组：未探索全黑、视野内可见、记忆区暗化并隐藏敌人。包含墙门遮挡、部分可见敌人裁剪、暗区敌人念力宽限、营地透传，提供 vanilla / classic / current 三种模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as（3119 行）；只支持当前根目录 1.02 宿主，DLC 两份 SWF 没有本模组 loader。

## 2. 用户偏好与协作约定

- 视觉修改必须先用原版同场景截图校准离线模拟，每次只改一个变量；模拟确认后再做三模式真机比较，请用户目检。不要复活已回滚的墙面传播/记忆播种方案。
- 修血条勿无条件 hpbar.visible=true；沿用隐藏时压暗、恢复时 visDetails 重算。
- 游戏 SWF 修改和 release 部署按单独授权与发布门禁执行；修改宿主前核对、合并现有 loader。
- 跨模组问题只记录，不改其他模组；对外发消息需用户授权。
- 本轮是接手与基线检查，没有新的视觉修改授权或验收结论。保留现有 stash，不自动应用。
- 自动化真机验证需保持游戏窗口前台，后台低帧率曾造成假卡死。

## 3. 当前状态

- 代码版本 v0.27.1；接手起点 main / 458c96d，工作树原本干净。既有 MSW 未完成稿 stash 保留；完整集成已在 0d1becc，不应再套用旧稿。
- v0.27.1：classic 墙参与记忆变暗，墙记忆目标由游戏 visi 是否大于 0 决定；地板目标由 explored 决定。用于修墙外亮边，尚待用户目检。
- v0.27.0：MSW 聚合页注册 7 项设置，每 30 帧重试；get/set 即时生效，收页落盘。历史注册冒烟通过，设置页待用户目检。
- 最近记录的真机冒烟：2026-09-06，err=0。本轮没有启动游戏，不能视为运行/观感验收。
- 2026-09-10：修复 build/build_test.bat 两处括号提示导致的提前退出；完整测试构建成功。测试 SWF 16540 字节，FFDec dumpAS3 仅 RealisticVisionMod，无 fe.* 存根混入。
- 本轮 src、release SWF、config 的 SHA256 均与接手基线相同；仅修测试构建入口并更新接手文档。
- 当前配置：enabled=1，mode=current，dim=0.35，doordim=0.5，litmin=0.6，fadestep=0.1，maskblur_classic=6，maskblur_current=4，telegrace=3，base_rooms 空，debug=0。
- 已回滚：v0.25.9 的 resetRoom 按 visi 播种 explored（2716223）。v0.25.8 的“墙恒亮”已经被 v0.27.1 改写，历史版本描述不是当前状态。

## 4. 正在进行与卡点

- 首要遗留：current 墙内阴影位置/渐变与原版不同。尚未建立与当前 8×8 管线逐步对应的可靠模拟。
- 当前源码基线：
  - onFrame 仅递增一次 frameCount；移动阈值 1.5px、移动重算至少间隔 3 帧、结构哈希每 2 帧、兜底重算每 30 帧。
  - 视野由眼点向瓦片投射线，含门透光和距离衰减；墙只由可见非阻挡邻格点亮，不沿厚墙内部链式传播。
  - vanilla 恢复受管对象并透传；classic 用原版位移 1px/格位图，写 (tx,ty+1)，融合游戏 visi 与记忆。
  - current 用每格 8×8 子格、模糊与单侧约束；墙四象限分别取自身/东/南/东南样本；游戏 visi 被写成二值。
  - resetRoom 以 loc.id 保存/恢复房间记忆；不再按游戏 visi 播种；current 清 visi，不改 t_visi。
  - classic 为交替 ENTER_FRAME 门控；真实频率依宿主帧率，不能把历史“30Hz”标题当作当前实测。
- design/architecture.md 的部分调度参数、vision-system.md 早期设计和源码旧注释已落后；以当前函数体为准。
- rv0253-wall-smudge-sim2.py 是历史 classic 候选模拟，不能直接当作 current 模拟。

## 5. 已知问题

- classic v0.27.1 墙外亮边、MSW 设置页、旧 Pip 选项页注入行，均保留目检待办。
- 历史 adl64 测试实例配置写盘失败；当前 saveConfig catch 已无条件记录 “auto config write error”，不是静默。正常游玩环境是否复现尚未知。
- 部分可见狮鹫手臂受 internal 成员限制；全隐时另扫手臂隐藏。当前敌人掩膜已设置 cacheAsBitmap 并使用模糊透明度，旧“Flash mask 必然二值、5px 锯齿上限”表述不再适合作为现状结论。
- classic 光缘最外圈历史记录约 12–28px 小偏差（接受）；SATS 扫描把记忆区当可见（D3）、暗区抓敌瞬间 alarma 已触发（D5）为已接受取舍。
- 跨模组历史记录：RConnect autoTravelLand 到达后角色死亡，正常环境未复核；本模组不负责修复。
- GPU 渲染不可行是既有实验结论；本轮未重新测量。

## 6. 下一步（按优先级）

1. 后续视觉开发从 current 墙内阴影入手：核对原版/当前同场景截图和现行源码，建立可复现模拟，再单变量比较；未经视觉验证不宣称修复。
2. 收集 v0.27.1 classic 亮边与 MSW 7 项设置的用户目检结果；核对切换模式与重启后的配置持久化。
3. 下一次真机检查覆盖门、厚墙、部分可见敌人/血条/武器、念力宽限、营地豁免、F10/F11/F12、旧选项页注入行与流畅度。
4. 若配置仍写盘失败，读取具体异常再诊断；联机相关仅在本模组兼容范围内核查。

## 7. 深入了解与操作入口

- 开发历程：state/journal.md，最新接手条目含构建结果及基线指纹；设计理由：decisions/decisions.md（D1–D21）。
- 架构入口：design/architecture.md、design/vision-system.md，读取时按第 4 节校正过时部分。
- 图像基准：knowledge/experiments/shot_vanilla.png、shot_current.png、shot_classic.png、shot_classic_v0258.png。
- 模拟历史：knowledge/experiments/classic-v5-original-pipeline.md、classic-memory-boundary-sim.md、rv0253-wall-smudge-sim2.py。
- 测试构建：在 build 目录运行 build_test.bat，产 build/RealisticVisionMod_test.swf；此脚本不部署。build.bat/build.sh 含旧机器路径且写 release，不直接当接手检查入口。
- 工具：D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk；Java：D:\Program Files\Adobe Animate 2024\jre；FFDec：同 tools/ffdec/ffdec.jar，以 java -jar 启动。
- 实测档案：knowledge/experiments/2026-08-27-autotest-verification.md；运行/部署按 remains-runtime-debug、remains-auto-testing、remains-release-gate、remains-swf-patching 技能。
- 游戏机制导航：../../shared-knowledge/knowledge-validation/discoveries/game-mechanism-atlas-2026-09-09.md；源码首选 ../../game-reference/decompiled/1.02/src102/scripts/。
