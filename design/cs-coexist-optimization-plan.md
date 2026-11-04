# RealisticVision × ContinuousScene 共存卡顿：调查与可执行优化方案

- 状态：**方案（本轮不改源码、不部署）**；§8 工单可直接执行，§7 是验收矩阵
- **基线 = 现行部署 v0.35.0-aperture-grade**：`release/RealisticVisionMod.swf` 51,634B / `C97A6F6C…D76E`（2026-11-04 06:22:57 由并行会话部署），准确源 `build/fov-fix-20261104/v0350/src/RealisticVisionMod.as`
  - 本方案**所有行号以 v0.35.0 源为准**；静态审计 [`build/cs-rv-20261104-audit/AUDIT.md`](../build/cs-rv-20261104-audit/AUDIT.md) 的行号基于 v0.34.8，附录 §10.1 给对照
  - 若实施时又有并行会话部署新版，**必须重新冻结基线并 rebase**（本模组历史上已发生 3 次：cs-window / locmem / eye-boundary 都在他人部署后换基重放）
- **生效配置**：`File.applicationStorageDirectory/RealisticVision_config.txt` 优先，缺失才回退 `release/config.txt`（`RealisticVisionMod.as:604-609`）。本机 store 副本现为 `dim=0.6 / doordim=0.85 / soft_current=25 / preset=0 → fogSub=4 / cs_window=1`，**与 `release/config.txt` 不是同一份**；新键必须两处都写，现场回退改 store 副本
- 宿主：`pfe.swf` 1.02（`A9B39CC7…2D94`）；CS 现行为 0.9.8（`285625F4…8ACF`，2026-11-04 04:46 部署），由并行会话持续演进（本轮只读）
- 用户症状（2026-11-02 23:06）：**ContinuousScene 与 RealisticVision 同时开启时发生严重卡顿**；单独开任一显著更轻
- 授权：用户要求"详细调查并编写可执行的优化方案文件"

---

## 1. 结论摘要

> **实施进展（2026-11-04）**：阶段 A（W8+W7+W2+W1）已实现、**已部署为 v0.35.1-csoptA（52,690B `31bdc9a2…`）并完成运行时实测**：隔离 CS 沙箱 `random_mane` 240×125 行走工况，RV 自报 **12.63 → 9.95 ms/帧（−21.2%）**、整帧中位 85.5 → 80ms、>100ms 帧数 −27.8%，6/6 交错窗口方向一致。离线 A/B 34/34 PASS（标准房 200 帧逐像素相同）。详见 [`build/csopt-20261104/REPORT.md`](../build/csopt-20261104/REPORT.md) 与 [`knowledge/experiments/2026-11-04-csrv-moving-ab.md`](../knowledge/experiments/2026-11-04-csrv-moving-ab.md)。回退：备份 `before-v0351-csoptA-20261104-131846-c97a6f6c/` 或 `large_view_gate=0`。
>
> **重要修正**：下表 W3 行原写的"大图 2–3ms/帧"是**过推**（把 D59 的 0.4ms/帧全部当作随对象数增长）。合成微基准表明逐视觉工作不随地图规模增长，大图额外成本约 **0.3ms/帧**。排序据此调整：W8 > W1（突发）> W2 ≈ W3 > W7。实测也印证：W8+W2+W7+W1 合计 −2.68ms，与微基准预测的 −2.1~−2.4ms 同量级。

`cs_window`（v0.34.6）只收窄了**三处地图尺寸循环**。让"RV 单独开不卡、与 CS 同开才严重"的，是另外几类东西。两条证据线合并后的排序（合成微基准见 §3.4，in-game 证据见 §3.1）：

| 排序 | 编号 | 问题 | 性质 | 量化（合成微基准，非游戏实测） |
|---|---|---|---|---|
| 1 | **W8** | `sceneRefreshWallFieldFast` 角循环只 `continue` 体内，**遍历仍是全图墙角**，每项还做 `%`、`/` | 每帧 **O(全图墙角)** | 30,000 项 **1.75ms** → 窗内 1,200 项 0.072ms ⇒ **≈1.68ms/帧（下界，真实循环体更重）**；实际墙角数待测 |
| 2 | **W1** | `applyVision` 的"墙场变化但非 FOV 帧"把**全图 `wallTiles`** 逐块重绘进 fogCache/currentSight | 突发 **O(全图墙)×子格²** | 6,000 瓦片×16 子格×3 次像素 = **6.67ms/次** → 600 瓦片 0.70ms ⇒ **≈5.96ms/次**；与 RV 自报 `ms=4.32/120` 的 **120ms 峰值**同量级 |
| 3 | **W3** | `applyWorldVisuals` 三段全量扫描（Pt 链 / 层子节点 / units 武器）+ `hideEnemies` 武器链 | 每帧 **O(对象数)** | **已修正**：合成微基准的链遍历段 1,070 节点 = 0.18ms/帧；D59 在 48×25 房测到的 0.4ms/帧里**大部分是逐视觉工作（getBounds/refreshMask/遮罩），不随地图规模增长**。⇒ 大图相对标准房**额外**的 W3 成本约 **0.3ms/帧**（链遍历 + 层扫描），不是早先按 D59 全额外推的 2–3ms |
| 4 | **W2** | `computeFov` 的 `fov` **全数组清零** | 每次 FOV 重算 **O(map)** 写 | 30,000 写 **0.278ms** → 2,809 写 0.019ms ⇒ **≈0.258ms/次**（移动时≈每帧） |
| 5 | **W7** | `enemyState` 每帧 `new Vector.<int>(spaceX*spaceY,true)` | 每帧 **O(map) 分配** | 67.5µs/帧 + **120KB/帧** 零填充垃圾（48×25 只有 4.8KB，所以标准房看不见）；成本以 **GC 长帧**出现在 RV 计时之外 |
| 6 | **W4** | `refreshWallField` rebuild 分支 | 事件驱动 **O(map)** 尖峰 | 开门即触发（原生 `Box.setDoor` 写 `tile.opac=0`）：两次全图 `getTile`（≈60,000）+ 数千 `drawRect` + 两个 30,000 元素数组重建 |
| 7 | **W6** | 雾层/墙层**掩膜合成面积**疑似随地图面积增长 | 每帧（**渲染阶段，不进 RV 计时**） | `wallBmp` 世界尺寸：标准房 ≈1,960×1,080，大图 ≈**9,640×5,080（23 倍面积）**；单层 32bpp 上界 ≈187MiB；合成微基准**覆盖不到**，只能靠诊断臂 C/D |
| — | W5 | classic 模式 `advanceMemory` 全图 + 全图分类 + `structHash` 全图 | 仅 `mode=classic` | 默认配置不触发；F12 切到 classic 后大图**更糟** |

