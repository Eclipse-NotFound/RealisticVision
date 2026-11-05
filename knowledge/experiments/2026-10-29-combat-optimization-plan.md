# D59：扫射/交战卡顿排查与优化方案（只读；未替换模组本体）

2026-10-29。用户要求针对轻机枪等连发武器扫射、与敌人交战时卡顿，从敌人遮罩、子弹/特效动画计算等方面排查并给出优化方案，明确“不实际替换模组本体文件”。

## 0. 本轮边界与基线

- **未改** `mods/RealisticVision/src/`、`release/`、玩家配置/存档；没有启动游戏，也没有新增性能样本。
- 正式安装仍是 D56 `v0.33.11-effect-clip`，46,441B，SHA256 `BD64B5BB…CE4A9AD`；config 为 `current / dim=0.35 / soft_current=20`。
- 下文证据分三类，逐条标注：
  - **实测**：既有 D44/D56/D57/D58 冻结证据的重新读取，不是本轮新跑；
  - **代码事实**：当前主源码（含未发布 authority 开发线）与 `game-reference/decompiled/1.02/src102`；
  - **推断**：未验证的因果解释。
- 本轮目标只是确定“下一步先改什么、怎么证明有效”，不是直接给出可部署优化包。

## 1. 结论摘要

1. **最近的测试协议漏掉了最大的移动态成本。** D56/D57/D58 都是玩家固定位置：current 每 120 帧只有 4 次视野重算（30 帧兜底，`RealisticVisionMod.as:969`），RV 单帧约 3.29ms。D44 的受控移动路线里 `computeFov`、`fillFogCache` 均为 115/120 帧调用，计时代码插桩 profile 合计约 **13ms/帧**（其中 `applyVision` 4.98、`updateWallSurface` 2.45、`hideEnemies` 5.13）。真实交战需要移动/走位，这一项必须在 D56 上复测后再定优先级。
2. **遮罩的成本主要不在“图形裁得不够小”，而在逐对象 mask 关联。** D44 small-02 同场景六敌：current 正常 43.66/60.38ms，撤掉 RV 拥有的遮罩后 33.70/33.24ms；classic 42.06/45.07 → 32.97/33.32ms。D56 后 current 与关闭 RV 的差距已降到约 4.8ms（D57 19），所以继续缩小遮罩几何的收益上限很低；要再降，必须减少被遮对象数/遮罩关联数，或改变表示方式。
3. **current 的遮罩绘制代价已经较小，classic 的绘制代价仍明显。** D57 19：current normal−off 的 4.84ms 中，RV 调用 3.29ms、绘制后阶段仅 +0.82ms；classic normal−off 的 13.29ms 中，绘制后阶段 +7.69ms。用户当前用 current，因此主要目标应是移动态的 RV 调用（约 13ms 的旧 profile），而不是继续暴力裁遮罩。
4. **>100ms 尖峰不是单一 RV 步骤造成的。** D57 19：长帧分布在 RV 调用内（常伴随 55–68MiB 内存下降，提示 GC）、下一原生 72–107ms、其它监听 60–300ms、绘制/调度 155–248ms；关闭 RV 仍有 109ms 帧。RV 单方面无法承诺消除所有卡顿，需要并行做长帧/跨模组归因。
5. **建议顺序**：P0 类别归因（不改模组）→ P1 零画质清理 → P2 移动态刷新/脏区（主收益）→ P3 遮罩结构与特效分级（含画质决策）→ P4 长帧/跨模组归因。

## 2. 证据

### 2.1 固定位置 vs 移动态

