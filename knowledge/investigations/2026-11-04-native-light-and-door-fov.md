# 原生视野光照（lightBmp/lighting）与门窗、半墙机制调查

> 调查日期：2026-11-04
> 任务性质：**只读静态反编译源码调查**（与 RealisticVision / RV 的替代实现做对照）。
> 边界声明：本次**未修改**任何源码/配置/release，**未启动游戏**，**未写测试登记**；唯一写入是本文件。
> 原生证据根：`game-reference/decompiled/1.02/src102/scripts/fe/`（下称 `fe/`），下文写 `文件名:行号`，完整路径见 §10。
> RV 证据：`mods/RealisticVision/src/RealisticVisionMod.as`（只读引用）。
> 结论标注：**[已证实]**=代码直接可见；**[推论]**=由代码推导但未运行时验证；**[未知]**=本次未查到/证据不足。
> 注意：任务描述中的“10px 子格”与当前 RV 源码不符——当前 RV 为每瓦片 8×8 子格（5px），见 `RealisticVisionMod.as:119`、`RealisticVisionMod.as:1970`；下文按当前源码写，历史版本请另核对。

---

## 0. 结论速览

| # | 问题 | 一句话结论 | 状态 | 关键证据 |
|---|---|---|---|---|
| 1 | lightBmp 粒度/插值 | 1 个样本/瓦片角，贴到 49×28 的 alpha 位图，`scale=40`、`smoothing=true` 双线性放大 | 已证实（双线性属 Flash API 语义） | `Grafon.as:141-143`、`Grafon.as:203-206`、`Grafon.as:225` |
| 2 | 射线起点/眼点瓦片 | 起点=眼点（`gg.X+storona*12`, `gg.Y1+stayY*0.247`≈`Y-52.7`）；从 `_loc16_=1` 起采样 40px/步，**眼点瓦片 opac 从不扣**；一般情形目标角点瓦片也不扣 | 眼点瓦片：已证实；目标瓦片：推论+边界例外 | `Location.as:3137-3138`、`Location.as:3210-3214`、`Location.as:3194/3208` |
| 3 | 透光门/窗 | 逐格**累减** `opac`（非二值）；无“门景最低亮度”概念；近场“平顶”只是 `lDist1` 内距离项饱和 + 穿越格数恒定造成的表象 | 已证实 | `Location.as:3215-3227`、`Location.as:3167-3175`、`AllData.as:4858-4876` |
| 4 | visi/t_visi 时序 | 亮：`visi += 0.1`（每次 updVisi）追 `t_visi`；暗：仅 `retDark` 房间 `t_visi -= 0.025`；运行时内嵌房间 639 个中只有 **2** 间 retDark，非 retDark 房间亮度只升不降（棘轮） | 已证实 | `Tile.as:271-279`、`Location.as:3235-3248`、`RoomsProb.as:3532/4999` |
| 5 | “平滑”来源 | 主因是 40px 角点场 + 双线性放大；其次是时间棘轮/0.1 步进。**浅层没有 blur**（visLight 无 filter；只有 visSats 有 BlurFilter） | 已证实机制；视觉归因为推论 | `Grafon.as:225`、`Grafon.as:183`、`Location.as:3140/3394-3404` |
| 6 | 原生单位感知 | 独立的 9px 步进**二值**检测：只看 `phis==1` 的方块矩形，不看 `opac`、不看 `visi` | 已证实 | `Location.as:2366-2386`、`Unit.as:4560-4641`、`World.as:52` |
| 7 | zForm>0 半墙 | `opac=0`（光完全不管）、`phY1` 下移（只挡下半格移动/AI 视线）；上半格可站；眼点在上一~两行，正常碰撞下不会落在 `opac=1` 瓦片里 | 半墙机制已证实；眼点结论为推论 | `Tile.as:281-297`、`Tile.as:2568-2583`、`Unit.as:3100-3101` |
| 8 | RV 该用 40px 角点还是更细子格 | 复刻原生观感 → 40px 角点采样 + 双线性；更细子格是另一种质感（更真实、边缘更硬），若坚持子格需补 ~40px 低通 | 推论（由 1/5 推导） | 见 §5、§8 |

---

## 1. 原生光照场 `lightBmp`：每瓦片角 1 样本 + 双线性 ×40

### 1.1 数据结构与屏幕映射

- 1.02 的地图尺寸固定为 48×25 瓦片（`World.as:40-42`，`Location.as:265-268`），瓦片 40×40px（`Tile.as:8-10`）。
- 光照掩膜是固定 **49×28** 的 `BitmapData`：`Grafon.as:141-143`（`lightX=49`、`lightY=28`）。初始填充 `0xFF000000`（不透明黑）：`Grafon.as:224`；`lightRect` 同尺寸：`Grafon.as:172`。
- 它挂在 `visLight` 精灵下，`visLight.scaleX = visLight.scaleY = Tile.tileX = 40`，位置 `x=-20`、`y=-60`：`Grafon.as:203-206`。
- `lightBitmap` 构造为 `new Bitmap(this.lightBmp,"auto",true)` → **smoothing=true**：`Grafon.as:225`。即 1 个 texel 放大到 40×40 屏幕像素，采样时启用平滑（双线性）；
  - `[已证实]` smoothing 开；`[推论/API 语义]` 具体过滤为双线性（未做像素抓取验证）。
- 坐标换算（由上面 3 个常量直接算）：像素 `(i,j)` 覆盖世界 `x∈[40i-20,40i+20]`、`y∈[40j-20,40j+20]`，**中心正好是 (40i, 40j)**；即每个 texel 的中心落在**瓦片角点**上。
- 写像素时用 `(tileX, tileY+1)`：`Location.as:3162`、`Location.as:3238`、`Location.as:3247`、`Location.as:3273`；`Grafon.setLight()` 同样写到 `(x, y+1)`：`Grafon.as:695`。
  - 所以瓦片 `(x,y)` 的亮度值画在“中心=(40x,40y)”的 texel 上 = 该瓦片**左上角**。
  - 反过来：一个瓦片的显示亮度 = 它 4 个角点样本的双线性插值（4 texel 中心正是该瓦片 4 角）。这正是“每瓦片角 1 样本”的准确含义。
