# D37 两模式性能对照

生产基线是 D36 v0.33.3 的冻结源 `build/combat-visibility-output/production/src`，不是包含未发布 authority 开发的 `src`。所有输出在忽略目录 `build/native-performance-output`；新试验使用新名字，不覆盖已运行证据。正式安装只能由 `deploy.py` 使用 `review.py` 钉住的同一份字节执行。

最终选择 `candidate-12`：classic 按视口绘制并在镜头跳转时从已有采样补绘；低分辨率输入逐帧核对，只重算发生变化的格子及相邻墙格；墙前景复制计划复用，但材质像素仍每帧读取；FOV 遍历限制到原半径的保守范围；current 缓存本地已见子格分类，写入时立即失效，共享探索保留原扫描。不降低分辨率、更新频率、视距或修改原生亮度。

`select.py candidate-12` 冻结生产输入，仅改版本；`package.py build/check` 构建六类生产包和两进程设置验证；`development.py` 只把本轮生产差异合入开发树并单独编译，不安装开发包。`review.py` 检查精确源码、测试证据与环境后，`deploy.py` 备份 D36、原子替换 RV、正式路径独立启动确认版本/设置/心跳，失败回滚。

核心验证：

- `checks.py build/run checks-final --candidate candidate-12`：缓存、地形、设置、共享探索与 helper 像素。
- `fov_check.py` / `memory_check.py`：分别核对完整 FOV 数据和跨移动/破墙/共享探索/重置的记忆图。
- `measure.py build/run wide-final-visible --candidate candidate-12 --verify --wide`：实际视口、缩放、亮度边界、柔化和常亮开关。
- `measure.py build/run exact-final-visible --candidate candidate-12 --verify`：默认相机下完整图像与逻辑对照。
- `wide-final-parent` / `exact-final-parent`：相同输入保留根节点的父子显示层级再取图，用于最终像素验收。
- `measure.py build/run timing-final-visible --candidate candidate-12`：无插桩/无逐帧截图的同输入交替计时。
- `measure.py build/run native-final --candidate candidate-12 --live --native`：原生持续开火，按 off/A/B/B/A/off 分模式交替。off 为同一 CS 场景内的原生渲染路径，并非无其他模组的游戏。
- `weapon.py build/run weapon-final --candidate candidate-12`：完整所选组合的真实 childObjs 武器回归。
- `display_check.py display-matrix-final`：36项独立检查；合成根节点矩阵可校准位置，但非整数缩放可能改变边缘栅格化，保留父子层级的取图与父层绘制严格一致。

上列 build 的参数不应机械附到 run；详见各脚本 `--help`。AIR 独立应用 ID、存储和私有桌面；始终使用官方共享测试登记。性能结果只比较同轮数据。D37 根据已观察的内存回落采用 5 GiB 启动下限，最终计时还核对全程至少 3 GiB 可用；像素验证轮的耗时不用于发布收益。

## 取图工具纠正

早期沿用的 `draw(fogVis, cameraMatrix)` 漏掉 `fogVis` 自身为 scrollRect 补偿的位移，也在普通回放漏掉实际相机缩放。它会取到屏幕外区域，不能当作最终视口验收。`*-visible` 轮用 `fogVis.transform.matrix.concat(cameraMatrix)`，画布尺寸取真实屏幕。独立实验发现这种合成矩阵的位置正确，但0.658333…缩放下与保留父子层级的边缘栅格化仍不同（94像素，最大64/255）；因此它不是逐像素屏幕等价的通用公式。最终 `*-parent` 在同步检查中将根节点暂挂到空Sprite、按相机矩阵绘制父层，再在finally恢复原父层/索引；36项独立验证确认此路径严格相同。旧轮完整逻辑场比较和纯更新计时保留其范围，旧合成截图/雾draw耗时不作为最终视觉/绘图结论。`timing-final-visible`的draw仍是隔离软件绘制耗时，不能当作GPU帧耗时。

01–04 为全图缓存探索；05 编译失败；06 镜头补绘缺口由 07 修复；08–12 逐步加入精确优化。13–17 是因旧取图坐标误判尝试的缩放回退方案，已经淘汰。18 保留整图基础缓冲的替代也被淘汰。最终回到 12，经纠正后的视口重新验证。不要把目录编号大小当成版本优劣，或部署未选候选。