| 指标 | D57 19 固定位置 current | D44 profile 受控移动 current |
|---|---:|---:|
| `computeFov` 调用 | 4/120 帧 | 115/120 帧 |
| `fillFogCache` 调用 | 4/120 帧 | 115/120 帧 |
| RV 总耗时 | 3.29ms/帧 | 约 13ms/帧（插桩口径） |
| `applyVision` | — | 4.98ms（其中 `fillFogCache` 3.53ms/次） |
| `updateWallSurface` | — | 2.45ms/帧 |
| `hideEnemies` | — | 5.13ms/帧 |
| 其中 `applyWorldVisuals` | 约 2ms/帧（220–252ms/120） | 3.87ms/帧 |
| 其中 `refreshMask` | 少量重算 | 371ms/120 = 3.09ms/帧，**97.4 次/帧** |
| 其中 `applyMask` | 少量 | 106ms/2058 次 = 0.05ms/次 |
| `prepareOcclusion` | — | 0.09ms/帧（48×25 房间） |

D44 profile 的调用次数（current）：`refreshMask` 11,690/120 帧、`applyWorldVisual` 9,741/120 帧、`computeFov` 115、`applyMask` 2,058。classic 同类调用为 `refreshMask` 10,673/120、`applyWorldVisual` 10,209/120、`hideEnemies` 6.38ms/帧。

**边界**：D44 profile 是旧构建 + 计时插桩，嵌套函数不能相加、绝对值不可当正式帧率；它只证明“移动时每帧全量重算”这一结构，D56 上必须复测。

### 2.2 遮罩关联的成本（D44 small-02，六敌，90 帧/窗）

| 模式 | 条件 | 均值/ P95 / 最大 ms | 说明 |
|---|---|---:|---|
| current | off | 33.30 / 40 / 75 | 关闭 RV |
| current | normal | 43.66 / 56 / 78 | D43 时代正常遮罩 |
| current | nomask | 33.70 / 40 / 77 | 仅诊断：撤掉 RV 拥有的 mask 并恢复 cache |
| current | normal（第二窗） | 60.38 / 116 / 243 | 随机弹体/粒子更多 |
| current | nomask（第二窗） | 33.24 / 39 / 54 | 同上 |
| classic | off | 33.36 / 41 / 71 | 关闭 RV |
| classic | normal | 42.06 / 51 / 137 | |
| classic | nomask | 32.97 / 40 / 50 | |
| classic | normal（第二窗） | 45.07 / 63 / 95 | |
| classic | nomask（第二窗） | 33.32 / 42 / 71 | |

同场景 `masks` 峰值 167–180，`maxObjects` 109–142；`noobjects`（隐藏对象父层）也接近 33ms。**结论**：在这个六敌场景里，逐对象遮罩关联可占 10–27ms；但 `nomask`/`noobjects` 都不可作为画质方案。D56 之后 current 的遮罩差距已降到约 4.8ms，说明“按 D56 的当前实现，继续缩遮罩图形”上限不高，**减少遮罩对象数/关联数**才是新变量。

### 2.3 长帧分段（D57 19，238 个完整间隔，单位 ms）

| 条件 | 帧间隔 均值/P95/最大 | RV | 下一原生 | 其它监听 | 绘制后 |
|---|---:|---:|---:|---:|---:|
| current / off | 49.66/65/265 | 0.00 | 7.84 | 4.76 | 36.91 |
| current / normal | 54.50/73/166 | 3.29 | 8.49 | 4.84 | 37.74 |
| classic / off | 43.89/58/104 | 0.00 | 7.79 | 4.42 | 31.58 |
| classic / normal | 57.18/71/120 | 5.53 | 7.78 | 4.49 | 39.27 |

current 的差距主要来自 RV 调用本身；classic 的差距主要来自绘制后阶段。>100ms 样本在 off 组也存在，不能全部归 RV。

### 2.4 P0 试跑记录（2026-10-29 14:16–14:42，未取得性能数据）

用户批准 P0 后，按 D58 工具链新建 `build/mask-budget`：复制 `build/combat-split` 的探针与运行器，加入固定/移动开关和 unit / hpbar / weapon / arm / bullet / part 六类撤罩变体；RV 从 `build/combat-split-output/baseline/src`（与 D56 生产源逐字节一致）编译，探针 SWF 编译成功。实际启动 AIR 时遇到环境阻塞：

