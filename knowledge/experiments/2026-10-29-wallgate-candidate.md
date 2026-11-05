# D59 P2-A：wall-surface 门控候选与 P1 清理（未采用）

2026-10-29 晚。按 P0/profile 结论实现第一个**无画质改动**的候选：`updateWallSurface` 输入稳定时跳过重建，并附带 P1 零语义清理。候选只在隔离副本中编译、通过 active 窗口 A/B；**未合入 src、未替换 release、未部署**。

## 1. 候选改动

候选源：`build/mask-budget-output/candidates/wallgate/src`（由 D56 准确生产源复制）。

1. **墙面输入门控**（`RealisticVisionMod.updateWallSurface`）：
   - 仅 current、`cfgWallBright=false`、前墙对象存在且 visible 时启用；
   - 当 `loc / view / 前墙对象 / fovVersion / wallLightVersion / wallStructureVersion` 均未变，且缓存年龄 <30 帧时，跳过整次 `RVWallSurface.update`；
   - `wallLightVersion` 在 `applyVision` 实际处理雾层（fogDirty/blur）及 `refreshWallField` 改变墙场时递增；`wallStructureVersion` 在 `wallGeometryDirty` 时递增；
   - `resetOff` 清空缓存；每 30 帧强制刷新一次，兼顾第三方 mask 状态。
2. **P1 清理**：
   - 删除 `hideEnemies` 的 `hiddenPos/visiblePos/exempt`（只写不读，约每帧 3 个容器 + 每单位坐标数组）；
   - `enemyState` 接受调用方 bbox，`hideEnemies` 每单位只算一次 `unitBBox`，`applyMask` 复用；
   - `applyUnitWeapons` 删除未使用的 `exempt` 参数。
3. **独立子变体（已否决）**：每隔一帧跳过 `updateWallSurface`（墙明暗 15Hz），用于测试画质换性能；结果见 §3，明显回退，不进入候选。

## 2. 固定位置 A/B（active 1280×720，同轮 ABBA）

| 轮次 | 条件 | 帧间隔均值 | RV | P95 | >100ms |
|---|---|---:|---:|---:|---:|
| 05b | normal | 37.38 | 2.76 | 48 | 2 |
| 05b | wallgate | 36.65 | 1.70 | 44 | 0 |
| 07 | normal | 37.53 | 2.60 | 48 | 0 |
| 07 | wallgate+P1 | 37.03 | 1.70 | 47 | 0 |

- 两轮固定位置：帧间隔约 **-0.5 ~ -0.7ms（-1.3% ~ -2.0%）**；RV 稳定从约 2.6–2.8ms 降到 **1.70ms（-35%）**；05b 的 >100ms 从 2 次降到 0。
- 这是“输入稳定时省掉整次墙面重建”的直接结果，方向一致，但幅度不足以称为“明显性能收益”。

## 3. 移动位置 A/B

| 轮次 | 条件 | 帧间隔均值 | RV | P95 | >100ms |
|---|---|---:|---:|---:|---:|
| 06 | normal | 49.64 | 13.86 | 61 | 0 |
| 06 | wallgate（不含 P1） | 50.43 | 13.51 | 60 | 2 |
| 08 | normal | 54.07 | 10.65 | 78 | 3 |
| 08 | wallgate+隔帧墙更新 | 60.21 | 10.25 | 85 | 7 |

- 移动态门控只在“无 FOV/雾变化”的帧生效；本轮移动窗口大部分帧在重算，RV 仅 -0.35ms，帧间隔反而 +0.8ms，属噪声/轻微回退。
- 隔帧墙更新子变体明显更差（+6.1ms、>100ms 3→7），说明跳帧会造成下一帧缓存/合成反噬或其它时序问题，**淘汰**。

## 4. 结论与边界

- wallgate+P1 是一个**安全方向**的候选，但当前收益只有固定位置约 1.3%–2.0%，移动态没有可确认收益；不满足用户“只在有明显性能收益时才接受画质/时序取舍”的标准，也达不到修复扫射/交战卡顿的目标。
- 因此**没有合并、没有部署**；正式仍 D56 `BD64B5BB…CE4A9AD`，主 src/release/config/玩家数据未改。
- 尚未做像素/可见性验收（候选未进入发布线）；本轮数据只做同轮配对，active 默认桌面 1280×720 与 D58 私有桌面不可直接比较。
- 下一方向需要明确取舍：
  1. 墙面/雾层更新节流（更低频率）——可能 -1~2ms，但需要用户接受墙明暗滞后；
  2. 敌人身体 mask 的绘制成本（P0 仅这一类固定/移动 4/4 窗一致，约 -3.4ms）——需要软边/硬边质量决策；
  3. 长帧的跨模组/原生归因（用户已允许），因为固定/移动的 >100ms 尖峰仍有 RV 外来源。

## 5. 证据路径

- 候选源：`build/mask-budget-output/candidates/wallgate/src`
- 固定 A/B：`build/mask-budget-output/05b-wallgate-fixed`、`07-wallgate-p1-fixed`
- 移动 A/B：`build/mask-budget-output/06-wallgate-moving`、`08-wallgate-toggle-moving`
- 工具：`build/mask-budget/run.py`（`--p2` 计划、`--popen` active 窗口）
- 正式：`release/RealisticVisionMod.swf` SHA256 `BD64B5BB…CE4A9AD` 未变
