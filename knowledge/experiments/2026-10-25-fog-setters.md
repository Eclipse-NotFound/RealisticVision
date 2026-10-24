被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build
技能归属：用户级（diagnosing-bugs）；Remains工作区（其余）
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# D49：雾层同值设置无整体收益，继续收窄计算热点

候选未采用，正式仍D44 v0.33.10（638E2D40…FE343710）。本轮414项画面检查通过，但完整战斗两模式均值和>100ms次数没有改善，不能据最大值下降部署。测试已结束，整体卡顿目标尚未完成。

## 范围和可证伪假设

准确基线为build/combat-render-output/production-final2/src，主源SHA256 cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d。没有叠加D45–D48失败方案，也未混入HEAD的authority开发。

ensureFog每帧重复设置scrollRect、colorTransform、blendMode、visible、位置；RVWallSurface重复挂mask和设置层次。本轮只在实际属性相同时跳过setter，颜色检查全部8个分量，外部修改仍恢复。常亮路径截图前的必要临时解罩保留，没有减少刷新或改变视野/动画算法。

预测为：若这些同值设置造成显著重复合成失效，候选应在完整战斗中减少整帧间隔。结果未支持有可采用的收益，不能反推引擎内部完全没有失效。

## 画面验证

- FogChecks：120帧严格整雾像素相同。小/大房尺寸切换、current/classic、红外切换、镜头缩放/平移，另主动改变crop、颜色变换、blendMode、visible、mask和位置，确认下一次ensureFog修复。
- EquivalenceChecks：230项严格相同。复用D39冻结的移动视口、墙形/材质alpha变化、半高墙、常亮开关、已知/未知、NaN、透明重叠材质、扫描中断后恢复及分数缩放夹具；基线helper改为准确D44。
- 原生大型场景：192×75格，96个合成单位，8组模式/常亮/亮度/柔化/视距组合，64次整雾和原始场严格相同，含红外切换与外部显示状态扰动。保留父容器捕获；在比较前移除了旧工具主动扩大classicLogicRegion的调用，D44对D44直接比较完整原始字段。此为画面回放，不将其计时用于性能结论。

local-01/checks.json的summary因日志末尾空行而为空，不能据此推断通过项数；数量来自原始FogChecks.log与EquivalenceChecks.log的COMPLETE行（120、230），两个进程均退出0。原生validation为64/exit0。没有失败截图或人工新画面验收，不将数值相同描述成新的视觉效果改善。

## 干净完整战斗

combat-01，启动可用内存8,172,244,992B，无其它AIR/Java；启动CPU快照33.4%，不能代表全程系统空闲。14个manifest入口requested/ok一致，RV基线/候选由探针在子域额外加载。独立AIR ID、隐藏桌面、HighQoS仅测试进程，正式启动策略未改。

原训练房14单位加6名原生佣兵，真实AI、SMG、弹体和粒子继续。两模式各off/normal/candidate/candidate/normal/off，暖机210帧，采样180帧，每条件358个配对间隔，共2148。受控位置限制击退/飞行造成的路线差异，不是自由游玩。未并行归档、去重、编译或重IO。

| 模式 | 条件 | 平均ms | P95 | 最大 | >100ms | RV更新平均ms |
|---|---|---:|---:|---:|---:|---:|
| current | 关闭RV |43.53|61|110|1|0.01|
| current | D44 |61.47|84|232|5|13.11|
| current | guard |61.77|87|132|7|13.20|
| classic | 关闭RV |42.88|57|97|0|0.00|
| classic | D44 |65.70|99|182|15|13.58|
| classic | guard |66.44|95|135|16|13.69|

两模式均值略高、>100ms略多；不以最大值下降或classic单项P95改善掩盖整体未达标。没有为这个候选继续跑自由战斗、生产设置或部署门禁。正式包不变。

## 原始D44的短时热点诊断

profile-01从D44另建未优化的profile-base，两个模式各预热90/采样180，分段与函数嵌套计时仅用于下一步定位。不是上述候选，也不是新的性能验收；不将此轮绝对帧率与combat-01拼接。

| 路径 | current ms/帧 | classic ms/帧 |
|---|---:|---:|
| applyVision / applyVisionClassic |5.800|3.239|
| fillFogCache |4.556|不走此路径|
| updateWallSurface |2.611|2.589|
| hideEnemies |4.911|7.400|
| applyWorldVisuals（包含于hideEnemies） |3.678|5.178|
| refreshMask（跨身体和效果，嵌套） |2.517|5.006|
| classicLogicRegion（嵌套） |不走此路径|3.456|
| 对象边界/记录准备 |0.589|0.728|
| 效果明暗coverage判定 |0.350|0.450|
| worldVisualHasFilters（嵌套） |0.044|0.022|

每帧约82/88次applyWorldVisual，97/91次refreshMask，classic约57次classicLogicRegion；current约394次fillWallTile、52次recalcTile。嵌套项不能相加，插桩自身有成本，毫秒分辨率不适于解释单次微调用。

下一步优先验证classic重复生成原始插值工作图的复用：可以考虑提前生成私有工作像素，但必须只按原查询的确切范围发布到fogCache，不能重复D40扩大查询改变显示的问题。先核对实际调用重叠和失效条件，再提出候选。current另查fillFogCache的墙格/边界填充；尚未实现，不承诺收益。滤镜树检查较小，不再作为首要方向。

## 收尾与边界

D48上一轮收尾已核对并提交eb5095a，报告台账补登记。本轮测试工具build/fog-setters，原始输出build/fog-setters-output，长期证据fog-setters-d49-20261025。共享登记、实例及描述符按自有测试收尾，无操作玩家进程、无写真实pfe存储，无出站协调消息。

CS回报线程CPU诊断已退出，并请求后续绘制精度诊断窗口；属于协作回报，未据此作本轮性能结论。D49最后短诊断结束后不再追加AIR/JVM，归档如遇既有测试先等待。候选未部署，4项外部WIP保留；目标仍active。
