# 阴影显示与单位/特效遮挡的交叉归因

只用于隔离诊断，不能编译到 release。输入是准确生产 combo-v4 AEA30314，当前宿主 CA94AF17；开发主源码不参与。

- `prepare.py`：只运行一次，冻结源/宿主/选定模组，派生本轮驱动。已存在输出时拒绝，不能重复覆盖历史证据。后续手动调整已反映在 `run.py`，不要重跑生成器覆盖。
- `native_check.py`：比对现有 FFDec 导出中75个 MainMenu/MainFE 方法体，验证原生计时协议适用当前宿主。只读其他模组。
- `run.py`：复用私有桌面、随机AIR ID和只读存档种子，独占登记 `game`；默认静音，CPU采样仅自有句柄。宿主及模组来自冻结副本。`--reuse-from`只复用相同源码的二进制，仍生成新探针/证据目录。
- `SavedFireProbe.as`：off/完整/跳过hideEnemies/隐藏fogVis/同时两者，正反顺序共10窗，每窗90帧预热+180帧采样。`skip-hide`包含单位、血条、武器、独立手臂及弹体/Part处理，改变显示与部分原生visible依赖，不是纯绘制开关。
- `DisplaySnapshot.as`：预热末及计时末记录显示层父链；不在完整计时间隔中。两个快照分处原生后/RV后，不能据阶段差异认定污染。
- `cpu_sampler.py`：每秒读取同一自有进程的累计CPU时间/周期，内存积累，结束保存。包含全部线程；低CPU不能区分GPU等待/IO/限帧/未调度，高CPU也不能独占归给绘制。每秒样本只适合解释数秒停顿。
- `CachePixels.as`：可选缓存试验的同帧快照。原位置、小数平移和缩放下，对比缓存/非缓存，并以连续两次非缓存作为控制。仅快照不覆盖跨帧缓存失效/原地破墙，不等于真实最大化窗口验收。
- `--clip-pair`：进一步拆分baseClip裁切与airPixels凹口补绘；`--layers-pair`：拆分fogBitmap地板雾与wallLayer厚墙阴影。全部只修改测试显示，不能作为修复发布。
- `analyze.py`：只统计 `frames` 中具有下一间隔的179个样本/窗，精确分段；CPU只取完整落在采样窗/长停顿里的实际桶，不插值或补零。

示例（Python使用已探测运行时）：

```text
run.py 01-large-factorial --full --plain --native-timing --native-screen --private-visible --sweep --solo
run.py 02-fog-cache --full --plain --native-timing --native-screen --private-visible --sweep --solo --cache-pair --reuse-from=01-large-factorial
analyze.py 01-large-factorial
run.py 03-contour-components --full --plain --native-timing --native-screen --private-visible --sweep --solo --clip-pair
run.py 04-floorwall-components --full --plain --native-timing --native-screen --private-visible --sweep --solo --layers-pair
```

`--solo`删除随机敌人但仍构造六名狮鹫。测试是私有桌面普通窗口模拟2560×1521有效尺寸，不操作玩家的真正最大化窗口。全组合排除 LightAndDarkness；其他模组名单与指纹以每次build.json为准。
