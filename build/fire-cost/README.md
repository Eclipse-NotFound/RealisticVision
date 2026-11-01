# 开火分配与组合绘制调查

准确 combo-v4 生产源和宿主冻结在 `build/fire-cost-output/inputs.json`。
本目录仅生成隔离实验，不修改正式安装、玩家配置或其他模组。
运行游戏前通过 ModLoader `Registration` 排队；唯一应用 ID、私有桌面、静音。
原件和失败运行均保留；每个命令必须用全新的输出目录名。

- `prepare.py`：冻结生产源、宿主和选中的模组。已运行，不覆盖历史输入。
- `instrument.py`：在实际分配/释放点记录数量与像素，不用内存下降冒充 GC 事件。
- `phase.py`：缩放裁切原型；`--both-edges` 生成第二版。两版都在 f=123 出现严格像素差异，已否决。
- `witness.py`：只用匹配像素数或已知位置的变化证明输入**不同**；不确定时保留完整比较。没有抽样判定相等。
- `pixel_check.py NAME --source=witness --offset-grid`：两个独立显示树连续运行，严格 ARGB 比较；每次快捷路径另用原比较核对不等。
- `prepare_lad.py`：只读冻结正式启用的 LightAndDarkness，独立清单 `optional-lad.json`。
- `run.py`：复用指纹锁定的 `build/maximized-flow/run.py`，原生轻机枪与六名狮鹫开火，记录完整帧间隔。
- `analyze.py NAME...`：从完整 `evidence/result.json` 计算每窗/分组摘要，P95 使用 nearest-rank。

原生运行例（使用工作区 Python，参数不省略）：

```text
run.py NEW --allocation --full --solo --sweep --both --plain --private-visible --maximize
run.py NEW --lighting-cross --full --solo --sweep --plain --private-visible --maximize --short --no-cpu
run.py NEW --source=witness --try-candidate --compact-pair --full --solo --sweep --both --moving --plain --private-visible --maximize --short --no-cpu
```

`--lighting-cross` 在自有运行实例内交叉 RV 开关和弹体照明开关；场景灯具保留。
这项诊断有意改变测试画面，仅用于归因，不能作为无损优化发布。
其他原生计时沿既定基准排除 LAD，不能混用两轮绝对数值。

01 在运行游戏前因插桩锚点计数失败；02 修正锚点范围后完成。
05 的 1440 帧图片相等，但每帧改模糊参数，未命中候选比较分支，覆盖检查失败。
07 保持滤镜参数，1441 项检查通过，2287 次不等快捷判断均经完整原比较核对。
不是放宽阈值或忽略失败；05 原件保留。

08原生ABBA对照无确认收益：current整帧均值59.95→62.26ms，classic63.87→63.59ms，
正反方向不稳定。三份候选都未采用、未部署；完整解释见 `knowledge/experiments/2026-11-01-fire-cost.md`。

性能以完整帧间隔为主。RV 函数耗时、光照最后一次渲染耗时、图像分配量只是各自分段，
不能相加冒充全帧、不能直接换算游戏 FPS。`field.elapsedMs` 不包含同帧早一次渲染的合计。
原生随机弹道、后台负载、窗口顺序仍是边界；配对方向和尾延迟一起检查。
