# current 跑动与像素边界调查夹具

本目录包含 2026-09-20 调查工具与 v0.29.0 候选验证。测试只在 build/motion-test-output 生成临时源码/SWF，不改 src/release。历史变体固定读取 `37c25ba` 的 v0.28.2 源码，避免候选修改后旧锚点失效；`soft-medium` / `soft-wide` 使用当前源码，后者仅把地板滤镜从 4/q3 改成 6/q3。

候选验证（在模组目录依次执行）：

```powershell
node build/motion-tests/run.mjs soft-medium --checks --assert
node build/motion-tests/run.mjs soft-medium --assert
node build/motion-tests/run.mjs soft-wide --assert
node build/motion-tests/run-game.mjs soft-medium
node build/motion-tests/run-game.mjs soft-wide
node build/motion-tests/bench-game.mjs --soft
```

`SoftHarness` 验证淡入显示、柔化与记忆/单位可见性分离、已知墙几何后的错误历史、1000 条门水/越界射线、短视距、动态遮光、破墙、单位掩膜、换房与切模式。`bench --soft` 的六例交替写 `bench-soft-*`，不覆盖旧调查。性能仍是模组固定步回放成本，不是真实战斗 FPS；最终候选两次适中复测之一有 67ms 峰值。

归档脚本 `soft-evidence.py` 读取上述结果及墙回归、测试构建，写 `knowledge/experiments/current-soft-v0290`，拒绝覆盖已有归档。地板允许受限柔化带，不再把几何边界外所有非黑像素都判为错误；原墙黑芯、逻辑遮挡、原版记录仍有独立断言。旧 `analyze.py` / `make-evidence.py` 保留为历史调查入口，不应覆盖旧证据。

在 RealisticVision 目录运行：

```powershell
node build/motion-tests/run.mjs baseline --assert
node build/motion-tests/matrix.mjs baseline profile gate1 immediate fast-rays fast-sync no-clamp hires coverage corner-history
node build/motion-tests/matrix.mjs --game baseline profile fast-rays fast-sync hires coverage corner-history
node build/motion-tests/bench-game.mjs
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/motion-tests/analyze.py
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/motion-tests/make-evidence.py
```

- 第一条是可重复红信号：实际 onFrameInner 连续 60 帧移动，显示连续停留超过一帧即失败；当前正式源码预期返回 1。`MOTION GREEN` 仅指时间连续性，不代表抗锯齿或整体发布通过。
- 编译使用 `debug=false optimize=true`，仅保留结果 trace。普通沙箱可能阻断 AIR 导致空日志/超时，使用工具级审核启动独立实例，不能用没有输出判算法失败。
- 小夹具 24×18 单墙角，4px/步，预热40帧再移动60帧；真实源码方法，游戏类型用可控存根。完整场景正常 newGame→beginMission("rbl")→gotoLoc(2)，48×25，预热40帧、移动90帧，每步4px，正常 onFrameInner 调度。
- 完整场景暂停世界物理、按固定位置输入回放；测量模组处理，不是游戏FPS。舞台目标30Hz来自真实 stage.frameRate。无敌人运动/战斗，不改变原版 visi/t_visi，执行后恢复单位显示。
- 完整游戏共享 build/motion-test-output/game，**run-game、bench-game 必须顺序**；测量性能时其他测试也顺序。资源副本与独立 app id 隔离真实用户存档。
- `run-game`含逐帧取图，适合几何对照，分配/缓存扰动会影响后续调用计时。**性能结论优先 bench-game**：同进程、同输入、首尾交替、没有PNG编码/场景取图，仍包含位图比较及可能的GC噪声。
- bench-game 依赖 run-game 已准备好的公共资源副本与引导器；11个案例分别归档 bench-*/motion.json。入口包含所有必要等待和150秒上限。应用id为 rv-motion-game-bench；单案例为 rv-motion-game-<variant>。
- 首次 bench 的 AIR 运行完整成功，Node解析因额外 CR 报错；已修 trimEnd，从原日志恢复11个CASE。不是第二次运行成功，不增加实测次数。
- `make-evidence.py`拒绝覆盖已归档指纹；后续实验另设日期目录。分析器会核对完整房间输入一致，缓存版本24帧与基线逐像素一致。不要把 `fovVersion` 变化数当视野重算次数（墙的单位掩膜也会递增）；以 rays>0 统计重算。

| 变体 | 单一改变或组合 | 用途 |
|---|---|---|
| baseline | 仅改访问权限，保留方法体 | 正式算法基线 |
| profile | 粗阶段计时/射线计数 | 定位成本；不对每条射线计时 |
| gate1 | 每帧算FOV，显示条件不变 | 反例：持续移动时显示任务饿死 |
| immediate | 原频率，同帧显示 | 分离显示延迟与三帧节流 |
| fast-rays | 每次FOV前平铺遮光值，DDA读取缓存 | 测重复 getTile/tileOpac 成本 |
| fast-sync | fast-rays + 每帧FOV + 同帧显示 | 时间连续性实验 |
| no-clamp | 不把模糊结果压回原始硬边 | 在旧的严格黑区条件下失败；不等于D25分层柔化候选 |
| hires | 16×16子格，保持世界模糊尺度/边框 | 全图加密成本与台阶对照 |
| coverage | 边界子格四点积分，其他保持 | 负结果：更贵、改善小 |
| corner-history | 四角历史写到0/7而非0/1 | 修正错误曾见记录的独立验证 |

缓存原型尚缺玩家越界/换房/破墙/开门/水变化回归；每次FOV重建缓存保证本场景输入一致，不是可直接投产的长期缓存策略。coverage 保留二值 seenSub，也未重新设计记忆边缘。本轮不声称解决全部抗锯齿。
