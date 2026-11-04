# 2026-11-04 W4：墙拓扑变化尖峰实测与归属（阶段 C 立项依据）

## 一句话

在 CS 连续大图上，**每发生一次墙拓扑变化（墙被打掉/门开关跨实心阈值），那一帧会多花 96–115ms**；其中 **RV 占约 +35ms**（同装置 RV 关只有 +61~68ms）。RV 的「整图墙几何重建」函数本身只占 **6–15ms**，其余约 20ms 在它引发的级联（墙面膜重建 + 雾重画 + 遮罩失效 + 渲染侧重栅格化）。

## 装置

- 测试台 `build/cs-rv-20261104/`（隔离 CS 沙箱，`random_mane` 240×125，真实行走 X 跨度 310px）。
- 新增 **风暴臂**：驱动每 45 帧把玩家周边 3 块**实心墙**的 `opac` 在 1↔0 之间翻转（`phis` 同步），模拟墙体被破坏/恢复——这正是原生 `Area`/`Box` 改写 tile 之后 RV 的 `scenePrepareOcclusionFast` 会观察到拓扑变化的那条路径。翻转帧号写进 `result.json.stormFrames`。
- 臂：
  - **Z** = 风暴 + RV 开（v0.35.1-csoptA）
  - **W** = 风暴 + RV 关（`enabled=0`，用来扣掉原生+CS 的份额）
  - **X** = 风暴 + 墙重建分段计时探针（见 §3）
- 环境注意：X/W/Z 三批是**串行独占**跑的（资源守卫要求无其它 AIR）；玩家游戏/其它会话 AIR 在跑时本轮不再启动（`--allow-foreign` 只用于后续功能轮）。

## 结果

### 每次拓扑变化的尖峰（帧间隔 − 本地基线，鲁棒口径：`max(iv[k-1..k+3]) − median(iv[k-10..k-6])`）

| 臂 | 轮次 | 翻转次数 | 中位尖峰 | 逐次样本 |
|---|---|---|---|---|
| Z（RV 开） | storm-01 | 11 | **+108ms** | 79,75,116,136,116,161,82,84,121,76,108 |
| Z | storm-02-01 | 9 | **+115ms** | 70,109,177,183,166,115,106,82,115 |
| Z | storm-02-04 | 10 | **+96ms** | 102,68,94,128,98,69,57,90,108,104 |
| W（RV 关） | storm-02-02 | 11 | **+68ms** | 66,101,44,74,62,118,65,49,68,83,73 |
| W | storm-02-03 | 12 | **+61ms** | 42,110,15,83,83,143,47,37,57,39,69,65 |
| X（探针） | wallprobe-01 | 11 | +96ms | 122,85,145,85,120,170,87,89,89,96,112 |
| X | wallprobe-02 | 10 | +108ms | 89,113,185,129,94,127,88,68,151,102 |

⇒ **RV 自己的份额 ≈ 100 − 65 ≈ +35ms/次**（同装置、同图、同驱动，唯一差别是 RV 开关）。

### 重建函数内部（X 臂插桩，每次重建写一行日志）

`RVW rebuild total=… A=… B=… C=… runs=… walls=… corners=…`，240×125 地图实测：

| 段 | 含义 | 实测 |
|---|---|---|
| A | 数组分配 + `wallRaw.fillRect` + `graphics.clear/beginFill` + 4 条边框 `drawRect` | **0–2ms** |
| B | 主行扫描：每行 run 检测（每格 2 次 `getTile`，共 ~60,000）+ 每 run 一条 `drawRect`（**2,098 条**）+ `wallTiles.push`（**5,212**）+ 墙角去重（**8,666**，含 `used[]` 检查） | **5–15ms** |
| C | `endFill` | 0ms |
| 合计 | | **6–15ms** |

⇒ 重建函数只解释 RV 份额的 1/3~1/2；其余 ~20ms 在级联里（`wallStructureVersion++` 使 `updateWallSurface` 缓存失效 → 墙面膜重建；`fovVersion++` 使单位掩膜全失效；雾层重画；以及新的 2,098 条路径的渲染侧重栅格化——这段不进 RV 的 AS3 计时）。

## 进一步归属（各加一组对照臂，结论是"不在 RV 脚本、也不在雾层子树"）

