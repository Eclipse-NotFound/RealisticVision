# 跨地图/楼层首个房间"整间已探索"——房间记忆按 loc.id 撞名的修复（v0.33.17-locmem）

2026-11-02。用户报告：进入新地图/新楼层后到达的第一个房间里，整间以"记忆区暗度"显示（墙和家具仍可见），
像之前探索过一样；截图处于 `马哈顿废墟 - 5`（random_mane 第 5 层）刚到达的房间。

## 结论

跨房间记忆 `roomMem` 旧实现按 `loc.id` 存 `explored[]`。`loc.id` 只是**Land 内坐标**
（`fe/loc/Land.as:945-957`：`"loc"+landX+"_"+landY`，z>0 再加 `_z`），跨 Land 重名；而所有
Location 一律 48×25（`fe/loc/Location.as:265-266` 取 `World.cellsX/cellsY`），模组恢复时的
`mem.length == n` 尺寸校验**永远成立**。于是每次 Land 重建（读档、出口箱下一层、世界地图非 base 图）
后，新 Land 的到达房间会命中旧 Land 同坐标房间的记录，把旧的 `explored[]` 恢复成"整间已探索"。

修复：房间级记忆改为 **Location 对象弱键**（`Dictionary(true)`），与原版"记忆随 Location/Tile 实例存活"
一致——Land 重建后新对象天然不命中；缓存 Land 复用（脚本 `gotoland` 回已访问地图）时同一批
Location 对象仍保留记忆。`rangeMem`（视距光场）同样改对象键。

## 根因证据（1.02 反编译源码）

| 事实 | 证据 |
|---|---|
| `loc.id` 只含坐标，跨 Land 必重名 | `fe/loc/Land.as:945-957`（`newLoc`）；`Land.as:1180-1185` 到达房固定取 `act.begLocX/begLocY` |
| 每张图入口坐标固定：random_mane = (0,4)，其余多为 (0,0) | `fe/GameData.as:367`（random_mane）、`:24,:80,:175,:243,:462,:560,:563,:647` |
| 所有房间恒 48×25，尺寸校验形同虚设 | `fe/loc/Location.as:265-266`；`fe/World.as:40-42`（cellsX/cellsY） |
| `loc.id` 在同一 Land 内也不唯一（prob 房全是 `loc0_0`） | `fe/loc/Land.as` 的 `buildProb`（约 783-802 行 `newLoc(room,0,0,0,{prob:...})`） |
| Land 重建条件 | `fe/loc/Game.as:351`（`curLand.land==null || crea`）；`crea` 由 `Game.as:458`（beginMission）、`Game.as:469`（gotoNextLevel 出口箱）设置；读档 = 新 `Game`（`World.as:1008`） |
| 游戏内读档不清空模组记忆 | `World.loadGame`（`World.as:969-1055`）从不置 `allStat<1`，模组 `resetOff` 只在 `allStat<1` 触发；入口 `fe/inter/PipPageOpt.as:707` → `World.as:1305` |
| 原版记忆语义 = Location/Tile 实例生命周期 | `Tile.visi/t_visi`（`fe/loc/Tile.as:64-66`）；`Location.lighting` 见 `Location.as:3108-3255`；存档不序列化 visi（`Game.save` 86-163、`LandAct.save` 267-301、`Location.saveObjs` 3552-3562） |
| 缓存 Land 复用时原版保留记忆 | `Game.lands`/`LandAct.land` 缓存（`Game.as:67-83`、`LandAct.as:12`）；脚本 `gotoland` 不设 `crea` |

## 修复内容

候选 `v0.33.17-locmem`（自已部署 `v0.33.16-fx-fast` 派生）：

1. `roomMem:Dictionary = new Dictionary(true)`（Location 弱键 → `explored[]`）；
   `rangeMem` 同样改弱键，`resetOff` 重建。
2. `resetRoom`：离开时 `roomMem[this.curLoc] = explored.concat()`；进入时
   `roomMem[loc] as Array`，尺寸不符或不同对象 → 全未探索（原逻辑保留）。
3. 恢复成功时每会话记一行 `roommem restore loc=<id> explored=<n>`，供真机核对恢复路径仍生效。
4. 版本字符串 `v0.33.17-locmem`；未改配置键、未改其它行为路径。

源码：`build/landmem-fix-20261102/src`（改动仅 `RealisticVisionMod.as`：roomMem/rangeMem 字段与
resetOff 重建、resetRoom 存取、updateRangeLight 键、版本字符串）；构建脚本
`build/landmem-fix-20261102/build.ps1`（存根 SWC + airglobal external，与 fx-fast 同配方）。

## 验证

- 构建：**47,862B，SHA256 `35243D0F23E3E137546E5BBA54991A5FEE68EB188C46D610BC08293E97489D29`**
  （mxmlc 退出 0；仅已知 `RVExplorationCarrier` 无构造函数警告）。
- 官方 ModLoader 路径、隔离副本（独立 app id `pfe-rv-locmem-smoke-0001`、独立 AIR 桌面）：
  `init ok v0.33.17-locmem settings=ModSettings-v1 enabled=true`、`ModSettings settings registered`、
  `tick 1/181/361/541/721/901`，loader `requested_RealisticVisionMod`/`ok_RealisticVisionMod` 配对，无错误。
- 代码级：按上表证据，跨 Land 不再可能命中旧记录；同一 Land 内同一 Location 对象重进仍恢复。
- **未做**：本轮没有在真机里自然走一次"下一层"来复现/对照（需要专用驱动强制 `gotoNextLevel`），
  也没有性能计时（改动只把每房间一次字符串键换成对象键，无分配增加）。真机由用户下一次换层/读档核对；
  若 `RVision.log` 出现 `roommem restore` 说明恢复路径正常，若新楼层首房不再整间发暗即为修复生效。

## 边界与回滚

- 不改变原版 visi/地图/传送判定；只改模组自有记忆的键。
- 回滚：`build/backups/before-locmem-20261102-013447/RealisticVisionMod.swf`（47,801B，
  SHA `F3223BF193D60922E31EF88FB2674B9D945A7C21C35A3F0F3E8B21098A43799A`）复制回
  `release/` 并重启游戏。
