# 墙内阴影与classic投影复验

**2026-09-19 状态纠正：当前 v0.28.1 源码在新增墙/地板接缝测试中失败，不能仅凭旧39项与小墙端点通过就部署。此轮只有诊断，无新修复。**

在RealisticVision模组目录运行。需要本机Flex/AIR、Animate JRE、游戏自带adl64/runtime；可通过RV_FLEX_SDK、RV_JAVA覆盖工具位置。普通沙箱中AIR启动可能被阻断，此时使用工具级审核放宽，只运行隔离实例。

## 原有墙内阴影（39项）

    node build/wall-tests/run.mjs --baseline
    node build/wall-tests/run.mjs
    node build/wall-tests/run-game.mjs

--baseline固定为8748feb（v0.27.1，预期失败）；不带该项测试当前源码。--revision <提交哈希>可指定另一旧版，不接受分支名或命令片段。

## classic小墙块投影（v0.28.1）

    node build/wall-tests/run.mjs --edges --revision 6c0170e
    node build/wall-tests/run.mjs --edges
    node build/wall-tests/run-game.mjs --training --revision 6c0170e
    node build/wall-tests/run-game.mjs --training

第一条运行v0.28.0，预期墙角偏差约20px，掩膜分类不齐；第二条运行候选，预期WALL_EDGE_TESTS PASS。--edges覆盖真实computeFov、墙外端点、10方向/相机缩放平移、亮暗区、掩膜取样、静止缓存、模式切换初始14帧、无暗邻居墙外亮度和记忆渐变。

仅调查旧版时，可加--probes。它操作旧classicBmp，**必须与--edges及修复前--revision同用**：

    node build/wall-tests/run.mjs --edges --revision 6c0170e --probes

探针会改变当次渲染对象，是因果取证，不作为最终候选验证；后续新旧正式比较要重跑不带--probes的两条边缘命令。

--training新开隔离档，正常从begin旅行至rbl，再通过gotoLoc(2)进训练房loc1_0。玩家约(1080.8,640)，24帧推进正常记忆。分别输出实际游戏场景、纯阴影、tile数据；CAPTURED仅表示采集完成，不表示修复通过。

新旧训练采集后，用带Pillow的Python执行build/wall-tests/compare-training.py；它先断言整个训练输入一致，再比较纯阴影，断言current整图差0、两模式墙内差0，输出小墙角位置和右侧亮度剖面。目前系统PATH无python，已验证依赖路径：

    C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe

最后归档当次日志、指纹和交互对照：

    node build/wall-tests/make-edge-evidence.mjs

输出knowledge/experiments/classic-edge-v0281/。make-evidence.mjs是历史v0.28.0归档脚本，不要用它覆盖已保存的旧报告指纹。

## 梯子口、厚墙内角接缝（2026-09-19）

    node build/wall-tests/run.mjs --seams --revision 6c0170e
    node build/wall-tests/run.mjs --seams
    node build/wall-tests/run.mjs --seams --seam-probes

第一条8/8通过；当前源码第二条预期7/8失败，最大相邻亮度差89。这是定位尚未修复的问题，不是已修复回归绿灯。第三条仅作单变量因果探针，改变当次夹具对象，不能当作候选效果。

    node build/wall-tests/run-game.mjs --training --seams --revision 6c0170e
    node build/wall-tests/run-game.mjs --training --seams

两条顺序运行。完整1.02训练房按上层→梯子底部→回上层的路线取样；调用原版lighting/lighting2累积沿途亮度，再调用实际模组绘图。每版本捕获两位置的classic/current/原版和纯阴影。原版visLight取图必须传入它自身的变换矩阵；只draw该容器会得到原始1px/格缩略图。不会读取用户存档，不等于重放用户截图当帧。

用本页上述带Pillow的Python依次运行：

    build/wall-tests/inspect-seams.py --baseline
    build/wall-tests/inspect-seams.py
    node build/wall-tests/make-seam-evidence.mjs

测量器输出game/*seam-measurements.json；候选运行先验证新旧输入完全一致、current整图/墙内未变，接缝值只作诊断指标，不把已知坏候选判为通过。最后一条仅作首次归档，输出knowledge/experiments/classic-seams-20260919/；已有指纹文件时拒绝覆盖，后续新实验应另设目录。报告为2026-09-19-classic-wall-seams.md。

--seams夹具使用独立seams/输出与rv-wall-fixture-seams app id；完整游戏仍共用game/，必须与所有其他完整游戏场景、revision顺序执行。

## 验证方式与边界

- 同类用例共用输出目录，**顺序运行**。普通夹具、edges各有独立编译目录/app id；完整游戏的random_mane与training共用资源副本，二者以及不同revision之间必须顺序。
- WallHarness/WallEdgeHarness在独立不可见AIR程序中直接调用实际模组方法，以Bitmap.draw读取最终像素。临时源码只将private改为public，方法体不改；游戏类用编译存根与可控制Location夹具提供。
- 原版参照复刻Grafon.setLight从(1,1)开始、写(x,y+1)、(-20,-60)、40倍平滑显示。覆盖横/竖/角墙、弱光、邻地板角、记忆、retDark、切模式、同尺寸换房、破墙、静止照明、门及掩膜缓存。
- classic中心场参考独立使用矩形相交，验证相位；40px粗格不等于连续多边形切线。其中一个水平掠角差21px是采样模型差异。薄墙的投影中心仍会影响可见侧约20px，不宣称所有墙外亮度未变。
- 掩膜检查用5px格中心，忽略阈值±1取整，验证取样分类，不等于实际战斗中所有姿势/血条/武器验收。
- GameProbe经副本已有loader启动，等待allLandsLoaded后正常新档/旅行。直接调用实际模组绘图方法，没有启动正常startup，也不做快捷键或六模组战斗。
- random_mane旧场景固定cfgFadeStep=0、visCur=1，只测原版墙形状；training使用正常记忆推进。不要混淆两者或把CAPTURED当PASS。
- 完整场景动画可变化；compare-training.py比较純阴影并断言输入一致，不能用场景PNG哈希判current回退。
- 12×10与48×25计时仅为渲染更新循环，不是游戏帧率、受控性能基准或长期游玩验收。
- 副本仅含公共游戏资源和本模组测试引导器。根pfe.swf、真实release/config和pfe存档均不改；其他模组缺件的loader报错属刻意隔离。
- 生成物位于build/wall-test-output/（忽略目录）；超时后退出并清理临时描述符。app id仅用rv-wall-fixture/rv-wall-fixture-edges/rv-wall-game-probe-training/rv-wall-game-probe-random。

## 输出

夹具baseline.log/candidate.log包含原始断言、计时与PNG数据；edges位于edges/子目录。游戏场景在game/，旧版本带baseline-前缀。报告归档会移除日志中的PNG/DATA大行并单独保留图片和JSON；过程生成物可重建。
