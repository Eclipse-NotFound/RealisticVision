# D59 建议方向执行：完全可见特效快路径与全暗 Part 解除 mask（未采用）

2026-10-30 02:20 起。按上一轮建议实现两个像素风险最低的候选，并用 active 1280×720 六敌场景做固定/移动 A/B。**未改主 src/release/config，未部署**；正式仍 D56 `BD64B5BB…CE4A9AD`。

## 1. 候选

源：`build/mask-budget-output/candidates/visfast/src`、`fulldark/src`（均由 D56 准确生产源复制）。

- **visfast（完全可见特效快路径）**：`applyWorldVisual` 在取得这个 bbox 的 `worldMasks` raster 后，若 `raster.coverageFov===fovVersion` 且 `raster.fullyLit`，直接释放旧记录并返回，不调用 `refreshMask`；若 `fullyDark` 且已有空 mask 关联，也直接返回。严格保持“完全可见/完全不可见”已有分类，不新增像素判断。
- **fulldark（全暗 blit Part 解除 mask）**：对 `fe.graph::Part` 且只有单个 Bitmap 子节点、无滤镜的目标，在 fullyDark 时隐藏该 Bitmap 子节点、解除 RV mask/cache，根 `visible`/动画/寿命不改；恢复时先还原子节点，再走原 mask 路径。基于 D56 已验证的 dark-child 路径，新增“解除 mask”变量。

## 2. 固定位置 A/B（15-visfast-fulldark-fixed）

| 条件 | 帧间隔均值 | RV | P95 | >100 |
|---|---:|---:|---:|---:|
| normal | 43.72 | 3.14 | 59 | 3 |
| visfast | 47.61 | 3.47 | 63 | 2 |
| fulldark | 49.30 | 4.54 | 68 | 5 |

逐窗显示明显漂移（normal 两窗 47.14/40.30ms，candidate 50.42/44.81，fulldark 45.08/53.52），但两个候选在对应窗口都未显示稳定收益，fulldark 第二窗明显更慢（+13ms）。

## 3. 移动位置 A/B（16-visfast-fulldark-moving）

| 条件 | 帧间隔均值 | RV | P95 | >100 |
|---|---:|---:|---:|---:|
| normal | 46.18 | 7.42 | 59 | 1 |
| visfast | 47.68 | 7.95 | 62 | 3 |
| fulldark | 48.53 | 8.40 | 68 | 1 |

visfast 出现一次 RV 148ms 异常（>100），fulldark RV 升高约 1ms；两者均值均比 normal 慢约 1.5–2.4ms。**不支持任何收益结论**。

## 4. 视觉效果

- 两个候选的固定/移动截图（`15-.../evidence/scene-*.png`、`16-.../evidence/scene-*.png`）目检未发现明显差异；但截图不是逐帧像素对照，随机 AI/粒子/HUD 也会不同。
- visfast 理论上只跳过已有 fullyLit/fullyDark 分类，像素等价；fulldark 理论上只把“空 mask 隐藏”改成“子位图隐藏”，也应像素等价。两者都缺少正式恢复/动画断言，不能作为发布证据。
- 没有观察到“全暗敌人/特效漏出”的迹象；但本轮没有专门构造边界穿越和恢复场景。

## 5. 结论

- 两个候选都没有性能收益：固定 +3.9/+5.6ms，移动 +1.5/+2.4ms（同轮配对，环境漂移大，但方向均不利）。
- 可能原因：fullyLit raster 在交火特效中占比不高，快路径命中有限；fulldark 的 mask 解除/恢复在明暗边界反复切换时造成缓存失效，反而更慢。
- **未合并、未部署**。这两个方向作为“像素等价候选”已被本轮否证；继续投入同一路线收益低。

## 6. 剩余最大项与下一步

- `fillFogCache` 仍是最大单项（3.40–3.48ms/次，移动时约 95% 帧调用）；任何不降低频率的候选都需要角点射线复用/脏瓦片，尚无严格等价实现。
- 下一步应优先：
  1. **fillFogCache 的角点复用诊断**：先只统计“上一帧角点可见性相同”的瓦片比例和误判，不直接发布；
  2. **跨模组长窗排除矩阵**（TDFC/MSW/FirearmAttachments），用更长窗口或稀有长帧触发；
  3. 若必须拿到更大帧收益，需要用户明确接受雾层/阴影更新频率或子格精度的画质取舍。
- 两侧候选源与失败数据保留；不重跑旧目录。

## 7. 证据

- 固定：`build/mask-budget-output/15-visfast-fulldark-fixed`（含 scene-*.png）
- 移动：`build/mask-budget-output/16-visfast-fulldark-moving`（含 scene-*.png）
- 候选源：`build/mask-budget-output/candidates/visfast/src`、`fulldark/src`
- 正式：`release/RealisticVisionMod.swf` SHA256 `BD64B5BB…CE4A9AD` 未变