另两个**正确性**缺口（顺带修，不属于性能）：

- **`guard<5000` 截断**（`v0350:995`、`:1661`、`:4306`、`:4439`）：`loc.firstObj` 按创建顺序**追加到链尾**（原生 `Location.addObj`，`game-reference/…/fe/loc/Location.as:2271-2293`），链长超 5000 时 RV 静默停止处理**最新的对象**——大图里正好是弹体与粒子。30,000 瓦片的地图可能触顶，必须实测链长。
- **CS 包装导致狮鹫手臂失效**：CS 把层子节点包进 `flash.display::Sprite` wrapper（`SceneObjectCulling.as:103-115`），RV 用 `getQualifiedClassName(child).indexOf("visualGrifArm")==0` 分类（`v0350:4467-4468`）→ 永远 false，暗处手臂不再被 RV 遮挡（静默视觉退化，不增加每帧成本）。

三项"CS 交互猜疑"已验证**不成立**，不必再查（审计 §4）：

1. RV 掩膜 Shape 不会每帧反复 `addChild`（稳定态 `visual.parent` 就是同一个 wrapper；只有进房/CS 重绑那一帧重挂一次）。
2. `visLight.visible` 不是 CS 在抢（生产 CS 从不写 visible；抢的是原生 `Grafon.as:425`/`UnitPlayer.as:397`/`Consol.as:463`，属既有问题）。
3. `fillFogCache`/`updateWallSurface`/`RVWallSurface` 已是**视口域**，不是 O(map)，不该围着 `cs_window` 再收窄。

---

## 2. 现状：`cs_window` 到底做了什么

激活（`v0350:1160-1164`）：`cfgCsWindow==1 && grafon!=null && "sceneLarge" in grafon && grafon["sceneLarge"]==true`；每帧 `updateCsWindow(loc)`（`v0350:2307-2318`）算 `csWin = scenePaintBounds() ∪ 玩家±(视野半径+1瓦片)`。

已门控三处：`scenePrepareOcclusionFast` 瓦片扫描（`v0350:1738-1742`）、`sceneRefreshWallFieldFast` 角循环**体**（`v0350:1788-1790`）、`hideEnemies` 远敌分类（`v0350:4200-4219`）。

`scenePaintBounds()`（`v0350:2290-2301`）：`spaceX>48 || spaceY>25` 时返回"相机视口 ±4 瓦片"，否则整张图。**这条分支是标准房/大图的分界线**，后续所有改动都必须复用它门控，保证标准房行为零变化（现有 8,598 项严格等价断言因此继续当护栏）。

> ⚠️ 逃生口的代价：`cs_window=0` 或宿主缺 `loc.space` 时，`prepareOcclusion` 会退回**每帧全图 getTile 扫描**（`v0350:1832-1852`），比开窗口还慢得多。所以"卡顿时先关 cs_window"不是好的现场建议。

---

## 3. 证据基础

### 3.1 已有实测（引用，非本轮）

| 来源 | 数据 | 用法 |
|---|---|---|
| `build/cs-window-20261103/evidence/csrv-final-on*/RVision.log` | 大图静止时 RV 自报 `ms=4.32/120`、`3.67/31`、`3.42/16`、`3.10/25`——**均值 3–4.3ms，峰值 120ms** | 证明①持续成本存在（3–4ms）；②存在 **100ms+ 的 AS3 尖峰**（只可能是 W1/W4 这类突发路径） |
| 同目录 `result.json`（ON/OFF 四轮） | 均值 75.5 / 82.6 / 84.6 / 86.2ms，两臂无一致差异 | 该轮是**静止**工况，未分离渲染侧成本；可作"静止大图约 75–86ms/帧"的环境基线 |
| CS `knowledge/experiments/scene-compat-20261024.md:148-153` | 大场景 71.48ms vs 普通房 44.59ms（RV/光/WB **全关**） | 大场景本身已贵 1.6×；RV 增量必须在这之上单独测 |
| CS 同文件 `:153` | 逐帧遍历对象均值 **普通房 141.6 → 大场景 1070.8** | W3 的规模因子 |
| RV `state/MEMORY.md` D59 条 | 普通房 `applyWorldVisuals` 约 **0.4ms/帧**（99.5 visual、`firstObj` 链 132.5、层子节点 275/帧）；移动态 `updateWallSurface` 2.73ms、`fillFogCache` 2.03ms | W3 的基线成本，按对象数外推 |

### 3.2 静态可证（本轮 + 审计，行号见附录）

- `fov` 只有一个写者（`computeFov`），其余全只读 → W2 可安全窗口化（证明见 §4.5）。
- 一次 `computeFov` 之后，`fov` 的**非 NONE 集合 ⊆ 扩展视野盒**（第一循环写圆盘盒、第二循环只把范围外扩 1 且只写 `FOV_VISIBLE`）。
- `currentSightData` 在每次雾重绘后被置 null（`v0350:2361`、`:2377`）→ `sightClasses` 每帧整图分配（W7）。
- `wallGeometryDirty` 置位点：`resetRoom`（`v0350:1298`）、`scenePrepareOcclusionFast` 拓扑变化（`v0350:1757-1762`）、`prepareOcclusion` 首次/全扫（`v0350:1826-1831`、`:1848-1850`）；清除点 `v0350:2349`（current）。
- CS 剔除的可见域 = 镜头视口 **+560px**（`SceneObjectCulling.as:41-42`、`:53-54`：±320px 再留 240px）；而 `csWin` 在相机一侧只有 **4 瓦片=160px** 余量（`v0350:2296-2299`）。**所以任何"按窗口跳过对象"的方案，判据域必须 ≥ csWin⊕14 瓦片**，否则会出现"CS 仍在画、RV 已跳过"的一两帧未遮罩（这也是本方案优先选"增量游标"而不是"窗口跳过"的原因）。

### 3.3 本轮实测：**未取得**（环境阻断），设施已就绪

本轮安排了实测取证（T1），**未拿到任何帧数据**，原因是环境而非方法：