- 位图是**黑色 alpha 掩膜**：alpha=`floor((1-visi)*255)`，RGB=0：`Location.as:3162` 等；`Grafon.as:224`（初始黑）。它在 `visual` 层级里位于 `visFront`（前墙）之后、`visObjs[4]` 之前，`blendMode="normal"`：`Grafon.as:191-202`、`Grafon.as:357-368`。所以它压暗其下方的墙/地板/单位/水，而 UI 粒子（visObjs[4]/5）在它上方。
- 只写 `x=1..47`、`y=1..24`（循环 `1..<spaceX/spaceY`）：`Grafon.as:689-699`、`Location.as:3141-3145`。列 0/48、行 0/1/26/27 永远保持初始黑 → 房间边缘固定有黑色半格/黑带。`[已证实]`
- 非 `black` 房间：`Location.black` 默认 true（`Location.as:51`），`noblack` 选项把它关掉（`Location.as:442-444`）并把所有 `visi` 初始化为 1（`Location.as:530-543`）。此时 `visLight.visible=false`：`Grafon.as:425`。
- 另有全局黑暗色调 `colorBmp/shadBmp`（`Grafon.as:427-437`、`Grafon.as:623-644`）和屏幕边缘 `ramT/ramB/ramL/ramR` 镜头花边（`Grafon.as:227-235`）；它们不是逐角可见度场，也不带模糊，别和 `lightBmp` 的平滑混为一谈。`[已证实]`

### 1.2 为什么“墙造成的边界很平滑”

- 墙 `opac=1`（`Tile.as:198-201`、`Tile.as:299-309`），对射线是强烈的 1.0→0 落差；该落差只落在**角点样本**上，然后被 ×40 的双线性插值抹成约 **40px 宽的线性过渡带**。`[已证实]` 机制；`[推论]` 这是“墙边平滑”的主因。
- 叠加时间维度：`visi` 以 0.1/次向目标追（§4），边界变化被低通；非 retDark 房间还只升不降，观感稳定不闪。`[已证实]`
- 注意：原生没有对 `visLight` 做额外的模糊；`visSats` 才有 `BlurFilter(3,3,1)`（`Grafon.as:183`），`specEffect` 里的大模糊是特殊视觉效果（参数>100 时给整个 `visual` 加 BlurFilter：`Grafon.as:1427-1430`）。
  - `[推论]` “雾层贴图本身的模糊”这一解释不成立：平滑来自**位图缩放的双线性** + 时间棘轮，而不是第二层模糊贴图。

---

## 2. `lighting()` 的射线：起点、步进、扣除

### 2.1 起点怎么定（像素值）

- 默认参数（玩家移动时调用 `lighting()`，见 §4.3）：
  - `param1 = this.gg.X + this.gg.storona * 12`；
  - `param2 = this.gg.Y1 + this.gg.stayY * 0.247`。
  - 证据：`Location.as:3137-3138`。`lighting` 签名是 `param1:int, param2:int`（`Location.as:3108`），所以两个眼点坐标会被**截断为整数像素**。
- 代入玩家数值：
  - 玩家 `stayX=50, stayY=70`（`AllData.as:20-24`），站立时 `Y1 = Y - scY = Y - 70`（`UnitPlayer.as:503-506`；移动中每步同步：`Unit.as:2504-2506`）。
  - 所以眼点 ≈ `(X ± 12, Y - 70 + 17.29) = (X ± 12, Y - 52.71)`。
  - `storona` 是 ±1 朝向（默认 1：`UnitPlayer.as:349`；随移动更新：`UnitPlayer.as:2540-2573`）。`12` ≈ 身体半宽 `scX/2=25` 的一半。
  - 对照原生 AI 眼点：`eyeX = X + scX*0.25*storona`（=X±12.5）、`eyeY = Y - scY*0.75`（=Y-52.5）：`Unit.as:3100-3101`。**光场起点与 AI 眼点基本同一个点**（12 vs 12.5px、52.71 vs 52.5px 的取整差异）。`[已证实]`
- 细节：公式用的是 `Y1 + stayY*0.247` 而不是固定的 `scY*0.75`；坐下时 `scY=sitY`（默认 `stayY/2`，`Unit.as:1037-1044`），而 `stayY` 仍 70，于是眼点会变成约 `Y-17.7`（贴地）。这不是眼点进入墙内的路径，但做像素级复刻时要注意。`[已证实公式；实际观感未验证]`
- 其他调用点（说明光场不总是以玩家为中心）：Land 载入时用 `(gg.X, gg.Y-75)` 初始化一次（`Land.as:1231`）；`lightAll()` 对带 `light` 标记的对象以对象为原点打 3 次（`Location.as:3094-3106`）；`UnitSpectre` 也会调用 `lighting(X,Y)`（`UnitSpectre.as:70`）。每次调用都可能抬高 `visi`。`[已证实]`

### 2.2 采样序列：跳过眼点瓦片（以及一般情形跳过目标角点瓦片）

- 每瓦片角点 `(40x, 40y)` 独立求值：`Location.as:3141-3145`。半径外（`dist >= lDist2`）直接不追（除 retDark 衰减）：`Location.as:3150-3153`、`Location.as:3155-3163`。
- 距离因子 `_loc6_`：`dist<=lDist1` → 1；否则 `(lDist2-dist)/(lDist2-lDist1)`：`Location.as:3167-3175`。`lDist1=300`、`lDist2=1000` px，并会乘房间 `visMult`：`Location.as:129-131`、`Location.as:643-648`。
- 射线方向按主轴归一：主轴步长恰为 `±Tile.tileX/±Tile.tileY`（40px），另一轴按斜率连续推进：`Location.as:3182-3209`。`|dx|==|dy|` 时把 `_loc10_++`（避免正 45° 退化）：`Location.as:3178-3181`。
- **步进从 `_loc16_ = 1` 开始**：`Location.as:3210-3211`。第 1 个采样点 = 眼点 + 40px（主轴方向）。
  - 设眼点 `x = 40k+f`（`0<=f<40`），样本落在 `x = 40k+f±40i`，恒在第 `k±i` 列 → 采样依次覆盖相邻瓦片，**不会落在眼点自己所在的第 k 列**。
  - 结论：**眼点所在瓦片的 `opac` 从不参与扣除**。`[已证实]`（正是问题 2 的核心）
