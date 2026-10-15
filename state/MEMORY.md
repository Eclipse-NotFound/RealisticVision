# RealisticVision —— 开发记忆入口

> 2026-10-15 22:27:59 D27 **已部署**：设置新增“已探索墙边常亮”（默认开、即时保存）；关闭后墙面随视野变暗，classic/current的透明凹口与墙边阴影修复始终生效。正式安装v0.31.1-wall-options-candidate，35,017B，SHA256 `BAA48289D9CF86F64CFF53B4734032AD29C89C3AC1704DB2D89038D4B8DB4275`。精确安装验收候选，保留改键与场景兼容；212项开发检查、8组图像、20项生产字节设置检查和正式路径init/设置注册/tick1/181/361通过。备份和单模组回退见[部署回执](deployment-v0311-2026-10-15.md)。平均额外渲染约9.8～13.7ms；大型全模组战斗未验。需保存并重启游戏生效。

> 2026-10-15 菜单改键已安装：本模组改键候选已随统一六客户端安装并从正式路径读回，七模组23项联合两进程346项通过。当前正式SHA256 E99608088A8B00B4442BC3AEF52D8035336F0123EA5A96D55503C90B1F6E0808。入口「模组→对应模组→快捷键」，保存后重启游戏加载新版；本机偏好即时保存。备份/回退及权限见[keybind-deployment-2026-10-15.md](keybind-deployment-2026-10-15.md)。下方候选及旧安装记忆保留历史；未发布WIP没有带入本次安装。

> 2026-10-15 菜单改键候选完成，未部署：调试、总开关、渲染模式三项可在「视野系统→快捷键」修改并即时保存，提示文字同步。准确生产线候选E9960808…1F6E0808，排除墙面候选与authority WIP；最终七模组346项和公共39项通过。详情见[keybind-integration-2026-10-15.md](keybind-integration-2026-10-15.md)。

> 2026-10-15 D26历史墙面候选（已由上方D27替代），**未部署**：用户确认“已探索墙边常亮”，D26 更新旧 D22 的记忆墙压暗要求。classic/current 共用实际材质轮廓，墙内约12px亮面、至32px渐隐；墙芯/未探索背面/地板雾效及敌人视野保持各自规则。候选 v0.31.0-wall-surface-candidate，29,879B，SHA256 `6DE9C96EBF48E7CB9E01479DD5661E21625625E2EE9C1B6F9E5F640B7518E06D`。当时正式安装为 v0.30.5-scene；当前安装见顶部改键部署。历史报告与对照：[已探索墙面](../knowledge/experiments/2026-10-15-explored-wall-surface.md)。

> 2026-10-15 16:18:17 当前安装已随 ContinuousScene 0.5 更新为 **v0.30.5-scene**，SHA256 `B7695DF82AA45FDB783C4EB88AFFCB0C34A7674E3A052D2FD128867172A83A49`。来源为冻结的0735491生产线加CS兼容补丁，未发布authority接口或既有WIP；不要用HEAD直接覆盖。详见[本轮部署记录](deployment-scene-v05-20261015.md)。当前回退仅经 `ContinuousScene/build/upgrade-v05.ps1 -Action Rollback`；下方旧部署与回退说明保留作历史，既有开发内容不变。

> 2026-10-14 23:10 ContinuousScene预绘兼容已升级：**v0.30.4-scene**，SHA256 `89B391BCE114534D6F2C0147BD4B136602168EE4362AA36F6F0C37ECD47173B5`。大图视野快照在有可见单位需要时才复制，场变化即时失效；原视野、遮罩和小房间保留。42项视野、48项场景、15项安装启动通过。仍由0735491生产线叠加补丁，不发布authority接口/WIP。当前回退归ContinuousScene/build/rollback-v03.ps1；详见[本轮部署记录](deployment-scene-v03-20261014.md)。下方0.30.3为历史。

> 2026-10-14 ContinuousScene兼容已安装：**v0.30.3-scene**，SHA256 `ED76EC15666FD8CD50ACF0149F7EC32F2602D2E68D753580A0EC5814B95A2E99`。用户明确允许必要兼容修改。大场景雾绘图、模糊和显示裁切按镜头范围，小房间范围/逻辑视野/共享探索保留。安装包从原安装线0735491叠加补丁构建，不包含HEAD的authority接口和下述既有WIP；切勿用HEAD未经核验直接覆盖。37项视野、全模组44项和正式原生启动通过。详见[兼容部署记录](deployment-scene-20261014.md)，配置未改，备份归ContinuousScene统一管理。

