# D59 其他未检查方向的详细调查

2026-10-30 00:35–00:40。用户要求对其他未检查方向做详细调查，并授权自行启动测试。除已试过的 FOV 节流、敌人身体 mask 阈值、wallgate、跨模组粗排除外，本轮补了 `applyWorldVisuals` 内部归因和更细的跨模组排除。未改主 src/release。

## 0. 方法

- 复用 active 1280×720 探针与 D56 生产源；移动六敌交火；`14-wvdiag-moving` 用带内部计时的诊断候选（行为与 D56 相同，仅加 `getTimer`/计数），120 采样帧。
- 计时是插桩口径，有额外开销，只能用于比较同一函数内部各段占比，不能当完整帧性能。
- 跨模组排除沿用 `12-minus-rconnect`、`13-minus-continuous` 与全组合 baseline `10-dir12-moving`。

## 1. applyWorldVisuals 内部归因（移动，120 帧）

`14-wvdiag-moving` candidate 两窗合计：

| 计数/段 | 数值 | 每帧 |
|---|---:|---:|
| `applyWorldVisuals` 调用 | 165 | 1/帧 |
| `applyWorldVisual` 调用 | 16,419 | **99.5/帧** |
| `loc.firstObj` 链节点 | 21,864 | **132.5/帧** |
| `visObjs` 层子对象检查 | 45,395 | **275/帧** |
| 其中狮鹫手臂命中 | 990 | 6/帧 |
| `refreshMask` 调用 | 16,887 | **102/帧** |
| `applyWorldVisuals` 总耗时 | 757–790ms | 4.6–4.8ms/帧（插桩） |
| 其中逐 visual 调用 | 704–757ms | 4.3–4.6ms/帧（插桩，嵌套在扫描内） |
| 链扫描段 | 668–701ms | 约 4ms/帧（含逐 visual） |
| 层扫描段 | 65–72ms | 约 0.4ms/帧 |
| 单位武器段 | 1–2ms | 约 0.01ms/帧 |
| 清理段 | 16–21ms | 约 0.1ms/帧 |

- **扫描不是主成本**：每帧只遍历约 133 个链节点、275 个层子对象；层扫描约 0.4ms/帧。把链/层改为增量发现，乐观也只省 0.3–0.8ms。
- **逐 visual 工作才是大头**：约 99.5 次/帧，每次 `applyWorldVisual` 都要 `getBounds`、bbox/key、raster 查找、`refreshMask` 和绘制关联；`refreshMask` 约 102 次/帧。
- 因此未检查方向中优先级更高的是 **减少被处理的 world visual 数量**（完全可见特效提前跳过、全暗 blit Part 不再挂 mask），而不是链/层扫描器。

## 2. fillFogCache（最大未处理项）

同一诊断移动窗口：`fillFogCache` 530–543ms / 156 次 = **3.40–3.48ms/次**，156/165 帧调用（约 95% 帧）。这是单项最大 AS3 成本，比 `updateWallSurface`（371–388ms/165 ≈ 2.3ms/帧插桩）和 `applyWorldVisuals`（4.6ms/帧插桩）之外的其它项都大。

可能路线：
1. **降低 FOV/雾更新频率**：已试 0.25→2.5px，RV 降 1.47ms 但完整帧不改善、P95 变差；更高阈值（5–8px）可能提高收益，但阴影边界滞后更明显，需要画质验收。
2. **角点射线复用/脏瓦片**：每瓦片 4 条角射线；移动时全部重算。只有证明“输入量化/边界不变”才能跳过，像素严格等价很难；可先做“上一帧角点可见性相同则复用”的诊断，量化误判和收益。
3. **低分辨率子格/减少混合瓦片 64 次 raycast**：直接降画质，需用户接受。
4. **把雾层更新与 FOV/掩膜分离**：例如掩膜每帧、雾层隔帧；已试墙面隔帧失败，雾层需单独验证。

## 3. 其他未检查方向清单

