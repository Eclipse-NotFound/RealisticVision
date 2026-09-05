# RealisticVision —— 开发记忆入口

> 新会话从这里开始。协议见工作区 GOVERNANCE.md §8；本模组参数见 ../AGENT_SCOPE.md。

## 1. 这个模组是什么

视野系统模组：三态视野（未探索全黑 / 视野内亮 / 记忆区暗色隐藏敌人），含破坏墙、透光门、敌人部分可见裁剪、念力规则（隔墙抓物品可、抓敌人不可）、三档渲染模式（`vanilla` 透传 / `classic` 仿原版 / `current` 平滑阴影，F12 轮换）。源码为单文件 `src/RealisticVisionMod.as`（约 2800 行），入口类 `RealisticVisionMod`。

## 2. 用户偏好与协作约定

- **每次修改后请用户游戏内实测**（F10 面板 / F12 模式 / PipBuck 面板）——本模组大量修复史由用户观感反馈驱动。
- 修复血条问题时勿无条件 `hpbar.visible=true`（历史教训：曾致全敌人满装甲条，用"隐藏时压暗 + 恢复时 visDetails 重算"）。
- **pfe.swf 改动需多模组协调**：改前必须反编译核对线上加载器清单，他人改动先合并。
- 跨模组问题只报告不修对方文件。
- 本模组仅支持 1.02；DLC 两份 SWF 从未打过本模组 loader。

## 3. 当前状态

- **v0.25.9**（2026-09-04）：classic 记忆状态以游戏 visi 场播种（resetRoom：visi>0 → explored=1）——修"读档后模组黑雾盖住游戏已照亮区域"（游戏 visi 场随存档持久化，模组记忆不从零开始）。冒烟 err=0。**待用户目检**。
- **v0.25.8**（2026-09-04）：墙不参与记忆调暗（墙 memT=gameA 恒显游戏 visi 值）——修厚墙上方视角黑芯灰雾（原版语义：墙 visi 常亮，亮墙恒亮/未亮墙恒黑，记忆暗色仅用于地板）。
- **v0.26.0**（2026-09-04）：classic 恢复原版位移架构——雾层 1px/瓦片、原版位移（x=-半格、y=-1 格半、写 (tx,ty+1) 行、位图 (spaceX+1)×(spaceY+2) 富余黑边）、墙与全部瓦片同走"游戏 visi + 记忆语义"，**墙专用层最终退役**。依据：原版墙面基准截图剖面实测（4 瓦片 = 亮/黑/黑/亮 + 40px 线性坡，位移双线性精确复现，校准脚本与数据见 knowledge/experiments）。
- **遗留已知问题：current 墙中阴影位置/渐变与原版有差异（未解决）**。后续再攻：以 shot_vanilla|current|classic.png 为基准校准离线模拟，模拟内迭代成功后再部署。
- 墙渲染迭代教训（v0.25.2→v0.25.7 六连败，2026-09-04 回滚 061dfbe/00583ab）：像素观感问题必须先在离线模拟里对齐"原版同场景截图"基准再上真机，每次只改一个变量，改完同场景三图对比；v0.25.6/7 的"墙面受光传播"思路见 git 历史（7b7525c/5098bc0）。
- v0.25.0（08-27/29）：渲染模式切换注入哔哔小马选项页原生列表。**注入行待用户打开选项页目检**。
- v0.24.8（08-27）：classic 30Hz 门控失效修复（frameCount 双递增，D21）+ autotest 埋点——已 8 轮真机自动化验证。
- 已定论：GPU 渲染不可行（renderMode 由 application.xml 决定；开销在 CPU 侧）。
- 游戏本体文件未改动；release 回滚 = `build/release_backup_v0247.swf`（游戏 SWF 回滚 = 根目录 `pfe_1.02_before_rvision_merge_20260815.swf`）。
- 工具链（本机实测可用）：flexsdk `D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk`；java 用 `D:\Program Files\Adobe Animate 2024\jre`；ffdec 走 `java -jar ffdec.jar`（exe 启动器找不到该 JRE）。测试构建用 `build\build_test.bat`（产物不覆盖 release）。

