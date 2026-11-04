---
title: v0.35.2-shadowfix：弹体定向矢量裁剪与单位贴墙防隐形
status: deployed
date: 2026-11-04
baseline: v0.35.1-csoptA (52,690B / 31bdc9a2…)
artifact: release/RealisticVisionMod.swf 54,198B / 50f681352594965e7efca1c70e7fe5725c6022e824314d80934a0fdc6fee079e
plan: design/projectile-and-turret-shadow-optimization-plan.md
build: build/shadowfix-20261104/
---

# v0.35.2-shadowfix：弹体定向矢量裁剪与单位贴墙防隐形

被测技能：remains-runtime-debug、diagnosing-bugs、remains-mod-build、remains-release-gate
测试工作区：`D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision`

用户两条主诉：①「阴影对激光和高速弹药的遮盖效果不佳」②「有时即使炮塔退出阴影，其也不会显示（不代表
只有炮塔有问题）」。本轮不只是调参：两条各有一个机制性缺陷，缺一都改不动。

## 1 根因

### 1.1 弹体：矢量遮罩被画成了实心包围盒

`RefreshMask` 输出的遮罩位图本身是对的，问题在**它怎么被用**。v0.34.7 的 C-Bul-1 为消除高速旋转弹体
的位图缓存击穿，把遮罩与被遮罩对象的 `cacheAsBitmap` 全部关掉。Flash/AIR 的规则是：**任一侧为
false 就退化为标准矢量剪裁遮罩**——此时渲染器只取 `graphics` 的闭合轮廓，**完全忽略位图里 alpha=0
的像素**。而代码在"部分可见"分支画的是

```actionscript
shape.graphics.drawRect(drawClip.x, drawClip.y, drawClip.width, drawClip.height);  // 整个包围盒
```

于是只要弹体包围盒碰到亮区，**整个矩形**都按"100% 透传"处理：激光远端、子弹尾迹在阴影里的部分全部
原样显示；只有弹体完全没入全暗瓦片（走 `graphics.clear()`）才会整体消失。这解释了"激光在暗处照样亮"
与"高速弹药遮不住"，也解释了为什么现象随光照边界出现、而不是随距离。

### 1.2 单位：实心墙进分母 → 迟滞死区锁死

`unitBBox` 为了方便边界过渡，把包围盒**四周各外扩 1 瓦片**。炮塔的体型是 38×38 且大量放在 `y=1`
（紧贴天花板），外扩后包围盒是 3 列×4 行 = 12 瓦片，其中第 0 行整排是天花板实心墙、贴墙角时再加一整
列——常驻 5~8 个**不可能是"单位所在空间"的实心墙瓦片**，而它们在视野场里恒为全暗（权重 0）。

`enemyState` 的 80%/15% 门控用 `litWeight/tileCount` 作可见比例，实心墙把这些格子白算进分母：真实
可见的 2~3 格自由空间，比例只有 `2/12≈0.17`~`3/12=0.25`，正好撞上迟滞分支

```actionscript
if(gateRatio>=0.15) return prevSt==0 ? 0 : 2;
```

即**从全隐过来的单位（`prevSt==0`）恒返回 0**。玩家把光打过去、炮塔身位明明已经在亮区，状态却卡在
"全隐"，`hideUnit` 每帧强制 `vis.visible=false`。这条对任何贴墙/贴顶/半身贴箱体的单位都成立，所以
用户说"不代表只有炮塔有问题"。

配套两个次级缺陷：软遮罩的 alpha 映射 `2a-255` 会把交界亮侧压暗（贴天花板的身位首行只剩 ~1/3）；
淡入 `fadeCount` 未初始化、中途被打断时 `alpha` 残留 0.05~0.2 且无人复位。

## 2 改动

| 开关（默认 1） | 内容 |
|---|---|
| `proj_shadow_clip` | 弹体/激光改**定向矢量裁剪**：沿弹体轴向按视野场分段采样（步长 = 1 子格），只把亮段画成定向四边形；全亮摘罩走原生直绘、全暗挂空罩。静止弹体用 `fovVersion + sightGen + x/y/rot/scaleX + 外框宽高` 缓存键复用 |
| `turret_wall_guard` | ①`enemyState` 里 `opac>=1` 的实心墙**不进分母**（仍参与 `combined/mixed` 判定，旧语义不变）；②**核心锚点**：身位中心点（`u.X, u.Y-scY/2`）在亮区且 `st==0` → 抬到 2；③`finishCurrentMask` 的 `keepLitSide`：核心在光里时改用不侵蚀亮侧的 alpha 映射（全暗子格仍硬切 0）；④`fadeCount/baseAlpha` 初始化 + `st==0` 无条件复位 + `showUnit` 恢复基准 alpha |

## 3 证据

### 3.1 离线 A/B（同进程，baseline = v0.35.1，`ShadowFixHarness` 23/23 PASS）