| 尝试 | 结果 |
|---|---|
| 默认 workspace-write | 启动前创建 `%APPDATA%\pfe-modsettings-rv-motion-*` 测试存储 `PermissionError`，无法复制只读种子 |
| `danger-full-access` | `adl64.exe` 在游戏初始化前退出 `0xC0000142`（STATUS_DLL_INIT_FAILED）；同目录原版 D58 harness `12-env-check` 也得到同一退出码 |
| 私有桌面 + workspace-write | 进程能启动，但 5min 无帧/无日志；测试登记已中断并释放，无性能数据 |
| 固定测试应用 ID + 预置存储 | 默认桌面立即退出或私有桌面无帧；无数据 |

因此本轮**没有**新的分类成本或移动态 RV 数字。这些失败是测试启动环境/工具链问题，不能写成 RV 候选失败，也不能据此声称任何优化有效。主 src/release 未改；测试登记已释放。P0 需要在能启动 AIR（真实 AppData + 私有桌面，或既有 agent-debug 通道）的环境重跑；六类变体与运行器已就绪，测量协议不变。

在 P0 完成前，既有证据只能给出粗粒度优先级：D57 19 的 `hideEnemies` 内“动态世界特效 220–252ms/120 帧”占绝大多数，“单位/武器 16–17ms/120 帧”很小；D41 移动/静止同输入对照 current 4.737→17.1–22.4ms、真实跑动 RV 12.8ms。因此 P2（移动态）与 P3（Part/Bullet 特效遮罩）仍是优先方向，敌人身体/血条/武器 mask 的 AS3 份额小；渲染份额仍未拆分。**这不是 P0 结论**，不能替代分类实测。

### 2.5 P0 结果（2026-10-29，active 1280×720）

后续找到可用的 active 可见窗口通道后，P0 已完成固定/移动两套六类归因（详见 [P0 报告](2026-10-29-mask-budget-p0.md)）。关键数字：

- 固定位置：normal 51.29ms / RV 3.72ms；off 38.80ms。
- 移动位置：normal 49.97ms / **RV 8.20ms**；off 34.72ms。移动态 RV 比固定位置高约 4.5ms，确认固定位置协议低估。
- 六类中只有 **unit body mask** 在固定/移动两套、4/4 窗都方向一致（固定约 -3.36ms，移动约 -3.55ms）；它只有约 6 个 mask/帧。
- Part mask 数量最多（约 35/帧），但固定两窗 -9.09/+6.09ms、移动两窗 +0.38/-9.30ms，不能据此排名；hpbar/weapon/arm/bullet 小于窗间漂移。
- 撤任何一类 mask 都没有降低 RV 的 AS3 时间，变化集中在绘制后段；说明主要成本是 mask/cache 关联的绘制，而不是 refreshMask 的几何计算。
- 移动态分函数 profile：`updateWallSurface` **2.73ms/帧**、`fillFogCache` 3.39ms/次（99/120 帧，约 2.03ms/帧平均）、`applyWorldVisuals` 1.85ms/帧、`refreshMask` 仅 0.85ms/帧。因此 **P2.1 掩膜刷新节流上限 <0.5ms，不应作为主方案**；P2 应先做 `updateWallSurface` 增量/复用与 `fillFogCache` 脏区。
- P2-A 候选（墙面输入门控 + P1 清理）已实现并 A/B：固定位置 -0.5~-0.7ms（RV 2.6–2.8→1.70ms，约 1.3%–2.0%），移动态无确认收益/轻微回退；未达到“明显收益”，**未采用、未部署**。详见 [wallgate 报告](2026-10-29-wallgate-candidate.md)。
- 绝对耗时受 active 默认桌面与测试环境漂移影响；这是方向性归因，不是发布验收。

## 3. 代码热点（当前主源码行号）

### 3.1 移动态：FOV 每帧全量重建，掩膜随之全部重算

