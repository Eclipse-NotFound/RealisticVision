# D48：相邻动画共用已模糊视野场

基线为准确D44生产源，未叠加D45–D47的失败候选。候选只在无root/子树滤镜、对象完全位于4×4格内、原有支持边距足够容纳模糊核时复用共享块；其它条件仍走原始局部路径。只复用模糊后的采样，保留每个对象原来的遮罩图形、缓存偏好和绘制顺序。

classic仅在整个共享块已由原逻辑查询补算完成时允许使用；不扩大classicLogicRegion范围、不提前发布fogCache，不新增探索或逻辑视野。current从原currentSight复制。旧局部遮罩外侧支持带可能不同，必须由整图像素验证证明这些差异确实不可见；不能仅凭数学推导称画面等价。

prepare.py冻结候选与继承测试工具，禁止覆盖。group.py走共享测试登记；checks-steps.json进行密集严格图像/阳性与原生动画检查。perf.py使用无原生包装的off/normal/candidate往返完整战斗探针；性能结果出来前不部署。

输出在build/shared-mask-output；所有新试验使用新名称，不覆盖D47或本轮已结束证据。此文件记录方案，不代表已通过。

## 本轮结论

全部候选不采用，正式仍D44。shared/shared-v2分别通过361+888图像/原生检查；reference/reference-v2在加强的动态滤镜夹具中同帧出现24个像素差异。第一轮shared计时受本会话去重IO干扰，仅诊断；shared-v2干净12窗无稳定性能收益。详见knowledge/experiments/2026-10-25-shared-mask.md。

reference-perf-steps.json未运行且不得续跑；候选根not-adopted.json记录原因。旧计划、首次失败源与修改后的工具都为证据，不重建覆盖。下一步独立检查整张雾层的重复同值显示设置，不能把本轮候选混入正式源。
