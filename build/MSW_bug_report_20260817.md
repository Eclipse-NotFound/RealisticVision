# Bug 排查说明：读档崩溃 #1009（卡在载入界面）

> 报告日期：2026-08-17
> 排查：RealisticVision 开发者（跨模组协作转达，未改动任何 MSW 文件）
> 对象：MoreSkills&Weapons（MSW）模组
> 严重度：高（自动存档后无法进入游戏）

## 现象

启动游戏读档时崩溃并卡在载入界面：

```
TypeError: Error #1009
	at fe.unit::Invent/addLoad()
	at fe.unit::Invent()
	at fe::World/newGame1()
	at fe::World/step()
	at fe::MainMenu/mainStep()
gr_stage: 0
```

## 根因

`Invent.addLoad()`（读档流程）中访问 `this.items[id].xml` / `this.items[id].kol`，
当存档里的物品/弹药 id **不在游戏物品表（AllData `<item>`）** 时产生空引用 #1009。

- `Invent` 构造时只从游戏内置 `AllData.d.item` 构建 `items` 表；
- MSW 在运行时添加的新武器/弹药 id **不在这张表里**；
- 玩家获得/装备 MSW 武器后，存档 `invent` 写入这些 id；
- 重启读档 → `addLoad` 找不到 → 空引用 → 卡载入。

## 证据

1. **崩溃点**：`Invent.addLoad`（fe/unit/Invent.as）——`this.items[_loc2_.ammo].xml`
   与 `this.items[_loc2_].kol` 无空值保护。
2. **存档内容**（自动存档）：
   `%APPDATA%\pfe2` 与 `%APPDATA%\pfe3` 下
   `Local Store\#SharedObjects\pfe.swf\PFEgame0.sol`（2026-08-17 10:20-10:22 更新）
   包含以下非原版 id：
   `mswglau, fireballj, autoaxej, hmgj, mbulj, udarj, trej, skyboltj, intelj,
   magusj, moonj, mrayj, dragonj, drayj, eclipsej, bladesj, lightningj, policj,
   skinj, battlej, amul_adeptj, amul_berserkj, amul_magej, amul_sneakj,
   amul_sniperj, amul_sparkj, amul_warj, astealthj, autodoc, autodoc_rep, ...`
3. **与游戏数据对比**：对当前 pfe.swf 反编译 `fe.AllData`，提取全部 1735 个
   `<item>` id 比对——上述 id **全部不在**（`mswglau` 等也不在 weapon/spell 表）。
4. **来源**：`mswglau` 等仅出现于 MSW 模组源码（`MSWWeapon.as`）与文档，确认
   为 MSW 新增武器。
5. 与 RealisticVision 无关：报错堆栈为纯游戏代码；游戏文件（pfe.swf md5）未变；
   该模组不添加任何物品。

## 建议修复方向（任选，供 MSW 决策）

1. **注册进游戏物品体系**：MSW 在 `init` 时把新增武器/弹药注册到游戏可识别的
   数据源（若 MSW 用 AllData 扩展/注入机制，确保读档前 `Invent.items` 能解析
   这些 id；例如提供"物品表补丁"并在 `Invent` 构造后补注册）。
2. **存档兼容**：读档前对 `invent.weapons/items/ammos/fav` 过滤未知 id，或
   `addLoad` 中为未知 id 提供兜底（跳过并记日志）。
3. **数据内嵌**：若可行，把新武器/弹药作为 `<item>`/`<weapon>` 数据并入
   AllData（需与游戏本体补丁/其他模组协调——注意 pfe.swf 是多模组合并部署，
   改动需合并流程）。

## 立即恢复游戏的临时办法（用户侧）

备份/移走 `PFEgame0.sol`（自动存档）即可进入游戏（会丢失自动存档进度）；
手动存档若含 MSW 物品同样会崩，需 MSW 修复后读取。

## 备注

- 本报告由 RealisticVision 模组排查过程中发现并转达；未修改 MSW 任何文件。
- 如需复现细节或存档样本（脱敏），可联系 RealisticVision 开发者协助提取。