> 2026-10-12 RConnect B协作：用户明确授权“创建独立接口，与原版本接口保持隔离”。独立RVAuthorityViewAPI显示写入撤回接口已在B102双侧视野实机主67/0、加66/0；RV002独立检查15/0。原共享探索接口不变；B模式逐帧遮蔽开销仍待压力测试。 仅产物冻结于 mods/RConnect/build/ab，安装release未修改。详情见RConnect/state/host-authority-playable-2026-10-11.md末节。

> 2026-10-10 当前安装：**v0.30.2-candidate，25355B，SHA256 d5e0468ee17c55f2b9fd14a10b2b8849f023ade242a54d46028ada60cfb450ee**。用户在 RConnect 主会话明确授权的共享探索局部缓存已部署。只缓存本地子格编码，亮度/视野/采集频率及中英俄语言保持原规则。46项独立 AIR 检查（含475次原算法对照）、与正式 RConnect 22 配合的471项实机断言、无测试驱动双人启动检查通过。高密度开火仍未整体达标，不能解释为已消除所有卡顿。备份、实证与边界见[部署回执](deployment-v0302-2026-10-10.md)。下方旧安装记录为历史。

> 2026-10-08 玩家文档：按用户要求更新公开 GitHub 中英文首页、玩家指引、最新发布页说明与仓库简介，公开提交 1c3fd8f。未发布本地开发代码或更换安装包。详见 [发布记录](github-player-guides-2026-10-08.md)。

> 2026-10-03 当前安装：游戏内英文/俄文已安装，随原生语言入口切换。正式 SWF 25298 字节，SHA256 `72D2F75BA89E7B40CC78C5A5E48E1C61AF297753CBE2DCA929E0F1AD5BA6A303`。八模组安装前 4431、安装后 4432 项检查通过；中文保留，113 个设置值不变。当前语言发布与回滚以 [localization-2026-10-03.md](localization-2026-10-03.md) 为准；下方旧安装记录保留作历史基线。

## 2026-09-28 当前部署：模式切换提示 v0.30.1

用户明确“请部署”后，已发布源码55bb77e对应产物，22,311字节，SHA256 772E58A0CF384656632CFFD9503929188445CC4B19953A725B7B47801D3E7080。模式提示移至左上，仅实际切换时显示3秒，重复选择不续时，菜单/无世界也会到期。候选实际SWF的9项独立行为检查通过；正式路径新版init、设置注册与心跳1/181/361通过，测试实例已关闭。版本字符串保留v0.30.1-candidate，实际已部署。过程、证据和回滚见state/deployment-v0301-2026-09-28.md（相对模组根）。

## 2026-09-20 上次部署：共享探索 v0.30.0（历史）

用户明确“替换正式版本”后，已部署22310字节、SHA256 ce3abb8d1321df4f2a6e1053ecbb44aabff66a6e27f81b517d3a341b3a8dfb5b，版本标记保留 v0.30.0-candidate。配套 RConnect 0.2.3-dev，包含下述 ModSettings 迁移和保存修复。部署/回滚见 state/deployment-v0300-2026-09-20.md。

## 2026-09-20 较早的正式入口迁移（历史）
按用户授权，已发布的 v0.29.0-candidate 另加 ModSettings 注册与持久化修复（源码提交 eb92773），正式 SWF 为 20361 字节，SHA256 47403D06BB989EDA462599361E8CA921E356DA15541C32B737AF29EB03407AEB；启动标记含 settings=ModSettings-v1。当时尚未发布共享探索；现已由上面的 v0.30.0 部署替换。
入口改为 ModSettingsCarrier；配置优先 Local Store/RealisticVision_config.txt，首次读原 release/config.txt，写入应用存储。原模板 SHA 未变，F11/F12 保留；下文旧 F12 app:/ 保存失败现已修复。完整/无 MSW 组合与两次进程保存恢复、正式七模组字节启动通过。
回滚须恢复 ModSettings 迁移前整套宿主/客户端；备份在 ../ModSettings/build/backups/before-migration-20260920-142036。完整证据见 ../ModSettings/knowledge/experiments/2026-09-20-migration.md。本次安装不覆盖共享探索源码/记忆增量，也未重跑柔化算法性能。