- 采样个数 `_loc15_ = int(|40N - eyeX| / 40)`（主轴；`_loc15_` 声明为 int：`Location.as:3119`；赋值：`Location.as:3194`/`Location.as:3208`）。对 `f>0` 它等于 `N-k-1`，最后一个样本在 `40(N-1)+f` → 落在目标角点**前一列**；`f=0` 时是 `N-k`，最后样本正好落在角点边界（`getAbsTile` 向下取整会取到目标瓦片）。
  - 因此一般情形：**目标角点所在瓦片自身的 `opac` 也不被扣**（墙亮面的角会保持亮）；`[推论，含 f=0 边界例外]`
  - 推论效果：墙瓦片“靠近观察者一侧”的角点通常亮、另一侧暗；阴影过渡带落在墙瓦片上，再被双线性摊到 40px。
- 每格扣减：
  - `_loc17_ = getAbsTile(采样点)`（`Location.as:3213`；`getAbsTile` 见 `Location.as:2331-2338`，越界返回 `otstoy`）；
  - `_loc18_ = tile.opac`；若 `opacWater>0 && tile.water>0` 取 `max`（`Location.as:3215-3218`）；
  - `_loc6_ -= _loc18_`，`<=0` 截 0 并 `break`：`Location.as:3219-3227`。
  - 即**逐格累减**，不是“遇到门就二值阻断”。

### 2.3 眼点落在 `opac>=1` 瓦片里会发生什么？

- 代码层：该瓦片被**完全当作不存在**（§2.2：眼点瓦片永不采样），所有角点仍从该点向外求值 → 视觉上会从墙/门内部“透出去”，看到墙后。`[已证实（代码行为）]`
- 但正常玩法里眼点能否落在 `opac>=1` 瓦片内？见 §7 的推论：正常站立碰撞（50×70 身体盒）通常不允许；可能的例外是 `phis==3` 幽灵墙（玩家 `transT=true` 可穿、`opac` 可能仍为 1）、`loc.sky` 房间（`collisionAll` 直接返回 false）、或脚本传送/特殊状态。`[推论，未运行验证]`
- 另外：`opac>=1` 在现有内容中几乎等价于 `phis>0`（`opac=1` 只在 `Tile.inForm` 的 `phis>0` 分支设置：`Tile.as:198-201`；`Area.tileop` 只对 `phis==0` 设 0.2/0.25：`Area.as:186-192`；`Box` 的门用 `door_opac`）。`[已证实]`

---

## 3. 原生对透光门/窗的处理

### 3.1 各种门/窗的 `opac` 取值

- 门对象默认 `door_opac=1`、默认 `phis=1`：`Box.as:52`、`Box.as:72`；XML 读 `opac`：`Box.as:290-298`；门覆盖的每个瓦片 `opac=door_opac`：`Box.as:653-677`（`initDoor`，按对象可视范围 `X1..X2/Y1..Y2` 覆盖多格）。
- 具体值（`AllData.as:4858-4876`、`AllData.as:5038-5039`）：
  - `grate`/`hgrate`（栅栏）= **0.1**，且 `phis='2'`；
  - `window1`/`window2`（窗）= **0.2**，无 `phis` 属性 → 落到默认 `phis=1`；
  - `door1`/`door1a`/`door1b`/`hatch1`（木门/舱门）= **0.8**；
  - `door4`/`enclpole` = **0.3**；
  - `alib1`/`alib2`（A 力场）= **0.1**，`phis='1'`；
  - 其余金属门/隔断等没有 `opac` 属性 → `door_opac=1`（全遮光）。
- 墙：`Tile.inForm` 在 `phis>0` 时 `opac=1`（`Tile.as:198-201`）；`mainFrame` 也设 1（`Tile.as:299-309`）。
- 非实体半透明区域可由地图 area 的 `tileop` 设：`Area.as:186-192`；实际房间中见 0.2/0.25（如 `Rooms/rooms_plant.xml:495` 等）。
- 门的开关：`setDoor(open)` → `phis=0/原值`、`opac=0/door_opac`（`Box.as:679-686`）；**开门**时置 `isRelight=true`、`isRebuild=true`（`Box.as:688-692`），**关门不置**；门被摧毁 → `opac=0`（`Box.as:789-810`）。

### 3.2 原生光照里门窗的表现

- `[已证实]` 透光门/窗在原生光照中不是“整片平顶的门景亮度”，而是“**距离因子 − 沿途各格 opac 之和**”的连续可变量：`Location.as:3167-3227`。
  - 例：单穿 1 格窗（0.2）→ 角值 ≈ 距离因子−0.2；在 `lDist1=300` 内距离因子=1，于是约 0.8。
  - 穿 2 格（宽窗/斜穿/2 格宽门）→ 再减 0.2，得到 0.6；门对象越宽、穿越方向越斜，减得越多。
  - 若穿墙（1.0）→ 立即 0。
