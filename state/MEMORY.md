# RealisticVision —— 开发记忆入口

> 新会话从这里开始。协议见工作区 GOVERNANCE.md §8；本模组参数见 ../AGENT_SCOPE.md。

## 1. 这个模组是什么

视野系统模组：三态视野（未探索全黑 / 视野内亮 / 记忆区暗色隐藏敌人），含破坏墙、透光门、敌人部分可见裁剪、念力规则（隔墙抓物品可、抓敌人不可）、三档渲染模式（`vanilla` 透传 / `classic` 仿原版 / `current` 平滑阴影，F12 轮换）。源码为单文件 `src/RealisticVisionMod.as`（约 2330 行），入口类 `RealisticVisionMod`。

## 2. 用户偏好与协作约定

- **每次修改后请用户游戏内实测**（F10 面板 / F12 模式 / PipBuck 面板）——本模组大量修复史由用户观感反馈驱动。
- 修复血条问题时勿无条件 `hpbar.visible=true`（历史教训：曾致全敌人满装甲条，用"隐藏时压暗 + 恢复时 visDetails 重算"）。
- **pfe.swf 改动需多模组协调**：改前必须反编译核对线上加载器清单（2026-08-17 时为 5 个），他人改动先合并。
- 跨模组问题只报告不修对方文件（grafon-drawallobjs 表述错误已交 Sandevistan 维护者修正）。
- 本模组仅支持 1.02；DLC 两份 SWF 从未打过本模组 loader。

## 3. 当前状态

- **v0.24.7**（2026-08-21）：current/classic 性能优化五处（fov 重算节流 / 模糊钳制拆帧 / classic 30Hz 门控 / 武器扫描门控 / classic 掩膜采样零 raycast）——**待用户实测确认**。
- 已定论：GPU 渲染不可行（renderMode 由 application.xml 启动时决定，模组无法更改；开销在 CPU 侧计算）。
- 游戏本体文件未改动；git 27 提交，工作树干净。
- 部署：`release/RealisticVisionMod.swf` + `config.txt`；回滚 = `pfe_1.02_before_rvision_merge_20260815.swf` 或删除模组目录。

## 4. 正在进行与卡点

- v0.24.7 五项性能优化 + v0.24.6 两项修复（贴墙敌人武器误显 / 原版隐身敌人残留）均待用户实测反馈。

## 5. 已知问题

- 部分可见敌人的狮鹫手臂无法裁剪（internal 成员），全隐时手臂会被扫描隐藏。
- 掩膜形状随 drawAllObjs 重建后孤儿化已处理；mask 对象在单次房间会话内随死亡敌人累积（量级可忽略）。
- Sats 卫星扫描器把记忆区当可见（D3 取舍）；抓取暗区敌人瞬间 alarma() 已触发（D5 副作用）——均为已接受取舍。
- 敌人掩膜二值限制：Flash mask 是二值的，5px 子格是锯齿上限。
- classic 光缘最外圈 ~12-28px 过渡位置与原版有微小偏差（接受）。

## 6. 下一步（运行时验证清单，按序勾销）

1. 亮边与厚墙内部（进黑房间沿墙走动、破坏墙后观察）；
2. 念力宽限（拖敌出视野 3 秒中断 / 拖回不中断）；
3. 部分可见（敌人站视野边界只显示视野内部分，hpbar/武器同步裁剪）；
4. 门（关门后门后区域全暗）；
5. 暗区武器/手（掠夺者/狮鹫完全不可见）；
6. 营地无雾（腾飞小马营地，未生效则 F11 关闭并报告房间）；
7. F11 开关 / F10 面板 / config.txt 读写；
8. 帧率（雾层逐帧写 + 掩膜重绘开销）；
9. 与 Sandevistan（慢速/冻结）和 RConnect 的兼容性观察。

## 7. 深入了解

- **开发历程**：state/journal.md（v0.2→v0.24.7 共 52 个版本的完整流水：每版"用户反馈→根因→修复→验证"，多数无日期标注）
- **架构必读**：design/architecture.md（注入与构建 / 渲染管线三模式 / 敌人显示三态 / 配置表 / 常用操作命令）
- **设计**：design/vision-system.md（v0.2 起含修订记录）
- **决策**：decisions/decisions.md（D1-D20；D19 教训：平滑来自光源模型而非空间滤波）
- **实证**：knowledge/（光照管线/掩膜错位/念力机制/构建实验，含像素级模拟 js/as）
- **构建**：`cd build && bash build.sh`（stubs SWC + amxmlc）；产物验证 `ffdec-cli -dumpAS3`（期望只含 RealisticVisionMod）
- **技能**：remains-mod-build、remains-runtime-debug
