# RealisticVision —— 视野系统设计

> 版本：v2（v0.2 修订，2026-08-15）
> 目标游戏：REMAINS 1.02（pfe.swf）
> 本文描述模组自身设计。游戏本体机制结论见 `knowledge/`（未验证前不写入 shared-knowledge）。

## 0. v0.2 修订（玩家实测反馈）

- **自建瓦片对齐雾层**替代游戏 visLight 掩膜：游戏掩膜像素中心在瓦片角点
  （网格错位半格），硬边三态下亮值向暗瓦片四角渗透（"墙边亮边"）。自建
  BitmapData(spaceX×spaceY) 像素-瓦片一一对应，插在 visLight 后同级，逐帧写
  alpha；infravis 复刻到自建层。详见 decisions D8。
- **墙点亮单遍化**：阻挡瓦片仅由"视野可见的非阻挡邻瓦片"点亮，不链式传播
  （厚墙内部保持暗）。
- **litmin 0.5→0.6**：部分透光（wopac/门 opac=0.5）区域由"全亮"降为"暗色"。
- **敌人部分可见裁剪**（见 §5.1）：FOV 矩形掩膜挂单位 vis/hpbar/武器 vis；
  狮鹫手臂（UnitMerc.arm，internal）经显示树扫描隐藏。
- **念力宽限倒计时**（见 §6.1）：拖敌出视野 3 秒后中断，期间敌人可见。
- **安全基地**（见 §7.1）：`loc.base` → 正常渲染（无雾全亮）。
- **配置**：`release/config.txt` + F11 开关 + F10 面板（见 §7.2）。

## 1. 目标

一句话：实现实时视野更新，避免玩家看到墙壁等遮挡物后方的敌人。

三态视觉：

| 状态 | 定义 | 表现 |
| --- | --- | --- |
| 未探索（unexplored） | 从未进入过视野 | 全黑（掩膜 alpha 255） |
| 当前可见（visible） | 当前帧 FOV 内 | 正常显示 |
| 已探索但不可见（remembered） | 曾可见，当前离开视野 | 暗色：保留场景/地形/物品，隐藏敌人 |

已知特殊情况（均需覆盖）：

- 可破坏墙壁：视野计算必须实时读取墙壁当前状态。
- 部分门（door_opac < 1，如玻璃门）：提供门后区域暗色视野（游戏本体已有此机制）。
- 敌人（如天角兽）念力移动物品：物品在 remembered 区仍需实时显示其移动。
- 玩家隔墙念力（telemaster 天赋）：可隔墙选中并移动**物品**；**不能**隔墙选中**敌人**。

## 2. 复用的游戏本体机制（调查结论摘要）

详见 `knowledge/discoveries/`。核心：

- **光照管线**：每 Tile 有 `visi`（当前 0..1）/`t_visi`（目标）/`opac`（遮光率：墙=1、
  门=door_opac、水=loc.opacWater）。`Grafon.visLight` 是一张 49×28 像素的黑色掩膜
  Bitmap（scale 40×40、偏移 -20,-60），每瓦片中心像素 alpha = (1-visi)*255。
  `Grafon.setLight()`（public）按 `visi` 全量重绘掩膜。
- **显示层级**：`grafon.visual` 内 visBack → visBack2 → visObjs[0] → visObjs[1] →
  visObjs[2](单位) → visFront(前墙) → visObjs[3](特效/血条) → visVoda → **visLight** →
  visObjs[4](UI 粒子) → visSats → visObjs[5]。掩膜只压暗其下方所有层。
- **瓦片遮光实时性**：墙被破坏 → `Tile.die()` 置 `phis=0, opac=0`；
  门开 → `Box.setDoor(true)` 置门瓦片 `phis=0, opac=0` 并 `loc.isRelight=true`。
  因此只要逐帧读取 `tile.opac`，破坏墙/开门自动生效。
- **游戏自带 lighting()**：按玩家位置逐瓦片算亮度（LOS 步进累加 opac），只升不降
  （除非 retDark）。本模组完全接管 t_visi/visi 控制权（模组帧代码晚于游戏 step，
  每帧覆盖）。
