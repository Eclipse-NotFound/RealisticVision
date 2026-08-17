---
domain: rendering
type: discoveries

game-version:
  - "1.02"

confidence: high
verified: false

discovered-by: RealisticVision

evidence:
  - kind: decompiled-game-code
    symbol: "fe.loc::Tile.visi/t_visi/opac/updVisi; fe.graph::Grafon.setLight/drawLoc/drawAllObjs; fe.loc::Location.lighting/lighting2/step"

date-updated: 2026-08-15
---

# 游戏本体光照/可见性管线（1.02，src102 反编译）

> 模组内部发现，尚未经运行时验证（verified: false）。验证后再评估是否贡献
> shared-knowledge。

## 瓦片字段

- `Tile.tileX = Tile.tileY = 40`（public static）。
- `Tile.visi`（当前亮度 0..1）、`Tile.t_visi`（目标亮度）。
- `Tile.updVisi()`：`visi += 0.1; if(visi > t_visi) visi = t_visi;` ——**只增不减**
  （下降时瞬间钳到 t_visi）。
- `Tile.opac`（遮光率）：墙=1（`inForm` 在 phis>0 时置 1）；门瓦片=door_opac；
  水=loc.opacWater。`Tile.die()` 置 `phis=0, opac=0`。
- `Tile.phis`（碰撞）：1=实体墙；门瓦片在门关闭时=门.phis，开门时=0。

## 光照掩膜

- `Grafon.visLight`：lightBmp（49×28 px，scale=40×40，偏移 -20,-60）黑色掩膜，
  每瓦片中心像素 alpha = (1-visi)*255。
- `Grafon.setLight()`（public）：按 visi 全量重绘 lightBmp。
- 层级（grafon.visual 子级顺序）：visBack → visBack2 → visObjs[0..1] → visObjs[2]
  （单位/武器）→ visFront（前墙）→ visObjs[3]（特效/血条）→ visVoda → **visLight**
  → visObjs[4]（UI 粒子）→ visSats → visObjs[5]。掩膜只压暗其下方层。
- `drawLoc` 中 `visLight.visible = loc.black && World.w.black`（非 black 房间掩膜隐藏）。
- 非 black 房间加载时所有瓦片 `visi = 1`（Location 构造/加载处）。

## 原版 lighting（Location.lighting/lighting2）

- 触发：`Location.step()` 中 `loc.black` 且（玩家位移>0.5 || isRelight || isRebuild）
  → `lighting()`；否则 `relight_t>0` → `lighting2()`。
- `lighting(x,y,lDist1,lDist2)`（public）：每瓦片算亮度 = 1 - 路径累计 opac
  （主轴向逐瓦片步进，含目标瓦片自身）；lDist1 内=1，lDist1..lDist2 线性衰减到 0；
  只提升 t_visi（除非 retDark 则逐步降）；直接用 `lightBmp.setPixel32` 写掩膜。
- 破坏墙/开门本身**不**调 setLight：开门置 `loc.isRelight=true`；爆炸破坏置
  `isRebuild`。下一次玩家移动触发的 lighting() 才读到新 opac。
- **setLight / drawAllObjs 调用点只在 drawLoc**（见 conflict 记录）。

## 结论（对本模组）

- 复用 `tile.visi/t_visi` 实现三态视野可行；但 **visLight 掩膜像素网格与瓦片
  网格错位半格**（见下），硬边三态渲染必须自建对齐雾层（v0.2，decisions D8）。
- 破坏墙/开门后 opac 实时变化 → 逐帧读取 opac 的 FOV 自动生效。
- 敌人/武器在 visObjs[2]（掩膜下），物品 Box 在 visObjs[0/1]（掩膜下），
  UI 粒子在 visObjs[4]（掩膜上）。
- 狮鹫（UnitMerc）的持械手臂 `arm` 是 **internal 成员**（`World.w.grafon.
  visObjs[sloy].addChild(this.arm)`），模组只能通过显示树扫描间接处理。

## visLight 掩膜网格错位（重要，v0.2 视觉根因）

- lightBmp 49×28，scaleX/scaleY=40，x=-20，y=-60 → 像素 (i,j) 覆盖世界
  [(40i-20, 40i+20) × (40j-20, 40j+20))，中心 (40i, 40j) 落在瓦片**角点**；
  瓦片 (x,y) 中心 (40x+20, 40y+20) 对应像素 (x+1, y+2)。
- `setLight()` 把瓦片 (x,y) 写到像素 (x, y+1) → 该像素覆盖瓦片 (x,y) 的左上
  象限 + 相邻三瓦片的各一个象限。瓦片显示亮度 = 自身值(左上) + 右邻(右上) +
  下邻(左下) + 右下邻(右下)。
- 平滑渐变（原版 lighting）下不显眼；硬边三态下表现为"亮值向暗瓦片四角渗透"
  的亮边/亮角。另外像素行 0/1、列 0、48 从不被写（构造时全黑）→ 房间边缘
  固定黑色半格。
