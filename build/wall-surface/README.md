# 已探索墙面候选 v0.31.0

本工具只写本模组 build/knowledge，**不部署 release，不改用户游戏或真实存档**。

`prepare.py` 首次从 ContinuousScene 已安装生产线的冻结源码复制基线，要求 SHA256 `6979263b178b4deedf563a88c560614bd867d4fad89d806484b5a5b851c0d446`。以后复用并校验自己的 `build/wall-surface-output/baseline/src`，避免另一个场景实验重新生成源文件时被动混入新代码。首次无此指纹时必须核对安装线；不能改哈希来绕过。HEAD 另有 authority 接口/WIP，不作为发布候选的来源。

在模组目录，使用本机带 Pillow/numpy 的 Python：

```powershell
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/prepare.py
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/run.py checks
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/run.py build
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/run.py game
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/run.py game-rock
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/run.py bench
& 'C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' build/wall-surface/evidence.py
```

所有游戏/计时运行顺序执行，退出码非零时停止。`--integrate-main` 仅在主源码尚未整合时运行一次；锚点重复/缺失会拒绝，不自动覆盖后续修改。编译器位置在 run.py；当前使用本区 Sandevistan 的共享工具位置，只读工具，不写该模组。

- `checks`：26 项表面绘制（含独立 Flash alpha-mask 像素参照、半透明层、颜色变换回退、分块 gutter、换房/破损/资源释放），16 项既有柔化与敌人遮罩，21 项共享探索。通过标准为每个 AIR 程序成功退出、COMPLETE、无 FAIL。
- `game`：安装宿主副本、独立 app id、仅加载测试引导器。原生 newGame → rbl → 训练房，固定上下楼路线，两版本两模式。逐步确认原版字段不变以及 FOV/探索/敌人分类一致。截图取实际图层，旧实例必须 restoreAll，避免残留敌人掩膜污染后一组画面。
- `game-rock`：同一训练房几何，墙使用原生 G 石材，并将 (23,10) 设为半高墙。一次原版重绘后新旧共用同一纹理图；不把随机纹理的跨进程差异算成算法差异。不是用户存档复刻。
- `bench`：单进程、两模式各 120 对固定输入，逐帧反转 A/B 顺序；计时期间无 PNG/原版物理/敌人显示竞争，包含更新和 BitmapData.draw 合成。只表示该训练房的渲染工作量，不能换算战斗 FPS。
- `evidence.py`：校验候选源文件一致性，8 组完整图像中墙体 alpha=0 的区域必须与基线逐像素相同；各组深墙芯 156 个独立几何采样为黑；保存裁图、原始日志/结果、指纹和交互页。

AIR 的 app: 文件资源不可写，当前沙箱也不能创建 APPDATA 测试存储。本夹具经实测使用显式 native file URL 写自己的 `wall-surface-output/<case>/evidence`；有路径白名单守卫，真实存储和游戏安装目录不作为输出。早期 hex 日志导图和整层 erase 是已放弃的测试方案；各自的局部失败或慢速结果保留在忽略目录，不计入最终通过项。

最终候选在 `build/wall-surface-output/candidate/RealisticVisionMod.swf`。部署前仍须核对正式安装是否已变化，并执行发布门禁；不能用 `head-check` 或旧安装线覆盖后续场景兼容发布。