> 更新：2026-09-28。源码与正式安装均为 v0.30.1-candidate，继承 v0.30.0 共享探索与 v0.29.0 适中柔化。权限见 ../AGENT_SCOPE.md。

> 新增：RConnect 共享探索任务已获用户明确授权，在本模组实现 v0.30.0-candidate 可选接口，现已部署。同期 ModSettings 注册迁移由另一任务独立提交 eb92773，本接口叠加其后；没有混入对方暂存内容。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current 三模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组 loader。

## 2. 用户偏好与协作约定

- 模式标识不常驻右上角，只在切换模式时于左上角短暂提示；本次沿用3秒时长。
- 共享探索任务的新授权：宿主/加入者双向，各自控制接收，关闭后保留共享区域；RV 按自身设置显示。允许同时修改 RV 接口，禁止对 RConnect/RV 相互引入硬性依赖。本轮已获“替换正式版本”授权并完成部署。
- 用户已明确“认可你的设计，请继续”：落实 current 投影轮廓配连续地板渐变、适中/宽两档比较、刷新与错误亮点修复。不是尚待定案的讨论。本轮用户进一步明确“部署”，已完成正式替换与独立启动检查。
- D25：允许地板边缘有限柔和过渡，不把边界外所有非黑像素自动判错；柔化不扩大逻辑视野或探索。默认推荐适中约28px，宽档约41px供比较，均是斜边实测10%–90%范围。
- D26/D27：已探索墙边亮面约12px、至32px渐隐；常亮现在可在设置中关闭，默认开启。关闭仅控制墙面亮度，两模式始终按真实材质轮廓修复阴影溢出。墙芯/未探索背面仍黑，原版记录、地图/传送、地板规则与敌人视野继续隔离。
- 同场景、同输入对照，实际 AIR 复现；不能把固定步算法耗时当完整游戏FPS。用户精确存档、相机/历史与战斗验收仍需区分。
- 不写其他模组、不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，不恢复旧记忆播种/墙面受光传播。a583f1a念力守卫保留。

## 3. 当前状态

- D27墙面修复已安装：83项独立检查、岩壁65项与金属64项通过；8组开关的空气像素差0、远处地板差0、每组156个深墙芯点全黑。旧透明凹口复现0→255，即使关闭常亮也通过。11组优化前后逐像素相等。另20项生产字节检查验证设置/改键页、即时保存与跨进程恢复；正式原生启动通过。测试进程已退出，配置/宿主/清单指纹未变，未操作玩家游戏或存档。

- 本轮v0.30.1正式路径独立启动检查通过：新版初始化、ModSettings注册、tick1/181/361；提示行为9项由同一SWF独立夹具验证。实际用户存档的遮挡/布局未截图验收。旧v0.30.0的 **46b70da446 PASS** 联测记录仍有效，但未在本轮重跑联机或阴影回归。