- “平顶”只在特定条件下作为表象出现：`lDist1` 内距离项饱和（=1），且“穿过的透光格集合/格数”不变时，角值是常量 → 最近 300px 内会看到近似的“平台”；超过 300px 加入线性距离衰减，平台就变成斜坡。`[已证实公式；视觉为推论]`
- **原生没有“门景最低亮度”这一概念**：`lighting()` 中没有任何 `door` 特判/下限常量（`Location.as:3108-3255`）；在 src102 中搜索 `doorDim|doorLight|litmin|lightMin|minLight|doordim` 无结果。`[已证实]`
- “门景亮度”是 **RV 自己的概念**：`cfgDoorDim`（配置 `doordim`，默认 0.5）以及对 `FOV_DIM` 瓦片用 `doorView` + `floor=doordim` 的填充：`RealisticVisionMod.as:1968`、`:1991-1992`、`:2081-2089`、`:2181-2185`。`[已证实（RV 代码）]`
- 门窗的开/关对光场触发**不对称**：开门 `isRelight=true` 会立刻重算（变亮路径能生效）；关门不触发，且非 retDark 房间只升不降 → 关门后光场不会自行变暗（除非玩家移动触发重算，可是变暗分支在非 retDark 仍不生效）。`[已证实代码；视觉后果未实测]`

---

## 4. `visi/t_visi` 的更新是“升快降慢”吗？

### 4.1 上升

- `Tile.updVisi()`：`visi += 0.1; if(visi > t_visi) visi = t_visi;`：`Tile.as:271-279`。**每次调用 +0.1**，夹到目标。
- `lighting()` 中，当新目标 `_loc6_ > visi + 0.01` 时：`t_visi = _loc6_`，并当场写一次像素（内部调用一次 `updVisi`）：`Location.as:3235-3239`。
- 收尾阶段：`lighting()` 把 `relight_t = 10`（`Location.as:3140`）；玩家停下后，`Location.step()` 在 `relight_t>0` 时调用 `lighting2()`（`Location.as:3394-3404`），`lighting2` 只补“`visi != t_visi`”的像素（`Location.as:3257-3279`），每步最多 +0.1。
- 于是实际亮起速度 ≈ **0.1/步**；`World.fps=30`（`World.as:44`），最多 10 步 ≈ 0.33s 收敛。`[已证实]`

### 4.2 下降

- 只有 `retDark` 为 true 时才降：
  - 半径外：`t_visi -= 0.025`（`Location.as:3155-3163`）；
  - 半径内且新目标更暗：`t_visi -= 0.025`，并把 `t_visi` 夹到 `_loc6_`（`Location.as:3240-3248`）。
- 随后的 `updVisi()` 会把 `visi` 直接夹到变小的 `t_visi` → **显示值按 0.025/次 的速率随目标下降**（比上升慢 4 倍），而且只在 `lighting()` 被调用（玩家移动/rigger）时发生。`[已证实]`
- **关键事实：`retDark` 在整个 1.02 内容里只有 2 个房间定义**：
  - `RoomsProb.as:3532`（`retdark="1"`，tRust/blue 下水道房）与 `RoomsProb.as:4999`（`retdark="1"`，tDirt/cat 房）；
  - 外部房间数据对应 `Rooms/rooms_prob.xml:3527`、`Rooms/rooms_prob.xml:4992`；
  - 扫描范围：运行时加载的是内嵌房间 XML（`Rooms.as:2793-2822` 注册 `rooms_*`），`fe/rooms/*.as` 13 个类共 **639** 个 `<room>`；外部 `Rooms/*.xml`（另一份房间数据/编辑器数据）31 个文件共 662 个房间定义。两边的 `retdark` **都只命中 2 处**，且都是 `rooms_prob` 的同一对房间；全 `src102` 的 `.as` 里 `retdark` 也只有 `Location.as:478-481` 的读取 + 这两处。
  - 结论：**运行时 639 个房间里 637 个的亮度只升不降**。`[已证实（静态扫描）]`
- 非 retDark 房间因此是“**曾见最亮值棘轮**”：`t_visi` 只在更亮时被改写（`Location.as:3235-3239`；远距分支不置值），没有变暗路径；唯一重置是换房时 `drawLoc` 把 `lightBmp` 填黑再 `setLight()`（`Grafon.as:423-424`）。`[已证实]`

### 4.3 触发频率（对“平滑”的影响）

- `Location.step()`：仅当玩家 `dx/dy` 位移 >0.5、或 `isRelight`、或 `isRebuild` 时调用 `lighting()`；否则若 `relight_t>0` 调 `lighting2()`；每帧最后清 `isRelight`：`Location.as:3394-3405`。
- 所以“+0.1/帧”更准确地说：`+0.1/次 updVisi 调用`；移动中每步一次，停下后最多 10 步。`[已证实]`
- 对观感的影响：原生边界不是“每帧精确重算”，而是“目标瞬跳 + 显示值 0.1 步进追赶 + 只升不降”。这带来**强迟滞/记忆**：边界变化被时间低通，所以显得平滑稳定；副作用是任何一次“漏光”角值一旦升上去就永久保留（直到换房）。`[机制已证实；观感为推论]`

---

## 5. “平滑”到底来自插值还是别的东西？RV 该选哪种做法

- 来源排序（按代码证据）：
  1. **40px 角点场 × 双线性放大**：`Grafon.as:141-143`、`203-206`、`225`、`695` —— 最直接的“40px 宽线性过渡”。
  2. **时间棘轮**：`Tile.as:271-279`、`Location.as:3235-3248`、`Location.as:3394-3404` —— 抹掉逐帧跳变，且几乎不衰减。
  3. **角值本身连续**：距离线性衰减（`Location.as:3167-3175`）+ 分数 `opac` 累减（`Location.as:3215-3227`），再加上 360° 全向求值（无朝向锥，只有距离）。
