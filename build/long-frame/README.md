# D39 偶发长帧

基线D38正式6593EE35…8FD6EC06，准确六类源位于`build/followup-performance-output/production/src`。新输出只在`build/long-frame-output`，不得覆盖历史试验。

`trace.py`：完整组合先复现still/sweep/battle（冻结trace-full-01）；发现EXIT_FRAME重复广播不能作为整帧末端。V2用同一liveStep连续时间戳，保留绝对时刻，outsideRV包括驱动/camera/其他脚本/显示/调度，不作GPU归因。`trace-order-02`为事件序列反例。`analyze_trace.py`拒用V1阶段归因，输出v2文件而不覆盖旧分析。

候选01保留世界坐标轮廓；02排除常亮共享Rectangle的重用风险；03预计算精确采样模板；04补扫描异常持久失效。01未验收完整画面，不发布。`candidates.py`的主程序生成01，后续函数依次bright_guard、sample_kernel、durable_invalidation；每步要求新目录。

`helper.py`230组严格采样表/像素检查；`validate.py pixels`保留父层取图32+64组；`performance`同输入轮换与完整组合12扫动窗，最终无函数分段插桩；`weapon`保留D35真实武器泄露反例52项。所有AIR/JVM经共享game占用，独立应用ID和私有桌面，不操作玩家存档。

`select.py`冻结04，仅改版本；`package.py build/check`准确六类及36项设置；`development.py`只合生产差异到含authority开发树；`review.py`校验源码、加载、样本和环境；`deploy.py`从6593基线备份、原子替换RV、正式路径冒烟并失败回滚；`finalize.py`归档/更新状态；`closeout.py`隔离暂存，保留四项外部WIP。

剩余长帧并未全部解决；同输入更新耗时不是完整FPS。详见`knowledge/experiments/2026-10-22-long-frame-triggers.md`。
