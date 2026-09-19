# RealisticVision —— 开发记忆入口

> 更新：2026-09-19。用户授权后已部署独立念力热修复v0.28.0-grabfix.1；v0.28.1墙边阴影仍在另一路修复，未随本次发布。范围见../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。包含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current三模式。入口RealisticVisionMod，源码src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组loader。

## 2. 用户偏好与协作约定

- D22两次明确确认：两模式墙按原版黑芯/亮面/渐变，只压暗原光；原版维护visi/t_visi与地图/传送判定。地板保留模式区别。
- 上轮定位是“上方伸出的小墙块附近，阴影位置偏移、不贴墙”；本轮截图重点为“墙边亮带、拐角接缝”，不能混为同一症状。
- 视觉修复先同场景原版/旧版对照和实际AIR复现，每次只改一个变量。既要查墙内，也查墙/地板交界；纯阴影比较先核对全部输入一致。
- 不把“检查亮带”自动解释为改变D22渐变范围。原版自身也有宽亮面；若收窄需具体对照和新的目标确认。原游玩进度仍需目检。
- 2026-09-10已部署v0.28.0；2026-09-19用户在TDFC任务回答“允许”，明确授权本次念力修复合入与正式部署。授权不扩展到阴影候选发布；不新增委托、不用Ghost。
- 不写其他模组；既有MSW WIP stash保留。血条勿强制visible=true；恢复由visDetails重算。不要恢复记忆播种、墙面受光传播旧方案。

## 3. 当前状态

- **正式release为v0.28.0-grabfix.1，SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969。源码仍承接v0.28.1阴影工作；其旧候选接缝测试失败，未部署。** 念力守卫已单独提交a583f1a；并发阴影源码修改完整保留，没有混入该提交。
- 热修复仅补齐blockInvisibleGrab的vanilla/基地/配置安全房间透传条件。正式v0.28.0的原版显示不更新FOV，旧输入守卫却读全零FOV，误拦Q/右键；三模式候选36正例＋6基础LOS负例通过。正式路径独立启动cff44575再通过12＋2，设置注册和版本心跳正常；用户游戏需正常重启生效。
- 完整1.02训练房、两位置、同一探索路线：输入全同；current整图差0、两模式墙内差0，但classic墙/地板接边额外亮度跳变旧3/4→候选166/84（0..255）。原版参照也有墙边亮面，不能据此宣称用户截图所有细节已解释。
- 最小接缝夹具：v0.28.0 8/8通过；v0.28.1 7/8失败，全记忆最大相邻差89。只显示地板场后差0；统一半透明场无裁切漏缝；简单平移记忆矩阵仍差87。
- 原39项、小墙端点20.25→0.25px等旧证据仍成立，但不覆盖新接缝，不能替代它。念力专项不改变墙边候选的验收状态。
- 墙边诊断阶段的历史指纹：源码3B7F1D43B22DCB14B304D19E0584E6D2C7B8A0867279A0A70C0D1E24A157FD6E；旧测试SWF 1B20528A8DAD9D48D435391E628D15286E90A9561699F94F907BFD0BE6A47DFB。它们不再代表并发修改后的当前源码。旧正式57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0已备份为build/release_backup_v0280_before_grabfix_20260919.swf。
- 正式config仍current、dim=.35、debug=0，SHA256 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F。真实日志最近init是v0.28.0；既有saveConfig错误栈未扩修。

## 4. 正在进行与卡点

- D23将classic格角光照与中心FOV/记忆分开插值，墙中心延续邻地板记忆；地板合成到5px图，墙继续D22原尺寸显示。两张场各自平滑，**交界却不是同一亮度**：这是候选新硬接缝的已证原因。
- 修复必须同时保住D23小墙端点、D22墙内层次、未探索不漏亮。不能简单平移整个记忆场、删除墙层或把记忆全涂黑。墙边诊断后的源码修改正由原任务继续；念力任务不替其选择实现或宣布验收。
- 截图位置根据梯子/墙几何估计。正式v0.28.0复现场景未测出大硬接缝；原版也有类似宽亮边。未重放用户精确存档/相机/移动过程，截图细节的完整归因仍有边界。
- 测试取图注意：visLight自身有40倍缩放与(-20,-60)位移，BitmapData.draw需传入transform.matrix；沿路必须调用原版lighting/lighting2。错误早期参照已丢弃，归档是校正后的成对输入。

## 5. 已知问题

- current同一路线也有较大的边界明暗差（最大139/149），两版本相同；本次classic检查没有扩改current。
- v0.28.1粗格掠角、薄墙可见侧约20px渐变与增加的合成成本仍在；新增硬接缝不能再仅归入这些旧限制。
- v0.28.1阴影候选的正常startup、快捷键、真实战斗/血条/武器、念力、地图传送和六模组联动仍未验收。v0.28.0-grabfix.1已通过独立启动及六模组念力专项，不能代替阴影或长期玩法验收。用户原失败现场的实际模式未知，仍待重启后复验。
- F12的saveConfig SecurityError:fileWriteResource、部分狮鹫internal手臂限制、SATS记忆扫描/抓暗敌瞬间报警等历史问题仍未扩修。
- classic复用fogRaw/fogCache/fogBmp；同尺寸resetRoom必须清黑三图及fogBlurPending。透明RGBA需规范为0，避免静止重复合成。这些已修逻辑勿回退。

## 6. 下一步

1. 优先解决候选接缝：run.mjs --seams当前应失败；在同一失败用例上修，再重跑完整training --seams，并回归--edges和D22墙内39项。
2. 对原版自身宽亮面，保持当前D22目标；如要改变，先制作具体效果供用户判断，不擅自收窄/涂黑。
3. 阴影候选仍须独立验收再部署，并保留a583f1a的念力守卫。下次正式发布前应备份当前v0.28.0-grabfix.1；本次热修复回滚为build/release_backup_v0280_before_grabfix_20260919.swf（57FA…B6E0）复制回release并重启，不覆盖唯一备份。
4. 保留build/release_backup_v0271_before_v0280_20260910.swf（9423F7D727191C0F090EDD0C2E50D43339643F70F69E9D0F05C33114AE86A56D），它仅是上次部署回滚点。

## 7. 深入了解与复验

- 墙边报告：knowledge/experiments/2026-09-19-classic-wall-seams.md；图片、输入、指标和交互对照：classic-seams-20260919/。念力授权、构建来源、三模式证据和正式部署回执在../TDFC/knowledge/experiments/telekinesis-vision-validation-2026-09-19.md；本项目journal有自包含回滚记录。
- 前轮小墙：2026-09-12-classic-wall-edge-offset.md、classic-edge-v0281/、D23；原墙层次：2026-09-10-wall-shadow-v0280-validation.md、wall-shadow-v0280/、D22。
- 复验入口：build/wall-tests/README.md。新夹具run.mjs --seams；完整run-game.mjs --training --seams；旧版加--revision 6c0170e。Python inspect-seams.py先--baseline再候选。共享game/目录必须顺序运行。
- 构建只用build/build_test.bat，旧build.bat/build.sh含旧路径并写release。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；Java D:/Program Files/Adobe Animate 2024/jre；FFDec同tools/ffdec/ffdec.jar。只读取共用工具链，不读取其他模组源码。
- AIR普通沙箱可能失败，工具级放宽只运行独立app id/资源副本；禁止写真实pfe存档。带Pillow的Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。
- journal最新条目接续本轮；旧报告/旧对照页是历史范围，不能替代当前失败结果。