- 本会话文件沙箱**禁止写入 `%APPDATA%`**（已独立复核：pwsh 写 `%APPDATA%` → `UnauthorizedAccessException`；`%TEMP%` 普通文件可写）。
- AIR 子进程继承该限制 → `File.applicationStorageDirectory` 不可写（MinAIR 报 `Error #3003`；写已存在 store 报 `Error #3001`）→ 宿主 `pfe.swf` 启动早期停住：进程活着、CPU 空闲、`stderr/stdout` 0 行、`%APPDATA%` 下无 store，**ModLoader 一个模组都没初始化**。所以不是"进不了 random_mane"，而是"没进游戏"。
- 2026-11-04 00:59 那一轮能跑通（`build/cs-window-20261103/evidence/csrv-final-*`），是因为那轮会话的 AIR 子进程有 `%APPDATA%` 写权限。

已就绪、可直接交给有权限的会话（见 [`build/cs-rv-20261104/REPORT.md`](../build/cs-rv-20261104/REPORT.md) §3/§7）：

| 设施 | 状态 |
|---|---|
| 冻结输入（宿主 A9B39CC7 / RV v0.34.8 `E0437A7F` / CS 0.9.8 `285625F4` / `scene.xml` / `rooms_mane.xml`） | ✅ SHA 全部钉死（注意：RV 现已是 v0.35.0，需重新冻结） |
| 隔离沙箱 `runtime/`（CS runtime 复制：100 硬链接 + 694 复制；RV + CS 冻结快照 + 自有驱动） | ✅ |
| 驱动 `CsRvMoveProbeMod`（进 random_mane、±220px 折返移动、逐帧帧间隔 + X + tileHash + Pt 链/层子节点/units/fog 子树采样，全部写工作区） | ✅ 已编译 `EFE50FBE…` |
| 插桩 RV（13 个方法 getTimer 包装 + rebuild 计数 + 逐帧采样，`main["rvAuditAPI"]`） | ✅ 已编译 `09F07CED…` |
| 日志探针 RV（只把 `fileLog` 落到工作区，行为不变） | ✅ 已编译 `55F1311C…` |
| 六臂（A=RV off / B=RV on / C=隐藏雾层诊断 / D=摘 mask 诊断 / I=插桩 / L=日志探针）+ `game-coexist` 登记脚本 | ✅ |
| 实际运行 | ❌ 全部被上述权限阻断（`evidence/` 保留每轮失败原始日志） |

**结论**：本方案的所有"预期收益"在拿到 T1 数据前都只是**结构推断**，不得作为收益声明；§7 的 P1/P2 必须在有 `%APPDATA%` 写权限的会话重跑后才成立。

### 3.4 本轮取得的**合成微基准**（有数，但不是游戏实测）

游戏跑不动，于是用**同一 AIR 运行时**（`adl64.exe` 51.1.3.3、`debug=false`、`optimize=true`、1280×800 cpu、隐藏窗口）做了一个独立 AS3 工作负载模型，按 `spaceX=240 / spaceY=125 / tile=40px / fogSub=4` 复刻各路径的**循环与像素操作**，同进程 ABAB×5 轮、每变体每轮 ≥200 次。产物：`build/cs-rv-20261104/microbench/MICROBENCH.{json,md}`，复算 `python microbench/compile_run.py`。

| 组 | 路径 | A 全量（µs/次） | B 窗口/复用（µs/次） | **单次可省** | 若每帧 1 次 |
|---|---|---|---|---|---|
| M5 | **W8** 墙角落 30,000 项 `%/ /`+4 比较+continue → 窗内 1,200 项 | 1,747.5 | 71.75 | **1.676 ms** | 1.68 ms/帧（持续） |
| M4 | **W1** 墙像重填 6,000 瓦片×16 子格×(get+set+set) → 600 瓦片 | 6,665 | 701 | **5.96 ms** | 突发（非每帧） |
| M1 | **W2** `fov` 清零 30,000 → 53×53 窗 | 277.5 | 19.25 | **0.258 ms** | 每次 FOV 重算 |
| M3 | **W3** Pt 链 1,070 节点"is 判定+构造函数查表" → 只走新增 10 节点 | 180 | 1.7 | **0.178 ms** | 0.18 ms/帧（仅链段） |
| M2 | **W7** 每帧 `new Vector.<int>(30000,true)` → 复用+代次戳 | 67.5 | 0.15 | **0.067 ms** + 120KB/帧垃圾 | 0.07 ms/帧 + GC |
| M6 | 每帧 6×`new Rectangle`+2×`new Point` → 复用 | 0.8 | 0.16 | 0.0006 ms | 可忽略 |

**必须随数字一起引用的边界**（否则就是误导）：

- 这是**合成 AS3 模型，不是游戏实测**，不能外推帧率/卡顿收益；未建模对象字段访问、`getTile`/`visi` 读取、显示列表与合成、GC 停顿。
- **M5 是下界**：模型只含索引算术+比较，真实循环体还要 `advanceMemory` + `explorationLight`（`getTile`+`visi`）。但真实 `wallCorners` 长度**未知**（模型用 map 面积当上界），若实际墙角数只有 ~5,000，则 W8 的实省按比例缩到 ~0.28ms。
- **M4 的 6,000 瓦片是假设值**（30,000 瓦片里 20% 是墙）；且 W1 只在"墙场变化但非 FOV 帧"触发，频率未测。
- **M3 只覆盖 W3 三段中的链段**；层子节点 1,070 与 units 扫描未建模，而 in-game D59 证据（48×25 房、链 132.5+层 275 → 0.4ms/帧）说明**逐对象的实际工作（getBounds/refreshMask/applyFilter）才是大头**，所以 W3 的排序主要依据 in-game 证据，而不是 M3 的 0.18ms。
- M2 的内存曲线只说明"分配→回收锯齿存在"，**不等于测得 GC 长帧**。
- **W6（掩膜合成）完全未被覆盖**——它发生在显示列表/AIR 合成，合成模型碰不到，只能靠 C/D 诊断臂或游戏实测。

**两个视角合并后的排序**（本方案采用；2026-11-04 已按微基准修正 W3）：

1. **W8**（合成证据最强、纯遍历结构改动、风险最低）→ 阶段 A 第一项。
2. **W1**（单次 6ms 级、与 RV 自报 120ms 峰值吻合的突发路径）→ 阶段 A。
3. **W2**（0.26ms/FOV，等价性可证）→ 阶段 A。
4. **W7**（持续 0.07ms + 120KB/帧 GC 机制）→ 阶段 A。
5. **W3**（**修正后**：大图额外成本约 0.3ms/帧，主体是链遍历与层扫描；逐视觉工作与地图规模无关）→ 阶段 B，优先级低于 A。
6. **W4 / W6**（尖峰与渲染侧，需专门诊断）。

