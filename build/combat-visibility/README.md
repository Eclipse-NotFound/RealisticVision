# D36 武器泄露与战斗开销

基线为准确D35生产源 `build/regression-recovery-output/production-singlepass/src` 和7852F61E生产包。只写本模组新实验目录；测试采用官方登记、独立AIR ID、隐藏桌面及独立存储。禁止覆盖历史实验；每次使用新名字。

- `prepare.py`：从冻结生产源产生附件修复。`weapon-methods.as.inc` 为新增方法，生产无测试探针。
- `run.py build NAME --full` / `run.py run NAME`：真实原生Raider与其childObjs武器，同完整安装组合复现/验证。`inspect.as.inc`固定逻辑边界以隔离遮罩归属，记录真实像素、生命周期及恢复。不是用户存档重放或计时资格。
- `optimize.py`：保留weapon-only源，生成批量位图遮罩转换；精确旧式逐像素算法在MaskBatchChecks中作独立参照。
- `measure.py`：沿用D35大图同输入交替驱动，build/run/analyze；profile、verify、live分别运行。实际环境采样、无其他AIR/JVM与内存条件仍执行。
- `validate.py build/run NAME`：复用1536逻辑场、90设置、16射线/边界、21共享探索检查，另65组批量遮罩逐像素比较。

不直接从含authority工作的HEAD编译生产。正式包须从本轮candidate/src冻结；部署前检查源码、包、证据和当前安装未漂移。

本轮已完成：`regress-full-03`为52项真实武器检查；`checks-01`为1728项/组基础与位图检查；`exact-01`为32个原生大图一致性检查；`timing-02`为完整配对计时，`combat-02`为8个原生射击窗；生产包另36项。`timing-01`已中断作废，禁止拼接数据。所有目录冻结，后续实验另起名称。

`package.py`冻结并验证准确生产包；`review.py`核对证据；`development.py`仅编译含authority的开发源（不安装）；`deploy.py`核对D35指纹、备份、原子替换、正式路径复验及失败回滚；`finalize.py`一次性归档和产生不含外部WIP的状态快照。v0.33.3已部署，收益与局限见[报告](../../knowledge/experiments/2026-10-22-combat-visibility.md)。不得重跑本轮部署器覆盖后续版本。