- 源码 v0.30.1-candidate（仅提示改动，继承 v0.30.0 与 D25）：current 每帧位移刷新并当帧显示；地板4/q3柔化，修0/7角点历史；射线批次缓存比较实际门/水/墙，房间和宽高失效；近区整块填充、完整曾见块快路径、墙几何按结构变化重建。classic 渲染主体与念力守卫不改。
- currentSight 独立保存未柔化的单位可见性，地板按LOS/距离/亮度，墙按当前FOV和原版亮面；敌人可见侧淡出，粗格全亮不能跳过细分遮挡。提高记忆亮度不会显示隐藏敌人。
- 16项专项、1000条缓存/实时射线、墙形39项、classic小墙10方向、接缝8项通过。完整训练房上下两位置，classic纯阴影整图差0，current墙像素差0；原版字段改写0。单墙60/60、训练房90/90更新。
- 同眼位斜边暗边RMS：正式1.299、适中0.325、宽0.306px。最终同进程两次适中平均8.29/8.92ms、P95 10/11ms；正式平均8.89/9.04ms、P95 19/22ms。适中复测有一次67ms峰值，原因未定位，不承诺实战稳定帧率。
- 历史 D25 测试构建 build/RealisticVisionMod_test.swf：20,608字节，SHA256 5C26D604BA6AE33A92A5D11F8A6F6ABCFBF8BDE9663BAF3AB68E919A32B8C242。FFDec仅RealisticVisionMod，无fe.*存根。源码SHA 34F62748734B000D26D438668A455A5C4D2CC59B9FEF37CD78D078AA854BD10B。
- 历史 v0.29 部署源码dadd417的适中档，与测试SWF逐字节一致（20,608字节，5C26D604…B8C242）。为复用完整验证，未改构建标记v0.29.0-candidate。config仍current/dim=.35/debug=0，SHA 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F；根pfe仍5300EC4874E0404D298BB58C5D2A7469E82F93B455AD29AD64DD2E29D17241E7。
- 历史 v0.29 回滚备份 build/release_backup_v0282_before_v0290_20260920-110643.swf，SHA A8A7DAE9A755ACD7FC93101003AACE2C8CF2A0FF6A507318B3B7A7CAADB685E2；复制回release并正常重启可回到v0.28.2。
- 上次部署备份 build/release_backup_v0280_grabfix1_before_v0282_20260919.swf，SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969。旧部署实例22条心跳/六loader正常/F12入口见v0282部署报告，不属于新候选部署验证。

## 4. 正在进行与停点

- D27已按本对话“部署”指令替换release，精确对应 `build/wall-options-output/candidate/RealisticVisionMod.swf`；回执 `state/deployment-v0311-2026-10-15.md`，部署日志 `state/deployment-v0311/`。工具 `build/wall-options/README.md`；画面实证 `knowledge/experiments/wall-options-v0311-20261015/`。对照页标记已部署，历史开发报告保持原验收时点；浏览器交互未验。
- 候选来源固定为v0.30.5-scene基础快照，并叠加本轮已正式安装的改键源码（主文件83F27414…BD3F58C8，另固定RVKeybinds与语言目录）；源码位于本轮installed-keys/src，不自动跟随外部生成目录。原完整候选不含新改键，不能再用；新的D27包保留改键且不含authority WIP。head-check仍不是部署包。

- 共享探索接口：src/RVExplorationCarrier.as 发布 active/capture/merge，独立记忆按 Location 实例隔离；子格/瓦片/墙光仅参与记忆显示，不写原版字段或本地 FOV/currentSight。未安装 RConnect 时原功能照常。契约 design/shared-exploration-api.md；验证 knowledge/experiments/2026-09-20-shared-exploration-api.md。
- 历史共享探索候选 build/shared-exploration/RealisticVisionMod.swf；独立回归 build/shared-exploration/run_checks.py。RConnect侧联测日志在其M31报告/JSON。当前正式版已叠加v0.30.1提示修改，不能再拿旧共享探索候选覆盖。
- 本轮候选开发、两档实际绘图、回归和测试编译完成。说明：knowledge/experiments/2026-09-20-current-soft-candidate.md；对照页 current-soft-v0290/comparison.html，可逐帧切换适中/宽档。已按用户要求部署适中档。部署回执2026-09-20-v0290-deployment.md，证据deployment-v0290/。正式路径独立实例确认新版标记、MSW设置注册与17条心跳至2881；测试PID51952已关闭、描述符已删除，用户实例未操作。
- 浏览器URL策略拒绝自动打开本地HTML，未绕过。脚本语法已检查、原始PNG已目检，但浏览器交互未实测；给用户文件链接即可，不宣称页面已打开。
- 原调查 ef82898/37f3284 与讨论534865e保留；当前motion-tests旧变体固定读取37c25ba，新soft-*读取当前源码。不要让历史实验改用新源码，或覆盖current-motion-20260920证据。

## 5. 已知问题与边界

- D27最终同进程三组轮换回放：classic基线/关闭/开启均值8.17/17.92/20.58ms，P95 12/25/29ms；current 9.31/20.68/23.04ms，P95 11/24/29ms。平均额外约9.8～13.7ms，最大53ms；不是完整战斗FPS。整张最终输出分支无收益已撤回，采用局部内容比较缓存；大型连续场景、全模组负载与用户存档未验。