---

## 4. 逐项根因与修法

> 格式：现状 → 为什么是放大器 → 修法（可执行）→ 不变量/等价性 → 风险。

### 4.1 W3：三段全对象扫描（in-game 证据最强的一项）

**现状**

```as3
// hideEnemies 尾部 v0350:4306-4334  每 needFov 帧 + 每 3 帧
var obj:Pt = loc.firstObj;
while(obj != null && guard < 5000) { if(obj is Weapon) { … } obj = obj.nobj; guard++; }
// 紧接着 v0350:4339 → applyWorldVisuals(w,loc)
//  (a) v0350:4439-4460  再来一次 loc.firstObj 全链（Part/Bullet/PhisBullet/SmartBullet）
//  (b) v0350:4462-4486  for(layer in visObjs) for(i = numChildren-1 …)  ← 只看 visualGrifArm
//  (c) v0350:4488-4511  for each(unit in loc.units) ← 只为 state==1 单位的 childObjs 武器
```

CS 把**整张连续地图装进同一个 `Location`**，于是这三段的域从"整间房"变成"整张图"。按 D59 的 0.4ms 基线外推，大图 2–3ms/帧。

**修法（分三步，风险递增）**

**B1 合并遍历（低风险，先做）**：把 (a) 与 `hideEnemies` 的武器链合并成一次链遍历。语义不变（同一条链、同帧、链序），只是两次 ~1,070 节点遍历变一次。

**B2 Pt 链增量游标（中风险，主收益）**：原生链只在**链尾追加**，`remObj` 修补指针。因此：

```as3
private var fxCursor:Pt = null;         // 上次遍历到的节点
private var fxCursorLoc:Location = null;
private var fxLive:Vector.<Object> = new Vector.<Object>();   // {pt, vis, kind}
```

- `loc !== fxCursorLoc` 或 `fxCursor == null` 或 `!fxCursor.in_chain` → 全量遍历一次重建游标（每房间一次，或对象被删后的兜底）；
- 否则从 `fxCursor.nobj` 开始走，只处理**本帧新追加**的对象，`Part/Bullet/…` 记入 `fxLive`；
- 每帧对 `fxLive` 逐项执行原 `applyTransientVisual`/`applyWorldVisual`（同一调用），`visual.parent == null` 时剔除；
- 遍历结束把游标推进到当前链尾。

等价性：任何对象在第 N 帧在链中，要么第 N-1 帧前已在链里（→ 已注册），要么第 N 帧被追加（→ 游标从旧尾扫到新尾必遇）。删除的对象 `vis.parent==null` 被剔除，而 `applyWorldVisual` 对 `parent==null` 原本直接 return（`v0350:4587`）。故"处理集合"逐帧等价。

**B3 层子节点 → ADDED 注册表（中风险，同时修视觉缺陷）**：给每个 `visObjs` 层挂 capture 阶段 `ADDED`/`REMOVED`，只对新子节点分类一次：

- 直接子节点类名匹配 `visualGrifArm` → 注册；
- 若是 `Sprite` wrapper 且 `numChildren==1` → 取内层 child 判类（**修复 CS 下的手臂遮罩**）；
- 每 120 帧审计一次兜底（对齐 CS `audit()`）。

每帧只遍历注册表（0–个位数）。**注意**：若用户关掉 CS 的 `objectCullingEnabled`，层结构回归直挂，同一套事件注册仍成立，不需分支。

**B4 `worldVisualHasFilters` 缓存（低风险）**：`v0350:4735-4742` 递归 `numChildren`，按 visual 缓存到下一帧即可。

**风险**：B1 极低；B2 中（验证"边遍历边删""换 loc""跨楼层"，见 V8）；B3 中（新增/移除/换层/reparent 四类夹具，见 V6）。
**不做"按窗口跳过对象"**：CS 的 560px 剔除余量 > `csWin` 的 160px 余量，窗口跳过会漏画；若将来要做，必须 csWin⊕14 瓦片 + 回滞 + "有记录者不跳"。

### 4.2 W7：`enemyState` 每帧整图 `Vector` 分配（GC 主源）

**现状**（`v0350:3698-3716`）：

```as3
if(cfgMode=="current" && currentSightData==null && currentSight!=null && (spaceX>48||spaceY>25))
   this.currentSightData = new Vector.<uint>();                 // 3698-3704：每代一个小对象
if(cfgMode=="current" && currentSightData!=null) {
   if(bb 有效) {
      if(this.classifiedSight !== this.currentSightData) {
         this.classifiedSight = this.currentSightData;
         this.sightClasses = new Vector.<int>(spaceX*spaceY,true);   // 3712-3715：120KB/代
      }
```

`currentSightData` 每次雾重绘后被置 null（`v0350:2361`、`:2377`）→ 每代一次 O(map) 零填充分配。附带每个未分类 bbox 瓦片还各 `new` 一个小 `Vector.<uint>`（`v0350:3736-3740`）。

**为什么是放大器**：分配本身不进 `ms` 均值，但 60fps × 120KB = 7.2MB/s 确定性垃圾 → 周期性 GC 停顿。本工作区多有"每帧 JSON/克隆 → GC 掉落"的前科（Addiction/RConnect/FirearmAttachments 均 ~139–1,400 新对象/帧）。

**修法（低风险，逐格等价）**：

```as3
private var sightClasses:Vector.<int> = null;     // 每房间一次
private var sightClassGen:Vector.<int> = null;    // 代次戳，每房间一次
private var sightGen:int = 0;                     // 视野场每变化一次 +1
```

- 两处 `this.currentSightData = null;` → 改为 `this.sightGen++;`（保留 `currentSightWritten` 原语义）；
- `classifiedSight !== currentSightData` → `sightClassGen[ti] == sightGen`；
- `currentSightData` 改成**稳定空向量**（`data.length==0` 分支语义不变，`v0350:3736-3740`）。

等价性：分类结果只依赖"本代是否已分类"，代次戳精确复刻"换新数组"的失效语义。`resetRoom`/`resetOff`（`v0350:1256`、`:1297` 已把两者置 null）要同步把 `sightGen` 归零或让数组重建。

**风险**：低-中。必须逐条核对 `currentSight` 写路径都在"置代"之后（`v0350:2361`、`:2377`、`:2493` 的 `fillRect` 清旧区、`:2355` 循环）——漏一条就会用上一代分类。

