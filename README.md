# RealisticVision —— 《Remains》视野系统模组

实时视野更新：未探索区域全黑、当前视野内正常显示、离开视野的已探索区域暗色显示
（保留场景/地形/物品、隐藏敌人）。支持可破坏墙壁、玻璃门暗色视野、敌人念力移动
物品实时显示、玩家隔墙念力（物品可、敌人不可）。

## 目录

```text
src/                 模组源码（RealisticVisionMod.as，文档类）
build/
  build.sh           构建脚本（Git Bash）
  stubs/             游戏公共 API 编译期存根（勿随 release 发布）
  GameStubs.swc      构建中间产物
  patched/           MainFE 加载补丁（pfe_patched_out.swf + MainFE.as）
  decompiled-current/ 研究用：当前 pfe.swf 的 MainFE 反编译
release/             模组产物 RealisticVisionMod.swf
design/              架构设计（vision-system.md）
decisions/           技术决策
state/               当前开发状态（current-status.md）
knowledge/           模组专属发现/实验
```

## 构建

依赖（本机路径，见 build.sh）：

- Git Bash + Java 8
- Apache Flex 4.16.1 SDK（`C:\Users\micha\Documents\_sandevistan_dev\flexsdk`）
- FFDec（`C:\Users\micha\Documents\_sandevistan_dev\ffdec`，仅用于补丁/研究）

```bash
cd build && bash build.sh
# -> release/RealisticVisionMod.swf
```

## 加载补丁（已部署，见 state/current-status.md 合并记录）

游戏 pfe.swf（1.02，SWF41）的文档类 MainFE 已被修改为加载三个模组：
Sandevistan、RConnect、RealisticVision。本模组加载器指向
`app:/mods/RealisticVision/release/RealisticVisionMod.swf`（文档类静态
`RealisticVisionMod.init(main)`）。

- 合并源码：`build/patched/MainFE_merged.as`（三方合并版）
- 合并产物：`build/patched/pfe_merged.swf`（已部署到游戏根）
- 重新生成：`ffdec-cli -replace pfe.swf out.swf MainFE build/patched/MainFE_merged.as`
- 回滚：游戏根 `pfe_1.02_before_rvision_merge_20260815.swf`
- DLC 下其他版本（1.03/1.04）由 RConnect 补丁覆盖，本模组暂不部署。

## 配置与游戏内调试

- `release/config.txt`：enabled（总开关）、dim（记忆区暗度 0.35）、doordim（透光
  门/水后视野亮度 0.5）、litmin（可见阈值 0.6）、fadestep（平滑步长）、telegrace
  （拖敌出视野宽限秒数 3）、base_rooms（追加安全基地房间 id，逗号分隔）、debug。
  修改后重启生效。
- **F11**：运行时开关渲染模式（写回 config.txt）。
- **F10**：诊断面板（房间、visible/dim/unexplored 计数、念力倒计时、当前模式）。
- 关键事件走 `trace`（RVision 前缀）。

## 已知取舍

见 `state/current-status.md` 与 `decisions/decisions.md`。