| 臂 | 含义 | 中位尖峰 |
|---|---|---|
| Z | 风暴 + RV 正常 | **+129 / +111 / +83** |
| W | 风暴 + RV 关闭 | +68 / +61 |
| **Y** | 风暴 + RV 正常但**每帧隐藏整层雾**（fogtest-01） | **+95 / +111**（≈ 与 Z 同） |
| **V** | 风暴 + RV **加载但惰性**（`mode=vanilla`，不做任何视效） | **+82 / +69**（≈ 与 W 同） |

- **隐藏整层雾不降低尖峰**（Y ≈ Z）⇒ 那 35ms 不是雾层的 mask/表面重栅格化。
- **RV 惰性时尖峰回到 RV 关闭水平**（V ≈ W）⇒ 放大器是 RV 的**活动视效**（单位/武器/特效的 `cacheAsBitmap` + 遮罩、`visLight` 接管），不是"RV 存在本身"。
- 而 X 臂的 AS3 分片（`computeFov` / `applyVision` / `updateWallSurface` / `hideEnemies`，帧号已用重建日志的 `f=` 对齐）在风暴帧上**与普通帧相同**（applyVision 中位 6ms、wallSurface 中位 5ms），墙几何重建本身稳定 **8–16ms**。

⇒ 事件成本的构成大致是：**RV 脚本 8–16ms（重建）+ 显示列表侧（RV 的 mask/cache 让一次全场景重绘更贵）≈ 20–25ms**。后者没有任何 AS3 计时能看见，只能用"开关某项视效"的对照臂去逼。

**测量可信度声明**：fogtest-01 / inerrtest-01 两批是在**玩家游戏与另一会话 AIR 同时运行**时跑的（`--allow-foreign`，AGENTS §8 允许但只作功能/归属），逐次样本离散大（38–218ms）。因此 Y≈Z、V≈W 这两个关系只当作**方向性证据**，不作为数值结论；要定量必须在独占机器上重跑 `fogtest`/`inerrtest` 各 2 批。

## 对阶段 C 设计的直接含义（修正版）

1. **只做"行桶化重建"**能省 8–16ms 里的一部分（约 10ms 上限），**不是 35ms**；而且事件成本的大头在显示列表侧，行桶化对它无效。
2. 真正的大头要先定位到"哪种视效"。可行的下一批对照臂（每批 ~2.5 分钟）：
   - `enemy_mask_fast=0`（改走逐单位软遮罩，看是否更贵）；
   - 关闭单位 `cacheAsBitmap`（需要一个小补丁的候选 SWF）；
   - 只保留雾层、不挂单位遮罩（候选补丁）。
3. **不建议**现在就做"行桶 mask"或"视口掩膜"：前者收益有限，后者已被 Y 臂间接否定（雾层不是放大器）。
4. 稳态成本与事件成本要分开立项目标：稳态已由阶段 A 拿到 −21%（实测），事件尖峰需要新的定位手段。

## 尚未取得（下一步）

- 独占机器上的 fogtest / inerrtest 复测（当前两批受玩家游戏与其它会话 AIR 污染）。
- "哪种视效是放大器"的定论：需要在**候选 SWF** 上做单项关闭（`cacheAsBitmap`、单位遮罩、特效遮罩）的对照臂。
- 玩家真实前台的尖峰体感（沙箱隐藏窗口 ~10fps，绝对值不可搬）。

## 复现

```powershell
cd mods\RealisticVision\build\cs-rv-20261104
python run_grid.py --batch storm-0X --order Z,W,W,Z --window-ms 40000 --settle-ms 6000
python analyze_storm_robust.py storm-0X-*
# 事件成本归属：雾层隐藏(Y) / RV 惰性(V)
python run_grid.py --batch fogtest-0X --order Z,Y,Y,Z --window-ms 40000 --settle-ms 6000
python run_grid.py --batch inerrtest-0X --order Z,V,V,Z --window-ms 40000 --settle-ms 6000
# 探针（墙重建分段）：先在 ..\csopt-20261104 里 python make_wall_probe.py && python build_probe.py
python run_grid.py --batch wallprobe-0X --order X --window-ms 45000 --settle-ms 6000
python analyze_slices_compare.py wallprobe-0X-01-X
```