- **不是**来源：`visLight` 上没有 `BlurFilter`（`Grafon.as:180-226` 整个构造过程没有给 `visLight/lightBitmap` 挂 filter）；`visSats` 的 `BlurFilter(3,3,1)` 是卫星视觉（`Grafon.as:183`）；全屏模糊只出现在特殊效果参数 >100 时（`Grafon.as:1427-1430`）。`[已证实]`
- 门窗“光锥”的量化上限：每个角点一条射线、主轴 40px 步进，所以光锥的边界落在 40px 角点格上；一个 2 瓦片宽的窗最多影响很窄的一列/几列角点，经双线性摊成 40~80px 的柔带。这跟“墙的 40px 斜坡”是同一套网格，差别主要是**幅度**（1.0 vs 0.2/0.8）。`[已证实机制；视觉幅度对比为推论]`
- RV 当前实现（只读对照）：
  - `current` 模式：每瓦片 8×8=5px 子格，仅对边界/透光瓦片做完整 raycast（`RealisticVisionMod.as:119`、`:1970`、`:2045-2066`）；`fogBitmap.smoothing = true`（`:1219-1227`），再叠加 `curBlur`（默认 20px：`:610`、`:624`、`:1943`）。
  - `classic` 模式：`classicRaw` 为每瓦片 1px、按原生角点相位（`classicLightMatrix` 缩放 = FOG_SUB=8、偏移 -4/-12：`:359-362`、`:1231-1244`），并从原生 `tile.visi` 读光（`:277-285`）；对 `opac>=1` 墙另有 `joinClassicWalls` 接边（`:2665-2737`）。
- **问题 5 的回答**：若目标是“复刻原生的平滑”，正确做法是**在 40px 瓦片角点网格上采样 + 双线性放大**（RV classic 的 `classicRaw` 路线），而不是更细的子格射线。更细的子格（5px）是“更接近真实几何”，会让边界更硬、更准确，但和原生 40px 量化场不是同一种质感；若必须用子格，需要再补 ~40px 的低通才能接近原生观感。`[推论（由 1/4/5 代码链推导；未做画面对比）]`
- 补充：RV 的眼点是 `(gg.X, gg.Y - gg.scY*0.75)`（`RealisticVisionMod.as:1513-1517`），比原生少了 `storona*12` 的水平偏移（原生见 `Location.as:3137`）。拍对照截图时同一站位会得到不同的场，尤其贴墙/门缝时差异放大。`[已证实差异；影响大小未验证]`

---

## 6. 原生单位感知：`isLine`/`look` 是另一套判定

### 6.1 `Location.isLine`（视线二值检测）

- 采样：`n = floor(max(|dx|,|dy|)/World.maxdelta) + 1`，`World.maxdelta=9`（`World.as:52`）；从 `i=1` 到 `n-1` → 间距 ≤9px，且**两端点都不直接采样**（眼点附近、目标点附近各有一个小于 9px/一格的盲区）：`Location.as:2366-2386`。
- 判据：采样点所在瓦片 **`phis == 1`** 且点落在 `phX1..phX2 / phY1..phY2` 内 → 返回 false：`Location.as:2376-2382`。它**完全不看 `opac`、不看 `visi`**。`[已证实]`
- 后果（由 opac 表反推）：
  - `window(phis=1, opac=0.2)`：光能透，但 AI 视线**完全被挡**；
  - 木门/金属门（`phis=1`，0.8/1.0）：挡视线（木门在光里还透 0.2 的亮度）；
  - 栅栏 `grate/hgrate(phis=2, opac=0.1)`：不挡视线（判定只认 1），但光几乎被挡（0.1×格数）；
  - `zForm>0` 半墙：`phis` 仍是 1，但 `phY1` 下移 → 只有射到其“下半格”的采样点才算挡（可越过上半格看）。`[已证实]`
- 其他 `isLine` 使用者（说明它是原生的通用 LOS）：`Weapon.as:1657-1661`、`UnitPlayer.as:1792`、`UnitPlayer.as:1934`、`Unit.as:4751`、`Unit.as:4776`、`UnitAlicorn.as:1159`、`UnitBossAlicorn.as:610`、`UnitPet.as:372`、`Spell.as:260`。

### 6.2 `Unit.look`（AI“能否看见目标”）

- 眼点：`eyeX = X + scX*0.25*storona`、`eyeY = Y - scY*0.75`（`Unit.as:3100-3101`），与光场起点基本一致（§2.1）。
- 射线：`n = floor(maxdist/9)+1`，起点索引 `mater ? 1 : 4`（`Unit.as:4620`；`mater` 默认 true：`Unit.as:208`）→ 普通实体单位从第 1 个样本开始（≈9px），**非实体/幽灵类**（`mater=false`，如 `UnitPet`/`UnitSpectre`/`UnitNecros`）才从第 4 个样本开始（最多跳过 ≈36px）；判据与 `isLine` 相同：只查 `phis==1` 且在矩形内（`Unit.as:4623-4630`）。
- 调用方：`findCel()` 用 `listen/look` 决定是否锁定玩家（`Unit.as:4664-4696`）；`look` 的距离/视野锥/视觉衰减等见 `Unit.as:4560-4641`。
- **与光照无关**：`look()` 全文没有读取 `visi`/`t_visi`/光照场；即 AI 在纯黑房间里照样能用几何 LOS“看见”目标。`[已证实]`
- `visi` 的原生消费者（不是 AI 视线，但会吃 `tile.visi`）：
  - 鼠标目标清空：目标格 `visi < 0.1` 时清 `celObj`（`Location.as:3486-3489`）；
  - 单位噪声表现：`getTileVisi()` 用 `loc.getAbsTile(X, Y-scY/2).visi > 0.3`（`Unit.as:4527-4530`；`makeNoise` 里使用：`Unit.as:3253-3261`）；
  - 大地图着色：取 `visi` 及其右/下邻的 max（`Location.as:2761-2784`）。
- 结论：原生“单位能不能看见”是**几何 LOS 二值判定**，跟光照雾层是两套体系；光场主要服务显示 + 少量小逻辑。`[已证实]`

---

## 7. 顺带查证：`zForm>0` 的墙是“不挡视线但挡移动”的半墙吗？

### 7.1 机制

