# D42：原生特效与狮鹫肢体遮挡

基线为D41准确生产源和安装指纹，来自`build/boundary-load-output/production`。本目录不使用含未发布authority的开发树构建生产包。

- `prepare.py`：一次性冻结基线；不得重跑覆盖证据。
- `candidate.py` / `world-visuals.as.inc`：复用原遮罩栅格，按独立视觉的位置裁切；完全可见区保留原生绘制。
- `run.py` / `inspect.as.inc` / `extra.as.inc`：原生狮鹫、子弹、激光、火花、爆炸和弹壳实际像素；重入、死亡、移除、独立枪口与粒子动画。
- `render.py`：已有身体、血条和武器的实际绘制回归；后续只有独立效果遍历变化时按方法全文匹配复用。
- `measure.py`：D41与候选原生墙面/地板/逻辑的严格像素对照。
- `native_walk.py`：真实方向键跑动及狮鹫射击的完整组合对照，测试登记和隐藏AIR隔离；不要把局部更新计时当FPS。
- `validate.py`：顺序完成画面与准确包设置验证，不部署。
- `package.py`、`review.py`、`deploy.py`：冻结版本、核对来源/结果、备份及正式路径隔离冒烟；失败回滚本轮安装。
- `development.py`：只将生产差异合入开发树，保留其未发布authority显示写入；编译仅证明语法有效，不代表authority联机已验。不可再次运行已合入的补丁。
- `finalize.py`、`closeout.py`：部署成功后归档报告、更新记忆并精确暂存；保留四项外部WIP，不提交他人改动。

所有运行使用新目录和应用ID。`reproduction-01`的爆炸首帧未初始化、`functional-02`的明区缓存像素变化、`native-01`的夹具贴地计数和`native-02`的遍历越界均保留为失败证据，不能作为最终通过依据。