- 候选仍为5px逻辑采样及四角快速分类，不是连续多边形可见性重写。未覆盖任意窄缝/全部缩放相位、用户精确存档、长时间战斗和六模组共同负载。单位掩膜零泄漏断言针对采样点，不是任意亚像素几何证明。
- 一次67ms峰值未定位；宽/适中间约零点几毫秒差视为噪声，不据此选档。完整训练房视距3000/10000，与普通房不同。
- classic既有40px粗格掠角（一个方向与连续切线差21px）、薄墙可见侧约20px渐变仍保留。旧 F12 app:/ 保存错误已由 ModSettings 迁移修复，配置写入本端应用存储。狮鹫internal手臂、SATS记忆扫描/抓暗敌瞬间报警等旧限制保留。
- 同尺寸resetRoom清黑共用三图、fogBlurPending及原版墙角相位等旧修复保留；新currentSightData随房间清空重建。

## 6. 下一步

1. D27已部署完成，玩家保存并正常重启后生效。「模组→RealisticVision视野系统→已探索墙边常亮」可开关；关闭常亮仍保留两模式阴影修复。不要用旧D26或未经核验的HEAD覆盖安装。
2. 本次回退仅使用 `build/backups/before-wall-options-20261015-222759-aa7db9/RealisticVisionMod.before.swf`（E9960808…1F6E0808），恢复此前改键版；先核对当前安装和备份。不能用旧改键/场景联合回退处理本次单模组安装。
3. 如继续墙面性能优化，针对原雾快照、动态局部合成及真实多敌人/大场景取证；保持D27开关与修复独立、D22记录隔离、D24/D25地板规则及念力守卫，不减少刷新造成破墙或镜头残影。
4. 用户游戏不自动关闭；部署后需保存并正常重启。此前回滚点与stash保留。

## 7. 深入了解与复验

- 本轮入口：`knowledge/experiments/2026-10-15-wall-bright-option.md`、D27、`build/wall-options/README.md`；最终指纹/图像/日志在wall-options-v0311-20261015。D26旧记录仍留原址。SDK在本区 `mods/Sandevistan/build/tools/`，仅只读使用。

- 最新发布：state/deployment-v0311-2026-10-15.md与state/deployment-v0311/；此前v0301回执是历史。当前宿主为ModLoader加载链；正式检查沿用pfe-modsettings-rv-deploy-前缀及-nodebug，独立存储。部署前指纹抄录与探针心跳等待不足已修正并保留记录，均未替换安装；最终生产字节与原生启动通过。
- 新候选：2026-09-20-current-soft-candidate.md / current-soft-v0290/ / D25。新SoftHarness.as与motion-tests/README.md列完整命令，--checks专项、soft-medium/soft-wide、run-game和bench-game --soft。
- 原调查：2026-09-20-current-motion-investigation.md / current-motion-20260920/。证实三帧+次帧约10Hz、只提频会饿死显示、max硬钳制台阶、角点误写亮点。全图2.5px成本高，四点积分收益小。
- 既有classic修复：2026-09-19-classic-wall-seam-fix.md / classic-seams-v0282/ / D24；部署2026-09-19-v0282-deployment.md。D22/D23旧报告与念力交接见journal。
- 构建只用build/build_test.bat（旧build.bat/build.sh会写release）。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk，Java D:/Program Files/Adobe Animate 2024/jre，FFDec同tools/ffdec。
- AIR使用独立app id和资源副本，禁止写真实pfe存储；性能试验顺序，优化编译debug=false/optimize=true并保留trace。完整游戏共享输出目录的脚本也顺序，限时150秒并核对成功退出。普通沙箱AIR/FFDec可能初始化失败，走工具审核，不凭空日志认定算法失败。
- Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。知识库KB-000056已有性能比较方法，不重复记卡。

缓存验证工具的旧算法已固定到提交d634b5769f9af1949d2114b4643d37d97af8f7b6及规范化源码SHA f2e1b49c…，避免后续HEAD变化变成新算法自比。执行实际取源/指纹检查，并与已验证02中的原始源码逐字一致；本次仅修未来构建工具，已部署SWF与02证据不变。
