# D29 墙面性能验证与部署

准确生产源从冻结的 D28 `build/wall-restore-output/candidate/src` 派生，只替换墙面 helper 和版本号。`inputs.json` 固定基础源码，`prepare.py` 固定最终 helper。不要直接用含 authority 工作的 HEAD 主源码发布。

使用 Codex runtime Python，工作目录为 RealisticVision：

```text
python -X utf8 build/wall-performance/prepare.py
python -X utf8 build/wall-performance/run.py checks
python -X utf8 build/wall-performance/run.py compile-game --name bench-reuse --bench
python -X utf8 build/wall-performance/run.py run-game --name bench-reuse
python -X utf8 build/wall-performance/run.py compile-game --name game-reuse
python -X utf8 build/wall-performance/run.py run-game --name game-reuse
python -X utf8 build/wall-performance/run.py compile-game --name game-rock-reuse --rock
python -X utf8 build/wall-performance/run.py run-game --name game-rock-reuse
python -X utf8 build/wall-performance/run.py build
python -X utf8 build/wall-performance/production.py
python -X utf8 build/wall-performance/evidence.py
python -X utf8 build/wall-performance/deploy.py prepare
python -X utf8 build/wall-performance/deploy.py deploy
```

上列为可核对的执行顺序；已经冻结的产物与证据不要重跑覆盖。`runtime-inputs/pfe.swf` 是 CS 0.7.0 更新后的只读宿主副本，其 SHA 固定在 `runtime-inputs.json`。其他素材沿 D28 冻结副本；测试清单只加载本次探针。FFDec 的实际类列表需另行写入 `classes.json`；生产包不得包含测试存根或 authority 类。

每个运行使用唯一 AIR ID、隐藏窗口及自己的存储。性能测试独占运行、四版本同进程轮换；240 帧/模式/版本，计时只包含更新和雾层绘图。分段插桩仅存在于 `profile-*` 测试源，不进入候选。不要把这些时间当完整游戏 FPS。

严格差分检查比较 D28 与候选的真实 AIR 输出，包含动态光照、破坏、透明/重叠/带变换材质、半高墙、视口、缩放、重置与开关。原生金属/岩壁场景另核对原版记录、FOV、探索、敌人分类和16组雾层图。准确生产 SWF 用两进程设置探针验证，之后才允许定向部署。部署器保存当前 BAA 备份，原子替换 RV，独立正式路径检查失败自动回滚；不更换其他模组、配置或宿主。

保留的中间实验：`profile-vectors`（全图转换无收益）、`profile-sparse`、`profile-wall-cache`、`bench-final`（测试驱动帧上限不足）、`bench-final-pass`（扩大样本发现峰值）、`game-final`（复用缓冲区前的金属对照）。这些不能代替最终候选证据。