### 4.3 W1：`wallTiles` 全图重绘（最贵的突发成本）

**现状**（`v0350:2350-2362`）：

```as3
if(wallChanged && !needFov && !sceneViewChanged) {
   var maskChanged:Boolean = false;
   this.currentSightWritten = null;
   for each(var wi:int in this.wallTiles)                          // 全图墙瓦片
      if(this.fillWallTile(wi % this.spaceX,int(wi / this.spaceX),true)) maskChanged = true;
   if(maskChanged) this.fovVersion++;
   this.currentSightData = sceneLarge ? null : this.currentSight.getVector(this.currentSight.rect);
}
```

`fillWallTile(trackMask=true)`（`v0350:3038-3091`）走 16 子格 × (读旧值 + 写 fogCache + 写 currentSight)。

**触发条件为什么常开**：`sceneRefreshWallFieldFast` 每帧以 `advance=true` 推进墙角记忆（`fadestep=0.1`），窗口内还有角没收敛 `wallA` 就变 → `changed=true`。每次 FOV 变化后约 10 帧收敛；原生光照变化也触发。表现为"停下来/开火时掉帧"。

**修法（低-中风险）**：把遍历域换成"本帧可见域"：

```as3
if(wallChanged && !needFov && !sceneViewChanged)
{
   var maskChanged:Boolean = false;
   this.currentSightWritten = null;
   if(this.largeViewGate())          // cfgLargeView==1 && (spaceX>48||spaceY>25)
   {
      var r:Rectangle = this.wallRefreshRect();
      for(var wy:int=int(r.top); wy<int(r.bottom); wy++)
         for(var wx:int=int(r.left); wx<int(r.right); wx++)
         {
            if(loc.getTile(wx,wy).opac < 1) continue;
            if(this.fillWallTile(wx,wy,true)) maskChanged = true;
         }
   }
   else for each(var wi2:int in this.wallTiles)
      if(this.fillWallTile(wi2 % this.spaceX,int(wi2 / this.spaceX),true)) maskChanged = true;
   if(maskChanged) this.fovVersion++;
   this.currentSightData = sceneLarge ? null : this.currentSight.getVector(this.currentSight.rect);
}
```

`wallRefreshRect()` = `scenePaintBounds() ∪ (eyeX/eyeY ± (locDist2/40 + 1) 瓦片)`，clamp 到地图，返回复用字段。**必须独立算**，不能直接复用 `csWin`：CS 未安装但地图大时 `csWin` 仍是 `resetRoom` 的整图初值（`v0350:1319-1320`），复用会退化成全图；独立算在两种情况下都正确。用 `eyeX/eyeY`（`computeFov` 写入，v0.35.0 已是钳制后的 `visionEye`）而非 `loc.gg`，与射线起点一致。

**语义不变量**：

1. **绘制域**：`fogVis.scrollRect`（`v0350:1560-1575`）之外不参与合成；窗口含视口 ±4 瓦片 + 圆盘，覆盖模糊/双线性外溢。
2. **掩膜取样域**：`currentSight` 只被"视野圆盘内"单位消费（state 1/2 要求 `fov != NONE`）；窗口外单位是 state 0（隐藏）。
3. **自愈**：`fillFogCache` 遍历域本来就是 `sceneBounds`（`v0350:2506-2508`），下次进入视口即覆盖。
4. **`maskChanged → fovVersion++`** 收窄为"窗口内掩膜跨阈值"，即窗口外陈旧掩膜不再强制全体单位掩膜重取——收益方向，需 V3/V4 验证无可见差异。

**风险**：低-中（唯一可见风险是"窗口外雾像素陈旧"，而它不可见）。

### 4.4 W8：`wallCorners` 只门控了循环体

**现状**（`v0350:1782-1790`）：`for each(index in corners)` 遍历**全图墙角**，每项先 `index % width`、`int(index / width)` 再四次比较后 `continue`。

**修法（低风险）**：`wallCorners` 按行生成（`v0350:2830-2851` 的 y 外循环、x 内循环逐行 push），建表时同步记录 `wallCornerRowStart:Vector.<int>`（长度 spaceY+1），窗口化时只遍历窗口覆盖的行区间。**值语义完全不变**（窗外角本来就被 `continue`，`changed` 只是 OR 累积，与顺序无关）。

消费点需同步：`v0350:1782`、`:2865`、`:3389`（classic）、`joinClassicWalls`；classic 继续全量遍历。

**风险**：低。

### 4.5 W2：`fov` 全数组清零

**现状**（`v0350:1992`）：每次 FOV 重算 `for(clearIndex < spaceX*spaceY) fov[...] = FOV_NONE`。

**修法（低风险）**：只清上一轮写过的扩展盒。

```as3
private var fovClearAll:Boolean = true;
private var fovWriteX0:int, fovWriteY0:int, fovWriteX1:int, fovWriteY1:int;

// computeFov 内，替换 v0350:1992
if(this.fovClearAll) {
   for(var ci:int=0,n:int=this.spaceX*this.spaceY; ci<n; ci++) this.fov[ci]=FOV_NONE;
   this.fovClearAll = false;
} else if(this.fovWriteX1 > this.fovWriteX0 && this.fovWriteY1 > this.fovWriteY0) {
   for(var ix:int=this.fovWriteX0; ix<this.fovWriteX1; ix++) {
      var ib:int = ix + this.fovWriteY0*this.spaceX;
      for(var iy:int=this.fovWriteY0; iy<this.fovWriteY1; iy++, ib+=this.spaceX) this.fov[ib]=FOV_NONE;
   }
}
// 紧接着（两个循环之前）记录本轮写入超集：
this.fovWriteX0 = Math.max(0, fx0-1); this.fovWriteY0 = Math.max(0, fy0-1);
this.fovWriteX1 = Math.min(this.spaceX, fx1+1); this.fovWriteY1 = Math.min(this.spaceY, fy1+1);
```

`resetRoom`（`v0350:1319` 附近）追加 `this.fovClearAll = true;`。

**等价性**（证明见审计 §3.1）：非 NONE 值只可能出现在扩展盒内；每次调用先清上轮盒再写本轮盒 ⇒ 任意时刻与"全清+重算"逐格相等。边界：半径变化双向、传送、**异常半写（记录点必须在写之前，异常时下一帧多清一次而不是漏清）**、classic 的全图读（只要求"与全清一致"，满足）。

**风险**：低（`fov` 唯一写者）。收益：每次重算 30,000 → 约 2,800 次写。

