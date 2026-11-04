# 2026-11-04 B3：CS 对象剔除包装层导致狮鹫手臂漏遮挡——修复与验证

## 一句话

ContinuousScene 的 `SceneObjectCulling` 把 `grafon.visObjs[*]` 的每个子节点包进**单子 Sprite
wrapper**；RV 用 `getQualifiedClassName(层子节点)` 识别 `visualGrifArm`，读到的是
`flash.display::Sprite`，于是**手臂在暗处/记忆区不再被 RV 遮挡**（按原生亮度直绘）。
v0.35.3-armwrap 改为"按内层子节点重新分类、并用内层做中心点采样与遮罩"，已部署。

## 现象与根因

- 关闭 CS（或普通 48×25 房间）：层子节点直挂，`visualGrifArm` 可被识别 → 手臂正常被遮挡。
- 开着 CS 的连续大图：层子节点全被替换成 `Sprite` wrapper，类名判定恒 false →
  `applyWorldVisuals` 的手臂分支永不命中，手臂在任何暗区都完全可见。
- 这不只是"看起来亮"：手臂是**玩家自身**的视觉，原生按整块亮度直绘；RV 的视野语义在
  暗处应把它压到与身体一致，否则手部会从雾里"浮出来"。

## 修复（v0.35.3，键 `arm_wrap_fix`，默认 1）

1. **包装探测**（每 60 帧一次，仅 `sceneLarge` 宿主）：扫描各对象层前 64 个子节点，
   若发现"单子容器里装着 `visualGrifArm`"，置 `armWrapMode=1`；未命中则逐子节点探测
   完全关闭（零额外开销）。
2. **按内层分类**：命中包装模式后，对未判定为手臂的子节点，跳过 `Shape`（RV 自己挂的
   遮罩）后若只剩**唯一非 Shape 子节点**，用它的构造器做缓存键与类名判定。
   —— 这条"跳过 Shape"是必须的：第一版用 `numChildren == 1`，结果 RV 挂上遮罩后
   wrapper 变成 2 个子节点，分类失效 → **遮罩每帧创建/释放交替**（离线夹具把这个
   抖动抓出来了）。
3. **内层生效**：`fxCenterDim` / `fxCenterLit` / `applyWorldVisual` / `applyTransientVisual`
   全部作用在内层手臂上（wrapper 自身坐标为 0，用它会遮错位置）。
4. 缓存以**内层构造器**为键，避免把"是手臂"污染给所有 wrapper。

## 验证

离线夹具 `ClipRowChecks` 同目录的 `ArmWrapChecks`（baseline = v0.35.2，candidate = armfix）：

| # | 断言 | 结果 |
|---|---|---|
| 1 | baseline：直挂手臂在暗处被遮挡（对照） | PASS |
| 2 | baseline：**被包装的手臂不被遮挡（缺陷复现）** | PASS |
| 3 | candidate：直挂手臂仍被遮挡（无回归） | PASS |
| 4 | candidate：**被包装的手臂被遮挡（已修）** | PASS |
| 5 | 遮罩挂在内层手臂上，不是 wrapper | PASS |
| 6 | 普通被包装视觉不被误判为手臂 | PASS |
| 7 | 包装探测真的置位（`armWrapMode=1`） | PASS |
| 8 | 亮区反证：手臂回到亮处后摘除遮罩 | PASS |
| 9 | 连续 3 帧遮罩稳定（无创建/释放抖动） | PASS |
| 10 | 40 帧移动 + 周期改墙拓扑下，`fogCache/currentSight/wallRaw/wallA` 与 v0.35.2 **逐字节相同** | PASS |

合计 **11/11 绿**。

既有 34 项 `CsOptHarness` 拿 v0.35.2 当基线跑：**所有等价性断言全过**，只有 3 条
"针对 v0.35.0 的机制假设"失败（例：断言基线会按代次重新分配 `sightClasses`——v0.35.2
本身已含 W7，故不成立），不是回归。

**运行时实证**（隔离 CS 沙箱，真实 CS 大图）：`RVision.log` 出现
`auto arm wrap detected layer=2 index=18`，`init ok v0.35.3-armwrap`，`err=0`。
⇒ 缺陷在游戏里确实存在（基线版本那 18 号子节点从未被识别），且修复真的命中了。

## 部署

- `release/RealisticVisionMod.swf` = **v0.35.3-armwrap，54,629B，`db8c3ed1…`**
  （上一版 v0.35.2-shadowfix `aea1af3a…`）。
- 备份：`build/backups/before-v0353-armwrap-20261104-202958-aea1af3a/`
  （SWF + release config + store config）。
- 配置：`release/config.txt` 与 `%APPDATA%\pfe\Local Store\RealisticVision_config.txt`
  均写入 `arm_wrap_fix=1`。
- **需重启游戏生效**；回退 = 覆盖备份 SWF，或把 `arm_wrap_fix` 改 0（只关本项）。

## 已知边界

- 只覆盖"单子 wrapper 包一个手臂"的形态；若将来 CS 改成嵌套两层包装或把手合并进
  其它容器，探测会退化为不修复（不回归，仍有原行为）。
- 探测只认 `visualGrifArm` 前缀，与原有识别规则一致；其它手臂类名不受支持（本来也不支持）。
- 未验证：手臂在**部分可见**区域的渐变质量（原设计就是中心点二值，本次未改语义）。
