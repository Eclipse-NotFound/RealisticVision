# C1 弹体 raster 粗格量化：无损等价通过、性能方向不稳定，未部署（附：开火期 FOV 级联归因）

被测技能：remains-mod-build / remains-auto-testing / remains-runtime-debug / remains-release-gate / remains-mod-memory
测试工作区：D:/Program Files/Steam/steamapps/common/Remains
日期：2026-11-02 深夜 – 2026-11-03
方案入口：[boundary-fire-stutter-plan](../../design/boundary-fire-stutter-plan.md) §3 C1（用户指示"按方案执行，先做无损修复"）

# 基线与冻结

- 正式安装 = **v0.34.4-door-smooth**（49,080B / `2d536086…6e711b3f`，2026-11-02 18:49 由并行会话部署）；准确生产源 `build/perf-20261102/src`（=fire-exhaustive-output/fxlib344/src，SHA 133bd236…）。本轮 22:5x 只读核对无变化。
- baseline/candidate 冻结于 `build/boundary-c1-output/{baseline,candidate}/src`（prepare.py 校验 release 指纹后才复制）；候选改动仅 `RealisticVisionMod.as` 两处：新增 `WORLD_RASTER_CELL=2` 常量 + `applyWorldVisual` 瓦片区间量化（x0/y0 向下、x1/y1 向上对齐 2×2 瓦片粗格），版本串 v0.34.5-raster-grid。
- 候选编译 49,071B（基线 49,007B）；探针轮与基准轮候选字节一致（deploy 断言核对）。

# 实现（C1）

`applyWorldVisual` 原按弹体精确瓦片区间生成 `worldMasks` 键——移动弹体每跨瓦片产生新 raster（分配+copyPixels+分类，跨界时再加 blur+Shape）。量化后弹体在粗格内移动时键不变，`refreshMask` 的 `(fovVersion, 签名)` 早退跨帧生效，同弹道连续弹丸共享 raster。语义无损论证：同一视野场采样、外框只增不减、模糊半径仍被 MASK_PAD 包含、填充矩阵锚点始终瓦片对齐。

# 图像等价（checks-02，通过）

探针 `BoundaryC1ProbeMod`：同进程加载 baseline/candidate 双实例，真实 Bullet/SmartBullet/PhisBullet 经生产 dispatch，人工视野场（亮 x<300/暗 x≥300）：

- **A/A 对照**（同版本两次应用）严格相等后才开始对比；
- 场景 A 静态 6 位置 × current/classic × 4/8 子格：**逐像素严格相等**（BitmapData.compare==0）+ 语义计数（跨界亮侧保留 >100px、暗侧恒 0、深暗隐藏）；
- 场景 B 位移扫掠 250→460 每 2px（含每 40px 交错 fovVersion++ 失效）：每步严格相等；**阳性对照：raster 集合 baseline 12 → candidate 6**（量化实际生效）；
- 场景 C 持续绑定 60 步 × 3 弹类（几何逐帧交替）：逐步严格相等；
- 场景 D 直接 `applyWorldVisual(dynamicBounds=false)`（手臂/长枪路径）4 位置：严格相等。
- 合计 **623 项全过**；证据 `build/boundary-c1-output/checks-02/`（含 4 张代表 PNG）；登记 92e70ed… 通过。

# 性能 A/B（fire-exhaustive 链，CombatRenderProbe，LMG+6 敌固定站位，718 间隔/版本，benchmark-eligible）

rv=每帧 RV onFrameInner 耗时（插桩同施于三版本）。rv( incumbent 复本 vector )兼作同字节 A/A 参照。