### 4.6 W4：`wallGeometryDirty` 的整图重建尖峰

**现状**（`v0350:2806-2857`）：`new Array(n)`×2、`wallRaw.fillRect`、逐行两遍 `getTile`（≈60,000 次）、每段墙/地板 run 一条 `drawRect`、重建 `wallTiles`/`wallCorners`。触发：开门/破墙（原生 `Box.setDoor` 写 `tile.opac`，`Box.as:679-693`）、进房。

**为什么不能"分帧重建"或"只建窗口"**：`wallClip`/`floorClip` 是 `fogBitmap`/`wallLayer` 的**唯一 mask**（`v0350:1527`、`:1537`）。分帧中途渲染 → mask 不完整 → 整层雾/墙漏出；只填窗口 → 窗口外也未遮罩。两种都会肉眼可见（审计 §3.4 与本文一致）。

**修法（两种，均要求"同一帧内原子提交"）**

1. **行桶 mask（推荐）**：把 `wallClip`/`floorClip` 从"单个 Shape"改成"每行一个 Shape 的容器"（mask 允许 DisplayObjectContainer）。拓扑变化时只重画受影响的行；`wallA/wallRaw/wallTiles/wallCorners` 与 mask 在同一帧提交。开门只影响 1–2 行 → 成本从 O(map) 降到 O(行×行内 run)。
2. **双缓冲原子换**：重建到 staging Shape，完成后同一帧把 `fogBitmap.mask`/`wallLayer.mask` 指过去（进房全新重建用这条）。

同时用 `wallRebuildPending` 把重建合并到最多每 N 帧一次（`wall_rebuild_frames`，默认 2）。

**风险**：中高（mask 语义错会让整层雾/墙消失或反转），必须 V5 像素级 A/B。**收益**：中等（消除每次进门/开门的 O(map) 尖峰）。

### 4.7 W6：雾层/墙层掩膜合成面积（待诊断臂定论）

`wallBmp` = `(spaceX+1)×(spaceY+2)` 像素放大 40×；`fogBitmap` = `(spaceX*fogSub+2*FOG_PAD)`（`FOG_PAD=4`、`fogSub=4`）放大 10×：

| 场景 | wallBmp 世界尺寸 | fogBitmap 世界尺寸 |
|---|---|---|
| 48×25 房 | 49×27 → 40× → ≈1,960×1,080 | 200×108 → 10× → ≈2,000×1,080 |
| 240×125 大图 | 241×127 → 40× → ≈**9,640×5,080** | 968×508 → 10× → ≈**9,680×5,080** |

若 AIR 的掩膜子表面按"被遮罩对象 bounds"分配，则每帧雾层合成成本随地图面积增长，且**不进 RV 的 `atMsSum`**——正好解释"RV 自报 3–4ms 却严重卡顿"。诊断臂见 §8/T1（臂 C 隐藏雾层、臂 D 摘 mask）；两臂都改变画面，只用于归因。

静态上界参考（**不是实测**）：单层 32bpp 若按上述尺寸分配 ≈187 MiB/层，两层 ≈375 MiB——一旦成立足以解释严重卡顿；是否真的按 bounds 分配必须靠 C/D 实测。

**若确诊** → 阶段 D：把 `wallRaw`/`fogCache` 的**工作位图改成视口尺寸 + 原点偏移**（如 64×40 瓦片），索引换算统一走 `fogOffsetX/Y`，掩膜对象 bounds 降到视口级。改动面大，排在 A/B 之后。

### 4.8 W5：classic 模式（非默认，单列待办）

`mode=classic` 时多出 4 条 O(map) 路径：`advanceMemory` 全图（`v0350:3211`）、全图双循环（`v0350:3213-3271`）、`prepareClassicCells`（`v0350:3304-3334`）、`structHash` 每 2 帧（`v0350:1683-1697`）。默认 current 不走，但 F12/选项页切过去后大图明显更糟。窗口化方案与 current 不同（时间积分语义、`classicCells.dirty` 的 1 瓦片邻域扩散），须单独设计与像素 A/B，**不在本方案默认路径内**。

### 4.9 顺带的小项（低风险、低收益，可打包进阶段 A）

| 项 | 位置 | 改法 |
|---|---|---|
| `guard<5000` 截断 | `v0350:995`、`:1661`、`:4306`、`:4439` | 提到 20,000 并在触顶时记录一次；先实测真实链长（T1） |
| `ensureFog` 每帧幂等写 | `v0350:1560-1586` | `scrollRect`/`x/y`/`colorTransform`/`blendMode` 写前比较，不改变可见结果 |
| `scenePaintBounds` 每帧多次 new Rectangle | `v0350:2290-2301` 及各调用点 | 复用静态 Rect（注意调用点可能持有引用） |
| `RVKeybinds.tick` 每帧 `getDefinitionByName` + `getChildByName` | `RVKeybinds.as:64-79` | 注册成功后缓存类引用 |
| `worldMasks` 清扫尖峰 | `v0350:4517-4524` | 每 60 帧全扫改每帧固定 N 条 |

---

## 5. 配置键设计

**注意生效路径**：`loadConfig` 先读 `applicationStorageDirectory/RealisticVision_config.txt`，不存在才回退 `release/config.txt`（`v0350:604-609`）；`saveConfig` 写 store 副本（`v0350:860-864`）。⇒ 新键要**两处都写**，否则本机会读不到 `release/config.txt` 的改动；现场回退应改 store 副本。

| 键 | 默认 | 语义 | 回退 |
|---|---|---|---|
| `cs_window` | 1 | 既有 CS 适配（三处门控） | 0 = v0.34.5 语义（会退回全图扫描，更慢） |
| `large_view_gate` | 1 | **阶段 A 实现版只门控 W1**（墙重填视口化）；W8/W2/W7 无独立键——它们逐格/逐像素等价，回退靠恢复备份 SWF | 0 = W1 回到全图 `wallTiles` 重填 |
| `wall_rebuild_frames` | 2 | （阶段 C，未实现）重建合并帧数 | — |
| `fog_view_bitmaps` | 0 | （阶段 D，未实现）视口尺寸工作位图 | — |

解析点：`v0350:635-757` 的 `else if(key == …)` 链（建议插在 `cs_window`（`:688`）之后）；写回点 `v0350:800-860`。性能键不进 UI 设置页。

---

## 6. 阶段划分与排序理由

