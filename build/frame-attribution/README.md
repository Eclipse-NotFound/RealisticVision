# D47：完整帧归因

D46否定了按清理周期直接推断长帧主因的方向。先检查准确安装宿主的MainMenu.mainStep注册，再在隔离试验中以包装函数直接计时。原游戏先注册priority=0，模组后加载；包装函数在已有priority=1监听器之后、所有priority<=0监听器之前，保持原先相对顺序。每个探针间隔要求原生t_save恰增1，并要求原生序号与区间分解严格成立；不使用EXIT_FRAME作为边界。

每个完整间隔分为：本次探针耗时、探针结束至下次原生更新开始、下次原生更新、其后至下次探针。第二段仍包含显示合成、其它事件/计时器、帧率等待与系统调度，不能直接叫GPU时间。只有把直接测量和剩余部分分清后才决定下一项改动。

完整组合，两模式，0或6个新增原生雇佣兵；训练房原有单位保留，0不表示空场。D44与关闭RV往返，真实AI/SMG弹体仍运行。正式源与安装不改，所有运行走共享登记与独立隐藏AIR。

assets.py只在结束的本模组D45/D46试验内，对七种相同哈希的原生媒体做硬链接去重；不链接宿主、模组SWF或正式游戏资产，不删除独有材料。将这些素材视作不可修改文件。

## 已结束的试验与入口

结果见knowledge/experiments/2026-10-25-frame-attribution.md；正式仍D44，identity不采用。

- run.py / CombatRenderProbeMod.as：原生包装归因与缓存清点；plan只有off/normal，不能用于候选性能比较。fe/NativeTimingAccess.as只读测试内部计数器，绝不进生产。
- identity.py：从固定D44源派生候选。validate.py为361严格图像/阳性和888原生检查；lifecycle.py另补60项状态恢复。
- perf.py / IdentityCombatProbe.as：无原生包装的12窗完整战斗比较，off/normal/candidate往返，未带identity计数器。source文件名在隔离构建时转回对应入口类名。
- analyze.py核对归因；verify-results.py核对清点/性能的构建指纹、实际加载及有效窗口；finish.py冻结原始证据和自身状态。
- prepare.py、prepare-identity.py仅保留历史初建过程，已保护禁止覆盖现有修复；prepare-perf.py亦禁止覆盖。不要重跑已结束plan或把初版脚手架当最新工具。

本轮候选未进生产包、自由游玩、设置或部署门禁；不得把1309项通过写成性能修复成功。后续实验另建目录，保留当前失败/无收益证据。
