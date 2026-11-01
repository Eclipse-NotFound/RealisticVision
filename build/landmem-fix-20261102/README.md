# landmem-fix-20261102 — RV v0.33.17-locmem（房间记忆改按 Location 对象弱键）

修复用户报告的"进入新地图/新楼层后到达的第一个房间整间显示为已探索"。根因与证据见
[报告](../../knowledge/experiments/2026-11-02-land-memory.md)，
部署与回滚见[回执](../../state/deployment-v03317-20261102.md)。

## 内容

| 路径 | 说明 |
|---|---|
| `src/` | 准确生产源：自 `build/fx-fast-20261102/src` 派生，改动仅在 `RealisticVisionMod.as` |
| `build.ps1` | 存根 SWC + airglobal external 的 mxmlc 构建脚本（与 fx-fast 同配方） |
| `out/` | 构建产物与编译日志（不入库，见 `.gitignore`） |

## 改动摘要（仅 RealisticVisionMod.as）

1. `roomMem` / `rangeMem` 由 `Object`（`loc.id` 键）改为 `Dictionary(true)`（Location 弱键）。
2. `resetOff` 重建两个字典；`updateRangeLight` 用 `loc` 键。
3. `resetRoom`：离开存 `roomMem[curLoc]`，进入读 `roomMem[loc]`；恢复成功时每会话记
   `roommem restore loc=… explored=…`。
4. 版本字符串 `v0.33.17-locmem`（官方冒烟 init 行可见）。

## 构建

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
```

产物 `out/RealisticVisionMod.swf`：47,862B，
SHA256 `35243D0F23E3E137546E5BBA54991A5FEE68EB188C46D610BC08293E97489D29`。

> 注意：本机 mxmlc 同源码两次编译字节不同（实测 47,862B/47,861B，SHA 不同，疑为编译器内嵌
> 随机标识）。判产物以同一次构建字节 + 冒烟日志版本串为准，不要用重编译哈希复核源码对应。

## 验证要点

- 官方 ModLoader 隔离副本冒烟：`init ok v0.33.17-locmem settings=ModSettings-v1`、
  `ModSettings settings registered`、tick 1–901、requested==ok、无错误。
- 未做真机自然换层 A/B：需要专用驱动强制 `World.w.game.gotoNextLevel()` 才能在同一会话里
  构造"旧 Land 记忆 → 新 Land 到达房"。当前以 1.02 反编译证据链 + 用户真机确认作为验收分工。