- `Tile.setZForm(z)`：`phY1 = (Y + z/4)*Tile.tileY`；`z>0` 时 `opac = 0`：`Tile.as:281-297`。z 由地图 token 里的 `,`/`;`/`:` 触发（1/2/3）：`Tile.as:224-238`。
- 渲染：`drawKusok` 对 `zForm>0` 的墙贴图把 `scaleY` 改为 `(phY2-phY1)/40`，并把 y 移到 `(phY2+phY1)/2`（`Grafon.as:848-852`）；`floorMask` 也按 `zForm/4` 下移（`Grafon.as:876`）。→ 视觉上墙变“矮”，只占瓦片下半部分。`[已证实]`
- 碰撞判定：`collisionTile` 只比较 `phX1..phX2 / phY1..phY2`（`Unit.as:2568-2583`），移动/卡墙用它（`Unit.as:2041-2059`、`:2291-2358` 等）。→ 瓦片**上半格（y<phY1）不是实体**。
- 但 `Location.collisionUnit`（传送/NPC 放置用的粗检）只看 `phis>0`，**不看 phY1**（`Location.as:2340-2364`）→ 半墙对这类检测仍是整格实体。

### 7.2 玩家能不能站在上半格？眼点会不会落进 `opac=1` 的相邻瓦片？

- 能站在上半格：`[推论]` 由 `collisionTile` 的矩形判定直接可得——只要身体 50×70 盒（`AllData.as:20-24` + `Unit.as:2541-2566`）不与别的实体瓦片相交，脚在 `phY1` 之上的位置不会被该半墙瓦片拦下。实际站位稳定性由移动解算决定，本次未运行验证。
- 眼点：站立/移动时 `Y1=Y-scY`，眼点 ≈ `Y-52.7`。若脚在 `w*40..w*40+10`（zForm=1 的上半格），眼点 ≈ `w*40-42.7~-47.7` → 落在**上一行**（zForm=3、脚更靠下时）或**上两行**。`[由公式直接推导]`
- 能不能落在 `opac=1` 瓦片：`[推论]` 正常碰撞下**不能**。理由：身体盒高 70px，覆盖眼点所在行；40px 宽的实体瓦片只要包含眼点 x（`X±12`），就必然与 50px 宽的身体盒在 x 上重叠（`X±25`），y 上该行被身体盒完全覆盖 → `collisionTile` 会判碰撞，玩家不能合法站在那。加上 §2.3 的等价关系（正常内容 `opac=1` ⇒ `phis>0`），所以“半墙 + 贴墙”本身不构成眼点进实体瓦片。
- 例外（可能出现“眼点在 `opac=1` 瓦片内”的路径，均未实测）：
  - `phis==3` 幽灵墙：`Spell.gwall` 把它设成 3（`Spell.as:441-453`），玩家 `transT=true` 可穿过（`UnitPlayer.as:383-385`、`Unit.as:2570`），而 `opac` 可能仍是 1（它本来就是墙）→ 站在幽灵墙里时原生光场会忽略该格；
  - `loc.sky` 房间：`collisionAll` 直接 `return false`（`Unit.as:2544-2547`），移动碰撞被跳过；
  - 脚本 `setPos/teleport`、被其他单位挤压等非正常站位（`Unit.as:2804-2826`）。
- 还有一个“原生代码自己也担心这个”的旁证：`UnitAlicorn` 更新眼点时若 `loc.getAbsTile(eyeX,eyeY).phis` 非 0，会把 `eyeY += 20` 抬出墙格（`UnitAlicorn.as:651-656`）。说明原生也承认眼点可能落进实体格，并在个别单位上打补丁；玩家光场没有这个补丁。`[已证实代码；是否可触发未验证]`
- 附带：shipped 地图里 `zForm>0` 瓦片最终 `opac=0`。因为只有 token 首字符走 `fForms`（有 `phis=1`，`Tile.as:213-215`），后续字符走 `oForms`（`Tile.as:240-247`）；`oForms` 里只有 `ed=0 id='100'` 带 `phis=1`，其余 ed=2/3/4 都无 `phis`（`Form.as:110-125`、`AllData.as:6418-6520`）。地图 token 形如 `H,` / `H;` / `H:`（`Rooms/rooms_nio.xml:5`），改 zForm 后 opac 保持 0。`[已证实（静态数据）]`
- 小结：这套机制更准确的描述是——**光完全不管（opac=0）；移动只挡下半格；AI 视线只挡下半格（可越过上半格看）**。所以“不挡视线但挡移动的半墙”只对**玩家光照雾层**成立，对单位 LOS 是“部分挡”。`[已证实]`

---

## 8. 对 RV 的直接含义

> 以下每条都标了 `[已证实]`/`[推论]`；涉及 RV 行为的均为只读代码推导，未运行验证。

1. **[已证实] 复刻原生边界质感的正确粒度是 40px 瓦片角点 + 双线性放大，不是 5px 子格。** 原生就是每瓦片角 1 个 alpha 样本（`Grafon.as:141-143/203-206/225/695`），RV 的 `classic` 路线（`classicRaw` 1px/瓦片 + 原生角点相位矩阵，`RealisticVisionMod.as:359-362/1231-1244`）才是仿原版；`current` 的 8×8=5px 子格（`RealisticVisionMod.as:119/1970/2045-2066`）是“更真实的几何”，边缘天然比原生更硬。若用户要“像原版一样平滑”，优先对齐 classic，而不是继续加密子格。

2. **[已证实] 原生没有“门景最低亮度”。** 透光门/窗只是逐格减 `opac`（`Location.as:3215-3227`），亮度 = 距离衰减 − Σopac；`doordim`/`cfgDoorDim` 是 RV 概念（`RealisticVisionMod.as:1968/1991-1992/2081-2089/2171-2186`）。RV 对 `FOV_DIM` 瓦片强制下限 0.5，会把原生连续渐变变成“平台”，这本身就会改变门窗边界的质感。`[推论]` 若 A 的抱怨点在门窗，先做“doordim=0 vs 0.5”的 A/B。