|轮次|顺序|场景|incumbent normal|incumbent vector(A/A)|candidate C1|
|---|---|---|---|---|---|
|c1grid-01c|正序|轻载（rv≈3ms）|36.73 / rv 3.30|35.98 / rv 3.22|**35.96 / rv 2.89**|
|c1grid-02|反序|重载（rv≈14-17ms）|49.61 / rv 13.61|49.82 / rv 15.08|**53.28 / rv 16.79**|
|c1grid-diag-01|正序|轻载（rv≈1-2ms）|39.57 / rv 1.90|39.54 / rv 1.29|**39.96 / rv 1.14**|
|c1grid-diag-02|正序|轻载（rv≈1-2ms）|34.29 / rv 2.36|33.95 / rv 1.46|**33.66 / rv 1.36**|

（diag 两轮带额外计数/眼点采样插桩，计时仅供参考，不计入收益判定。）

- 轻载轮候选 rv −10%~−40%、逐窗 3/4 相邻对有利（01c：refreshMask 345→200ms/窗、调用 3778→3606）；重载轮反向（rv +1.7~+3.2ms、refreshMask 调用 3858→3852 **未降**、单位成本 +22%——量化栅格更大在持续失效下纯亏）。
- 整帧方向随轮翻转、无稳定收益 → **不满足稳定收益纪律（KB-000123 r5），C1 不部署**。

# 关键归因发现：开火期 FOV 级联是 RV 重载场景的主导成本

逐窗插桩（profile：calls/ms 每窗合计）揭示重载轮的真实结构（c1grid-02，450 帧/窗）：

- **computeFov 246~343 次/窗 ≈ 每 1.3~1.8 帧一次全量 FOV 重算**（固定站位、无移动）；轻载轮仅 6~27 次。三版本（含未改动的 incumbent 复本）同样出现 → **世界驱动，与 C1 无关**。
- 级联单价：computeFov ≈0.6ms + **fillFogCache ≈11.9ms/次** + applyVision 雾显示重绘 + updateWallSurface ≈3.2ms + 全部 raster/敌人掩膜失效重算 → 重载轮 rv≈15ms/帧中 **fillFogCache+applyVision+updateWallSurface 合计 ≈13ms 占绝对主导**；弹体 refreshMask+applyWorldVisual 合计仅 ≈0.9ms。
- 诊断轮 c1grid-diag-01（cfgAutoTest 计数）：needFov 原因分解 **h（透明度/结构变化）仅 1~5 次/窗**，f（90 帧兜底）5 次/窗。
- **眼点轨迹（c1grid-diag-02，逐帧 playerVisionEye 采样）**：固定站位稳态下**眼点完全静止**（360 帧零位移、m=0）——排除"射击动画/瞄准追踪带动眼点"假设；窗 0 的 m=32 为初始落位。
- **对重载轮 c1grid-02 复核 positions**：**玩家身体位移帧 235~359/360，与 computeFov 198~366 逐窗一一对应**——churn 源是**交战中被击退/踉跄造成的真实位移**（371~397 敌方射击命中玩家的 staggers），眼点随身体移动触发全量级联。
- 结论：**FOV 级联由战斗位移驱动**（非动画抖动）：开火/交战 → 承受命中 → 小幅持续位移 → 每 ≥4px 一次 computeFov+fillFogCache(≈11.9ms)+雾重绘+墙体重建+全部遮罩失效。用户症状"有正在渲染的阴影边界时开火卡顿"的机制：边界在屏时失效重建量最大；开阔地同样付 fillFogCache 成本但遮罩重建少，主观更轻。**症状二（敌人活动卡顿、敌数无关、不稳定复现）同源**：敌命中→玩家位移→级联，是否卡顿取决于敌方是否持续命中（几何/掩体依赖）。
- C1 失败原因也由此定位：FOV 级联使 raster 缓存每 1~2 帧全失效，粗格复用无从积累；失效重算时更大的量化栅格反而 +22% 成本。轻载轮（churn 少）复用才兑现。

# 眼点轨迹（c1grid-diag-02）

逐帧采样活动实例 `playerVisionEye`（诊断插桩，不用于计时排名）：

