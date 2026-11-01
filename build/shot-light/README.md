# 开火照明调查工具

2026-11-01用户最新约定：后续RealisticVision性能测试关闭光与暗，只评估RV本体。
本目录保留为独立照明研究入口，不作为RV性能基准；`run.py`必须显式带`--lighting-study`才启动。
RV对照采用光与暗不加载的固定组合，仅改变RV关闭/current/classic；加载日志也须核对LAD未启动。
光与暗的算法研究与结果另行记录，不混入RV收益结论，不更改玩家正式加载名单。

只写 RealisticVision 内的隔离输出。读取匹配正式 LAD 0.7.0 的冻结源；不改他模组或 release。
调查结论见 `../../knowledge/experiments/2026-11-01-shot-light.md`，原件 `../shot-light-output`。

- `prepare.py`：仅首次冻结，要求新输出目录。不能覆盖历史输入；保留真实 RV combo-v4 和宿主 9D8662。
- `profile.py`、`run.py`：实际玩家轻机枪与六敌；共享测试登记、私有桌面、随机 AIR 身份、静音、独立存储。
  `--lights-detail` 细分阴影生成/叠光和来源，仅作归因。默认帧照明累计覆盖前后两次绘制。
- `candidate.py`、`check.py`、`TrailChecks.as`：光带循环等价和局部计时；不能据此承诺完整帧性能。
- `raster.py`：复用独立矢量绘图树；`--raster-verify` 逐次与原算法比较，`--raster-pair` 同进程 ABBA。
- `geometry.py`：保留每条射线，只在半径、路径类型、每个顶点严格相同时复用原位图。上述运行增加 `--geometry`。
- `check_geometry.py`、`GeometryChecks.as`：900组光场，覆盖墙体变化、半透明材质、锥形/全向光与缓存清空。
- `direct.py`：直接用渐变填充轮廓的独立实验；专项运行增加 `--direct`，出现像素差异即淘汰。
- `direct_full.py`：分别检验近似全向与严格360度输入；12普通夹具通过后，13扩大取材、14限于合法弹体范围仍出现像素反例，未采用。
- `build_lad.py`：直接调用现有 Java/Flex 编译器；源、存根和产物都留在本模组输出目录。
  01 的 PowerShell AuthorizationManager 失败保留；没有放宽执行策略或关闭保护。
- `analyze.py`、`archive.py`：逐窗统计、匹配完整间隔及冻结证据。归档一次性生成，不覆盖既有档案。

每次运行必须新名称；先核对当前输入指纹，不能无条件重放历史 prepare 或将诊断包安装。
native runner 本体来自已指纹锁定的 `build/maximized-flow/run.py`。
有 `baselineRender` / `originalMakeLight` / 诊断开关的包只是比较工具，不是可部署产物。
`lightingTotal` 是当前回调之前的两阶段累计；与 `nextInterval` 做逐帧关联要使用分析器的 `lightingTotalNext`。
窗口均值与最后一次照明 `lightingMs` 均不能当作整个游戏的独占CPU或FPS。
