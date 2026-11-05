# D59-P0：六类遮罩归因与移动态 RV 成本（active 窗口实测）

2026-10-29 20:00–20:48。用户批准 P0 后，在 `build/mask-budget` 探针上完成固定位置/移动两套六类遮罩归因。正式安装仍为 D56 `v0.33.11-effect-clip`，主 `src/`、`release/`、config、玩家数据未改。本报告是归因证据，不是候选或部署依据。

## 0. 方法与边界

- 探针：D58 `SavedFireProbe` 的扩展版；plan 为 16 窗 ABBA：`off, normal, unit, hpbar, weapon, arm, bullet, part, part, bullet, arm, weapon, hpbar, unit, normal, off`。
- 每窗 45 帧预热 + 120 帧采样（`--short`），每类 2 窗、238 个完整间隔；同一 AIR 进程内连续切换变体，`windowActive=true`。
- 场地：`random_mane / loc1_3`，48×25，六个狮鹫 SMG + 玩家原生 LMG，移除随机原生单位；六敌按固定位置生成并持续开火。
- 正式 14 模组组合；D56 生产源逐字节校验；探针、RV、vector 均编译通过。
- **显示环境**：默认桌面上的 1280×720 active 窗口（`--onscreen --small-window --activate`），不是 D58 的 2560×1521 私有桌面。因此绝对耗时不能与 D57/D58 直接比较，只能做同一进程/同一轮的相对对照。
- 同轮 `afterProbe` 包含绘制、调度和下一次原生步骤前的等待，不是 GPU 独占耗时；RV 调用是 AS3 开销。`performanceEligible=true` 只代表端点资源政策和其它 AIR 检查通过，不保证其它会话/后台负载全程空闲。
- 变体的语义：`*-nodraw` 仅撤掉该类 RV mask，目标仍保持在显示树中并恢复 cache；这是**归因**，不是画质方案。部分目标会因此在本应被遮的位置露出，不能用于发布。

## 1. 固定位置结果（每类 2 窗，119 间隔/窗）

| 变体 | 帧间隔均值 | RV 调用 | 绘制后 | P95 | >100ms |
|---|---:|---:|---:|---:|---:|
| off | 38.80 | 0.00 | 25.29 | 57 | 4 |
| normal | 51.29 | 3.72 | 32.82 | 69 | 4 |
| unit-nodraw | 47.93 | 3.96 | 29.74 | 68 | 3 |
| hpbar-nodraw | 48.13 | 3.90 | 30.72 | 67 | 2 |
| weapon-nodraw | 49.90 | 3.69 | 31.94 | 65 | 4 |
| arm-nodraw | 49.00 | 3.70 | 31.41 | 64 | 3 |
| bullet-nodraw | 49.94 | 3.78 | 32.06 | 73 | 3 |
| part-nodraw | 49.79 | 3.86 | 30.74 | 76 | 4 |

逐窗方向（与相邻 normal 窗配对）：

| 类别 | 第 1 窗 Δms | 第 2 窗 Δms | 方向 |
|---|---:|---:|---|
| unit | -4.44 | -2.28 | 两窗均更快 |
| hpbar | -5.79 | -0.53 | 两窗均更快但幅度差大 |
| weapon | -4.12 | +1.35 | 不一致 |
| arm | -3.86 | -0.71 | 两窗略快 |
| bullet | -1.29 | -1.42 | 两窗略快 |
| part | -9.09 | +6.09 | 明显不一致 |

## 2. 移动态结果（每类 2 窗，119 间隔/窗）

| 变体 | 帧间隔均值 | RV 调用 | 绘制后 | P95 | >100ms |
|---|---:|---:|---:|---:|---:|
| off | 34.72 | 0.00 | 21.75 | 47 | 0 |
| normal | 49.97 | 8.20 | 29.11 | 63 | 2 |
| unit-nodraw | 46.42 | 7.47 | 26.15 | 59 | 0 |
| hpbar-nodraw | 48.41 | 7.71 | 28.46 | 63 | 3 |
| weapon-nodraw | 50.84 | 8.15 | 29.15 | 65 | 2 |
| arm-nodraw | 51.52 | 7.98 | 29.53 | 66 | 1 |
| bullet-nodraw | 52.93 | 8.07 | 30.13 | 68 | 2 |
| part-nodraw | 45.51 | 7.90 | 24.44 | 58 | 1 |

逐窗方向：

| 类别 | 第 1 窗 Δms | 第 2 窗 Δms | 方向 |
|---|---:|---:|---|
| unit | -1.87 | -5.24 | 两窗均更快 |
| hpbar | +1.13 | -4.25 | 不一致 |
| weapon | +3.88 | -2.13 | 不一致 |
| arm | +4.76 | -1.67 | 不一致 |
| bullet | +7.09 | -1.17 | 不一致 |
| part | +0.38 | -9.30 | 不一致 |

## 3. mask 数量与类型（fixed normal，120 采样帧）

- 每帧可见 mask 均值 **126.8**，最大 158；`off` 为 0。
- 单类撤罩计数（该行各窗均值）：unit 6、hpbar 6、weapon 6、arm 6、bullet 2.4–2.6、**part 35–36.5**。
- 窗口末 mask 类型清单（`maskInventory.types`，约 59 个实际挂载）：
  - `hpBar` 6、`vissmg10` 6、`visualGrifArm1` 6；
  - `flash.display::MovieClip` 23–24（探针无法细分到具体原生类，主要是 blit Part 根）；
  - `visualGilza` 12–13、`visReplic` 3、`visualBullet` 1–2。
- 原生对动态对象没有逐对象 mask/cache（`game-reference` 1.02 已核对）；这些 mask 全部由 RV 引入。

