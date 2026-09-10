# 墙内阴影复验

在 RealisticVision 模组目录运行：

```text
node build/wall-tests/run.mjs --baseline
node build/wall-tests/run.mjs
node build/wall-tests/run-game.mjs
```

第一条测试固定基线 8748feb，预期失败；第二条测试当前源码。
前两条共用临时编译目录，**必须顺序运行**。游戏验证用不同目录和 app id。
需要本机 Flex/AIR、Animate JRE、游戏自带 adl64/runtime；可通过 RV_FLEX_SDK、RV_JAVA 覆盖编译工具位置。

## 验证边界

- `WallHarness.as` 在独立不可见 AIR 程序中直接调用模组实际绘制方法，并用真实 Bitmap.draw 比较最终像素；临时源码只将 private 改为 public，方法体不替换、不重写算法。游戏类由编译存根与可控制 Location 夹具提供。
- 原版基准准确复刻 Grafon.setLight 的 **从 (1,1) 起写入**、(x,y+1)、(-20,-60)、40 倍平滑显示。覆盖横墙、竖墙、墙角、微光、邻接地板角、记忆、retDark、切模式、同尺寸换房、墙破坏、静止照明、门景与单位掩膜缓存。
- 0.8/1.25 缩放检查的是墙内部亮度；不将它表述为所有相机位置的边缝验收。12×10 性能循环只测渲染更新，不是完整游戏帧率。
- `GameProbe.as` 经测试副本已有 loader 启动，等待 allLandsLoaded 后新开独立存档、旅行至 random_mane。它直接运行当前模组的实际渲染函数，在同一帧的原版画面上做墙像素对照；不调用正常模组 startup，不做敌人战斗/快捷键/六模组合测。
- 完整游戏对照将 cfgFadeStep 暂设为 0、visCur 设为 1，以固定记忆进度而只检查原版墙形状。地板可见范围不同是正常模式差异；正常记忆衰减由夹具另测。
- 游戏副本仅包含公共游戏资源和本模组测试引导器，未复制或启动其他模组。游戏根 pfe.swf 与真实 release/config、真实 pfe 存档均不改动。
- 输出在 `build/wall-test-output/`（忽略目录）；程序有超时，退出后删除本次临时描述符。只使用 rv-wall-fixture / rv-wall-game-probe 的独立应用存储。

## 产物

baseline.log / candidate.log：断言、粗略耗时和 PNG 数据；baseline-*.png / candidate-*.png：控制场景；game/game.log、game/game-*.png：完整游戏对照。最终有用证据由测试报告归档，过程生成物可由脚本重建。
