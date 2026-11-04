# RealisticVision：激光/高速弹药阴影遮盖失效与炮塔/单位退出阴影不显示 —— 深度调查与优化方案

> 文档编号：RV-DESIGN-20261104-PROJ-TURRET-SHADOW  
> 日期：2026-11-04  
> 责任模组：RealisticVision  
> 调查基线：**v0.35.1-csoptA**（当前已部署正式安装，SWF 52,690B，`31bdc9a2…`；基底 v0.35.0-aperture-grade）  
> 状态：**已实施并部署（v0.35.2-shadowfix，2026-11-04）**。见下方「实施更新」。
> 关联工单：
> - [v0.34.2 激光阴影历史修复](../knowledge/experiments/2026-11-02-fx-liberation.md#v0342-laser-shadow-修复)
> - [v0.34.7 边界开火与单敌卡顿方案](boundary-and-enemy-stutter-optimization-plan.md)（C-Bul-1 / C-Ene-1）
> - [v0.35.1 CS 共存性能优化方案](cs-coexist-optimization-plan.md)（阶段 A：W8+W7+W2+W1）
> - 游戏本体反编译源码：`fe.weapon.Bullet`、`fe.unit.UnitTurret`、`fe.unit.Unit`、`fe.loc.Tile`

> ### 实施更新（2026-11-04）
> **v0.35.2-shadowfix 已部署**：54,198 B / `50f68135…079e`；基底 v0.35.1-csoptA（`31bdc9a2…`）；
> 备份 `build/backups/before-v0352-shadowfix-20261104-165437-31bdc9a2/`。
> 实施与方案的**4 处偏离**（理由见[实施报告](../build/shadowfix-20261104/REPORT.md) §4）：
> ①§4.4 的「实心墙法向膨胀」改为**keep-lit alpha 映射**——实测旧映射在 `maskblur_current=4` 下
> 只把交界第一行压到 79（不是方案估的 15~18px 全透明），真正的"整只不显示"是迟滞死锁，做逐子格
> 膨胀性价比不足；②新增**静止弹体裁剪缓存键**（方案未提），把静止视野帧成本压到 +0.4µs/对象；
> ③核心锚点放在 `hideEnemies` 调用点而非 `enemyState` 内部（后者多路提前 return）；
> ④§2.3「炮塔大部分落在 18px 真空区」按实测修正为 1~2 行子格。
> **证据**：离线 A/B 23/23 PASS（同一炮塔 baseline `st=0` / 候选 `st=2`；弹体遮罩几何
> `x=240..960` → `x=300..630`）；标准房 200 帧视觉场逐像素不变；大图 90 帧无"更隐"回归；
> 微基准交战帧弹体 0.034→0.0096 ms/对象（−72%）、`enemyState` 不变；隔离沙箱真机加载
> `init ok v0.35.2-shadowfix` 并进入 `random_mane`（208 units）无报错。
> **未验证**：玩家真机观感、classic 模式、极密集交战外观。开关 `proj_shadow_clip` / `turret_wall_guard`。

---

## 0. 核心结论速览

经过对 `RealisticVisionMod.as` 渲染管线、Flash/AIR DisplayObject 遮罩底层机制以及游戏本体（`Bullet`、`UnitTurret`、`Unit`）反编译源码的系统性走查与交叉验证，两个主诉现象的根本原因完全查明：

| # | 症状 | 根本原因机制 | 致命缺陷位置 | 关键证据 | 优化方案核心 | 性能预期 |
|---|---|---|---|---|---|---|
| **A** | **阴影对激光和高速弹药遮盖效果不佳** | **Flash 矢量遮罩机制性失效**：v0.34.7 为避免弹体位图击穿引入 `dynamicBounds`，强行将遮罩与被遮罩对象的 `cacheAsBitmap` 设为 `false`。根据 Flash Player 规范，任意一方为 false 时遮罩退化为**标准矢量剪裁遮罩**，完全忽略位图 alpha 通道；代码以 `drawRect` 绘制包围盒，导致**整个矩形被视作 100% 透明透光视窗**，阴影遮盖彻底失效。 | `RealisticVisionMod.as:4861-4869`<br/>`4850-4856` | 只要激光/高速弹有一端在亮区，其包围盒生成的 `drawRect` 矩形使深暗阴影内的整段激光与尾迹 100% 直通透显。 | **定向几何矢量裁剪（OBB Vector Clip）与激光分段光线裁剪**：不启用高开销的动态位图遮罩，按视野场直接计算可见区间，生成精准多边形矢量路径。 | **零位图重栅格化**，无 GPU/CPU 显存拷贝，比原全图包围盒位图更快且彻底修复遮盖。 |
| **B** | **炮塔/单位退出阴影后有时不显示** | **四重机制共振叠加**：<br/>1. **包围盒外扩+实心墙拉低加权比例**：贴墙/天花板炮塔外扩 1 瓦片把上方实心墙（恒暗）算入分母，导致 `gateRatio` 始终在 0.1~0.2 徘徊；<br/>2. **迟滞死区（Hysteresis）锁死在 0**：`prevSt=0` 时唤醒需 `gateRatio>=0.25`，炮塔被永久扣死在全隐；<br/>3. **软遮罩调色板截断（`2*i-255`）致贴墙处透空**：模糊过渡带前半段直接斩断为 alpha=0，炮塔身体恰好在死区内；<br/>4. **`fadeCount` 未初始化与 alpha 残留**。 | `RealisticVisionMod.as:3871-3918`<br/>`3764-3767`<br/>`4203-4209`<br/>`4397-4401` | 天花板炮塔（`sX=38,sY=38,y=1`）包围盒 12 瓦片中实心墙占 3~6 瓦片，最大可见比仅 0.167，`st` 恒判 0；即使入 2，天花板下 20px 遮罩全透空。 | **实心墙瓦片剔除分母 + 实体核心保底可见通道 + 贴墙法向支撑膨胀 + 渐显透明度安全守卫**。 | 计算量仅涉及少量 O(1) 状态判断，不增加每帧遍历，**完全零性能拖累**。 |

---

## 1. 深度调查：阴影对激光与高速弹药遮盖失效机理

### 1.1 历史背景：从“开火卡顿”到“遮罩失效”的演变链条
1. **v0.33.16 之前的旧实现**：
   所有子弹和特效都走 `applyWorldVisual`，给每个弹体创建独立的 `Shape` 遮罩，并设置 `visual.cacheAsBitmap = true` 与 `shape.cacheAsBitmap = true`。
   - **痛点**：高速位移和旋转的弹体导致 Flash 底层位图缓存每帧击穿并重新栅格化（Cache thrashing），伴随大量小位图分配与 GPU 纹理上传，造成激烈的开火掉帧（尤其是散弹枪或机枪密集射击时）。
2. **v0.34.2 的局部修复（激光初次修复）**：
   - 发现激光弹（`vis.laser`）拉伸上千像素，原点在亮处时整条激光直接直绘，远端穿入阴影不暗化。于是将激光弹强制送入 `applyWorldVisual(..., dynamicBounds=true)`。
3. **v0.34.7 引入的 C-Bul-1（灾难根源）**：
   - 为了彻底消灭高速弹体（`kind == 2`）旋转击穿缓存造成的掉帧，实施了 C-Bul-1 补丁：
     ```actionscript
     // RealisticVisionMod.as:4861-4869
     if(dynamicBounds)
     {
        if(shape.cacheAsBitmap) shape.cacheAsBitmap = false;
        if(visual.cacheAsBitmap !== record.cache) visual.cacheAsBitmap = record.cache;
     }
     ```
   - 补丁注释声称：`“改矢量裁剪遮罩……代价：跨界弹体边界由 alpha 渐变变为遮罩场 alpha>0 硬边”`。
   - **然而，这一技术假设与 Flash/AIR 底层渲染规范彻底背道而驰！**

### 1.2 为什么 Flash 矢量遮罩无法使用 `beginBitmapFill` 实现阴影截断？
在 Adobe Flash Player / AIR 显示列表体系中，关于 `DisplayObject.mask` 存在硬性底层契约：
- **Alpha 遮罩（位图/透明度遮罩）模式**：
  **必须同时满足** `maskedObject.cacheAsBitmap == true` 且 `mask.cacheAsBitmap == true`。只有在此模式下，Flash 渲染器才会读取遮罩位图的 Alpha 通道进行逐像素的离屏 Alpha 混合。
- **标准矢量裁剪遮罩（Vector Clipping Mask）模式**：
  只要两者中**任何一个**的 `cacheAsBitmap` 为 `false`，渲染器立即降级为标准矢量裁剪！
  **在矢量裁剪模式下，Flash 完全忽略 `beginBitmapFill` 所传入位图的任何像素内容和 Alpha 通道！Flash 仅仅提取矢量绘图路径（Vector Graphics Path）的闭合几何轮廓作为裁剪多边形，轮廓内视为 100% 透传，轮廓外视为 0% 剔除！**

看 `RealisticVisionMod.as` 中的实际绘制逻辑（4850-4856 行）：
```actionscript
if(drawDark)
   shape.graphics.clear();
else if(drawClip != null)
{
   shape.graphics.clear();
   shape.graphics.beginBitmapFill(BitmapData(raster.m2e), new Matrix(drawScale,0,0,drawScale,drawX,drawY), false, true);
   shape.graphics.drawRect(drawClip.x, drawClip.y, drawClip.width, drawClip.height);
   shape.graphics.endFill();
}
else
   shape.graphics.copyFrom(Shape(raster.m2).graphics);
```

#### 灾难性后果推导：
1. 当激光或高速弹药有一部分在亮区时，`raster.fullyDark` 为 `false`，进入 `else if(drawClip != null)` 分支。
2. 代码调用 `shape.graphics.drawRect(drawClip.x, drawClip.y, drawClip.width, drawClip.height)` 绘制了一个**实心轴对齐矩形（AABB）**。
3. 由于 `shape.cacheAsBitmap = false`，Flash 矢量裁剪管线直接把这个矩形路径当作裁剪范围。
4. **位图 `raster.m2e` 中暗区的透明像素在矢量遮罩下完全不生效！**
5. 结果：**只要该包围盒触碰到亮区，包围盒矩形内的整条激光、整颗子弹、整个高速拖尾，全部以 100% 不透明度完整显示出来！**
6. 只有当弹体完全没入全暗瓦片（`drawDark == true`）且 `shape.graphics.clear()` 时，弹体才会被整体隐藏。
7. **结论**：模组当前的“阴影对激光和高速弹药遮盖效果不佳”，本质上是**矢量遮罩被画成了实心包围盒矩形，在几何上完全丧失了阴影轮廓**！

### 1.3 激光与高速弹药的几何特性差异
针对该问题，激光与常规弹药需要分类施策：
1. **激光弹（Laser）**：
   - 实例：`fe.weapon.Bullet`，其 `vis.laser` 存在且 `this.spring >= 2`。
   - 视觉形态：极长（500~1500px）、极细（宽度约 4~8px）、固定朝向的线段。
   - 问题特性：斜向激光的 AABB 包围盒极其庞大，若用位图遮罩则显存开销巨大且每帧重建卡死；若用矩形矢量遮罩则直接透出整条光束。
2. **高速弹药（High-speed Projectiles）**：
   - 实例：`fe.weapon.Bullet`、`PhisBullet`、`SmartBullet`。
   - 视觉形态：长度适中（20~100px，由 `vis.scaleX = vel / 100` 沿飞行方向拉伸）、高移速（40~150px/帧）。
   - 问题特性：飞行跨越明暗交界处时，若按原点查表二值处理会导致“头部进暗区尾部整条突然消失”；若按包围盒矩形裁剪则暗区部分全部透光。

---

## 2. 深度调查：炮塔及单位退出阴影不显示机理

用户反馈：“实测发现有时即使炮塔退出阴影，其也不会显示（不代表只有炮塔有问题）”。调查证实，这是四个相互关联的逻辑漏洞共同导致的确定性故障。

### 2.1 漏洞一：`unitBBox` 强制外扩 + 实心墙瓦片拉低可见加权比例
在 `RealisticVisionMod.as:3757-3773`：
```actionscript
private function unitBBox(loc:Location, u:Unit):Array
{
   var x0:int = Math.floor((u.X - u.scX / 2) / Tile.tileX) - 1;
   var x1:int = Math.floor((u.X + u.scX / 2) / Tile.tileX) + 1;
   var y0:int = Math.floor((u.Y - u.scY) / Tile.tileY) - 1;
   var y1:int = Math.floor(u.Y / Tile.tileY) + 1;
   // 边界钳制...
   return [x0,y0,x1,y1];
}
```
- 外扩 1 瓦片的初衷是避免小体型敌人在 40px 瓦片边界跳变，扩大掩膜候选区。
- **但炮塔的物理定位非常特殊**：
  在 `AllData.as` 与 `UnitTurret.as` 中，标准炮塔 `phis sX=38, sY=38`，房间放置大量在 `y=1`（天花板紧贴天花板瓦片 `y=0`）。
  `u.Y = 80`（基准脚点），`u.Y - u.scY = 42`（顶部贴着天花板 `y=40` 瓦片边界）。
  外扩 1 瓦片后：
  `y0 = Math.floor(42/40) - 1 = 0`，`y1 = Math.floor(80/40) + 1 = 3`！
  纵向跨越 `ty ∈ [0, 1, 2, 3]` 共 4 行；横向跨越 `tx ∈ [22, 23, 24]` 共 3 列。
  **包围盒总瓦片数 `tileCount = 12` 个瓦片！**
- **不可透光实心墙的污染**：
  第 0 行（`ty = 0`）全是天花板上方的实心岩石/合金墙壁（`Tile.opac == 1`）。
  在 `currentSight` 视野图中，实心墙内部永远是 0（黑色/不可见）。
  如果炮塔还处于墙角，侧面又有一列实心墙瓦片。
  **在 12 个瓦片中，天生就有 3~6 个绝对全暗的墙体瓦片计入分母！**

### 2.2 漏洞二：施密特迟滞（Hysteresis）死区将单位死锁在全隐（`st = 0`）
在 `enemyState`（3902-3918 行）：
```actionscript
var gateRatio:Number = litWeight / tileCount;
var prevRec:Object = this.unitVis[u];
var prevSt:int = prevRec != null ? int(prevRec.state) : -1;
if(gateRatio >= 0.85 && dimTiles == 0) return 1;
if(gateRatio >= 0.8) return dimTiles == 0 && prevSt == 1 ? 1 : 2;
if(gateRatio >= 0.25) return 2;
if(gateRatio >= 0.15) return prevSt == 0 ? 0 : 2; // <--- 致命死区
if(gateRatio >= 0.1) return prevSt == 2 ? 2 : 0;
return 0;
```
现在带入炮塔的真实数值：
1. 炮塔原本在阴影中未激活（`prevSt == 0`）。
2. 玩家持光源走近，或者视野扫过天花板下方，炮塔实际身体所在的房间空间（`ty = 1, 2`）已被照亮（例如有 2 个瓦片变亮，`litWeight = 2.0`）。
3. 计算可见比例：`gateRatio = 2.0 / 12 = 0.1667`！
4. 检查分支：
   - 不满足 `>= 0.25`；
   - 落在 `gateRatio >= 0.15` 区间！
   - 代码执行：`return prevSt == 0 ? 0 : 2;`！
   - **因为 `prevSt == 0`，代码直接返回 `0`（全隐）！**
5. **故障复现**：**炮塔所在的有效空腔完全暴露在光线之下，但由于实心墙瓦片强占了分母，加权比例被稀释到 0.25 以下，死区判定让它永远停留在 `st = 0`！**
6. 只要 `st == 0`，`hideUnit(u)` 就每帧强制 `u.vis.visible = false`，炮塔永久隐形！不仅炮塔，**任何紧贴实心墙壁、角落或箱体的敌人，在由暗转明的过程中都会遭遇该死锁**！

### 2.3 漏洞三：软遮罩调色板截断（`2*i - 255`）致使贴墙贴顶处“整片透空”
假定玩家继续靠近，亮瓦片增加，`gateRatio` 终于冲破 0.25 门槛，进入 `st = 2`（软遮罩状态）。
按代码逻辑调用 `showUnit(u)`（把 `u.vis.visible = true`）并附加遮罩 `applyMask(w, u, ubb)`。
然而此时第二道致命陷阱被触发：
- `applyMask` 抓取 `currentSight` 对应区域，并应用高斯模糊滤镜（模糊半径约 20~25 像素）。
- 在天花板与房间交界处，上方墙体为 0（黑），下方房间为 255（白）。高斯模糊在交界处形成宽度约 30px 的平滑过渡带。
- 随后，`finishCurrentMask`（4201-4209 行）执行了调色板映射：
  ```actionscript
  for(var i:int = 0; i < 256; i++)
  {
     var alpha:int = Math.max(0, 2 * i - 255);
     this.maskAlphaMap[i] = alpha == 0 ? 0 : uint((alpha << 24) | 0xFFFFFF);
     this.maskZeroMap[i] = 0;
  }
  ```
- **截断分析**：
  `alpha = max(0, 2*i - 255)` 的数学含义是：
  **凡是模糊后 Alpha 值 $i \le 127$ 的像素，全部强制斩断为 $0$（绝对透明）！**
  这意味着在天花板瓦片边缘向下约 15~18 像素的空间内，遮罩位图的 Alpha 彻底归零！
- **炮塔身体直接被斩掉**：
  炮塔高度只有 28~38 像素，基座紧锁在天花板瓦片下方。
  它的基座、旋转支架和炮身绝大部分正好处在距天花板 0~20 像素的“遮罩绝对透明斩断区”内！
  结果：**即使 `u.vis.visible = true`，挂载的 Alpha 遮罩却把炮塔身体全部裁成透明！玩家肉眼看到的依然是一片空气！**

### 2.4 漏洞四：`rec.fadeCount` 渐显初始化与透明度残留
1. 在 `hideEnemies` 中，新建记录时未初始化 `fadeCount`（为 `undefined`）。
2. 在 D62 渐入分支（4397 行）：`if(st > 0 && rec.prevState == 0 && rec.fadeCount <= 0)`
   在 AS3 中，`undefined <= 0` 返回 `false`，导致初次出阴影时渐入判定可能失效或逻辑紊乱。
3. 若单位在边界微晃触发了渐入（`u.vis.alpha = 0.05`），但在接下来的帧由于上述漏洞被重新打回 `st = 0`，或者在非 FOV 帧被跳过：
   `showUnit(u)` 只做了 `u.vis.visible = true`，**从未保证将 `u.vis.alpha` 恢复为 1**。
   导致部分单位即使脱离了阴影，其实际 `alpha` 残留在 0.05 或 0.2，处于近乎隐形的半透明甚至不可见状态。

---

## 3. 优化方案设计原则与性能保障要求

根据用户指令：**“优化需不明显拖累模组性能表现”**。
RealisticVision 刚在 v0.35.1 实现了 RV 自身耗时下降 21.2%（−2.68ms/帧）的重大成果。本优化方案必须严格遵循以下铁律：
1. **绝不退回到每帧昂贵的动态位图 Alpha 遮罩**：严禁对高速旋转/位移的弹体和激光重新开启 `cacheAsBitmap = true`，坚决避免 Flash 渲染管线底层重栅格化。
2. **纯矢量几何轻量计算优先**：利用 Flash 硬件加速的矢量裁剪能力，将遮罩计算转化为纯 CPU 的线段求交与矩形求交（几十微秒级），生成精简的矢量路径。
3. **零垃圾回收（GC）压力**：复用既有对象与数据结构，不每帧 `new` 数组或临时位图。
4. **分类分治**：长条激光与短弹药分离处理；实体分类分母剔除实心墙为纯数学 O(1) 修正，完全不增添额外遍历开销。

---

## 4. 优化技术方案详案

### 4.1 支柱一：激光光束的“定向线段视野求交裁剪”（C-Laser-Clip）
针对激光（`vis.laser` 拉伸长达千像素）：

#### 核心算法逻辑：
激光在游戏中的本质是一条从发射点 $(X_0, Y_0)$ 延伸到命中点 $(X_1, Y_1)$ 的定向线段。
1. **利用既有视野场采样（Ray-March / Sight Step）**：
   - 模组已有常驻的 `currentSight`（或 `fov` 瓦片场）。
   - 激光起点为发射口 $(X_0, Y_0)$，步长取 1 瓦片（40px）或半瓦片（20px）沿激光角度做快速射线步进。
   - 快速求出激光在玩家视野中的**可见线段区间 $[t_{start}, t_{end}]$**（其中 $t \in [0, 1]$ 表示光束相对长度）。
2. **生成沿光束定向的矢量遮罩多边形（Oriented Vector Polygon）**：
   - 不需要任何位图，不需要高斯模糊！
   - 在光束可见区间 $[t_{start}, t_{end}]$ 两侧外扩光束半宽（如 8px），生成一个精准包裹可见光束的旋转矩形/多边形路径：
     ```actionscript
     shape.graphics.clear();
     shape.graphics.beginFill(0xFFFFFF, 1.0);
     shape.graphics.moveTo(p1.x, p1.y);
     shape.graphics.lineTo(p2.x, p2.y);
     shape.graphics.lineTo(p3.x, p3.y);
     shape.graphics.lineTo(p4.x, p4.y);
     shape.graphics.endFill();
     ```
3. **性能与渲染优势**：
   - `shape.cacheAsBitmap = false`，`visual.cacheAsBitmap = false`。
   - 标准矢量遮罩只用 4 个点构成的多边形进行硬件视口剪裁。
   - **穿入阴影的光束在交界处被矢量裁剪线干脆利落地截断，阴影外光束亮丽，阴影内彻底漆黑！**
   - 单帧计算耗时仅需几个三角函数与 5~10 次像素点采样（$< 0.02\text{ms}$），比原先申请 1000×500 的位图并模糊快了 **50 倍以上**，且内存分配为零！

### 4.2 支柱二：高速弹药与尾迹的“紧凑定向矢量裁剪”（C-Bullet-Clip）
针对高速弹药（`kind == 2`）：
1. **保留矢量裁剪语义，但废除实心 AABB 包围盒**：
   - 弹头位置 $(X, Y)$，速度向量 $(V_x, V_y)$，尾迹长度 $L = \text{vel} \times \text{scaleX}$。
   - 取弹头与弹尾在 `currentSight` 中的视野值。
2. **三态快速分派**：
   - **全亮（Fully Lit）**：弹头和弹尾都在亮区 $\implies$ 摘除遮罩，走原生直绘（零开销）。
   - **全暗（Fully Dark）**：弹头和弹尾都在暗区 $\implies$ 挂空 Shape 遮罩（零渲染）。
   - **跨界（Boundary Crossing）**：
     计算亮区端点到交界处的定向矩形（以弹体角度为长轴，弹体宽度加 6px 为短轴），向 `shape.graphics` 写入该定向短矩形。
     由于矩形仅仅覆盖弹体在亮区的那一部分，Flash 矢量遮罩精准裁切掉暗区部分，彻底消除“矩形把周围暗区一并透光”的缺陷！

### 4.3 支柱三：炮塔与边缘单位“实心墙分母剔除 + 核心保底”（C-Ene-WallFilter）
彻底解决炮塔及边缘敌人出阴影不显示的核心方案：

#### 1. 分母剔除实心墙（Solid Tile Exclusion）：
在 `enemyState` 的瓦片统计循环（3871 行）中：
```actionscript
for(var ty:int = bb[1]; ty <= bb[3]; ty++) 
for(var tx:int = bb[0]; tx <= bb[2]; tx++)
{
   var ti:int = tx + ty * this.spaceX;
   // 核心修正：不可透光的实心墙壁不属于生物/炮塔可见判定有效空间，直接跳过统计！
   if(loc.getTile(tx, ty).opac >= 1)
   {
      continue;
   }
   tileCount++;
   // 正常累计 litWeight ...
}
```
- **立竿见影的效果**：
  天花板实心墙（`opac >= 1`）不再作为分母计入 `tileCount`！
  炮塔包围盒的有效瓦片数从 12 骤降为真正处于空腔内的 6~8 个瓦片。
  原本有 2 个亮瓦片时：
  修正前：`gateRatio = 2 / 12 = 0.1667`（掉入死区，判定为 0）；
  修正后：`gateRatio = 2 / 6 = 0.3333`！
  **直接突破 `>= 0.25` 的唤醒门槛，顺利进入 `st = 2` 软遮罩状态并恢复显示！**

#### 2. 核心锚点保底唤醒（Core Anchor Fallback）：
- 检查单位的物理中心点 $(u.X, u.Y - u.scY / 2)$ 所在子格的 `currentSight` 像素。
- 若中心点直接落在亮区（`alpha != 0`），则无论边缘被墙体如何遮蔽，**强制保证最低状态为 `st = 2`（软遮罩）**，绝不允许跌落为 `st = 0`。
- 这一条兜底规则从根本上消灭了所有因体型、贴墙、姿态变化引起的偶发隐形。

### 4.4 支柱四：软遮罩贴墙法向支撑膨胀（C-Mask-WallDilate）
解决炮塔进入 `st = 2` 却被调色板截断裁成透明的问题：
1. **实心墙支撑面继承邻接可见度**：
   在 `refreshMask` 中为单位构建子格位图 `bd` 时：
   若瓦片本身是实心墙（`opac >= 1`），但紧邻的下方/侧方是可见空腔（炮塔基座所贴之处），在拷贝或写入子格时，将紧贴空腔的实心墙边缘 2~3 个子格填充为可见（0xFFFFFFFF）。
2. **物理意义**：
   实心墙是炮塔的安装基座，基座是看得见天花板的，它不应向房间下方投射一片“全透明的黑洞”。
   将贴紧的实心墙边缘标为可见后，高斯模糊在天花板与房间交界处生成的 Alpha 值稳定保持在 200~255，经过 `2*i - 255` 调色板映射后**不再被截断为 0**！
   炮塔基座与炮管完整显现，阴影在炮塔下方平滑羽化，观感极其自然！

### 4.5 支柱五：渐显状态与透明度安全守卫（C-Fade-Sanitize）
1. **记录初始化补齐**：
   在 `unitVis` 创建记录时显式声明 `fadeCount: 0`。
2. **`showUnit` 透明度守卫**：
   在 `showUnit(u)` 中追加安全守卫：若 `rec.fadeCount <= 0`，确保 `u.vis.alpha = 1`；避免任何因中途被打断造成的 0.05 残留。

---

## 5. 性能损耗评估与无损论证

根据模组治理要求，任何优化方案必须提供详尽的性能分析：

| 模块改动 | 改动前性能基准 | 改动后性能机制 | 性能差异与预期收益 |
|---|---|---|---|
| **激光遮盖优化** | 每帧 AABB 巨大位图分配 + `refreshMask` 遍历数十瓦片 + 矢量遮罩画实心矩形（耗时 ~0.5ms，且画面错误） | 沿线段步进 5~10 点采样 + 4 点矢量多边形（OBB）直绘 | **耗时降至 < 0.03ms**，内存零分配，**性能显著提升且画面正确**。 |
| **高速弹药遮盖** | 错误的全图包围盒矩形裁剪 | 仅在跨界时计算定向矩形，亮/暗两端走原速直绘 | 跨界计算量仅为数次加减乘除，CPU 耗时完全在微秒级噪声带内（$< 0.01\text{ms}$）。 |
| **实心墙分母剔除** | 每次循环无条件 `tileCount++` | 增加一次 `tile.opac >= 1` 判定（已有内存引用） | 每次单位状态计算仅循环 9~12 次，增加单次布尔判断耗时 $< 0.1\mu\text{s}$，整帧影响绝对不可测。 |
| **软遮罩法向支撑** | 原调色板截断直接吞噬贴墙贴顶像素 | 仅在贴墙边缘做 2 像素边界填充 | 仅在 FOV 变化或单位跨界时触发一次，不影响稳态帧率。 |

**总体性能定论**：本方案不仅**不会拖累模组性能**，反而因为消除了长条激光对大范围位图掩膜缓存的无效索求，在激光武器交战场景下能带来显著的性能恢复！

---

## 6. 配置开关与逃生口设计

为了确保与已有配置体系的兼容性，在 `config.txt`（及 Local Store 副本）中提供独立控制键：

```ini
# 激光与高速弹药阴影遮盖增强 (1=精准定向矢量裁剪, 0=回退原包围盒路径)
proj_shadow_clip=1

# 实体遮罩实心墙分母剔除与贴墙防隐形 (1=开启智能剔除防隐形, 0=回退旧版加权)
turret_wall_guard=1
```
当任何配置键设为 0 时，完全无缝回退到旧版逻辑，为真机验证提供完整的退路保障。

---

## 7. 分阶段实施路线与验证矩阵

### 7.1 阶段划分
- **阶段 1：实体贴墙死锁与透空修复（解决炮塔/单位出阴影不显示）**
  1. 实施 C-Ene-WallFilter（实心墙剔除 + 核心保底）；
  2. 实施 C-Mask-WallDilate（实心墙法向支撑，消除截断透空）；
  3. 实施 C-Fade-Sanitize（渐显安全守卫）；
  4. 离线夹具验证：天花板炮塔、墙角炮塔、门边单位出入阴影状态切换断言。
- **阶段 2：激光与高速弹药定向矢量裁剪（解决遮盖效果不佳）**
  1. 实施 C-Laser-Clip（激光定向线段视野求交裁剪）；
  2. 实施 C-Bullet-Clip（高速弹药定向矩形裁剪）；
  3. 离线夹具验证：穿透阴影的倾斜激光、高速位移子弹像素对照断言。
- **阶段 3：性能复测与发布门禁**
  1. 离线 Exact 像素断言全矩阵；
  2. 冒烟测试与 ModLoader 启动校验；
  3. 更新外置记忆与发布部署。

### 7.2 离线验证断言设计（Checklist）
- [ ] **Test-Turret-Ceiling**：固定在 `y=1` 的天花板炮塔，当光照从下方射入时，`st` 必须正确由 0 跃升为 2/1，严禁留在 0；
- [ ] **Test-Turret-Visible-Pixels**：在 `st=2` 软遮罩下，炮塔基座与身体在屏幕上必须具有大于 0 的有效像素，严禁整身透空；
- [ ] **Test-Laser-Shadow-Cut**：起点在亮区、终点在暗区的 1000px 激光，遮罩后在暗区内的像素必须严格为 0，严禁穿透透显；
- [ ] **Test-Bullet-Trail-Cut**：高速穿入暗区的弹尾，在暗区部分必须被精确裁剪，亮区部分保持原生亮度；
- [ ] **Test-Perf-No-Regression**：微基准循环 1000 次激光与弹药处理，耗时不得超过旧版。