- `onFrameInner`（917）：current 下 `moved > 0.25px` 即触发（962–965）；`needFov` 还包含 `frameCount%30==0`（969）和 `opacityChanged`。
- `computeFov`（1507）→ `fillFogCache`（1910）→ `fogBmp.applyFilter`（1899）；`fovVersion++`（992）使所有掩膜缓存失效。
- `refreshMask`（3037）只在 `lastFov == fovVersion && lastBb == sig` 时跳过（3059–3065）；移动时每帧都进入全量：`bd.copyPixels`/`threshold`（3097–3113）、`bd.compare`（3191）、`applyFilter`（3198）、`finishCurrentMask` 的 `paletteMap`+`threshold`（3269–3270）、`maskInput.copyPixels`（3235）。
- worldRaster 还有第二套分类：`m2e.getVector`（3689）+ `getColorBoundsRect`（3694）；同一 raster 每 FOV 版本至少 2 套分类、5–6 次全幅 pass。
- 固定位置下 30 帧兜底也会制造 4 次/120 帧的全量重建；移动时 30 帧条件被“每帧移动”覆盖，不再是主因。

### 3.2 逐对象 mask + cacheAsBitmap

- 敌人：`applyMask`（3016）给 `u.vis`/`u.hpbar` 各挂一个 Shape mask，并强制 `cacheAsBitmap=true`（3027–3034）；`refreshMask` 给 world visual 也挂 Shape（3757–3761）。每对象一个 Shape（3758）、每个 target 一次 mask 关联。
- 原生事实：`Part` 静态 blit 型本来就是 MovieClip 内单 Bitmap，且 `isAnim==0` 时原生已 `cacheAsBitmap=true`（`Part.as:124`）；`Bullet` 的 `vis` 是 MovieClip，每帧改 rotation/scaleX/alpha/visible（`Bullet.as:158–163,208–239`），原生不缓存。RV 对这两类都补 mask + cache，等于给动画 Bullet/手臂新增每帧缓存重建与逐对象合成。
- 本机 `application.xml` 为 DIRECT 渲染：显示列表由运行库软件渲染，mask/cache 的代价主要落在 CPU 绘制阶段；不能用“GPU 合成便宜”来解释。
- 用户可感知的“子弹动画计算”很可能不在 AS3 分支，而在绘制阶段：D44 `nomask` 能回到 33ms、D57 classic 绘制后 +7.69ms，均指向这里；但具体占比需 P0 分类。

### 3.3 每帧固定扫描与临时对象

- `applyWorldVisuals`（3598）每帧遍历 `loc.firstObj` 链（≤5000，3601–3614）、`grafon.visObjs` 六个层里的全部子对象（3617–3630），再对每个 visual 做 `getBounds`（3672）、字符串 key（3678）、`concatenatedMatrix`（3726）、`worldVisualHasFilters` 递归（3764–3771，每节点读一次 `.filters` 数组副本）；其中 filters 检查最多每 visual 调 2 次（3714 与 3730）。
- `hideEnemies` 每帧 `new Array`×2 + `new Dictionary` + 每单位 `[X,Y]` push（3381–3383、3409、3433、3449、3455、3461）；这些值没有任何消费者（`exempt` 只写不读）。
- `unitBBox` 每次调用新建数组（2861）；`enemyState` 内部已算一次，`applyMask` 又调一次（3460）。
- `prepareOcclusion` 在 current 下每帧全瓦片扫描（966、1479–1503）；48×25 实测 0.09ms，大地图按 tile 数放大。
- 世界特效按瓦片 bbox 键缓存 `worldMasks`（3679–3681）：新 bbox 要建 2 个 Shape + 最多 3 个 BitmapData；120 pass 过期、每 60 pass 清理（3650–3657）。持续扫射时弹体跨 40px 换键，形成分配/GC churn；D57 19 的 RV 调用内 55–68MiB 内存下降与 67–72ms 长帧是相关线索（不是因果证明）。

### 3.4 可以直接避免的“多余遮罩”