- **阶段 A（低风险，先合一个版本）—— ✅ 已实现、已实测、已部署（v0.35.1-csoptA，2026-11-04）**：**W8（角表分桶）** + W7（分类代次戳）+ W2（fov 增量清零）+ W1（墙重填视口化）+ 逃生口 `large_view_gate`。离线 34/34（标准房 200 帧逐像素相同；大图 CS 开/关 40 帧逐帧相同；W1 窗口内 539,328 px 零差异 + 1 帧自愈；W7 15→0 次重建；W8 7,019 角覆盖无遗漏）。运行时不重复测量：RV 自报 **12.63→9.95 ms/帧**、整帧中位 85.5→80ms、>100ms −27.8%。
- **阶段 B（中风险）—— 建议降级为"需要时再做"**：W3 修正后大图额外成本仅约 0.3ms/帧（B1 合并遍历省一半遍历、B2 增量游标再省剩余、B3 ADDED 注册表省层扫描**并修好 CS 下的手臂遮挡视觉缺陷**）。B1 可单独先上；B3 属"视觉行为改变"（手臂重新被遮挡），应独立立项与截图 A/B。
- **阶段 C（中高风险）**：W4 行桶 mask + 重建合并。需要专门的开门/破墙视觉 A/B。
- **阶段 D（实验，需 T1 确诊 W6 后立项）**：视口尺寸工作位图。**当前最未知、也可能最重的一项。**
- **阶段 E（非默认配置）**：classic 全图路径对齐。

每阶段独立构建、独立登记、独立部署、独立回滚；**不把多个未验收阶段打包成一次部署**。

---

## 7. 验收矩阵

### 7.1 正确性（任一失败即停止，不得进入性能阶段）

| 编号 | 方法 | 通过标准 |
|---|---|---|
| V1 | `tools/boundary-opt2/BoundaryExactProbeMod`（8,598 项：96 组场严格相同、弹体断言、8,000 射线回归、模式/分辨率矩阵）标准房 baseline vs candidate | 全过；`fov`/`seenSub`/`fogCache`/`currentSight` 与基线**逐元素/逐像素相同**（标准房不进入任何新分支） |
| V2 | 同上，`mode=classic` | 全过（证明阶段 A/B 没碰 classic） |
| V3 | 大场景整屏合成对比：同字节基线与候选、同帧同眼位同相机，比较**整个 Stage 像素** | 差异 0 |
| V4 | 大场景相机平移自愈：只靠原生移动把视口移入此前窗口外区域 | 进入视口后 **≤1 帧**与基线逐像素相同 |
| V5 | 开门/破墙（阶段 C）：开门前后各 30 帧整屏对比 + 该帧耗时 | 像素差异 0；最大帧显著低于基线 |
| V6 | 层/手臂专项（B3）：新增、移除、换层、被 reparent 四类夹具；CS 开/关两种形态 | 手臂在暗处被正确遮挡；无残留 mask；`objectCullingEnabled=false` 时同样正确 |
| V7 | 帧级：`init ok vX`、设置注册、`tick 1/181/361`、ModLoader 正式加载 | 与既有门禁一致 |
| V8 | 链增量游标（B2）：边遍历边删、换 loc、跨楼层、`guard` 触顶 | 处理集合逐帧等价；无漏遮罩 |

> v0.35.0 的既有离线证据（`tools/fov-fix-20261104/checks.py` 9/9、`checks_b2.py` 9/9）可作为 V1/V2 的前置参照，但那轮**运行时加载也没做成**（同一 `%APPDATA%` 限制），所以基线本身仍是"离线等价 + 未做 ModLoader 冒烟"状态。

### 7.2 性能（V1–V8 通过后）

| 编号 | 方法 | 通过标准 |
|---|---|---|
| P1 | 大图**移动**工况 ABBA（A=RV off，B=RV on 候选）≥2 轮，每轮 ≥60s，原始帧间隔全留 | 方向一致；记录玩家 X 跨度 ≥200px 证明真的移动 |
| P2 | 候选 vs 基线（同为 RV 开）同字节交替 ≥2 轮 | 均值不劣化，P95/长帧改善趋势 |
| P3 | 计数器插桩：`fov` 清零元素/帧、墙重填瓦片/帧、角循环项/帧、Pt 链节点/帧、层子节点/帧、`sightClasses` 分配次数、`rebuild` 次数与耗时 | A 阶段后：清零元素 ≈2.8k（非 30k）、墙重填 ≈视口墙数、角循环 ≈窗口行、分配 0/帧 |
| P4 | 开门尖峰：脚本开门，记录触发帧前 5/后 20 帧 | 最大帧明显下降（阶段 C） |
| P5 | GC 观察：每轮 `System.totalMemory` 曲线 + 长帧分布（参考 CS 的 v14 探针方法） | W7 后周期性回收次数/单次体量下降（机制指标，不等于帧率） |

**纪律**：测试前按 `mods/ModLoader/docs/TEST-REGISTRY.md` 登记（`resource=game-coexist`），串行跑；不允许把"窗口外像素陈旧但不可见"写成"画质等价已证"；方向不一致时按既有先例**不宣称收益**，只保留机制证据。

---

## 8. 工单

| 序 | 工单 | 依赖 | 预估 | 交付 |
|---|---|---|---|---|
| **T0** | **重冻结基线**：v0.35.0 源与新 SWF 哈希钉进实验目录 | — | 0.2 天 | ✅ `build/csopt-20261104/baseline/`（sha `8073d112…`） |
| **T1** | 实测取证：大图移动驱动 + 四臂（A/B/C/D）+ 插桩计数 | **需要能写 `%APPDATA%` 的会话** | 0.5–1 天 | 设施已就绪（`build/cs-rv-20261104/`），等待可运行会话 |
| T2 | 阶段 A：**W8 角表分桶** + W7 分配 | T0 | 1 天 | ✅ `prepare.py` P1/P2 + 34 项 A/B |
| T3 | 阶段 A：W2 fov 增量清零 | T2 | 0.5 天 | ✅ `prepare.py` P3 |
| T4 | 阶段 A：W1 墙重填窗口化 | T2、T3 | 1 天 | ✅ `prepare.py` P4（窗口内 539,328 px 零差异 + 自愈） |
| T5 | 阶段 A 合并候选 + 全量 P1/P2 | T2–T4 | 0.5 天 | ✅ 候选 `out/candidate.swf` 52,691B；**P1/P2 待可运行会话**；`deploy.py` 已就绪 |
| T6 | 阶段 B1：两链合并遍历 + `guard` 上限 | T5 | 0.5 天 | 待办（降级） |
| T7 | 阶段 B2：链增量游标 | T6 | 1–2 天 | 待办（降级，收益约 0.1–0.2ms/帧） |
| T8 | 阶段 B3：层 ADDED 注册表 + 手臂修复 | T5 | 1 天 | 待办（视觉行为改变，独立立项） |
| T9 | 阶段 C：行桶 mask + 重建合并 | T5 | 1–2 天 | 待办 |
| T10 | 阶段 D（条件）：视口尺寸工作位图（W6） | T1 确诊 W6 | 2–3 天 | 待办（**最未知**） |
| T11 | 阶段 E：classic 对齐（按需） | T5 | 2 天 | 待办 |