## 4. 正在进行与卡点

- **遗留已知问题：current 墙中阴影位置/渐变与原版有差异**（用户原始诉求，v0.25.6/7 两轮修复失败已回滚）。后续再攻：以 shot_vanilla|current|classic.png 为基准校准离线模拟，模拟内迭代成功后再部署。
- **saveConfig 在 adl64 测试实例写盘失败**（F11/F12 后 config.txt 不更新，catch 静默）：v0.24.8 已埋错误日志（"auto config write error"），下次任何会话按 F11/F12 即可从 RVision.log 拿到具体异常。用户正常游玩环境是否复现未知。
- **跨模组待报告（RConnect 维护者）**：autoTravelLand 到达即死——hp=100 存活出发，random_mane/raiders 到达后 localPose=lbl=die fr=14 卡死（非 t_die 正常流程）；begin 地不传送则存活。另：newGame(0,...) 实为加载 0 号槽（fe/World.as:823），需配存档模板。

## 5. 已知问题

- 部分可见敌人的狮鹫手臂无法裁剪（internal 成员），全隐时手臂会被扫描隐藏。
- 敌人掩膜二值限制：Flash mask 二值，5px 子格是锯齿上限。
- classic 光缘最外圈 ~12-28px 过渡位置与原版有微小偏差（接受）。
- Sats 卫星扫描器把记忆区当可见（D3 取舍）；抓取暗区敌人瞬间 alarma() 已触发（D5 副作用）——已接受取舍。
- 自动化测试前提：游戏窗口必须保持前台（后台 AIR 窗口 FPS 趋零，模组 ENTER_FRAME 心跳停摆造成"卡死"假象——8/18 实验"newGame 卡地形"的真实原因）。

## 6. 下一步（用户游戏内验证清单，按序勾销）

1. **回滚后回归确认**：classic 墙面恢复自身明暗+记忆统一灰（无亮带/脏迹）、current 无异常斑块——即 ac8f8b2 的已验收状态；
2. **v0.25.0 注入行**：哔哔小马 → 选项页列表末行「视野渲染模式」点击循环并持久化；
3. **v0.24.8 classic 流畅度**（30Hz 修复后首次真 30Hz）；
4. v0.24.7 原清单沿用：亮边与厚墙内部、念力宽限、部分可见（hpbar/武器同步裁剪）、门、暗区武器/手、营地无雾、F10/F11/config、帧率手感、与 Sandevistan/RConnect 兼容观感；
5. 任意会话按一次 F11/F12 → 查 RVision.log "auto config write error" 定位写盘失败；
6. 向 RConnect 维护者报告 autoTravelLand 到达即死问题。

## 7. 深入了解

- **开发历程**：state/journal.md（v0.2→v0.24.8 完整流水）
- **架构必读**：design/architecture.md（注入与构建 / 渲染管线三模式 / 敌人显示三态 / 配置表 / 常用操作命令）
- **设计**：design/vision-system.md；**决策**：decisions/decisions.md（D1-D21；D21=frameCount 单一递增原则）
- **本轮验证**：knowledge/experiments/2026-08-27-autotest-verification.md（埋点设计/八轮运行/断言数据/环境发现）+ logs-20260827/（原始日志）
- **构建**：`cd build && bash build.sh`（或 `build_test.bat` 出测试版）；产物验证 `java -jar <ffdec>/ffdec.jar -dumpAS3`（期望只含 RealisticVisionMod）
- **自动化验证**：remains-auto-testing 技能 + autotest 埋点（每 300 帧 `auto st` 统计行）；复用 RConnect autoGame/autoWalk 驱动，实例 appid `pferv1` + 临时描述符
- **技能**：remains-mod-build、remains-runtime-debug、remains-release-gate
