# 2026-10-14 大场景兼容安装

用户明确允许ContinuousScene任务对RealisticVision做必要兼容修改。安装v0.30.3-scene，25474字节，SHA256 `ED76EC15666FD8CD50ACF0149F7EC32F2602D2E68D753580A0EC5814B95A2E99`。配置模板SHA5136EE19…A3C7F保持，玩家已有偏好未改。

场景超过48×25时，仅对镜头附近加四格余量重画雾、模糊和显示裁切；保留全场逻辑视野判断及原有小房间路径。安装包以已安装源码线0735491构建，变换保存在ContinuousScene/build/compat_prepare.py。当前HEAD另含authority接口与其他任务未提交的RVAuthorityView/测试/记忆修改；这些没有发布，也没有被本任务提交。当前主源码合入了相同兼容改动供后续开发，但不等同本次release完整来源。

视野测试用该生产来源的复制源码暴露私有成员：SoftHarness16/16、SharedExplorationHarness21/21，包含1000射线对照、门/水/破坏失效、单位掩膜与共享探索不扩大视野。日志见ContinuousScene/knowledge/experiments/evidence/vision-v02-regression。相同正式候选参与全模组大场景44/44和安装后原生启动14/14。

同路线360帧短测：局部绘图但全图模糊中位57ms，局部模糊/显示裁切后48ms，临时关闭RV为33ms；全模组长距离最终56ms/p95 85ms/p99 123ms。不是RV内部单帧耗时，也不代表稳定30帧。测试只有当前192×60、current模式、少量敌人；更大/密集/联机及用户存档未验收。

旧安装包D5E0468E…B450EE在`../ContinuousScene/build/backups/install-20261014-181702/RealisticVisionMod.swf`（相对模组根）。整体回退依ContinuousScene/build/rollback.ps1及state/deployment-v02.json，配套根宿主、清单、WB一并恢复；先从大场景返回基地并保存。玩家游戏未关闭，正常重启后生效。
