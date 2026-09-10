# RealisticVision —— 开发记忆入口

> 更新：2026-09-10，v0.28.0 墙内阴影修复已部署。范围见 ../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。包含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current 三模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as；只支持根目录1.02宿主，DLC未装本模组loader。

## 2. 用户偏好与协作约定

- 本轮已授权修复 current 和 classic 墙内阴影；需要用户决定时使用 grilling。用户两次确认：墙按原版黑芯/亮面/渐变，只压暗原有光照；允许停止写原版亮度，地图/传送恢复原版曾见判定。详见 D22。
- 视觉修改先有同场景原版对照和离线复现，每次只改一个变量，再比较三模式并请用户目检。不要恢复已回滚的记忆播种/墙面受光传播方案。
- 游戏 SWF / 描述符与正式部署按工作区授权、发布门禁执行；用户随后明确说“部署”，本轮已部署正式 release。
- 血条勿强制 visible=true；沿用隐藏时压暗、恢复时 visDetails 重算。
- 跨模组只报告本模组兼容范围，不修改别人文件；发送外部消息须授权。
- 既有 MSW 未完成稿 stash 原样保留；完整集成已在0d1becc，不自动套用旧稿。

## 3. 当前状态

- **源码和正式 release 均为 v0.28.0，已部署**；修复提交 main / 35ecef6。部署复用通过验证的候选，没有重编译。
- 修复：墙用原版1px/格位图+原版位移直接显示，以互补 mask 与各模式地板分区；所有墙角（含邻地板）乘记忆衰减。删除全部 visi/t_visi 写入，门景仅增强显示；修零行零列恒黑和静止照明/单位掩膜同步。
- 独立AIR实际绘制：**39/39通过**，同套旧版9通过/30失败。横/竖/角墙可见像素差0，记忆取整误差≤2/255。
- 完整游戏副本：random_mane / loc0_4（48×25），current/classic各358,400墙像素差0，原版字段改写0。该对照固定记忆进度0、直接调用实际绘图函数；非正常startup/快捷键/战斗/六模组合测。
- 构建成功：build/RealisticVisionMod_test.swf，17,378字节；FFDec只含RealisticVisionMod，无游戏存根。源码SHA256：F7A7C001F665A64A685A5881503562E52E312D375933892ED1E19C71BCE2B571。
- 正式release SHA256：57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0。旧版备份：build/release_backup_v0271_before_v0280_20260910.swf（SHA256 9423F7D727191C0F090EDD0C2E50D43339643F70F69E9D0F05C33114AE86A56D）。需回滚时用此备份覆盖release/RealisticVisionMod.swf并重启。
- config未变，仍 enabled=1 / mode=current / dim=.35 / doordim=.5 / litmin=.6 / fadestep=.1 / maskblur_classic=6 / maskblur_current=4 / telegrace=3 / base_rooms空 / debug=0。
- 2026-09-10正式根目录pfe.swf与六模组release启动冒烟通过：新版本初始化、持续tick、MSW入口注册、F12事件进入cycleMode；独立app id隔离存档。仅主菜单启动/入口响应，不是三模式画面或六模组共同战斗验收。测试进程已结束，临时描述符已移除。

## 4. 当前实现与卡点

- 现行决定是 D22：原版维护照明记录，模组显示与游戏逻辑分开。D15的二元写入、v0.25.8墙恒亮、v0.25.9记忆播种均不是当前实现。
- current 地板保留8×8子格射线/模糊/单侧钳制；墙直接用原版位图，不再经过5px重采样后的二次平滑。fogCache中的墙子格只供地板滤镜/单位掩膜采样。
- classic 地板保留1px/格位移雾图；墙的邻地板角必须与地板记忆下限分开，避免弱光被抬亮。
- 原版与模组雾图的零行零列为恒黑；不能根据那些Tile的visi重亮边框。
- current 墙原版光照在站立期间也会改变；刷新墙采样，跨可见阈值才失效单位掩膜缓存，不重跑地板模糊。
- 原版同实例切房保留Tile亮度；磁盘存档不直接保存visi/t_visi。旧日志相关说法错误，勿据此播种记忆。
- 构建/夹具/完整游戏绘图及部署启动检查已过，**待用户目检整体衔接**。尚未验证所有墙装饰、相机边缝、长期性能和多模组共同战斗。

## 5. 其余已知问题

- MSW聚合页7项设置与旧Pip选项行仍待用户目检；本轮正式根目录启动中F12复现既有saveConfig的SecurityError:fileWriteResource。切换事件已响应，但配置无法持久化；本轮没有修此旧问题，config原文件哈希未变。
- 部分可见狮鹫手臂受internal限制；全隐时另扫手臂。当前掩膜使用cacheAsBitmap和模糊透明度，不沿用“mask必然二值”的旧结论。
- SATS在记忆区扫描、抓暗区敌人瞬间报警为既有接受取舍；用户本轮接受原版地图/传送判定后需随实测确认手感。
- 历史RConnect旅行后死亡只记录，不修别人模组。
- classic交替ENTER_FRAME更新，不能未经测量称30Hz。控制场景120次更新：旧版current301ms/classic12ms，候选303ms/38ms；不是完整游戏帧率。

## 6. 下一步

1. 用户下次正常启动即加载v0.28.0；同场景F12三模式目检：黑芯/整格坡、墙外衔接、记忆弱光、厚墙及门。
2. 后续修复设置保存失败；本次保留原config与默认current。
3. 追加真实敌人/血条/武器、念力宽限、地图传送、营地、设置页与多模组共同运行回归；出现新问题以具体截图/日志复现。
4. 不将本轮渲染数据和启动检查扩成所有玩法、所有环境或技能晋升结论。

## 7. 深入了解与复验入口

- **本轮报告**：knowledge/experiments/2026-09-10-wall-shadow-v0280-validation.md。
- **交互对照和原始断言**：knowledge/experiments/wall-shadow-v0280/。
- **部署实证**：同目录deployment-checks.json / deployment-runtime.txt / deployment-loader.txt；报告末尾“部署补记”。fingerprints.json保留部署前快照，勿重生成覆盖历史。
- **复验**：build/wall-tests/README.md；run.mjs --baseline（预期失败）→ run.mjs（候选）；run-game.mjs（完整游戏副本，新档）。
- **构建**：build/build_test.bat，仅写测试产物；build.bat/build.sh含旧路径且写release，勿直接用于检查。
- 工具：D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；Java：D:/Program Files/Adobe Animate 2024/jre；FFDec同tools/ffdec/ffdec.jar。
- 决策：decisions/decisions.md，现行墙方案D22；历程：state/journal.md。design/architecture.md和vision-system.md有旧历史，按D22校正。
- 历史截图shot_vanilla/current/classic.png与rv0253模拟保留作历史，不能当作当前实现验证。
- 后续运行/发布使用 remains-runtime-debug / remains-auto-testing / remains-release-gate / remains-swf-patching。
