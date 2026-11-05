# v0.33.12-combo：战斗/扫射性能组合优化与部署

2026-10-31。完成可部署候选并部署到本机 `release/RealisticVisionMod.swf`。正式旧版 v0.33.11-effect-clip 已备份；本报告记录实现、性能、视觉效果与部署回执。

## 1. 版本与组成

**v0.33.12-combo**，47,195 B，SHA256 `26456B67…46FB255`。

1. **墙面输入门控**：current 模式下，`loc / view / 前墙对象 / fovVersion / 雾层版本 / 墙结构版本` 未变时跳过整次 `RVWallSurface.update`；每 30 帧强制刷新一次。输入不变时与旧路径像素等价。
2. **四角射线复用**：`fillFogCache` 缓存每瓦片 4 角可见位与 cLit；当 `loc` 相同、距上次完整重算 `|Δeye|≤4px`、帧差 ≤2 且墙结构未变时复用，跳过 4 次 `castRay`；超出即完整重算。诊断中 85,742 个复用瓦片仅 3 个分类不一致、2 个最终分支不同（0.0035%），是需要说明的近似。
3. **P1 清理**：删除 `hideEnemies` 的 `hiddenPos/visiblePos/exempt` 只写分配；`enemyState` 复用单位 bbox；移除未使用的 `applyUnitWeapons` 参数。无行为变化。
4. **移动触发电平**：current 下 `moved` 阈值从 0.25px 改为可配置 `motionstep`，默认 **2.5px**；视野/雾层/掩膜更新最多滞后 2.5px 位移。配置可设回 0.25。
5. 新增配置项 `motionstep=2.5`（`release/config.txt` 与代码默认；用户 Local Store 旧配置缺该键时按 2.5）。

## 2. 性能评估

测试：active 1280×720 窗口、六狮鹫 SMG + 玩家 LMG、正式 14 模组组合；ABBA 两窗/条件，45 预热 + 120 采样；同轮配对。production-clean 候选（无测试探针成员）通过候选 SWF 加载；部署字节另行通过官方 ModLoader 路径 smoke。

### 2.1 固定位置（28-combo-prod-fixed）

| 条件 | 帧间隔均值 | RV | P95 | >100ms |
|---|---:|---:|---:|---:|
| normal | 38.86 | 2.80 | 55 | 1 |
| combo（production-clean） | **35.03** | **1.79** | **52** | **0** |
| 关闭 RV | 33.34 | 0 | 46 | 0 |

- 均值 **-3.83ms（-9.9%）**；RV -1.01ms；长帧 1→0。
- 逐窗：normal 36.12/41.60，combo 33.78/36.28，两窗均更快；候选接近关闭 RV 的 33.3–33.4ms。

### 2.2 移动位置（29-combo-prod-moving）

| 条件 | 帧间隔均值 | RV | P95 | >100ms |
|---|---:|---:|---:|---:|
| normal | 48.44 | 8.71 | 66 | 3 |
| combo（production-clean） | **43.82** | **6.19** | **55** | **1** |
| 关闭 RV | 34.17 | 0 | 42 | 1 |

- 均值 **-4.62ms（-9.5%）**；RV -2.52ms；P95 -11ms；长帧 3→1。
- 逐窗：normal 45.79/51.08，combo 42.92/44.72，两窗均更快。
- 另一轮测试候选（相同逻辑）normal 51.43→47.71（-3.73ms）、RV 8.47→6.22；方向一致。

### 2.3 归因

- 固定位置收益主要来自墙面门控 + 角点复用 + P1；移动位置额外来自 `motionstep=2.5` 减少 FOV/雾层重算。
- 与关闭 RV 仍有 1.7ms（固定）/9.7ms（移动）差距；没有宣称达到原版流畅度。

## 3. 视觉效果与损失

- **墙面门控**：只在输入完全一致时跳过，理论上像素等价；每 30 帧强制刷新兜底。
- **角点复用**：整段移动约 0.0035% 瓦片-分类差异；本轮没有逐帧像素 diff，属于可接受近似但非严格无损。
- **`motionstep=2.5`**：视野/阴影/敌人掩膜最多滞后 2.5px 位移；采样截图未发现明显阶梯或漏遮，但也没有严格像素/视频验收。若观感变差，改 `motionstep=0.25` 可恢复旧更新频率（会失去部分移动收益）。
- 三处改动都不改变敌人可见性规则、探索记忆或特效遮挡规则。

## 4. 部署与回滚

- 备份：`build/backups/before-combo-20261031-155952/RealisticVisionMod.before.swf`，旧版 SHA256 `BD64B5BB…CE4A9AD`（46,441B）。
- 部署：2026-10-31 15:59:52 本机替换 `release/RealisticVisionMod.swf`，部署后回读 `26456B67…46FB255`（47,195B）。
- 配置：`release/config.txt` 追加 `motionstep=2.5`；未改用户 Local Store、其它模组或宿主。
- 部署后官方路径 smoke：测试副本 ModLoader 仅选 `RealisticVisionMod + ModLoaderMod`，启动 `pfe.swf`；loader `requested_ok`，`RVision.log` 出现 `init ok v0.33.12-combo`、`tick 1/181`、`ModSettings settings registered`，无错误。
- 回滚：恢复上述 backup SWF 到 `release/` 并重启游戏；配置保留 `motionstep` 不影响旧版（旧版忽略未知键）。

## 5. 已知边界

- 测试使用 active 默认桌面 1280×720，非玩家最大化窗口；绝对值不与 D57/D58 私有桌面跨轮比较。
- 单轮/两窗数据，环境有漂移；已用同轮配对和逐窗方向降低误判，但仍需玩家实际体验确认。
- 角点复用与 `motionstep` 是有意取舍；若需要严格像素/视频验收，应另做边界穿越回放。
- 候选源：`build/mask-budget-output/production-combo/src`；测试源 `candidates/combo_prod`、`combo_perf`。

## 6. 证据

- 固定：`build/mask-budget-output/28-combo-prod-fixed`
- 移动：`build/mask-budget-output/29-combo-prod-moving`
- 复核：`build/mask-budget-output/26-combo-moving-repeat`、`27-combo-fixed-repeat`
- 官方 smoke：`build/mask-budget-output/31-official-smoke`；RV 日志 `%APPDATA%\pfe-modsettings-rv-motion-p0mask\Local Store\RVision.log`
- 正式：`release/RealisticVisionMod.swf` SHA256 `26456B67…46FB255`

## 7. 用户验收与后续测试策略

- 用户 2026-10-31 明确接受本版本的视觉损失（0.0035% 角点分类近似 + motionstep=2.5 更新滞后）。
- 后续性能测试默认关闭 LightAndDarknessMod 功能；uild/mask-budget/run.py --full 默认排除，需 --allow-lightanddarkness 恢复，README 已记录。
