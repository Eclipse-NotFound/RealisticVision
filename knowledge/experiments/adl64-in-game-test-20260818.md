# 实验：adl64 真机实测记录（v0.22.1，2026-08-18）

## 目标

用户反馈 current 模式最顶层像素锯齿（建议参考原版 smoothing 思路），并明确
要求启动游戏实测。本轮实现 fogBitmap smoothing=true 后，用 adl64 + RConnect
自动化技能尝试"启动到进实战"的完整实测。

## 实测过程与结论

### 1. 环境准备（RConnect 技能：docs/automated-testing.md + shared-knowledge）

- AIR 单实例陷阱：测试实例必须**唯一 app id**（pfe5/pfe6 + 临时描述符），
  否则 "invocation forwarded to primary instance"（我第一次用 application.xml
  就中招）；
- 存档隔离：`%APPDATA%\<appid>\Local Store\#SharedObjects\<swf名>\`；
  游戏存档 = SharedObject（PFEgameN.sol），**不是游戏目录 .sav**；
- trace 在 release 构建被编译剥离（反编译证实本模组所有 trace 消失）——
  改用**文件日志**（applicationStorageDirectory/RVision.log，RConnect 同款）；
- 驱动进实战：RConnect autoGame=1 配置（关菜单 mm.active=false →
  newGame → comLoad/等待 gg）自动完成。

### 2. 关键发现（按时间线）

1. **模组加载正常**：MainFE 6 加载器全部 init 成功；RVision startup 完成
   （stage=true、loadConfig OK）；onFrame 心跳持续（RVision.log tick 每
   180 帧）——**模组本体运行无异常**；
2. **newGame 流程卡"进入地形"**：游戏 trace "Создание местности → false →
   Вход в местность" 后不再推进（RConnect first snapshot 不出现）——
   **4 mod（pfe_1.02_before_tdfc_merge_20260817）与 6 mod 环境同样卡**；
   RConnect 8/17 同版本测试成功——差异在 mods 当前版本/存档/环境细节；
3. **自动读档卡死**：SharedObject 域存在 PFEgame0.sol 时启动自动读档，
   用户最新档（含 mod 物品，见 #1009 事件）导致主循环卡死（sandy/RV
   心跳停）——删除存档后主循环恢复；
4. **按键注入受阻**：keybd_event/PostMessage 注入 F12 均未触发模组
   saveConfig（config.txt 写权限已确认 OK）——AIR 键盘焦点/窗口遮挡问题；
   游戏窗口位于屏幕 337,97-1633,936（部分超出屏幕）且被 ZCode 等窗口
   遮挡——**多次截屏分析实际截到的是遮挡窗口**（OCR 证实），此前多轮
   "画面分析"不可靠；
5. Sandevistan 时停默认关闭（热键触发）、RandomRooms 只追加测试地形
   （#1056 已捕获不致命）——均不干扰。

### 3. 结论

- **模组本体：加载/初始化/帧循环全部正常**（文件日志证实）；
- **进实战环节受环境阻碍**（newGame 地形加载卡住 + 存档自动读档卡死 +
  窗口遮挡/按键注入），**未能完成游戏内雾层渲染的像素级验证**；
- smoothing=true 修复（current 5px 子格双线性插值）逻辑上成立（离线
  验证：子格间 5px 渐变带），**待游戏内实测确认观感**。

## 遗留问题 / 下一步建议

1. 玩家正常启动（Steam/Remains.exe）确认 newGame 是否正常——若正常，
   说明测试实例环境（adl64/无存档）与正式环境有差异；
2. 或提供干净的存档模板（不含 mod 物品的早期档）用于读档路径；
3. 画面验证需解决窗口置顶/遮挡问题（SetWindowPos TOPMOST + 截窗口区域）。
