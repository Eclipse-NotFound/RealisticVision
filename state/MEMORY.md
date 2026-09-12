# RealisticVision —— 开发记忆入口

> 更新：2026-09-12，v0.28.1 classic小墙块投影修复候选已验证，未部署。范围见../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。包含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current三模式。入口RealisticVisionMod，源码src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组loader。

## 2. 用户偏好与协作约定

- D22两次明确确认：两模式墙按原版黑芯/亮面/渐变，只压暗原光；原版维护visi/t_visi与地图/传送判定。地板保留模式区别。
- 本轮grilling定位：主要是“阴影位置偏移、不贴墙”，具体在“上方伸出的小墙块附近”。未收到重复询问保留D22的Q3答复；依既有授权和Q1/Q2实施，不把沉默记成确认。
- 视觉修复先同场景原版/旧版对照和实际AIR复现，每次只改一个变量；原游玩进度仍需用户目检。不要恢复记忆播种、墙面受光传播旧方案。
- 2026-09-10“部署”已完成v0.28.0；其后的本次问题反馈完成候选，正式release尚未替换。后续部署走发布门禁和独立启动检查。
- 血条勿强制visible=true；保持隐藏压暗、恢复由visDetails重算。
- 不写其他模组；既有MSW WIP stash保留，完整集成在0d1becc，不自动套用旧稿。

## 3. 当前状态

- **源码/测试产物v0.28.1，正式release v0.28.0；本轮未部署。** 仓库main，候选提交包含本记忆、D23与实证。
- classic修复：原版格角光照与中心FOV/记忆分开插值；地板合成到5px工作图；墙继续原版尺寸直接显示。敌人掩膜读取同一合成结果。
- 最小墙角：旧20.25px偏差→候选0.25px；10个方向/缩放对独立中心场差0。掩膜分类差2086→0，静止缓存稳定。
- 切回current同记忆初始14帧/外围差0；无暗邻居墙外亮度差0；记忆接缝99→255单调，最大单步16；原39项全部通过。
- 完整训练房rbl/loc1_0：同输入current整图差0，classic/current墙内差0，原版字段改写0；小墙顶轮廓x939→959，墙角x960。
- 构建build/RealisticVisionMod_test.swf成功，17,656字节；FFDec仅RealisticVisionMod，无fe.*。源码SHA256 3B7F1D43B22DCB14B304D19E0584E6D2C7B8A0867279A0A70C0D1E24A157FD6E；测试SWF SHA256 1B20528A8DAD9D48D435391E628D15286E90A9561699F94F907BFD0BE6A47DFB。
- 正式release SHA256仍57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0。config仍5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F；默认current、dim=.35，未改。

## 4. 当前实现与注意点

- D23补充D22：native光照样本在格角，computeFov在格中心，不能把二者先混合再整体平移。classic保持40px粗格插值，不是current的子格射线。
- 墙面可见性有邻居传播；用于地板投影时，墙中心延续相邻地板最深的记忆，避免端点提前消失。全图先推进记忆再取邻居，淡入淡出一致；无暗邻居/retDark不额外补遮挡。
- 全透明像素必须规范为0，BitmapData不会保留其RGB，否则静止时永久重绘。RGB反相后copyChannel转黑雾alpha；不能直接反转透明度，会跳过alpha0像素挖出亮洞。
- classic借用fogRaw/fogCache/fogBmp；同尺寸resetRoom必须清黑三图和fogBlurPending，否则切current初始淡入留旧图/白边。
- 墙图独立保留原版角位置与弱光，墙邻地板角也仅乘记忆衰减；零行零列仍恒黑。current静止原版照明与墙掩膜采样保持刷新。
- 原版同实例切房保留Tile亮度，磁盘存档不直接保存visi；不能据旧日志播种探索。

## 5. 已知问题与验证边界

- classic粗格插值仍会在正在投影的薄墙可见侧产生约20px渐变。实景小墙x960亮度129，至x985恢复255；无暗邻居墙边未额外变暗。一个掠角对连续切线仍差21px，中心场一致不等于所有多边形边界精确。
- 分场合成增加classic开销：完整48×25房60次更新，存档旧149ms/候选487ms；另轮候选273ms，环境噪声显著。不是实际帧率或长期性能结论；稳定场不重复合成已测。
- v0.28.1完整游戏验证直接调用实际绘图方法，没有正常startup、快捷键、战斗或六模组联动验收。
- v0.28.0正式根目录六模组启动冒烟曾通过，F12复现既有saveConfig SecurityError:fileWriteResource；本轮未扩修。MSW设置页7项与旧Pip行仍待目检。
- 部分狮鹫手臂受internal限制；SATS记忆区扫描及抓暗区敌人瞬间报警为历史取舍。真实敌人/血条/武器、念力、地图传送和长期游玩仍待扩测。

## 6. 下一步

1. 用户查看本轮小墙对照；后续部署v0.28.1时复用已验候选，并为当前v0.28.0新建唯一备份，再走正常入口冒烟。尚无v0.28.0回滚备份，不得误用v0.27.1备份代替本次部署前版本。
2. 保留现有build/release_backup_v0271_before_v0280_20260910.swf（SHA256 9423F7D727191C0F090EDD0C2E50D43339643F70F69E9D0F05C33114AE86A56D），它仅是上次部署回滚点。
3. 正常进度下目检小墙/薄墙渐变及移动开销；必要时继续按具体问题复现。
4. 设置持久化、真实战斗/血条/念力/地图传送等未在本次修复中扩写。

## 7. 深入了解与复验

- 本轮报告：knowledge/experiments/2026-09-12-classic-wall-edge-offset.md；实证/交互对照：classic-edge-v0281/。
- 前轮D22墙内验证：knowledge/experiments/2026-09-10-wall-shadow-v0280-validation.md及wall-shadow-v0280/；部署实证deployment-*仍保留。
- 复验：build/wall-tests/README.md。run.mjs --edges --revision 6c0170e（预期失败）→ --edges；run-game.mjs --training --revision 6c0170e → --training；compare-training.py断言输入一致/current未回退/墙内未变。共享输出目录必须顺序运行。
- 构建：build/build_test.bat只写测试产物；旧build.bat/build.sh含旧路径且写release，勿用于检查。
- SDK：D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；Java：D:/Program Files/Adobe Animate 2024/jre；FFDec同tools/ffdec/ffdec.jar。
- 本轮AIR/FFDec在普通沙箱失败，经工具级放宽后通过；仍只用独立app id/副本，未读写真实pfe存档。
- 原因：decisions/decisions.md D22/D23；历程：state/journal.md。design旧文和历史截图不等于当前实现/验收。