- **敌人识别**：`Unit.fraction != Unit.F_PLAYER`(=100)；`loc.gg` 玩家；
  `Unit.sost`：1 活动 / 3 死亡姿态 / 4 尸体。
- **敌人视觉**：`unit.vis`（MovieClip，挂 visObjs[2]）+ 独立 `unit.hpbar`
  （挂 visObjs[3]）——两者都要隐藏。
- **念力**：抓取在 `UnitPlayer` 的 grab 逻辑（mouse/键触发）；`pers.telemaster` 天赋
  跳过 `loc.isLine` LOS 检查（隔墙抓取）。`gg.dropTeleObj()`（public）干净释放。
- **房间切换**：`World.ativateLoc` → `Grafon.drawLoc`（重建全部位图 + setLight +
  drawAllObjs）→ `Camera.setLoc`。模组以 `World.w.loc` 引用变化检测房间切换。

## 3. 架构

单一文档类 `RealisticVisionMod`（SWF 由补丁后 MainFE 以子 ApplicationDomain 加载，
调用 `init(main)`——注入模型同 Sandevistan，见 shared-knowledge
`knowledge-validation/facts/modding-interop.md`）。

```
RealisticVisionMod
├─ init(main)          注册 stage ENTER_FRAME / MOUSE_DOWN / KEY_DOWN
├─ onFrame()           每帧主逻辑（晚于游戏 World.step）
│  ├─ 守卫：World.w / allStat>=1 / loc / gg 存在
│  ├─ 房间切换检测 → resetRoom()
│  ├─ FOV 计算（见 §4）
│  ├─ 三态写入 tile.visi / t_visi + grafon.setLight()
│  ├─ 敌人隐藏（见 §5）
│  └─ 念力规则（见 §6）
├─ resetRoom()         清空 explored、全瓦片 visi=0、强制 visLight.visible
├─ computeFov()        格网 raycast（见 §4）
├─ debugOverlay        F10 开关诊断信息（挂在 world.main）
```

所有对游戏对象的访问都走 **public 成员**（编译期静态类型来自 external-library
pfe.swf），遵守 sealed-class #1069 陷阱（本模组不做任何 bracket 探测访问，全部
import 静态类型）。

## 4. FOV 计算（computeFov）

- **光源点**：玩家眼点 `(gg.X, gg.Y - gg.scY*0.75)`（与游戏 `isLine` 一致）。
- **半径**：`loc.lDist2`（房间 @vis/visMult 已折算，默认 1000px = 25 瓦片）。
- **算法**：对半径内每个瓦片中心 `(cx,cy)` 从眼点按主轴向逐瓦片步进（与游戏
  `Location.lighting()` 相同步法），累加 `opac`（水瓦片取 max(opac, loc.opacWater)）：
  - `lit = 1 - Σopac`，opac 累计 ≥1 提前终止（blocked，lit=0）。
  - `lit >= 0.5` → **visible**（正常显示，target=1.0）。
  - `0 < lit < 0.5` → 透过玻璃门/水看到的区域 → **remembered-dim**（target=V_DIM），
    同时标记 explored——实现"门后暗色视野"。
  - `lit == 0` → 不可见：explored ? V_DIM : 0。
- **墙壁瓦片可见性**：opac>0 的瓦片自身 lit=0，但若其 8 邻域内有 visible 瓦片，
  则视为 visible（target=1.0）——玩家应当看见墙本身；否则按 explored 规则。
  瓦片归属判断用 8 邻域（对角墙也要露脸）。
- **输出**：每瓦片三态数组 `fov[x+y*W]`（2=visible,1=dim,0=none）+ `explored[]`
  持久位图（跨帧、随房间重置）。

### 重算触发

每帧重算（先求正确性；房间 48×25、半径 25 瓦片 ≈ 1900 条射线 × 平均 ~10 步，
AS3 30fps 预算内）。若实测卡顿，降级为：玩家位移>0.5px || loc.isRelight ||
loc.isRebuild || 每 20 帧兜底。

