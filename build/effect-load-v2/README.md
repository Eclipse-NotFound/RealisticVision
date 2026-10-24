# D43：密集特效开销

准确基线为D42 production-final，正式包0DBE…04F2BF。仅本轮输出写入effect-load-v2-output，历史实验不可重跑覆盖。

- setup.py一次性冻结；candidate.py生成保守的完整支持区全亮/全暗分类。
- bench.py在独立AIR交替处理100/500移动视觉；--edges检查边界与六档模糊。绘图比较位于计时外。
- functional.py复用原生弹体、粒子、狮鹫和生命周期回归；measure.py检查实际父层墙面与地板。
- native.py驱动六名原生UnitMerc持续smg10射击。native-01步行路线被原生击退破坏，故不是性能验收；native-02/03不驱动方向键，完整保留原生受击、移动和世界推进。--reverse倒换新旧顺序；--lean只做低开销运行监测。
- package.py准确包与设置；review.py绑定来源和验证；性能判断另存performance-decision.json，功能通过不自动部署。
- deploy.py备份、安装及正式路径隔离复验，失败回滚；development.py仅合入开发树并检查语法，绝不部署authority开发包。
- finalize.py归档报告与记忆；closeout.py只暂存本轮增量，保留外部WIP。

测试均使用唯一AIR应用ID、隐藏桌面、共享登记及自有进程清理；不操作玩家实例或真实存档。
