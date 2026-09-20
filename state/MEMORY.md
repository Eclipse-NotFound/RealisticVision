# RealisticVision —— 开发记忆入口

## 2026-09-20 当前部署：共享探索 v0.30.0

用户明确“替换正式版本”后，已部署22310字节、SHA256 ce3abb8d1321df4f2a6e1053ecbb44aabff66a6e27f81b517d3a341b3a8dfb5b，版本标记保留 v0.30.0-candidate。配套 RConnect 0.2.3-dev，包含下述 ModSettings 迁移和保存修复。部署/回滚见 state/deployment-v0300-2026-09-20.md。

## 2026-09-20 较早的正式入口迁移（历史）
按用户授权，已发布的 v0.29.0-candidate 另加 ModSettings 注册与持久化修复（源码提交 eb92773），正式 SWF 为 20361 字节，SHA256 47403D06BB989EDA462599361E8CA921E356DA15541C32B737AF29EB03407AEB；启动标记含 settings=ModSettings-v1。当时尚未发布共享探索；现已由上面的 v0.30.0 部署替换。
入口改为 ModSettingsCarrier；配置优先 Local Store/RealisticVision_config.txt，首次读原 release/config.txt，写入应用存储。原模板 SHA 未变，F11/F12 保留；下文旧 F12 app:/ 保存失败现已修复。完整/无 MSW 组合与两次进程保存恢复、正式七模组字节启动通过。
回滚须恢复 ModSettings 迁移前整套宿主/客户端；备份在 ../ModSettings/build/backups/before-migration-20260920-142036。完整证据见 ../ModSettings/knowledge/experiments/2026-09-20-migration.md。本次安装不覆盖共享探索源码/记忆增量，也未重跑柔化算法性能。

> 更新：2026-09-20。当前 v0.30.0-candidate 已正式安装，继承 v0.29.0 适中柔化。权限见 ../AGENT_SCOPE.md。

> 新增：RConnect 共享探索任务已获用户明确授权，在本模组实现 v0.30.0-candidate 可选接口，现已部署。同期 ModSettings 注册迁移由另一任务独立提交 eb92773，本接口叠加其后；没有混入对方暂存内容。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current 三模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组 loader。

## 2. 用户偏好与协作约定

- 共享探索任务的新授权：宿主/加入者双向，各自控制接收，关闭后保留共享区域；RV 按自身设置显示。允许同时修改 RV 接口，禁止对 RConnect/RV 相互引入硬性依赖。本轮已获“替换正式版本”授权并完成部署。
- 用户已明确“认可你的设计，请继续”：落实 current 投影轮廓配连续地板渐变、适中/宽两档比较、刷新与错误亮点修复。不是尚待定案的讨论。本轮用户进一步明确“部署”，已完成正式替换与独立启动检查。
- D25：允许地板边缘有限柔和过渡，不把边界外所有非黑像素自动判错；柔化不扩大逻辑视野或探索。默认推荐适中约28px，宽档约41px供比较，均是斜边实测10%–90%范围。
- D22：墙按原版黑芯、基础亮面、渐变，只压暗原光；游戏维护 visi/t_visi 与地图/传送判定。D24 classic 接缝修复保留。
- 同场景、同输入对照，实际 AIR 复现；不能把固定步算法耗时当完整游戏FPS。用户精确存档、相机/历史与战斗验收仍需区分。
- 不写其他模组、不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，不恢复旧记忆播种/墙面受光传播。a583f1a念力守卫保留。

## 3. 当前状态

- 本轮正式路径独立启动检查 **46b70da446 PASS**：双方 RC0.2.3 初始化、tick200、连接和 RV0.30 心跳；测试实例已回收。短窗口回滚和并行测试脚本版本竞争已解决并留在部署记录。

- 源码 v0.30.0-candidate（继承 D25）：current 每帧位移刷新并当帧显示；地板4/q3柔化，修0/7角点历史；射线批次缓存比较实际门/水/墙，房间和宽高失效；近区整块填充、完整曾见块快路径、墙几何按结构变化重建。classic 渲染主体与念力守卫不改。
- currentSight 独立保存未柔化的单位可见性，地板按LOS/距离/亮度，墙按当前FOV和原版亮面；敌人可见侧淡出，粗格全亮不能跳过细分遮挡。提高记忆亮度不会显示隐藏敌人。
- 16项专项、1000条缓存/实时射线、墙形39项、classic小墙10方向、接缝8项通过。完整训练房上下两位置，classic纯阴影整图差0，current墙像素差0；原版字段改写0。单墙60/60、训练房90/90更新。
- 同眼位斜边暗边RMS：正式1.299、适中0.325、宽0.306px。最终同进程两次适中平均8.29/8.92ms、P95 10/11ms；正式平均8.89/9.04ms、P95 19/22ms。适中复测有一次67ms峰值，原因未定位，不承诺实战稳定帧率。
- 历史 D25 测试构建 build/RealisticVisionMod_test.swf：20,608字节，SHA256 5C26D604BA6AE33A92A5D11F8A6F6ABCFBF8BDE9663BAF3AB68E919A32B8C242。FFDec仅RealisticVisionMod，无fe.*存根。源码SHA 34F62748734B000D26D438668A455A5C4D2CC59B9FEF37CD78D078AA854BD10B。
- 历史 v0.29 部署源码dadd417的适中档，与测试SWF逐字节一致（20,608字节，5C26D604…B8C242）。为复用完整验证，未改构建标记v0.29.0-candidate。config仍current/dim=.35/debug=0，SHA 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F；根pfe仍5300EC4874E0404D298BB58C5D2A7469E82F93B455AD29AD64DD2E29D17241E7。
- 历史 v0.29 回滚备份 build/release_backup_v0282_before_v0290_20260920-110643.swf，SHA A8A7DAE9A755ACD7FC93101003AACE2C8CF2A0FF6A507318B3B7A7CAADB685E2；复制回release并正常重启可回到v0.28.2。
- 上次部署备份 build/release_backup_v0280_grabfix1_before_v0282_20260919.swf，SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969。旧部署实例22条心跳/六loader正常/F12入口见v0282部署报告，不属于新候选部署验证。