| 断言 | 观测 |
|---|---|
| 弹体裁剪几何 | 旧遮罩 `x=240..960`（明暗交界在 640 ⇒ **暗侧 320px 全放行**）；新裁剪 `x=300..630` |
| 遮罩语义 | 全亮无遮罩（原生直绘）/ 全暗空遮罩；遮罩纯矢量（`cacheAsBitmap=false`） |
| 炮塔状态 | 同一贴天花板炮塔（bbox 12 格、5 格实心）：baseline `st=0`（全隐）→ 候选 `st=2`（软遮罩可见） |
| 核心锚点 | 比例口径仍判 0（`cfgWallGuard=0`）时，核心在光里 → 抬到 2 |
| 遮罩剖面 | 交界亮侧首行 79→167、次行 199→227；暗侧仍 0；深处仍 255（无整体变淡） |
| 渐入 | 中断的淡入 `alpha` 复位到基准；进行中的淡入不被拉满 |
| **场不变** | 标准房 **200 帧**：`fov/wallA/memCur/wallRaw/fogCache/currentSight/seenSub/explored` 逐帧逐像素相同 |
| **安全不变量** | 大图 90 帧行走：没有任何 v0.35.1 已显示的单位变隐（regressions=0；43 次状态变化全部是更可见方向） |

### 3.2 既有套件

| 套件 | 结果 |
|---|---|
| `SoftHarness` | 16/16 PASS |
| `SharedExplorationHarness` | 20/21（唯一失败项 `memory brightness setting still controls shared area` 在基线同样失败，属陈旧断言） |
| `CsOptHarness`（对 v0.35.0 基线） | 31/34；3 个失败项全部是「单位可见状态/分类逐帧相同」——本轮有意的语义变化；场/位图等价项与 W1/W7 机制项全过 |

### 3.3 微基准（同进程 ABAB×5，24 个跨界弹体/激光，`ShadowPerf`）

| 相位 | v0.35.1 | 候选 | 差 |
|---|---|---|---|
| 视野刷新帧 + 移动弹体（交战常态） | 0.0340 ms/对象 | 0.0096 | **−72%** |
| 视野刷新帧 + 静止弹体 | 0.0327 | 0.0081 | **−75%** |
| 静止视野帧 + 静止弹体（全缓存） | 0.0025 | 0.0029 | +0.0004 |
| 静止视野帧 + 移动弹体 | 0.0029 | 0.0067 | +0.0038 |
| `enemyState`（12 贴墙单位） | 0.000625 ms/单位 | 0.000625 | 0（候选还多算了 `unitCoreLit`） |

判读：交战/移动（视野在刷新）时弹体遮罩成本降到 1/4；只有"镜头完全静止、弹体仍在飞"的帧每对象多约
3.8µs（真实 2~4 发 ≈ ≤0.015ms/帧；24 发压力场景 0.09ms/帧）。单位分类成本不变。

### 3.4 真机加载（隔离沙箱，与正式配置一致）

`init ok v0.35.2-shadowfix` / `ModSettings settings registered` / 48×25 → `random_mane` 240×125
（208 units / 593 objects）/ `tick 181`；17 个模组全加载 `errors=[]`；无 RV 报错、无看门狗禁用。
证据目录 `build/shadowfix-20261104/evidence/smoke-03-final/`。

## 4 与方案的偏离

1. 「实心墙法向膨胀」改为 **keep-lit alpha 映射**：实测旧映射在 `maskblur_current=4`（σ≈1 子格）下
   只把交界亮侧第一行压到 79，并不是方案推测的 15~18px 全透明——真正"整只不显示"来自迟滞死锁。
   逐子格膨胀要多一遍子格遍历，性价比不足。
2. 新增**静止弹体缓存键**（方案未提），把静止视野帧成本压到 +0.4µs/对象。
3. 核心锚点放在 `hideEnemies` 调用点而非 `enemyState` 内部：后者有多处提前 return，调用点收口更
   不易漏，且对 `cfgEnemyFast=0` 的旧路径同样生效。
4. 方案 §2.3「炮塔大部分落在 18px 真空区」按实测修正为 1~2 行子格。

## 5 边界（未验证）

- 玩家真机观感：激光截断位置、炮塔贴天花板时的边缘羽化需要重启后肉眼确认；离线夹具量的是几何与
  像素，不代替观感。
- `classic` 模式与 `viewscale≠1` 未单独跑；`viewscale≠1` 时旧路径本就走完整支持区。
- 20+ 同屏弹体的外观与整帧成本未测（只有 24 对象微基准）。
- 弹体裁剪是**几何硬边**：高速运动不可察觉，慢速抛射物跨界时边缘会比以前的羽化硬。
- CS 包装层 `Location.getTile` 返回 null 的情形加了守卫（`tileSolid`），但未用真实 CS 包版本验证。

## 6 复现

```powershell
cd mods/RealisticVision/build/shadowfix-20261104
python build_swf.py --only candidate
python run_checks.py ShadowFixHarness --arm ab
python run_checks.py ShadowPerf --arm ab
python run_checks.py SoftHarness --arm candidate
python run_checks.py CsOptHarness --arm ab --baseline-dir ..\csopt-20261104\baseline\src
python deploy.py --expect <当前 release 指纹>
powershell -ExecutionPolicy Bypass -File run_smoke.ps1 -Name smoke-xx -RvSwf .\out\candidate.swf
```

逐行源码 diff：`build/shadowfix-20261104/production.patch.txt`（472 行 / 18 hunk）。