3. **[推论，高优先] RV `castRay` 把目标瓦片 `opac` 扣了两次**：DDA 循环在进入目标格时已经扣过一次（`RealisticVisionMod.as:1683-1713`），循环结束后又显式“second target sample”再扣一次（`:1746-1755`）。原生 `lighting()` 一般**不扣目标角点瓦片**（§2.2，`Location.as:3210-3229`）。对 `opac>=1` 的墙 RV 直接返回 -1（走墙体专门路径），所以这个差异**只暴露在透光门窗上**：门窗瓦片自身会比原生暗一个 `opac`，形成暗边/暗带；墙没有该问题 → 与“墙边平滑、门窗边界不自然”的现象吻合。建议实验：临时去掉第二次目标采样，比较同一扇窗的边界截图。`[待实测]`

4. **[已证实] 原生“平滑”有很大一部分来自时间棘轮（只升不降、0.1/步），不只是空间插值。** 非 retDark 房间没有变暗路径（`Tile.as:271-279`、`Location.as:3235-3248`、运行时 639 房间仅 2 个 retDark）。RV 的淡入/淡出是双向的（`RealisticVisionMod.as:2191-2195` 的 `advanceMemory`，每帧 ±`fadestep`），边界会“呼吸”，与原生的“记住最亮值”不同。若目标是仿原版，考虑在 classic 模式保留 max-hold/极慢衰减；若目标是“真实”，则保留双向渐变并明确这是有意偏离。

5. **[已证实] `tile.visi` 是“瓦片左上角角点”的样本，不是瓦片中心亮度**（`Location.as:3162/3238/3247/3273` 写 `(x,y+1)` + `Grafon.as:203-206/225` 的坐标换算）。RV 里任何把 `tile.visi` 当 tile 中心亮度用的逻辑会偏半格；`classic` 模式用原生 visi 并用原生角点相位（`RealisticVisionMod.as:277-285/359-362`）是自洽的，`current` 自建子格则不要混用原生 visi 的相位。顺带：现有 RV 知识 `knowledge/discoveries/lighting-vision-pipeline.md:47` 写“每瓦片中心像素”、`:51` 写 lighting “含目标瓦片自身”，按本次复核都**不准确**（前者与它自己第 67-77 行的角点修正矛盾；后者见 §2.2），建议后续更正。

6. **[已证实] 原生 AI 视觉与光照/雾层完全解耦**：`Location.isLine`/`Unit.look` 只做 9px 步进的 `phis==1` 矩形点采样（`Location.as:2366-2386`、`Unit.as:4619-4631`），不看 `opac` 也不看 `visi`。因此：窗 `phis=1` **挡 AI 视线却透光**；栅栏 `phis=2` **透 AI 视线却几乎不透光**；AI 在纯黑区域照样靠几何 LOS 发现玩家。RV 用 FOV 掩膜决定敌人可见性是玩法级改动；如果要让“能不能打/能不能看”和原版一致，不能只依赖雾层，需要显式决定是否借用 `isLine` 这套判定。

7. **[已证实] zForm>0 半墙对光是完全透明的**（`opac=0`，`Tile.as:281-297`），且只挡下半格移动/AI 视线；玩家可站在其上半格（`Unit.as:2568-2583`）。`[推论]` 正常碰撞下（身体 50×70 盒）眼点不会落到 `opac=1` 的瓦片里，所以“贴半墙/贴墙”本身不应产生原生式眼点穿墙；若 RV 出现 B 类漏光，优先怀疑：①RV 复刻了“跳过眼点瓦片”的语义（`castRay` 的 DDA 起点格不检查、`updateRangeLight` 也 `k=1` 起，`RealisticVisionMod.as:648-656/1683-1713`），在眼点因挤压/传送/幽灵墙进入实体瓦片时会漏；②RV 目标瓦片/角点统计差异（第 3 条）；③原生式的 40px 角点采样 + 双线性 20px 外溢 + 只升不降的棘轮会把“曾经漏过的亮值”永久留下。建议先在 debug 叠层里记录“眼点所在瓦片 opac/phis”和“漏光帧的射线首/末采样格”，再决定改哪一层。

8. **[推论] 若想同时要“接近原生的柔和”和“几何正确”，混合方案是：几何用较细 raycast（或 8×8 子格）保证遮挡正确，显示层再统一做约一个瓦片（~40px）的低通/双线性**；否则 5px 子格 + 20px blur 会产生既不是原生 40px 台阶、也不是裸子格锐边的第三种质感。当前 RV `current` 正是这条中间路线；A 的抱怨很可能就来自“门窗走 `doorView` 平台 + 子格边缘”，而不是“墙的 40px 角点场”。

---

## 9. 未查到 / 证据不足（不要当结论用）

- 全部视觉结论（“平滑/不平滑”的观感归因）**没有运行时验证**：本次未启动游戏、未截图、未做像素对比；属于代码链推导。
- `lightBmp` 的“双线性”是按 Flash `Bitmap(smoothing=true)` 的 API 语义推导，未抓取实际缩放输出验证过滤核。
- 目标角点瓦片“不扣 opac”有整数边界例外：若眼点 x/y 恰为 40 的整数倍（`f=0`），最后一个样本会落在角点边界，`getAbsTile` 向下取整会落到目标瓦片（`Location.as:3194/3208/3213/2331-2338`）；实际地图中的触发频率与影响未验证。
- 玩家眼点能否在正常玩法中进入 `opac>=1` 瓦片：代码推论“正常站立不能”，但幽灵墙/天空房/脚本/挤压等路径未实测；`UnitAlicorn` 的 `eyeY+=20` 补丁说明原生也承认眼点可能进墙（`UnitAlicorn.as:651-656`）——但那是另一个单位的光源，不是玩家。
- 每个门对象实际覆盖几格瓦片，取决于其可视宽度 `scX`（`Box.as:653-677`）；本次只从 `opac`/`phis` 属性与 `initDoor` 逻辑推断“宽门/多格扣多次”，未逐一核对 3D/资源宽度。
- `retDark` 的“仅 2 间”是基于静态数据扫描（运行时内嵌 `fe/rooms/*.as` 639 个房间 + 外部 `Rooms/*.xml` 662 个定义，均 2 处）；若运行期另有脚本/配置改写 `loc.retDark`，本次未发现（`retDark=true` 赋值只在 `Location.as:480`）。
- 原生 `lighting()` 的长列表参数（`lightAll`/`UnitSpectre`）在实战画面里的叠加权重，未做运行时观察。
- 未核对 1.03/1.04（DLC）反编译源码是否与 1.02 相同；本报告只对 1.02。

