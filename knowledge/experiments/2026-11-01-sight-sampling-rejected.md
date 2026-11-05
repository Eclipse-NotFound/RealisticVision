# D62 combo_v5 sight 采样方案（否决）

2026-11-01。尝试在 refreshMask 的 early-return 加入 currentSight 采样判断（24 个采样点），跳过内容未变帧的掩膜刷新。

## 实现

- `sampleSightContent()`：在 applyVision→fillFogCache 后采样 currentSight 24 个分散像素，与上一帧比较；全部相同则设 `sightContentSame=true`。
- refreshMask 条件扩展：`(lastFov==fovVersion || (sightContentSame && m2e!=null)) && lastBb==sig` → 跳过。
- 首版在新 raster 上崩溃（m2e=null 时跳过 refreshMask → coverage 扫描访问 null），加 `m2e!=null` 安全检查后修复。

## A/B 结果（移动，active 1280×720 六敌）

| 指标 | v0.33.15 normal | combo_v5 candidate | 差值 |
|---|---:|---:|---:|
| RV | 7.22ms | **6.39ms** | **-12%** |
| 帧间隔 | 44.34ms | 46.04ms | **+1.70ms（更差）** |

## 否决理由

1. RV 确实降 12%，但整帧反而 +1.7ms——非 RV 时间增加 2.5ms，可能是采样引起间接渲染变化或背景噪声。
2. 24 点采样是近似：有小概率漏检 currentSight 的实际变化，导致掩膜滞后（视觉影响，违反"优先零视觉影响"要求）。
3. 收益/风险比不理想：即使在最好情况下（RV -0.83ms），帧间隔也可能不改善。

## 结论

不合并、不部署。正式保持 v0.33.15-combo-v4。源码保留在 `build/mask-budget-output/candidates/combo_v5/src`。

## 当前零影响优化已达边际

v0.33.15 RV 约 3.6ms（移动）/1.2ms（固定），与关闭 RV 差距约 3.3ms/1.6ms。进一步降低需要：
- 减少被遮掩的弹体/特效数量（视觉影响）
- 更激进的 FOV 节流（视觉影响）
- 弹体遮罩结构重构（大工程）
