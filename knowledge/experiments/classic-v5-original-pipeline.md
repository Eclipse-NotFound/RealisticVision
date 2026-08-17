# 实验：classic v5 复刻原版雾状感（1px/瓦片 + smoothing + 半格错位）——离线验证（v0.18）

日期：2026-08-17

## 背景

用户反馈："classic 整体仍无原版的雾状感"。用用户提供的原版备份
（`C:\Users\micha\Desktop\Remains\pfe.swf`，未污染 1.02）反编译定位了
"雾"的确切来源。

## 原版雾状感三要素（反编译确认，fe.loc.Location / fe.loc.Tile / fe.graph.Grafon）

1. **1px/瓦片 alpha 遮罩 + Bitmap smoothing=true**（双线性插值）：
   - `lightBmp = new BitmapData(lightX, lightY, true, 4278190080)`（初始全黑 alpha 255）
   - `lightBitmap = new Bitmap(lightBmp, "auto", true)` ← **smoothing=true**
   - `visLight.scaleX/Y = Tile.tileX/Y`（40 倍放大）→ 相邻瓦片值之间
     **40px 连续渐变带**——原版"雾"不是瓦片块，是连续的渐变场
2. **半格错位**：
   - `visLight.x = -Tile.tileX/2`（-20）、`visLight.y = -Tile.tileY/2 - Tile.tileY`（-60）
   - `lightBmp.setPixel32(x, y+1, ...)` → 亮度像素中心落在瓦片西北角
   - 每个瓦片显示 = 自身值（西/北半）+ **东/南邻瓦值（东/南半）**——
     墙的亮面（东/南半显示邻接地板亮度）与暗边由错位自然产生（无需模拟）
3. **visi 渐进节奏**：
   - `Tile.updVisi()`：`visi += 0.1`，封顶 t_visi（**淡入每帧 +0.1**）
   - `Location.step`：移动 → `lighting()`（`relight_t = 10`）→ 之后 10 帧
     `lighting2()` 持续刷新 visi≠t_visi 的瓦片（雾"呼吸"）；站立 10 帧后冻结
   - retDark 房间变暗：`t_visi -= 0.025`/帧（**淡出尾迹**）；非 retDark 只升不降
   - 距离衰减：lDist1 内 1，lDist1→lDist2 线性（光缘环雾带）

## v5 方案（src/RealisticVisionMod.as）

- 新增 classic 独立雾层：`classicRaw`（1px/瓦片，spaceX × spaceY+1，初始全黑）
  + `classicBmp`（**smoothing=true**，scale=40，x=-20、y=-60，写 y+1 行）——
  结构复刻原版 lightBmp；
- **每帧读游戏 tile.visi**（游戏 lighting/lighting2 照常维护渐变节奏），按规则写：
  - fov!=NONE → (1-visi)×255（淡入渐亮/门景 doordim）
  - fov==NONE && visi≥0.99 && explored && !retDark → dimA（记忆区 166）
  - fov==NONE && visi>0.01 → (1-visi)×255（光缘环/残留雾带/光源物）
  - 其余 explored（非 retDark）→ dimA；否则 255 黑
- 变化才写像素（lastA 缓存，站立零写入）；边缘行列照抄原版（lighting 循环
  从 1 开始，恒定黑）；删 fillWallClassic/markSeenByDist（错位自动产生墙亮）。

## 验证（Node 像素模拟，rv_classic_v5_sim.js）

构建 1px 雾场 + 写入 y+1 + 40 倍双线性插值（模拟 smoothing），两种墙布局：

- 场景1（墙东未探索黑）：墙整体黑；地板↔墙交界 **40px 渐变中点 127.5** ✓
- 场景2（墙东亮区）：**墙东半显示东邻亮值（墙亮面自动产生）** ✓、
  墙西半自身黑 ✓、记忆区 166 ✓、166↔255 渐变中点 210.5 ✓

**ALL PASS**：错位墙亮面与双线性渐变带均成立——原版雾状感的核心机制复刻成功。

## 结论

classic v5 从"自渲染子格场"改为"原版管线复刻"（结构/错位/节奏全部同源），
雾状感机制经离线模拟验证；需游戏内实测确认观感（雾带、淡入呼吸、墙亮面、
记忆区 166 边界渐变）。
