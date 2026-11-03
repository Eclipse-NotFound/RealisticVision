# RV 阴影计算保真优化

本轮固定基线 v0.34.4-door-smooth，正式产物 v0.34.5-ray-loop。
结果与适用边界见 [实测报告](../../knowledge/experiments/2026-11-03-boundary-optimization.md)。

工具使用本机已验证的 `build/motion-performance/run.py`、`build/frame-performance/run.py`、`build/wall-surface/run.py` 和 ModLoader 登记/隐藏测试进程。它不是独立发行的测试框架。需使用含 psutil 的 Codex 运行时 Python；系统 Python311 缺少该依赖。游戏启动需经批准的正常用户执行环境，不能绕过启动完整性检查。

执行顺序：

1. `run.py <新名字> --profile`：冻结正式源和实际配置，诊断同字节 A/A；已有输出目录拒绝覆盖。
2. `prepare_candidate.py`：原始 DDA 局部索引候选；`--zero`：增加空格透光值为零时的等价早退。基线安装哈希不匹配时停止。
3. `run.py <新名字> --checks --candidate dda-zero`：数值、图像与持续绑定检查。
4. `run.py <新名字> --paired --candidate dda-zero`，另轮加 `--reverse`：无函数插桩的 ABBA / BAAB；`--paired --moving` 且不指定候选做同字节 A/A。
5. `analyze.py <运行名> ...`：保留全部长帧，输出均值、P95、最大值、>50/>100ms 和连续长帧；>5s 中断另标不适合帧耗时收益评估。
6. 审阅证据后 `build_release.py`：从冻结生产线构建，并仅把对应方法移植回含其他开发工作的 `src/`；不从 HEAD 构建正式包。
7. `smoke.py <新名字>`：实际正式字节经 ModLoader 初始化与原生帧检查；`deploy.py`：核对旧安装、备份、原子替换 RV SWF、回读指纹。
8. `archive.py`：把时间原始数组、统计、输入指纹和回执存入报告附件。

测试的 `enabled=true`、满耐久/补弹、固定射击散布与受控玩家轨迹只用于隔离实例。配置经 `loadConfig()` 加载并派生模糊参数；测试不写玩家设置、存档或名单。运行期原生素材可硬链接，不允许修改这些共享素材；链接不可用则复制。宿主始终是独立副本。

已部署后，原基线的 `prepare()` 安装指纹检查会按设计拒绝新运行。后续版本须另建冻结基线，不能放宽此校验来覆盖历史证据。
