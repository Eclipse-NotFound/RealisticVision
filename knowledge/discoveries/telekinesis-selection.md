---
domain: ui-systems
type: discoveries

game-version:
  - "1.02"

confidence: high
verified: false

discovered-by: RealisticVision

evidence:
  - kind: decompiled-game-code
    symbol: "fe.unit::UnitPlayer.control grab 段（teleObj = loc.celObj）；fe.loc::Location.getDist/step；fe.inter::Ctr.keyTele"

date-updated: 2026-08-15
---

# 玩家念力（telekinesis）选中/抓取机制（1.02）

> 模组内部发现，未经运行时验证。

## 抓取流程（UnitPlayer，control 内 grab 段）

1. 光标距离检查：`(X - World.w.celX)² + (Y - scY/2 - celY)² <= pers.teleDist`。
2. `loc.isLine(X, Y - scY*0.75, celX, celY)` —— 玩家到**光标**的 LOS
   （phis==1 阻挡，门瓦片对"门自身"豁免）。**pers.telemaster 天赋或 !loc.portOn
   时跳过此检查**（隔墙抓取能力来源）。
3. 在光标 50px 内找最近 `levitPoss && massa <= pers.maxTeleMassa` 的对象，
   直接写 `loc.celObj`（**不依赖 getDist() 的清除**）。
4. 再检查玩家到**对象**的 `isLine` LOS（同样 telemaster 跳过）→ 否则
   `gui.infoText("noVisible")`。
5. `teleObj = celObj`；对象 vis 加 teleFilter 光晕；`levit=1`；若是 Unit →
   `alarma(X,Y)`（惊动敌人）；`ctr.keyTele=false`。
- 释放：`dropTeleObj()`（public）：清 vis.filters/恢复 colorTransform、levit=0、
  teleObj=null。
- `Location.getDist()` 每帧：光标瓦片 `visi<0.1` → `celObj=null`（原版对暗处
  交互的拦截，但抓取段会自行重找 celObj，故**拦不住** telemaster 隔墙抓取）。
- 触发键：`Ctr.keyTele`，默认 Q，alt='rmb'（右键）。
- `pers.telemaster` 天赋存在时，物品和**敌人**都可隔墙抓取——本模组在帧尾
  强制释放"处于非 FOV 瓦片的被抓敌人"。

## 结论（对本模组）

- "玩家可以隔墙选中并移动物品"= 原版 telemaster 行为，无需改动。
- "玩家不能隔墙选中敌人"= 帧尾 backstop：`teleObj is Unit && fraction!=F_PLAYER
  && !FOV(瓦片)` → `dropTeleObj()`。副作用：抓取瞬间敌人已 alarma()（v1 接受，
  输入层拦截为后续增强）。