---

## 10. 证据索引（完整路径）

原生根目录：`game-reference/decompiled/1.02/src102/scripts/fe/`

- `graph/Grafon.as`：135-137（rectX/rectY）、141-143（lightX/Y）、172（lightRect）、180-226（visLight/lightBmp/smoothing）、183（visSats blur）、191-202（层级）、203-206（偏移/scale）、224-226（BitmapData/Bitmap）、357-368（warShadow blend）、423-425（drawLoc 重置 + setLight）、427-437（全局黑暗色）、685-701（setLight）、848-852/876（zForm 渲染）、1396-1431（specEffect 模糊）
- `loc/Location.as`：51（black 默认）、129-131（lDist）、167/193/201（opacWater/visMult/retDark 字段）、265-268（48×25）、344（gg）、386/418-420（opacWater 读取）、442-444（noblack）、478-481（retdark）、530-543（非 black 时 visi=1）、643-648（visMult）、2331-2338（getAbsTile）、2340-2364（collisionUnit）、2366-2386（isLine）、2761-2784（大地图 max 邻域）、3094-3106（lightAll）、3108（lighting 签名）、3137-3138（默认眼点）、3108-3255（lighting）、3257-3279（lighting2）、3394-3405（step 触发/relight_t）、3486-3489（鼠标 celObj 的 visi 门槛）
- `loc/Tile.as`：8-10（40px）、64-68（visi/t_visi/opac）、104-113（角点 phX/Y）、198-201（phis>0→opac=1）、204-247（dec/setZForm 调用）、271-279（updVisi）、281-297（setZForm）、299-309（mainFrame）、350-364（die）
- `loc/Box.as`：52（phis 默认）、72（door_opac 默认）、232-235（phis 读取）、290-298（door/opac 读取）、653-677（initDoor）、679-693（setDoor）、695-727（attDoor）、789-810（die）
- `loc/Area.as`：159-197（tileop/tilehp 区域改写）
- `loc/Land.as`：1231（载入时 lighting(gg.X, gg.Y-75)）
- `loc/LandAct.as`：84/227（opacWater 来源 wopac）
- `loc/Form.as`：110-125（fForms/oForms 解析）
- `AllData.as`：20-24（littlepip sX=50/sY=70）、4858-4876（门/窗/栅栏 opac）、5038-5039（alib）、6418-6520（mat：ed=1 墙 phis=1；ed=0 id=100）、9/33 等（其它单位 sX/sY 示例）
- `unit/Unit.as`：104-108（stay 默认）、208（mater 默认）、1018-1028（读 sX/sY）、2541-2566（collisionAll）、2568-2583（collisionTile）、2804-2826（teleport）、3100-3101（AI 眼点）、3253-3261（makeNoise/getTileVisi）、4527-4530（getTileVisi）、4560-4641（look）、4664-4696（findCel）
- `unit/UnitPlayer.as`：349（storona 默认）、383-385（transT=true）、503-506（Y1=Y-scY）、2540-2573（朝向更新）、1678/1703/2026（collisionUnit 传送判定）
- `unit/UnitAlicorn.as`：651-656（眼点进墙则 eyeY+=20）
- `unit/UnitSpectre.as`：70（lighting(X,Y)）
- `unit/Spell.as`：441-453（gwall→phis=3）
- `weapon/Weapon.as`：1657-1661（Weapon.isLine）
- `inter/Camera.as`：121-138（scaleV 与 visual.scale）
- `World.as`：36-42（tile/48×25）、44（fps=30）、52（maxdelta=9）
- `rooms/Rooms.as`：2793-2822（运行时注册内嵌 `rooms_*` XML，共 13 个房间类/639 个房间）
- `rooms/RoomsProb.as`：3532、4999（仅有的两处 `retdark="1"`；对应外部 `Rooms/rooms_prob.xml:3527/4992`）
- 房间数据示例：`Rooms/rooms_nio.xml:5`（`H,`/`H;`/`H:` 的 zForm token）、`Rooms/rooms_plant.xml:495` 等（`tileop="0.25"`）

RV（只读对照）：

- `mods/RealisticVision/src/RealisticVisionMod.as`：119（FOG_SUB=8）、359-362（classicLightMatrix 相位/缩放）、610/624（soft_current/curBlur）、1219-1227（fogBitmap smoothing=true/scale）、1231-1244（classicRaw 1px/瓦片）、1513-1517（RV 眼点，无 storona*12）、1683-1713（castRay DDA 循环）、1746-1755（第二次目标瓦片采样）、1943（applyFilter）、1968/1991-1992/2081-2089/2171-2186（cfgDoorDim/doorView）、2045-2066（8×8 子格 recalcTile）、2191-2195（advanceMemory 双向 fade）、2665-2737（joinClassicWalls 只对 opac>=1）
- `mods/RealisticVision/knowledge/discoveries/lighting-vision-pipeline.md`：47/51（本次复核认为不准确）、67-77（其自己的角点相位修正）

---

## 11. 一句话总结

原生光场是“**从玩家眼点（含朝向偏移 12px）出发、每瓦片左上角取 1 个样本、按 40px 主轴步进逐格累减 opac、再以 ×40 双线性放大**”的 360° 可见度棘轮场；它没有门景下限、几乎没有变暗路径（运行时 639 房间仅 2 间 retDark），墙的平滑来自 40px 角点 + 双线性 + 时间迟滞，而不是更细的射线或贴图模糊。原生 AI 视线则是另一套 9px 二值 `phis==1` 判定，与光照无关。RV 若追求原版观感，应优先对齐 40px 角点场；若要查 A（门窗边界）与 B（贴墙漏光），按 §8 的第 2/3/7 条做对照实验。