## 4. 正在进行与停点

- 共享探索接口：src/RVExplorationCarrier.as 发布 active/capture/merge，独立记忆按 Location 实例隔离；子格/瓦片/墙光仅参与记忆显示，不写原版字段或本地 FOV/currentSight。未安装 RConnect 时原功能照常。契约 design/shared-exploration-api.md；验证 knowledge/experiments/2026-09-20-shared-exploration-api.md。
- 候选 build/shared-exploration/RealisticVisionMod.swf；独立回归 build/shared-exploration/run_checks.py。RConnect 侧联测日志与最终哈希在其 M31 报告/JSON。正式 release 已替换为该产物，部署前核对源码指纹与 ModSettings 迁移一致。
- 本轮候选开发、两档实际绘图、回归和测试编译完成。说明：knowledge/experiments/2026-09-20-current-soft-candidate.md；对照页 current-soft-v0290/comparison.html，可逐帧切换适中/宽档。已按用户要求部署适中档。部署回执2026-09-20-v0290-deployment.md，证据deployment-v0290/。正式路径独立实例确认新版标记、MSW设置注册与17条心跳至2881；测试PID51952已关闭、描述符已删除，用户实例未操作。
- 浏览器URL策略拒绝自动打开本地HTML，未绕过。脚本语法已检查、原始PNG已目检，但浏览器交互未实测；给用户文件链接即可，不宣称页面已打开。
- 原调查 ef82898/37f3284 与讨论534865e保留；当前motion-tests旧变体固定读取37c25ba，新soft-*读取当前源码。不要让历史实验改用新源码，或覆盖current-motion-20260920证据。

## 5. 已知问题与边界

- 候选仍为5px逻辑采样及四角快速分类，不是连续多边形可见性重写。未覆盖任意窄缝/全部缩放相位、用户精确存档、长时间战斗和六模组共同负载。单位掩膜零泄漏断言针对采样点，不是任意亚像素几何证明。
- 一次67ms峰值未定位；宽/适中间约零点几毫秒差视为噪声，不据此选档。完整训练房视距3000/10000，与普通房不同。
- classic既有40px粗格掠角（一个方向与连续切线差21px）、薄墙可见侧约20px渐变仍保留。旧 F12 app:/ 保存错误已由 ModSettings 迁移修复，配置写入本端应用存储。狮鹫internal手臂、SATS记忆扫描/抓暗敌瞬间报警等旧限制保留。
- 同尺寸resetRoom清黑共用三图、fogBlurPending及原版墙角相位等旧修复保留；新currentSightData随房间清空重建。

## 6. 下一步

1. 部署已完成，用户保存并正常重启后加载共享探索接口和原适中柔化档。新反馈先核对 ce3abb8d…3a8dfb5b 与场景；本轮回滚应使用 v0.29 + ModSettings 备份 47403d06…407aeb，路径见本轮部署记录。
2. 若继续性能优化，围绕67ms峰值和真实多敌人负载取证，关注每帧位图/向量分配；现有短测不能定位其原因。保持D22/D24/D25和念力守卫。
3. 用户游戏不自动关闭；部署后需保存并正常重启。此前回滚点与stash保留。

## 7. 深入了解与复验

- 新候选：2026-09-20-current-soft-candidate.md / current-soft-v0290/ / D25。新SoftHarness.as与motion-tests/README.md列完整命令，--checks专项、soft-medium/soft-wide、run-game和bench-game --soft。
- 原调查：2026-09-20-current-motion-investigation.md / current-motion-20260920/。证实三帧+次帧约10Hz、只提频会饿死显示、max硬钳制台阶、角点误写亮点。全图2.5px成本高，四点积分收益小。
- 既有classic修复：2026-09-19-classic-wall-seam-fix.md / classic-seams-v0282/ / D24；部署2026-09-19-v0282-deployment.md。D22/D23旧报告与念力交接见journal。
- 构建只用build/build_test.bat（旧build.bat/build.sh会写release）。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk，Java D:/Program Files/Adobe Animate 2024/jre，FFDec同tools/ffdec。
- AIR使用独立app id和资源副本，禁止写真实pfe存储；性能试验顺序，优化编译debug=false/optimize=true并保留trace。完整游戏共享输出目录的脚本也顺序，限时150秒并核对成功退出。普通沙箱AIR/FFDec可能初始化失败，走工具审核，不凭空日志认定算法失败。
- Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。知识库KB-000056已有性能比较方法，不重复记卡。