- 武器状态直接沿用 owner 的 `enemyState`（3490–3492）：owner 部分可见时，其武器/血条即使整个位于全可见区也会被挂 mask。
- `applyUnitWeapons`（3513）会遍历 `childObjs` 对每个武器建 mask；`hpbar` 在 `state==2` 时无条件建 mask（3031–3034）。
- 全暗 worldRaster 走“空 mask”分支（3163–3167）：图形清空，但 mask 关联与缓存仍保留，目标仍走被遮绘制路径。

## 4. 优化方案

### P0（已完成）：遮罩类别归因实验，不改模组本体

结果见 [P0 报告](2026-10-29-mask-budget-p0.md)。固定/移动两套 active 窗口数据已完成；原先的 AIR 启动阻塞已通过“active 可见窗口 + Popen”通道绕过，但该通道与 D58 私有桌面不同，只作方向性归因。

目的：把 D44 的 10–27ms / 当前 4.8ms 拆成“敌人身体、血条、武器、手臂、Bullet、Part”六类，决定 P3 先改哪一类；同时测 D56 上的移动态 RV 成本，而不是继续拿固定位置数据做决策。

- 复用 `build/combat-render` 的探针（它已能做 `off/normal/nomask/noobjects` 与受控移动），新建 `build/mask-budget`，只编译探针，不编译/替换 mod 本体。
- 变体（每个都在同一进程内往返，配对同输入）：
  1. `off`：关闭 RV；
  2. `normal`：D56 正式源；
  3. `nomask-unit`：只撤 `u.vis + u.hpbar + childObjs` 武器 mask；
  4. `nomask-effect`：只撤 `Bullet/PhisBullet/SmartBullet/Part` mask；
  5. `nomask-arm`：只撤 `visualGrifArm`；
  6. `cache-off`：保持 mask，只把 RV 设过的 `cacheAsBitmap` 还原（仅诊断，允许画面错误）；
  7. `mask-off`：保持 RV 设过的 cache，只把 mask=null（仅诊断，允许画面漏出）；
  8. `hardmask`（后续候选）：特效用不透明二值 mask，不设 target cache。
- 协议：六狮鹫 SMG + 玩家 LMG，固定位置与受控移动（横移/绕圈，30fps 下 ≥4px/帧）两套；每变体两窗，90 帧预热 + 180 帧采样；记录帧间隔、RV 调用、分类 mask 数、`worldRasters` 保留量、内存前后、实际开火数。
- 判据：某一类能解释 normal−nomask 差距的 ≥50%（窗均值方向一致、不重叠）→ 该类进入 P3；若移动态差距远大于固定位置 → 先做 P2；若各类都不显著 → 停止继续在遮罩上投入，转 P4/P2.4。

### P1（零画质改动、低风险，先合入下一条开发线）

1. 删除 `hiddenPos/visiblePos/exempt` 及每单位坐标 push；`applyUnitWeapons` 去掉未使用的 `exempt` 参数（**像素等价**）。
2. `enemyState` 返回/接收 bbox，避免 `applyMask` 二次 `unitBBox`（**像素等价**）。
3. 每个 world visual 每帧只算一次 `hasFilters`，复用到 3714/3730 两处（**像素等价**，保留帧内变化检查）。
4. 父层 `concatenatedMatrix` 每帧缓存一次，传给 `applyWorldVisual`（**像素等价**，需断言帧内父层矩阵不变）。
5. 复用 `scenePaintBounds`/`Rectangle`/`Point` 与 key 字符串缓冲（**像素等价**）。
6. 全暗/全亮早退时 dispose 未使用的 `m2e`/`maskInput`（只影响内存；需确认后续分支不会复用）。
7. `prepareOcclusion` 增加按 `spaceX*spaceY` 的采样/计时计数器；大地图若 >0.5ms 再考虑增量脏标记。
8. 预估：0.3–1.5ms + 减少临时对象/GC 触发概率；**必须单独测量，不与 P2/P3 混算**。

### P2（主收益）：移动态“掩膜刷新降频 + 局部脏区”