- 稳态窗（1~5）：**眼点零位移**（span=0.0/0.0，m=0）——射击动画与瞄准追踪在本场景不动眼点；h=1~5、f=5。
- 窗 0（初始落位）：m=32、眼点漂移收敛（|live−computed| p95=1.15px、max=4.23px）。
- 复核重载轮 c1grid-02 的 body 轨迹：ggMoved 235~359/360 ↔ computeFov 198~366 逐窗对应（见上节）。

# 结论与下一步

1. **C1 不部署**：图像无损成立，但性能方向随场景相位翻转（轻载相位 −10%~−40% rv、重载相位 +22% refreshMask 单位成本），重载相位回退。候选源与全部证据保留（`build/boundary-c1-output/`、fire-exhaustive-output/c1grid*），若 FOV 级联被摊薄（raster 失效频率下降）可重估。
2. **新的第一优先：摊薄战斗位移触发的 FOV 级联**（fillFogCache ≈11.9ms/次 × 每 1~2 帧）。候选方向（需独立验证轮）：
   - 小位移增量化/区域受限重算：小 Δeye 下远场可见性大多不变——但普查 D51（射线空隙）同类尝试无稳定整帧收益，且 v0.34.3 明确收紧了跨起点角点复用（旧墙角阴影回归风险），不可直接回退；
   - 位移幅度分档：Δeye<8px 的战斗位移按 2~3 帧节奏重算（staleness 上限 ~2px/帧额外，与现有 4px 阈值同量级）——涉及眼点跟随语义，**需用户拍板**；
   - fillFogCache 本身的常数削减（射线批处理/早退）——历史上多个微优化无稳定收益，预期有限。
   该方向同时解释并可能缓解症状二（敌人活动卡顿），是两条症状的公共主因候选。
3. 弹体路径逐帧软遮罩（v0.34.3 语义）暂不动；C2/C3（弹体节流/降模糊）在级联摊薄前预计被淹没，暂缓。

# 工具与登记

- 工具 `build/boundary-c1-20261103/`（prepare/probe/smoke/deploy/windows/profiles/gen_*）；跑批坑：SavedFireProbe.as 须指 `build/fire-exhaustive/`（输出目录无副本）；`PYTHONUTF8=1` 必设（模板 runner 裸 read_text 走 GBK）；PYTHONPATH 需含 `build/composite-followup`（cpu_sampler）。
- 登记：checks-02 通过（game-coexist）；c1grid-01（SavedFireProbe 缺失）/c1grid-01b（GBK 解码）两次失败保留；c1grid-01c/02、diag-01/02 通过（benchmark-eligible）。
- 本轮**未改** release/config/src；正式安装仍 v0.34.4-door-smooth。

## 2026-11-03 独立复核更正（保留上文原实验记录）

新的[复核报告](2026-11-03-boundary-audit.md)重新读取本轮原始数据、测试驱动与生产快照，发现上文归因超出了证据：驱动直接 new 实例而未走配置加载，实际初值为 8 子格，安装模板解析后为 4；profile 含 90 帧预热共 450 帧，位置只有 360 帧；371–397 是敌方发射下界，不是命中/击退次数。轻重轮布局、出生位置及原生单位数不同，重载六窗部分可见敌人全为 0；同源对照的两份 SWF 也非同字节。

623 项图像通过和 C1 未部署状态保留；重载轮以同一 450 帧分母重算，applyVision+updateWallSurface 占 RV 耗时 81.9%–87.1%，但 fillFogCache 已含在 applyVision 内，不能重复相加。位移伴随高频重算是线索；“命中造成共同主因”“全量级联已唯一归因”“粗格导致全部性能差值”降级为待控制实验验证。diag-02 眼点静止只适用于所采窗口。

后续以[修订方案](../../design/boundary-fire-stutter-plan.md)为准：先对齐正式配置，再分离边界在屏/弹道跨界、固定眼点/命中位移、敌人不开火活动/开火。旧优先降频建议撤回；30fps 下 2–3 帧约 67–100ms，额外空间误差未经证明。此次为离线复核，没有新增游戏测试、候选或部署。
