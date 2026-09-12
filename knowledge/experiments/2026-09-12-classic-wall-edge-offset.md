# 2026-09-12 classic 小墙块投影偏位修复

被测技能：remains-auto-testing / remains-runtime-debug / diagnosing-bugs（生产故障修复，非技能晋升测试）
技能归属：D:/Program Files/Steam/steamapps/common/Remains/.agents/skills；C:/Users/hello/.agents/skills
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

## 结论与交付状态

v0.28.1候选已修复训练房间上方小墙块投影偏位。真实AIR最小场景的墙角轮廓偏差从20.25px降到0.25px；实际训练房间的墙顶外一行，半暗轮廓从x=939移至959，墙角x=960。同输入下，current整张阴影图差0，两模式墙内像素差0，原版亮度字段改写0。

源码与测试产物为v0.28.1；**正式release仍为v0.28.0，配置未改，本次未部署**。此前“部署”指令已在2026-09-10完成v0.28.0部署；本次为其后的问题反馈与候选修复。候选正常startup、正式路径快捷键和共同战斗未验收。

可查看[同场景交互对照](classic-edge-v0281/comparison.html)，切换纯阴影、整房间和小墙轮廓。画面由游戏实际绘制，未用生成式图像替代验证。

## 用户澄清与范围

- Q1：用户明确“主要是阴影位置偏移、不贴墙”，不是亮带强弱。
- Q2：具体位置是“上方伸出的小墙块附近”，不是厚横墙下沿或下方房间。
- Q3曾再次询问是否保留墙内原版层次与current，收尾时未收到答复。未把沉默当作同意；按已有D22明确授权和本次Q1/Q2定位继续修复，未扩大到墙内重绘或current观感重做。
- 改动可由候选提交回退。原版游戏文件、真实pfe存档、其他模组和既有MSW stash均未改。

## 复现与因果证据

目标是rbl训练房间loc1_0，48×25格。墙块占(23,10)/(23,11)，世界范围(920,400)-(960,480)；玩家约(1080.8,640)。独立新档先出生在begin，等待加载完成后beginMission("rbl")，再通过gotoLoc(2)进入训练房间；未使用任意gotoXY或直接改curLandId。

原版Grafon和v0.28.0 classic把输入写入(tx,ty+1)，按40倍、(-20,-60)显示，样本中心在格角。computeFov却向(tx+.5,ty+.5)×40的格中心投射。把二者先混成一个像素再通过格角管线显示，会把视野/记忆投影向左上偏半格。

最小复现：12×10格，仅(6,4)/(6,5)是墙，眼点(400,320)，墙范围(240,160)-(280,240)。真实computeFov后运行24次classic更新，在y=159取半暗轮廓最右端。几何切线为x=279.25。

    v0.28.0原样               expected=279.25 actual=259 offset=20.25
    只把地板位图平移(+20,+20)  contact=279
    只取消墙/地板裁切           contact=259
    格中心射线与矩形几何不符    0处
    v0.28.1最终候选             expected=279.25 actual=279 offset=0.25

整体平移仅用于定位，因为它同时移动原版照明。最初解除mask后白色Shape自行显示的对照已作废，存档是隐藏Shape后的有效结果。[原始探针](classic-edge-v0281/v0280-edge-probes.txt)保留完整日志。

## 最终实现（D23）

1. classicRaw只存原版格角光照与门景增强；classicMemoryRaw单独存格中心记忆进度及目标亮度。分别平滑插值到5px工作图，再合成为黑色透明度。未套current的射线、距离和模糊算法。
2. 墙仍由原版尺寸wallRaw/wallBmp直接显示；墙/地板裁切互补，visi/t_visi继续只读。
3. “墙面可见”邻居传播不能用来开放地板投影端点。墙中心延续相邻地板最深的记忆，使用全图推进后的同帧值跟随渐变。没有暗邻居时不补遮挡，避免给整圈可见墙边加黑带；retDark不补遮挡。
4. 部分敌人裁剪读取合成后的fogCache，修复旧classicRaw错行、错相位取样。墙格补入实际墙采样。
5. 全透明记忆像素规范为0，避免BitmapData丢弃透明RGB后不断误报变化。换房/切模式重置共用三张工作图及待办模糊，消除旧classic RGB与外围残留。

已排除的候选：直接反转透明度会因AIR跳过零透明度像素而挖出亮洞，改为反转不透明RGB后复制通道；全部墙中心一律黑会额外压暗无投影墙边，已收窄为相邻地板记忆延续。均非最终候选行为。

## 自动化结果

