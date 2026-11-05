# 2026-11-03/04 CS×RV 组合卡顿调查与 RV 大场景视口窗口适配（v0.34.6-cs-window）

## 用户报告

"ContinuousScene 与 RealisticVision 同时开启时会发生严重卡顿"（2026-11-02 23:06）。授权更改 RV 侧文件，倾向"为 RV 创建 CS 适配接口，不影响 RV 在 CS 关闭时的运行"；对 RV 本体有帮助的发现以反馈形式提交。

## 调查结论（源码级，基线 v0.34.5-ray-loop 生产源）

真实玩家日志确认当晚 CS v0.9.6 + RV v0.34.4 同场长时间运行 random_mane（240×125 瓦片连续大图）。RV 的全部历史性能测试都在 48×25 标准房间内做，大图尺寸放大的路径从未被计时。v0.34.5 的 "scene fast paths"（scenePrepareOcclusionFast / sceneRefreshWallFieldFast）只是标量访问优化，注释自述 "no temporal or viewport culling"——三个每帧热循环的遍历域仍是整张地图：

1. **`prepareOcclusion` 全图瓦片扫描**（onFrameInner 每帧无条件调用，v0.34.5 走列直访 fast path）：240×125 = 30,000 瓦片/帧（房间 1,200 → 25×）。
2. **`refreshWallField` 全图墙角循环**（每次 applyVision）：墙角数=全图墙拓扑（城市废墟图数千至近万）；每角 advanceMemory+explorationLight（getTile+visi 读）。
3. **`hideEnemies` 全单位分类**：大图 ~130 单位/帧（房间 6-20 → 7-20×），每敌 unitBBox 数组分配+bboxFovCount+状态机+武器。
4. 叠加项：v0.34.3 弹体软遮罩回归（RV 已另案归因为"边界开火卡顿"，方案见 boundary-fire-stutter-plan）。

次要发现（反馈项，未改动）：CS 0.9.5 物体剔除包装层使 RV 的 visObjs 顶层扫描（applyWorldVisuals 的 visualGrifArm 手臂识别）可能漏掉嵌套手臂——视觉问题，待专项验证。

## 适配接口设计（v0.34.6-cs-window）

- **激活条件**：每帧 `w.grafon` 上探测 `"sceneLarge" in grafon && grafon["sceneLarge"] == true`（密封类 in 探测不抛 #1069；未打补丁宿主/普通房间恒 false → 原路径零变化）。
- **窗口**：`updateCsWindow(loc)` = scenePaintBounds ∪ 玩家±FOV半径（`max(locDist2, loc.lDist2)`+2 瓦片）——射线只在该并集内行进，窗外瓦片本帧不可达、其场值可暂陈旧（窗口移过即自愈）。房间切换时窗口默认全图。
- **三处门控**：scenePrepareOcclusionFast 列/行扫描限窗；sceneRefreshWallFieldFast 角循环窗外 continue（记忆渐变暂停、接近后继续）；hideEnemies 对"窗外且已处于完全隐藏休眠态"的敌人跳过重分类（vis/hpbar/prior/武器 state 0 语义原样保留，applyUnitWeapons(u,0) 幂等维护）。
- **逃生口**：新配置键 `cs_window`（默认 1；0 = 关闭适配回 v0.34.5 精确全字段路径），随 saveConfig 持久化。

## 验证

- 官方配方编译（airglobal+GameStubs 外部库、mxmlc、swf32），49,581B，`A095A2F5…B4DB0`。
- 双沙箱 init ok v0.34.6-cs-window、无 watchdog/错误。
- 隔离沙箱（runtime-csrv，独立 AIR ID）驱动进入 random_mane 连续大图：RV 处理确认活跃（grafon.visLight 被 RV 隐藏贯穿 90s 静止窗）；同一沙箱用未改动 v0.34.5 做同构对照——行为一致，适配未引入新失败。
- 同字节交错 A/B（cs_window=1/0，各 2 轮，90s 静止/轮，全程游戏跑通）：ON 84.6/75.5 vs OFF 82.6/86.2（合并均值 −4.4ms/帧）。**测量环境被并行 bisect 自动化重载污染，方向混合、在噪声带内——不宣称收益**；结构性判断（窗口 ⊂ 全扫，门控开销可忽略）保证无回归。

## 沙箱阻塞问题（重要反馈，影响所有 RV 沙箱计时工作）

**RV 的文件日志（RVision.log tick/autotest 行）在任何沙箱进入连续大图的瞬间停止输出**——包括未改动的 v0.34.5 生产版与本轮 bisect 自动化自身的运行（各自独立 AIR ID 存储亦复现）。RV 本体仍活着并在处理（visLight 判别证实），仅日志通道死亡，根因未明（onFrame 前段代码与 fileLog 均无抛点；无 removeEventListener；无 stopImmediatePropagation）。这使 autotest 计数器 A/B 在沙箱不可用，本轮改用驱动侧整帧间隔统计。建议 RV 侧后续：①查 applicationStorageDirectory FileStream 在大图进入时的行为；②boundary-fire 计量迁移时注意此坑。

## 部署

- release/RealisticVisionMod.swf → `A095A2F5…`（v0.34.6-cs-window）；config.txt 字节级追加 `cs_window=1`。
- 备份 `build/backups/before-cs-window-20261104-005851/`（v0.34.5 SWF + 原 config）；回执 `build/cs-window-20261103/deployment.json`。
- 需重启游戏生效；回退 = 备份覆盖，或临时 `cs_window=0`。
- 真机收益待玩家重启后在 CS+RV 组合下体感核对。

## 对 RV 本体的反馈汇总（未改动本体，仅记录）

1. 上述三个 map-sized 循环的窗口化对 RV 未来任何大房间场景同样适用（不必绑定 CS——`cs_window` 门控以 grafon.sceneLarge 为代理，普通大房间可考虑独立的尺寸阈值门控）。
2. classic 模式的 `prepareClassicCells`（2916 行区域）同样是全图循环，本轮未处理（用户默认 current）。
3. `wallGeometryDirty` 触发的全图重建（墙拓扑变化帧，如开门）在大图上是一次 ~30k 瓦片 + graphics 重建的尖峰，可考虑分区化。
4. 沙箱日志死亡问题（见上节）。
5. 拷贝沙箱 `mods/ContinuousScene/build/runtime-csrv/`（含可复用 AB 驱动 `ab-driver.swf` 与 runner）保留供复测；测量时须避开 bisect 时段。

## 证据

- `build/cs-window-20261103/`：candidate.swf、compiler.xml、run_ab.{ps1,py}、diag/（诊断与 AB 驱动源）、evidence/csrv-final-{on,off}{1,2}/。
- 隔离沙箱 `mods/ContinuousScene/build/runtime-csrv/`（生产宿主 A9B3 + CS 0.9.6 + 候选 RV + AB 驱动）。
- 登记表：csrv-final-on1/off1/on2/off2、csrv-ab-on*、csrv-window-a-on（game-coexist）。