| 方向 | 代码/证据 | 预估收益 | 视觉风险 | 当前结论 |
|---|---|---|---|---|
| 完全可见特效提前跳过 | `applyWorldVisual` 99.5 次/帧，先 `getBounds`+refreshMask 再判 fullyLit | 可能 0.5–2ms | 需保证 bbox 全在可见区；否则边缘漏遮 | 最值得做；需边界夹具 |
| 全暗 blit Part 解除 mask + 隐藏子位图 | D56 只测过“隐藏子位图但保留 mask”，无收益；解除 mask 是新变量 | 若全暗 Part 占 35 个 mask 的一部分，0.5–3ms | 像素等价（都不可见），需动画/恢复断言 | 可做；先统计全暗占比 |
| 链/层增量发现 | 275 层子对象/132 链节点/帧 | 0.3–0.8ms | 漏发现=漏遮罩 | 收益有限，低优先 |
| 墙面高度扫描版本门控 | `RVWallSurface.update` 每帧 `heightAt` 扫描 | 0.2–0.5ms | 墙体变化漏检 | 像素等价候选，低风险 |
| worldMasks/raster 池化、早退 dispose | bbox 缓存 120 pass、每 60 pass 清理 | 主要影响 GC/长帧，均值小 | 内存/缓存语义 | 需内存/GC 证据 |
| 30 帧兜底整图重建 | 固定位置每 120 帧 4 次全量 FOV | 可能减少周期性尖峰 | 原生光变化漏检 | 需固定位置长窗/尖峰对齐 |
| 跨模组 TDFC/MSW/FirearmAttachments | 尚未单项排除 | 未知 | 无 | 下一步排除矩阵 |
| 音频/窗口/分辨率/Stage3D | 与 RV 无直接关系 | 未知 | 无 | 暂不归 RV |

## 4. 跨模组排除补充

| 组合 | 均值 | RV | 其它监听 | P95 | >100ms |
|---|---:|---:|---:|---:|---:|
| 全组合 normal（10） | 44.76 | 10.59 | 5.02 | 55 | 1 |
| 去掉 RConnect | 44.76 | 10.20 | 4.07 | 53 | 0 |
| 去掉 ContinuousScene | 43.77 | 10.63 | 4.49 | 55 | 0 |

- 两者各只有约 0–1ms/1 个长帧样本的线索；没有复现 D58 的 300ms 其它监听尖峰。
- 最小组合（仅 ModLoader+探针）因复制存档依赖其它模组，`Invent.addLoad #1009` 失败，不能作为干净基线；下一步只能做全组合逐项排除（TDFC、MSW、FirearmAttachments）。

## 5. 建议顺序

1. **完全可见特效提前跳过**：在 `applyWorldVisual` 的 `getBounds` 前后加一个保守的 tile/FOV 守卫，先做边界夹具证明不改变可见像素；这是收益/风险最平衡的新方向。
2. **全暗 blit Part 解除 mask**：从 D56 dark-child 的已验证路径扩展，先统计全暗 Part 占比，再做像素/恢复断言；若占比高，可能直接减少 mask 绘制。
3. **fillFogCache 角点复用/雾层隔帧**：只有前两项不足时再做；需要画质拍板，不能默认开启。
4. **跨模组**：用更长窗口或稀有长帧触发的全组合排除矩阵，优先 TDFC/MSW/FirearmAttachments。

## 6. 证据

- 诊断：`build/mask-budget-output/14-wvdiag-moving/evidence/result.json`（candidate profile 计数）
- 跨模组：`build/mask-budget-output/12-minus-rconnect`、`13-minus-continuous`、`10-dir12-moving`
- 现有候选/报告：`2026-10-29-wallgate-candidate.md`、`2026-10-29-mask-budget-p0.md`、`2026-10-30-three-directions.md`
- 正式：`release/RealisticVisionMod.swf` SHA256 `BD64B5BB…CE4A9AD` 未变