### 平滑过渡

模组自持 `visCur[]` 每瓦片当前值，每帧向 target 逼近（步长 0.15）；
`tile.visi = visCur[i]; tile.t_visi = target;` 然后 `grafon.setLight()`。
（游戏 `Tile.updVisi()` 只增不减，直接用它会在"可见→暗"时瞬间跳变，故自持。）

### 接管策略

- 模组帧代码晚于 `Location.step()`（ENTER_FRAME 注册时序，见 modding-interop），
  每帧覆盖游戏 lighting() 写入的 t_visi——即使 retDark 房间也不冲突。
- `grafon.visLight.visible = World.w.black` 每帧强制（非 black 房间原版会隐藏掩膜）。
- `World.w.black == false`（玩家关闭黑暗）时模组完全停用。

## 5. 敌人隐藏

每帧遍历 `loc.units`：

- 跳过：玩家（`u.player` / `u === gg`）、友好单位（`u.fraction == F_PLAYER`）、
  `u.invis`（游戏自管隐身）。
- `u.sost == 4`（尸体）：不隐藏——尸体按"场景/战利品"处理，在 remembered 区显示。
- 其余敌人：`u.vis.visible = (fov[tile]==visible)`，`u.hpbar.visible` 同值。
- 单位视觉经 `drawAllObjs`（进房时）重建后仍会重新挂上，本模组同帧晚于游戏
  执行，重新隐藏即时生效。
- 掩膜本身压暗 remembered 区物品（Box sloy 0/1 在掩膜下）→ 物品移动实时可见 ✓。

## 6. 念力规则

- **物品**：隔墙选中/移动保持允许——原版 telemaster 已跳过 isLine，无需改动。
- **敌人**：每帧检查 `gg.teleObj is Unit && fraction != F_PLAYER` 且其所在瓦片
  不是 visible → 调用 `gg.dropTeleObj()` 强制释放（backstop）。
- 输入层拦截（可选增强）：MOUSE_DOWN/KEY_DOWN 时若上一帧 `loc.celObj` 是敌人且
  不可见，`stopImmediatePropagation()` 阻止抓取开始。v1 先做 backstop。

## 7. 配置

v1 常量（后续可挪到 config.txt）：

```text
V_DIM        = 0.35   记忆区暗度（掩膜 alpha ≈ 166/255）
V_LIT_MIN    = 0.50   判定"可见"的最低 lit
V_FADE_STEP  = 0.15   每帧平滑步长
```

## 8. 已知交互与风险（v1 记录）

- PipBuck 地图以 visi 着色：remembered 区在地图上偏暗（符合 roguelike 惯例，接受）。
- `Unit.getTileVisi(0.3)`（Sats 卫星扫描器、makeNoise 判定）会把 remembered 区
  (0.35>0.3) 视为"可见"——Sats 扫描器可能标出暗区敌人。若后续要一致，V_DIM 降到
  ≤0.3 即可（代价是暗区更黑）。暂定 V_DIM=0.35，取舍记录在 decisions/。
- 进房瞬间 drawLoc 重建位图：全黑掩膜应在同帧 setLight 生效，首帧可能闪一下
  全亮（drawLoc 里 setLight 用的是旧 visi=1 的瓦片，模组在帧尾覆盖）。可接受。
- transp 潜行敌人：v1 不特殊处理（它们仍会被隐藏/恢复，恢复时可能影响其隐身
  视觉，实测后再定）。
- 天空房（sky/transpFon）：天空在 backBmp 外（visFon 不在掩膜下），未探索区只见
  纯黑瓦片+天空背景——与"黑色未探索"目标一致，可接受。

## 9. 部署

- 模组产物：`release/RealisticVisionMod.swf`。
- 加载补丁：修改 MainFE（保留 Sandevistan 加载器，新增本模组加载器），输出到
  `build/patched/pfe.swf`。**覆盖游戏安装目录需用户明确授权**，见 AGENT_SCOPE §5。
