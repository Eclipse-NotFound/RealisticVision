# D43：单次采样候选

准确基线为D42 production-final，正式包0DBE…04F2BF。仅本轮输出写入effect-load-v3-output，历史实验不可重跑覆盖。

- 来源生成记录为effect-load-v2/prepare_singlepass.py；随后把局部lit改为uniformLit以避免AS3函数作用域重名。v1完整帧回退、v2重复采样，均不部署。
- 算法在refreshMask原有采样中分类，classic复用threshold匹配数；全亮/全暗跳过模糊和辅助图，混合/边界/宽滤镜保留旧算法，raw区域缓存仍保留。
- bench.py在独立AIR交替处理100/500移动视觉；--edges检查边界与六档模糊。绘图比较位于计时外。
- functional.py复用原生弹体、粒子、狮鹫和生命周期回归；measure.py检查实际父层墙面与地板。
- native.py驱动六名原生UnitMerc持续smg10射击，不驱动方向键，完整保留原生受击、移动和世界推进。--reverse倒换新旧顺序；--lean只做低开销运行监测。
- package.py准确包与设置；review.py绑定来源和验证；性能判断另存performance-decision.json，功能通过不自动部署。
- deploy.py备份、安装及正式路径隔离复验，失败回滚；development.py仅合入开发树并检查语法，绝不部署authority开发包。
- finalize.py归档报告与记忆；closeout.py只暂存本轮增量，保留外部WIP。

最终复核使用native-03（RC DF0F）与native-05（RC 78C roomfix5）；分别报告每轮同进程对照。functional-03验证更新后的组合。safe-02-parent以与超时的safe-01-parent相同字节完成实际父层64组对照。group_gate.py仅在同一个真实登记内顺序借用子检查，不并行运行AIR；每项仍登记其子PID并等待退出。包装脚本故障/启动前资源中止保留在group-steps及各目录，脚本存在不代表执行成功。

native-06追加受控调度复核：构建带--calibrate，运行带--high-qos，只有自建测试进程使用显式策略并读回，采样窗口外固定计算2–4ms。生产启动器不变；此轮current完整帧基本持平，局部更新约减少20%，classic更新约减少6%。早期默认策略结果有波动，最长帧尚未解决；必须同时阅读performance-decision.json，不以局部CPU代替整体流畅度。native-05/06实际运行库为2050（含记录器），native-03为BD71，不能混标环境。

测试均使用唯一AIR应用ID、隐藏桌面、共享登记及自有进程清理；不操作玩家实例或真实存档。candidate-01为失败构建，candidate-02完成360帧但进程超时；retry_prepare.py冻结异常并准备candidate-03复测。脚本存在不表示已执行，以结果为准。
