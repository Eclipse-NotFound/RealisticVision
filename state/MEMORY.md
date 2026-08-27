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

- **v0.24.8**（2026-08-27）：① 修复 classic 30Hz 门控失效（frameCount 双递增奇偶 bug，D21）② autotest 埋点（config 键 `autotest`，默认关）③ 启动日志版本标记 ④ saveConfig 错误日志。**已经 8 轮真机自动化验证（含修复对半交替数据），待用户游戏内确认**。
- 已定论：GPU 渲染不可行（renderMode 由 application.xml 决定；开销在 CPU 侧）。
- 游戏本体文件未改动；release 回滚 = `build/release_backup_v0247.swf`（游戏 SWF 回滚 = 根目录 `pfe_1.02_before_rvision_merge_20260815.swf`）。
- 工具链（本机实测可用）：flexsdk `D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk`；java 用 `D:\Program Files\Adobe Animate 2024\jre`；ffdec 走 `java -jar ffdec.jar`（exe 启动器找不到该 JRE）。测试构建用 `build\build_test.bat`（产物不覆盖 release）。

## 4. 正在进行与卡点

- v0.24.8 待用户游戏内确认（重点：classic 模式帧率与光环观感——门控修复后 classic 才真正享受 30Hz）。
- **saveConfig 在 adl64 测试实例写盘失败**（F11/F12 后 config.txt 不更新，catch 静默）：v0.24.8 已埋错误日志（"auto config write error"），下次任何会话按 F11/F12 即可从 RVision.log 拿到具体异常。用户正常游玩环境是否复现未知。
- **跨模组待报告（RConnect 维护者）**：autoTravelLand 到达即死——hp=100 存活出发，random_mane/raiders 到达后 localPose=lbl=die fr=14 卡死（非 t_die 正常流程）；begin 地不传送则存活。另：newGame(0,...) 实为加载 0 号槽（fe/World.as:823），需配存档模板。

## 5. 已知问题

- 部分可见敌人的狮鹫手臂无法裁剪（internal 成员），全隐时手臂会被扫描隐藏。
- 敌人掩膜二值限制：Flash mask 二值，5px 子格是锯齿上限。
- classic 光缘最外圈 ~12-28px 过渡位置与原版有微小偏差（接受）。
- Sats 卫星扫描器把记忆区当可见（D3 取舍）；抓取暗区敌人瞬间 alarma() 已触发（D5 副作用）——已接受取舍。
- 自动化测试前提：游戏窗口必须保持前台（后台 AIR 窗口 FPS 趋零，模组 ENTER_FRAME 心跳停摆造成"卡死"假象——8/18 实验"newGame 卡地形"的真实原因）。

## 6. 下一步（用户游戏内验证清单，按序勾销）

1. classic 模式帧率/光环比对（v0.24.8 门控修复后应明显更流畅——原 v0.24.7 的 30Hz 从未生效）；
2. v0.24.7 原清单沿用：亮边与厚墙内部、念力宽限、部分可见（hpbar/武器同步裁剪）、门、暗区武器/手、营地无雾、F10/F11/config、帧率手感、与 Sandevistan/RConnect 兼容观感；
3. 任意会话按一次 F11/F12 → 查 RVision.log "auto config write error" 定位写盘失败；
4. 向 RConnect 维护者报告 autoTravelLand 到达即死问题。

## 7. 深入了解

- **开发历程**：state/journal.md（v0.2→v0.24.8 完整流水）
- **架构必读**：design/architecture.md（注入与构建 / 渲染管线三模式 / 敌人显示三态 / 配置表 / 常用操作命令）
- **设计**：design/vision-system.md；**决策**：decisions/decisions.md（D1-D21；D21=frameCount 单一递增原则）
- **本轮验证**：knowledge/experiments/2026-08-27-autotest-verification.md（埋点设计/八轮运行/断言数据/环境发现）+ logs-20260827/（原始日志）
- **构建**：`cd build && bash build.sh`（或 `build_test.bat` 出测试版）；产物验证 `java -jar <ffdec>/ffdec.jar -dumpAS3`（期望只含 RealisticVisionMod）
- **自动化验证**：remains-auto-testing 技能 + autotest 埋点（每 300 帧 `auto st` 统计行）；复用 RConnect autoGame/autoWalk 驱动，实例 appid `pferv1` + 临时描述符
- **技能**：remains-mod-build、remains-runtime-debug、remains-release-gate
