# D40 整体流畅度与长帧验证

基线是准确安装D39 83d8e590…205c7e65，六类生产源在`build/long-frame-output/production/src`。输出为`build/overall-flow-output`；历史目录不可覆盖，运行前按共享测试表自动登记。

- `prepare.py`只冻结一次。`candidates.py`产生01无效显示写入跳过、02直接alpha复制、03合并精确查表、04局部显示位图、05classic单次扫描、06延后局部显示快照。
- `measure.py build NAME --candidate candidate-05 --verify --wide`与`run NAME`做同输入对照。以`safe-`开头时，在有显示副作用的诊断查询之前取实际父层画面；`shared`额外覆盖动态共享探索。函数插桩只用于归因，不代替完整帧测试。
- `trace.py`记录同监听器连续帧、RV绝对起止、内存和场景状态。`--exclude`仅诊断隐藏雾层，不能发布；默认每帧设置位置的镜头扫动不等于真实跑步。
- `native_walk.py build/run NAME [--lean]`在原生平台使用真实方向键与跑动控制；除首次放置外不设位置或镜头。12窗每窗240记录帧，检查贴地、距离、折返和原生射击。`--lean`交换AB顺序，运行期间只观察本实例，避免反复全进程枚举。
- `system_analysis.py`明确纠正旧外部CPU采样的时序上界说法。100ms观察器自身最高263ms，`system-battle`不能作为发布性能验收。
- `select.py`/`package.py build/check`只构建candidate05准确六类候选与36项设置。`review.py`核对132项/组、两轮24窗、全部源和输入指纹；功能通过标为`FUNCTIONAL_PASS_RELEASE_HELD`，不因功能绿灯自动部署。
- `helper.py`是为02/03准备但**未执行**的检查，不能计入证据。`development.py`/`deploy.py`本轮未运行；部署器拒绝非PASS审查状态。

候选和正式安装必须区分。最终决策、数据及局限见`knowledge/experiments/2026-10-23-overall-flow.md`。