1. **刷新节流（首推）**：状态分类（全隐/全显/部分）与 mask 挂/摘仍每帧；软 mask 内容最多每 2–3 帧重建一次，按玩家位移（如 >2px）或 bbox 变化提前触发。预期 `refreshMask` 从约 97 次/帧降到 40–50 次/帧，`hideEnemies` 从 5.13ms 降到约 3–3.5ms。画质影响仅为软边滞后 ≤2–3 帧（66–100ms）；敌人进出阴影的状态切换仍即时。需专门做边界穿越截图与“全暗不漏出”断言。
2. **局部脏区**：`fillFogCache` 写 `currentSight` 时按瓦片标记 dirty；`refreshMask` 只在 bbox 命中 dirty 瓦片、或 bbox/模式/柔化变化时重建。移动时视野锥外/记忆区的大量 mask 可跳过；**理论上像素等价**，但需要严格对照证明确实没漏掉边界情况。
3. **30 帧兜底不无谓 bump 版本**：兜底仍可算 FOV，但只有实际改变 `currentSight`/墙场时才 `fovVersion++`；当前固定位置 4/120 次全量重算会连带 97 个 mask 重算一次，属于周期性尖峰。**像素等价**。
4. **FOV/雾层降频（可选，画质决策）**：移动时雾层按 2 帧更新 + 按玩家位移平移旧图，边界重算；可把 `fillFogCache` 3.5ms/帧砍半，但阴影边缘有 1 帧滞后，需用户确认。
5. **`updateWallSurface` 增量**：当前 2.45ms/帧；先查 `RVWallSurface.update` 是否在镜头移动时全量重绘，再考虑“旧墙图随镜头平移 + 只补新露出条带”，必须做严格像素对照。
6. **`fillFogCache` 瓦片级复用**：只重算 4 角分类或距离桶发生变化的瓦片；连续距离衰减意味着可能不是像素严格等价，只能作为“性能档”备选，不能默认开启。

### P3（遮罩结构，需画质决策）

1. **全暗特效：解除 mask + 只隐藏子位图**。Part 静态 blit 的根节点 `vis.visible` 会被 `Part.step` 读取（`Part.as:141–158`），不能改根；但可对“仅一个 Bitmap 子节点”的 Part 隐藏该 Bitmap、同时把 mask=null 并恢复 cache。D56 只测过“隐藏子位图但保留原 mask”，无收益；本项新增变量是**解除 mask 关联**，需证明全暗像素/动画连续性不变。对 Bullet 的动画 MovieClip 不默认套用。
2. **按目标分类**：血条/武器各自算 bbox 的 FOV 状态；全可见不挂 mask、全暗按既有规则隐藏，只有真正跨边界的才挂软 mask。预期每敌从约 3 个 mask 降到约 1.2 个；像素严格可验。
3. **硬边 mask 性能档**（用户 2026-10-29 选择“保持现状”，暂不推进）：对小型弹体/粒子/手臂使用不透明二值 mask，不设 target `cacheAsBitmap`；画质只差边界 5px 硬边，需截图对照与用户拍板。保留为以后可选项，不进入本轮实现。
4. **特效遮挡档位**（用户 2026-10-29 选择“保持现状”，暂不推进）：`full`（现状）/`performance`（小粒子不逐对象遮）/`off`（不做特效遮挡）；改变可见性语义，本轮不实现。
5. **raster 合并与池化（world-mask 子代理候选）**：合并 `bd`/`m2e` 两套分类、删掉 3087 冗余 `fillRect`、早退释放、按 bbox 量化复用/限容池；目标是把移动态 `refreshMask` 3.09ms 与分配/GC 降下来。需逐决策全等插桩 + 像素 + 原生回放。
6. **链/层增量发现**：`applyWorldVisuals` 的 `loc.firstObj`/`grafon.visObjs` 全扫是每帧固定成本；可用“上次链尾/已知非 arm 集合”增量发现新对象。风险是漏发现=漏遮罩，必须每帧断言“新旧发现集合完全相等”后再用。
7. **共享 mask 的边界**：一个 mask 对象能否同时遮多个 DisplayObject 在资料中说法不一；在严格验证前不作为主方案，只把同一 Shape 位图/几何复用列为次级候选。

