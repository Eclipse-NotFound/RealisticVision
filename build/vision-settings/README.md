# D34：视野设置

已部署v0.33.0-vision-settings。当前准确生产源/包：`build/vision-settings-output/candidate/`；完整证据：`knowledge/experiments/vision-settings-v0330-20261021/`。开发src含未发布authority，不可整包编译覆盖安装。

从模组根，用本机Codex Python运行。**本轮目录已冻结，不要原地重跑prepare/build/archive/deploy**。未来实验改OUT并重新固定基线；生产来源不是任意HEAD。`prepare.py`固定D32六类源与安装指纹，`run.py build`应用可审查的设置变换；随后checks、final_validation、deploy.py、archive.py。部署前确认未来最新已安装版本，不能沿旧OLD哈希回退后续更新。

本轮251条断言及正式路径复验通过。全部AIR已改用共享game占用、唯一应用ID和独立Windows桌面；纯Python分析可并行，AIR组件不再按offline启动。运行器超时只关闭自身句柄；不会操作玩家实例。

默认：dim=.35，viewscale=1，soft_current=20，soft_classic=0。柔化值是滤镜的世界像素尺度，不是精确边界10%—90%宽度。旧dim保存值保留；其它旧配置键/改键/语言不变。

默认完整最终画面与D32逐像素相同。非默认classic亮度保留逻辑遮罩参考；范围扩大采用模组自己的角点光照与探索记忆，不写原版visi/t_visi/lDist。倍率回调只重算，不用resetRoom清探索。原版/基地透传保持。

并行D33运动优化是独立候选，未混入本轮安装。后续合并应以新准确生产源为基础保留D34，再按新字节验证。原生回归是确定性训练房与阶梯夹具，不代表所有存档或高负载联机FPS。
