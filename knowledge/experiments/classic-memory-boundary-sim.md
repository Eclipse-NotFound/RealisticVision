# 实验：classic 记忆区边界子格化逻辑离线验证（v0.17.5）

日期：2026-08-17

## 背景

classic 记忆区（扫过但未覆盖）边界 v0.17.4 仍有三处问题（用户反馈"边界显示仍有
问题"）：
1. 全暗已探索瓦片整块填 166（40px 阶梯）——v0.17.3 的子格化在 v0.17.4 重写中
   回归丢失；
2. 边界带亮子格亮度取 `tile.visi`——游戏 visi 只升不降、记忆区瓦片恒为 1，
   窥光子格渲染成 alpha 0 全亮（记忆区边缘亮边）；
3. seenSub 只标记 fov==NONE 边界瓦片，可见瓦片不标记——扫过区变记忆后未标记
   子格显示黑（黑斑/黑洞）。

## 修复（src/RealisticVisionMod.as）

- `fillMemoryTile(tx,ty,dimA)`：记忆区/未探索统一按子格"曾见"历史填充
  （曾见→dimA，从未见→黑），带整块快路径（全见→fillRect(dimA)、
  全未见→fillRect(黑)）——classic/current 共用；
- `markSeenByDist`：classic 可见瓦片（fov!=NONE）按当前视野半径 lDist2 逐子格
  距离标记曾见（无 raycast）——记忆区按真实扫过范围子格化；
- classic 边界带亮度改用本子格实际光线 `lit×距离衰减`（下限 dimF），不再用
  游戏 visi；
- 标记完整性：`recalcTile`（含 doorView 分支）与 corner 采样对已探索瓦片同样
  标记；`fillLitTile` 整块标记；`fillWallClassic` 补标记；
- 边界带/`recalcTile` 暗子格分支去掉瓦片级 `explored` 兜底（标记完整后
  seenSub 即充分）。

## 验证（Node 模拟，临时目录 rv_memory_sim.js）

复刻 castRay(DDA)/computeFov/4 角采样/markSeenByDist/边界带 8×8/fillMemoryTile，
24×24 瓦片 + 多块墙体，玩家在左半区小范围活动后离开：

- ① 记忆区无黑洞：真值（任意路径位置距离≤lDist2 且 LOS 通透的子格）15378 个，
  标记遗漏 = 0（PASS）；
- ② 边界瓦片为子格粒度：FULL=456 / MIXED=30 / EMPTY=90——30 个部分曾见瓦片
  按 5px 子格填充（PASS）；
- ③ 离开后（全 cLit==0）记忆区填充与子格历史逐格一致（PASS）。

注：over（按距离过标）为预期行为——classic 可见瓦片显示是 40px 均匀的，按距离
标记与显示一致（墙后部分在可见时同样被均匀显示）。

## 结论

修复逻辑经离线模拟验证成立；需游戏内实测确认观感（记忆区边界 5px 平滑、无亮边、
无黑斑）。