### P4（长帧/跨模组归因，与 RV 并行）

- 复用 D57 19 的分段探针（RV / 下一原生 / 其它监听 / 绘制后），但把“其它监听”细分到具体模组：用 ModLoader 选择矩阵跑 RV-only、RV+单个可疑模组、全组合，同种子/同场景/移动交战。
- 记录 `System.totalMemory` 与长帧的关系；RV 的 raster/BitmapData 池化与早退释放是否降低 GC 型尖峰，用 >100ms 次数而非均值验收。
- 已知 D58 的 362ms 峰值有 300ms 在其它监听、关闭 RV 仍有 138ms；若 P4 证明尖峰主要不在 RV，需要在工作区层面协调，不能把它算作 RV 未优化。

## 5. 验证与验收门槛

- **功能/像素**：沿用 D44/D56 的 721 项（自动夹具）与 888 项（原生回放）严格对照；P1/P2.2/P2.3 要求严格 ARGB 相等；P2.1 属于有意的画质取舍，改为“边界截图 + 全暗漏出断言 + 用户确认 + 明确性能收益（用户 2026-10-29 要求）”，不得用放宽容差冒充通过。P3.3/P3.4 用户已选择保持现状，不再列入本轮验证。
- **性能**：同进程 interleaved `off/normal/candidate`，90 帧预热 + 180 帧采样，每条件至少两窗；固定位置与受控移动两套协议；报告均值/P95/最大/>100ms 次数 + RV 平均；不同进程/不同轮次的绝对值不互比；记录环境资格与实际开火数。
- **候选门槛（建议）**：移动态 RV 调用 ≤7ms（D56 基线需先复测）；完整帧均值/P95 相对 D56 改善 ≥8%，>100ms 次数不增加；固定位置无回退；无“全暗可见/记忆区漏出”截图反例；任一条件不满足则保留报告、不部署。
- **部署**：本轮明确不替换模组本体；任何后续候选仍需 D56 基线指纹核对、正式 14 模组组合、设置/改键/保存恢复检查，且不得把 authority 开发线混入发布包。

## 6. 已排除/不要重复的方向

| 方向 | 证据 | 为什么不再投入 |
|---|---|---|
| 继续缩小遮罩几何/裁切 | D56 grid clip 已部署；D57 alpha 裁切、身体 guard；D58 support 23%–95% 扫描减少 | 局部通过但整帧收益不稳定/回退；mask 关联数没变 |
| 预绘/identity blit/stable replay | D55/D56 多轮 | 像素或整帧失败，不能作为生产方案 |
| `effect_alloc` 少建临时对象 | D57 20–22 | 两轮方向不一致，classic 回退 |
| fractional 小数位移裁切 | D58 03–06 | f482 像素反例，普通扫射也不触发 quake |
| 强制 GC、减少特效、降刷新率、改变可见性规则 | 用户约束 | 与保持画面/功能冲突；只能做显式性能档并由用户选择 |
| `cacheAsBitmapMatrix` | AIR 桌面不支持 | 不作为方案 |

## 7. 需要用户拍板的点

1. P0 探针实验已获批准；本轮试跑受 AIR/测试存储启动环境阻塞，需换可启动通道重跑。
2. 软 mask 移动时滞后 2–3 帧：用户 2026-10-29 答复“只在有明显性能收益时才接受”；因此 P2.1 必须先证明移动态 RV 或完整帧有明确收益，再谈画质。
3. 特效遮挡性能档：用户 2026-10-29 答复“保持现状”，P3.3/P3.4 本轮不推进。
4. 跨模组归因：用户 2026-10-29 答复“允许”；P4 可继续进行，但只读日志/协调，不改其它模组。

## 8. 建议的下一步