**T1 的交接命令**（设施已编译好，见 REPORT §7）：

```powershell
cd "mods\RealisticVision\build\cs-rv-20261104"
python setup_sandbox.py                                   # 若 runtime/ 已存在可跳过
python build.py driver; python build.py noop; python build.py logprobe; python build.py instrumented
python run_grid.py --batch precheck-01 --order A --window-ms 20000     # 先确认产出 result.json + RVision.log(含 auto room 240x125)
python run_grid.py --batch abba-01 --order A,B,B,A --seed 2026110411 --window-ms 70000
python run_grid.py --batch diag-01 --order B,C,D,L,I --seed 2026110411 --window-ms 70000
python finalize.py
```

已知坑：部分沙箱进大图后 **RV 的 `RVision.log` 会停写**（`knowledge/experiments/2026-11-03-cs-scene-window.md` §沙箱阻塞），但 `build/cs-window-20261103/evidence/csrv-final-on*/RVision.log` 里 autotest 行正常——**每次运行现场确认通道**，主通道用驱动侧自写 JSON。

---

## 9. 明确不做的方向

1. 不再降画质换帧率（`vision_quality_preset=0` 已到底；进一步降级需用户拍板）。
2. 不动 `fillFogCache`/`recalcTile`/`updateWallSurface` 的遍历域——已是视口域，改错会破坏 `cornerReuse` 的跨帧一致性。
3. 不给整层开 `cacheAsBitmap`（2026-11-01 实测否决：48.18→55.68ms）。
4. 不做"隐藏屏外敌人/世界"式取舍（改变可见语义，历轮否决）。
5. 不按"窗口跳过对象"处理 W3（CS 560px 余量 > csWin 160px，会漏画）；用增量游标。
6. 不把"关 `cs_window`"当现场建议（会让 `prepareOcclusion` 退回每帧全图扫描，更慢）。
7. 不修改 CS 的 `release/`、`src/`；与 CS 只有三种合法交互：读公开标志（`sceneLarge`）、用显示树事件（ADDED/REMOVED）、把"同帧双尖峰"（RV rebuild + CS chunk 重绘）作为**反馈**告知 CS 维护者。
8. 不假设基线不变：并行会话正在高频部署（v0.34.9 06:18、v0.35.0 06:22），实施前必须重新冻结。

---

## 10. 附录

### 10.1 行号对照（v0.34.8 审计表 → v0.35.0 现行源）

| 主题 | v0.34.8 | **v0.35.0** |
|---|---|---|
| `onFrameInner` | 1040-1150 | **1128-1242** |
| `cs_window` 激活 | 1069-1074 | **1160-1164** |
| `ensureFog` | 1325-1496 | **1416-1587** |
| `scrollRect` 段 | 1470-1484 | **1560-1575** |
| `fogBitmap.mask` / `wallLayer.mask` | 1436 / 1446 | **1527 / 1537** |
| `scenePrepareOcclusionFast` | 1631-1675 | **1722-1766** |
| `sceneRefreshWallFieldFast`（角循环） | 1677-1728（1691） | **1768-1819（1782）** |
| `structHash` | 1592-1606 | **1683-1697** |
| `prepareOcclusion` | 1730-1763 | **1821-1856** |
| `visionEye`（原 `playerVisionEye`） | 1767 | **1858** |
| `computeFov` / `fov` 全清 | 1788-1897 / **1812** | **1968-2077 / 1992** |
| `scenePaintBounds` | 2079-2090 | **2290-2301** |
| `updateCsWindow` | 2096-2107 | **2307-2318** |
| `applyVision` | 2109-2260 | **2320-2471** |
| **W1 墙重填分支** | 2139-2151 | **2350-2362** |
| `fillFogCache` | 2267-2388 | **2478-2599** |
| `advanceMemory` | 2535 | **2791** |
| `refreshWallField`（rebuild） | 2546-2628（2550-2601） | **2802-2884（2806-2857）** |
| `updateWallSurface` | 2631-2669 | **2887-2925** |
| `fillWallTile` | 2709-2762 | **3038-3091** |
| classic 全图循环 | 2870 / 2872 | **3211 / 3213** |
| `prepareClassicCells` | 2963-2993 | **3304-3334** |
| `unitBBox`/`bboxFovCount` | 3283/3321 | **3624/3662** |
| `enemyState`（分配 `sightClasses`） | 3345-3471（3374） | **3686-3812（3715）** |
| `applyMask` / `refreshMask` | 3485 / 3506 | **3826 / 3847** |
| `hideEnemies`（武器链） | 3830-3998（3957） | **4171-4339（4306）** |
| `applyUnitWeapons` / `applyWeaponVisual` | 4000 / 4012 | **4341 / 4353** |
| `applyWorldVisuals`（链/层/units） | 4094-4184（4097/4121/4147） | **4435-4525（4439/4462/4488）** |
| `applyTransientVisual` / `applyWorldVisual` | 4196 / 4244 | **4537 / 4585** |
| `worldVisualHasFilters` | 4394-4401 | **4735-4742** |
| `sweepMasks` / `updateOptPanel` | 3759 / 4548 | **4100 / 4889** |
| `loadConfig` / `saveConfig` | 604-609（v0.35.0 起） | **604-609 / 860-864** |

### 10.2 术语

- **CsWin**：`updateCsWindow` 算出的"本帧可见域" = 相机视口 ∪ 玩家视野圆盘。
- **Pt 链**：`Location.firstObj` 起、经 `nobj` 串起的对象链表；**按创建顺序追加到链尾**。
- **fogSub**：每瓦片的子格边长；`fog_vision_quality=0` → **4**（每瓦片 4×4=16 子格）。
- **mask 语义**：被遮罩对象只在 mask 填充区域内绘制；未填充 = 完全遮住。