| 检查 | v0.28.0基线 | v0.28.1候选 |
|---|---:|---:|
| 最小小墙墙角偏差 | 20.25px，失败 | 0.25px，通过 |
| 8方向/布局、2相机缩放与平移，相对独立中心场 | 1/10通过 | 10/10通过，差0px |
| 未探索区 / 可见区亮度 | 0 / 255 | 0 / 255 |
| 部分敌人掩膜与画面分类不一致 | 2086个取样点 | 0 |
| 静止收敛后缓存版本 | 稳定 | 稳定 |
| classic→current初始14帧，对同记忆的干净current | 差0 | 差0，含外围 |
| 无暗邻居墙外，20%/50%/100%原版亮度 | 差0 | 差0 |
| 记忆阴影重新可见时的接缝取样 | 错位点一直255 | 99→255，最大单步16，单调 |
| 原有墙内阴影、记忆、门、破墙、同尺寸换房等 | 此前39/39 | 本轮39/39 |

掩膜检查使用实际applyMask和fogVis.draw，在5px格中心比较140透明度阈值，忽略阈值附近±1取整。它验证取样对齐，不是所有真实敌人姿势、血条或武器的战斗验收。

独立中心场使用矩形相交计算，不调用模组射线。它验证坐标一致，不把classic的40px插值误称为精确多边形阴影：一个水平掠角相对连续切线仍差21px，两者采样模型不同。

证据：[边缘基线](classic-edge-v0281/edge-baseline-results.txt)、[边缘候选](classic-edge-v0281/edge-candidate-results.txt)、[原有39项](classic-edge-v0281/wall-candidate-results.txt)。被测源码只将private开放给夹具，方法体不替换；游戏类由测试存根提供，AIR绘图真实执行。

## 完整训练房间

两版各开隔离实例，用实际游戏类和同一照明输入调用模组绘图方法。training-data中的房间、眼点、几何、原版亮度、FOV、探索/记忆数组完全相同；比较脚本先断言该条件，再比较纯阴影图，排除场景动画噪声。

- current：1920×1000阴影图变化0像素；墙内差0。
- classic：193,814个地板/边界像素改变，墙内差0；小墙顶外y=399的半暗轮廓939→959。
- 两模式visi/t_visi改写0；有改写时脚本直接失败。
- 剩余柔化：正在投影的单格厚墙，其中心样本仍影响两侧。小墙右侧y=440，x=960亮度由255降至129；x=965/970/975/980为163/195/227/249，x=985恢复255。它是当前classic粗格场约20px可见侧渐变，不能宣称所有墙外亮度都未改变。

[比较数据](classic-edge-v0281/training-comparison.json)、[基线记录](classic-edge-v0281/training-baseline-results.txt)、[候选记录](classic-edge-v0281/training-candidate-results.txt)。CAPTURED仅表示采集完成；通过证据来自像素/输入断言和目检。未启动正常模组startup、快捷键或共同战斗；副本缺其他模组文件的URL Not Found属于刻意隔离。

性能为单次计时，非游戏帧率或受控基准：48×25房间60次更新，存档中的classic基线149ms、候选487ms；current基线1990ms、候选2249ms。classic增加分场合成与掩膜取样成本，未宣称性能不变。先前同候选逻辑一轮为273ms，环境噪声也明显。静止时不重建合成图的断言通过；长期大房间、移动与战斗开销待实测。

## 构建与环境

- build/build_test.bat返回0；build/RealisticVisionMod_test.swf为17,656字节。FFDec -dumpAS3只输出RealisticVisionMod 0，无fe.*存根。
- 源码SHA256：3B7F1D43B22DCB14B304D19E0584E6D2C7B8A0867279A0A70C0D1E24A157FD6E。
- 候选SWF SHA256：1B20528A8DAD9D48D435391E628D15286E90A9561699F94F907BFD0BE6A47DFB。
- 正式release仍为57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0；config仍为5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F。[完整指纹](classic-edge-v0281/fingerprints.json)。
- 普通沙箱读取真实RV日志/CIM被拒绝，未获取真实游玩日志。普通沙箱AIR夹具超时、FFDec配置读取失败；通过工具级放宽后隔离测试和只读类检查成功，自动审核未拒绝。这些环境失败不记为模组故障。
- 测试仅用独立app id和副本；进程退出，临时描述符删除。系统PATH没有python，像素比较使用Codex依赖包路径。

## 本次产物与后续

复验入口为build/wall-tests/README.md。新增WallEdgeHarness、--edges/--revision/--probes、--training、compare-training.py、make-edge-evidence.mjs、上述实证和交互对照；原39项的弱光断言改为读取最终墙像素。

子代理classic_boundary_audit提供只读源码审查，指出透明RGB缓存和切换残留风险；主线均实际复现并修复。代理意见不是像素通过证据，未取得代理消耗统计。依grilling的事实委托要求执行，未另行加载parallel-delegate技能。

经验归属：坐标场混用与墙中心衔接属本模组，现落本报告及D23；原有D22仍成立。AIR/FFDec沙箱差异是2026-09-12单次环境观察，仅留本次记录，不更新正式技能或宣称晋升。

后续按发布流程处理候选部署与独立启动检查，并由用户在原进度目检小墙块；保留classic粗格渐变、薄墙可见侧和性能的上述验证边界。