先做 P0（已完成，active 窗口数据见 [P0 报告](2026-10-29-mask-budget-p0.md)）。移动态 profile 已给出：`updateWallSurface` 2.73ms/帧、`fillFogCache` 约 2.03ms/帧平均、`applyWorldVisuals` 1.85ms/帧、`refreshMask` 0.85ms/帧。P2-A wallgate 未采用（[wallgate 报告](2026-10-29-wallgate-candidate.md)）。三方向尝试已完成（[三方向报告](2026-10-30-three-directions.md)）：方向1 FOV 阈值固定 -0.8ms、移动无帧收益且 P95 变差；方向2 敌人身体 mask 80/20 阈值固定 -0.6ms、移动 **+12.9ms 回退**；方向3 排除 RConnect/ContinuousScene 各约 0–1ms、长帧样本极少，最小组合因存档依赖 #1009 失败。**没有可部署候选**。其他未检查方向的详细调查见 [other-directions 报告](2026-10-30-other-directions.md)：`applyWorldVisuals` 约 99.5 次 visual/帧、链 132.5 节点/帧、层 275 子对象/帧，扫描只约 0.4ms/帧，逐 visual 工作是大头；`fillFogCache` 3.4ms/次且 95% 帧调用，是最大未处理单项。按建议实现的 visfast（完全可见特效 raster 快路径）与 fulldark（全暗 blit Part 解除 mask）均未获收益：固定 normal43.72 / visfast47.61 / fulldark49.30ms，移动 normal46.18 / visfast47.68 / fulldark48.53ms；未部署（[报告](2026-10-30-visfast-fulldark.md)）。下一步优先 fillFogCache 角点复用诊断与 TDFC/MSW/FirearmAttachments 长窗排除，或需用户接受雾层/阴影画质取舍。角点诊断已完成（[报告](2026-10-30-corner-reuse.md)）：48×25 移动场景 99.86% 瓦片-FOV 四角结果完全相同；保守复用候选命中 86/156 FOV、约 298k 次射线，移动帧 -1.27ms（57.77→56.50）、P95 76→73、>100 5→4，但 RV 未降且环境负载高，不能确认。后续验证（[报告](2026-10-30-corner-verify-longwindow.md)）：85,742 个复用瓦片中仅 3 个分类不一致、2 个分支不同（0.0035%），分类近乎等价；但两轮性能方向不一致（18: -1.27ms；20: +0.73ms、RV +1.56、>100 3→6），**未证实收益**。长窗 TDFC 排除：去 TDFC normal 65.30 vs 全组合 67.44、其它监听 5.33 vs 7.59，但 RV/off 环境差异大、长帧均 5 次，TDFC 非尖峰主因。下一步：更干净的角点复用配对，或 MSW/FirearmAttachments 长窗排除，或接受画质取舍做雾层节流。

- 若移动态 RV ≥8ms：先做 P2.1 + P2.2（收益最大且不改可见性规则，只需接受软边 2–3 帧滞后）；
- 若遮罩分类显示 Part/Bullet 占主导：先做 P3.1 + P3.2（像素可验），P3.3/P3.4 作为用户可选档；
- 若两类都不显著：停止在 RV 遮罩上继续微优化，转 P4，并复查玩家实际配置/窗口/其它模组组合。

本轮不改模组本体，主 src/release 与玩家数据保持原样。


## 9. 2026-10-31 落地：v0.33.12-combo 已部署

组合候选通过 active A/B：固定 normal 38.86→35.03ms（-9.9%）、RV 2.80→1.79、>100 1→0；移动 normal 48.44→43.82ms（-9.5%）、RV 8.71→6.19、P95 66→55、>100 3→1。组成：墙面输入门控、四角射线复用、P1 清理、motionstep=2.5（可配置 0.25）。部署 47,195B，SHA256 26456B67…46FB255；旧版 BD64 已备份；官方 ModLoader 路径 smoke 通过。视觉为近似（0.0035% 角点分类差异、2.5px 更新滞后），未做严格像素/视频验收；回退用备份 SWF。[部署报告](2026-10-31-combo-deployment.md)、[回执](../../state/deployment-v03312-20261031.md)。