## 3.5 移动态分函数 profile（D56，active，插桩）

另跑 1 窗 `normal` 单例（`04-moving-profile`，120 采样帧，插桩有开销，只作归因）：

| 函数 | 总 ms/120 帧 | 每帧/每次 | 说明 |
|---|---:|---:|---|
| `updateWallSurface` | 450 | **2.73ms/帧** | 移动态最大单项 |
| `applyVision` | 465 | 2.82ms/帧 | 其中 `fillFogCache` 336/99 = **3.39ms/次**，99/120 帧调用 |
| `hideEnemies` | 365 | 2.21ms/帧 | 其中 `applyWorldVisuals` 305/165 = 1.85ms/帧；`refreshMask` 140/165 = 0.85ms/帧；`applyMask` 0.22ms/帧 |
| `computeFov` | 46 | 0.46ms/次 | 99 次 |
| `prepareOcclusion` | 16 | 0.10ms/帧 | |
| `refreshWallField` | 17 | 0.10ms/帧 | |

调用计数：`refreshMask` **86.9 次/帧**、`applyWorldVisual` 96.7 次/帧、`applyMask` 6 次/帧。总 RV 约 8.0ms/帧（与未插桩 8.2ms 接近）。

**含义**：移动态 RV 的大头是墙面合成（2.73ms）和雾层更新（2.03ms 平均），不是掩膜内容刷新（0.85ms）。因此“掩膜刷新节流”最多只能省其中一部分（按一半估计 <0.5ms），无法满足用户“只在有明显性能收益时才接受软边滞后”的条件；**P2.1 不应作为主方案**。下一步应优先做像素等价的 `updateWallSurface` 增量/复用与 `fillFogCache` 脏区，其次才是 `applyWorldVisuals` 的链/层扫描与 raster 分类合并。

## 4. 结论

1. **移动态 RV 成本显著高于固定位置**：同一 active 窗口，`normal` 的 RV 从 3.72ms 升到 **8.20ms**；帧间隔从 51.29 到 49.97ms（同轮 off 也不同，不能跨轮比较）。这与 D41/D44 的方向一致，确认近三轮固定位置协议低估了移动交战。
2. **只有“敌人身体遮罩”在固定/移动两套里都方向一致**：撤掉 6 个 unit body mask，固定 -3.36ms、移动 -3.55ms（4/4 窗更快）。说明这 6 个动画身体的 mask+cache 渲染成本高于数量更多的 Part mask。
3. **Part mask 数量最多（约 35/帧），但耗时证据不一致**：固定 -1.5ms（两窗 -9.09/+6.09），移动 -4.46ms（两窗 +0.38/-9.30）。不能据此宣布 Part 是主因，也不能据此设计新裁切；需要更多窗或更稳的环境。
4. **hpbar/weapon/arm/bullet 的幅度小于窗间漂移**，本轮不能排序；`bullet-nodraw` 移动第二轮甚至更慢，属于噪声或该轮背景负载。
5. **撤任何一类 mask 都没有降低 RV 的 AS3 调用时间**（RV 仍在 3.7–4.4ms/7.5–8.6ms 区间），主要变化在 `afterProbe` 绘制段。分函数 profile 进一步显示：移动态最大单项是 `updateWallSurface` 2.73ms/帧、`fillFogCache` 3.39ms/次（99/120 帧），而 `refreshMask` 只有 0.85ms/帧。**掩膜刷新节流不是主收益**；这与“mask 关联/cache 的绘制成本，而非 refreshMask 的几何计算”一致。
6. 本轮 active 默认桌面与 D58 私有桌面不同，且只有 2 窗/类；以上只能算**方向性归因**，不能作为最终性能验收。表格中的 P95/最大值受窗口/后台影响，未排除全部噪声。

## 5. 对下一步的含义

- **P2（移动态）仍是主收益方向**：profile 已显示 `updateWallSurface` 2.73ms/帧、`fillFogCache` 3.39ms/次（约 2.03ms/帧平均）是最大两项；下一步优先做**像素等价**的 `updateWallSurface` 增量/复用，再做 `fillFogCache` 脏区。掩膜刷新节流（P2.1）只有 ≤0.5ms 上限，不满足“明显收益”条件，暂不做。
- **P3 的结构性目标应优先看敌人身体 mask**，而不是数量最多的 Part：但软边敌人遮罩是画质核心，硬边/缺席不可接受；可行方向是“按目标分类避免不必要 mask”“减少 cache 重绘”“只在真正跨边界时挂 mask”，必须像素/截图验证。
- 用户已选择“特效遮挡保持现状”，因此 Part/Bullet 的“不遮/硬边/仅全黑”不推进；只能做像素等价的掩膜关联/分配优化。
- 本轮未改模组本体；探针、六类变体、fixed/moving 两套数据保留在 `build/mask-budget` 与 `build/mask-budget-output/{02-fixed-active,03-moving-active}`。脚本收尾返回码 1（收尾环境/登记断言），但两轮均 `D58 COMPLETE` 且证据文件完整；不作为发布证据。

## 6. 证据路径

- 固定：`build/mask-budget-output/02-fixed-active/evidence/result.json`、`analysis.json`
- 移动：`build/mask-budget-output/03-moving-active/evidence/result.json`、`analysis.json`
- 移动 profile：`build/mask-budget-output/04-moving-profile/evidence/result.json`（插桩，仅归因）
- 工具：`build/mask-budget/`（探针、运行器、`--moving`/六类变体）
- 正式：`release/RealisticVisionMod.swf` SHA256 `BD64B5BB…CE4A9AD` 未变
