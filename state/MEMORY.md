# RealisticVision —— 开发记忆入口

> 更新：2026-09-20。v0.29.0-candidate 已实现并验证，尚未部署；正式仍 v0.28.2。权限见 ../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current 三模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组 loader。

## 2. 用户偏好与协作约定

- 用户已明确“认可你的设计，请继续”：落实 current 投影轮廓配连续地板渐变、适中/宽两档比较、刷新与错误亮点修复。不是尚待定案的讨论。本轮已完成候选，未替换 release。
- D25：允许地板边缘有限柔和过渡，不把边界外所有非黑像素自动判错；柔化不扩大逻辑视野或探索。默认推荐适中约28px，宽档约41px供比较，均是斜边实测10%–90%范围。
- D22：墙按原版黑芯、基础亮面、渐变，只压暗原光；游戏维护 visi/t_visi 与地图/传送判定。D24 classic 接缝修复保留。
- 同场景、同输入对照，实际 AIR 复现；不能把固定步算法耗时当完整游戏FPS。用户精确存档、相机/历史与战斗验收仍需区分。
- 不写其他模组、不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，不恢复旧记忆播种/墙面受光传播。a583f1a念力守卫保留。

## 3. 当前状态

- 源码 v0.29.0-candidate（D25）：current 每帧位移刷新并当帧显示；地板4/q3柔化，修0/7角点历史；射线批次缓存比较实际门/水/墙，房间和宽高失效；近区整块填充、完整曾见块快路径、墙几何按结构变化重建。classic 渲染主体与念力守卫不改。
- currentSight 独立保存未柔化的单位可见性，地板按LOS/距离/亮度，墙按当前FOV和原版亮面；敌人可见侧淡出，粗格全亮不能跳过细分遮挡。提高记忆亮度不会显示隐藏敌人。
- 16项专项、1000条缓存/实时射线、墙形39项、classic小墙10方向、接缝8项通过。完整训练房上下两位置，classic纯阴影整图差0，current墙像素差0；原版字段改写0。单墙60/60、训练房90/90更新。
- 同眼位斜边暗边RMS：正式1.299、适中0.325、宽0.306px。最终同进程两次适中平均8.29/8.92ms、P95 10/11ms；正式平均8.89/9.04ms、P95 19/22ms。适中复测有一次67ms峰值，原因未定位，不承诺实战稳定帧率。
- 测试构建 build/RealisticVisionMod_test.swf：20,608字节，SHA256 5C26D604BA6AE33A92A5D11F8A6F6ABCFBF8BDE9663BAF3AB68E919A32B8C242。FFDec仅RealisticVisionMod，无fe.*存根。源码SHA 34F62748734B000D26D438668A455A5C4D2CC59B9FEF37CD78D078AA854BD10B。
- 正式release仍v0.28.2（源码37c25ba），18,877字节，SHA A8A7DAE9A755ACD7FC93101003AACE2C8CF2A0FF6A507318B3B7A7CAADB685E2。config仍current/dim=.35/debug=0，SHA 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F；根pfe仍5300EC4874E0404D298BB58C5D2A7469E82F93B455AD29AD64DD2E29D17241E7。
- 上次部署备份 build/release_backup_v0280_grabfix1_before_v0282_20260919.swf，SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969。旧部署实例22条心跳/六loader正常/F12入口见v0282部署报告，不属于新候选部署验证。

## 4. 正在进行与停点

- 本轮候选开发、两档实际绘图、回归和测试编译完成。说明：knowledge/experiments/2026-09-20-current-soft-candidate.md；对照页 current-soft-v0290/comparison.html，可逐帧切换适中/宽档。建议默认适中；正式部署尚未执行。
- 浏览器URL策略拒绝自动打开本地HTML，未绕过。脚本语法已检查、原始PNG已目检，但浏览器交互未实测；给用户文件链接即可，不宣称页面已打开。
- 原调查 ef82898/37f3284 与讨论534865e保留；当前motion-tests旧变体固定读取37c25ba，新soft-*读取当前源码。不要让历史实验改用新源码，或覆盖current-motion-20260920证据。

## 5. 已知问题与边界

- 候选仍为5px逻辑采样及四角快速分类，不是连续多边形可见性重写。未覆盖任意窄缝/全部缩放相位、用户精确存档、长时间战斗和六模组共同负载。单位掩膜零泄漏断言针对采样点，不是任意亚像素几何证明。
- 一次67ms峰值未定位；宽/适中间约零点几毫秒差视为噪声，不据此选档。完整训练房视距3000/10000，与普通房不同。
- classic既有40px粗格掠角（一个方向与连续切线差21px）、薄墙可见侧约20px渐变仍保留。F12 saveConfig SecurityError:fileWriteResource是既有问题；本轮未扩修。狮鹫internal手臂、SATS记忆扫描/抓暗敌瞬间报警等旧限制保留。
- 同尺寸resetRoom清黑共用三图、fogBlurPending及原版墙角相位等旧修复保留；新currentSightData随房间清空重建。

## 6. 下一步

1. 用户可查看两档对照；若明确部署，先按release gate核对本候选源码/SWF指纹、备份当前v0.28.2，再部署并独立正式路径冒烟。构建若有新改动，重新验证相关项，不能拿旧SWF部署。
2. 若继续性能优化，围绕67ms峰值和真实多敌人负载取证，关注每帧位图/向量分配；现有短测不能定位其原因。保持D22/D24/D25和念力守卫。
3. 用户游戏不自动关闭；部署后需保存并正常重启。此前回滚点与stash保留。

## 7. 深入了解与复验

- 新候选：2026-09-20-current-soft-candidate.md / current-soft-v0290/ / D25。新SoftHarness.as与motion-tests/README.md列完整命令，--checks专项、soft-medium/soft-wide、run-game和bench-game --soft。
- 原调查：2026-09-20-current-motion-investigation.md / current-motion-20260920/。证实三帧+次帧约10Hz、只提频会饿死显示、max硬钳制台阶、角点误写亮点。全图2.5px成本高，四点积分收益小。
- 既有classic修复：2026-09-19-classic-wall-seam-fix.md / classic-seams-v0282/ / D24；部署2026-09-19-v0282-deployment.md。D22/D23旧报告与念力交接见journal。
- 构建只用build/build_test.bat（旧build.bat/build.sh会写release）。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk，Java D:/Program Files/Adobe Animate 2024/jre，FFDec同tools/ffdec。
- AIR使用独立app id和资源副本，禁止写真实pfe存储；性能试验顺序，优化编译debug=false/optimize=true并保留trace。完整游戏共享输出目录的脚本也顺序，限时150秒并核对成功退出。普通沙箱AIR/FFDec可能初始化失败，走工具审核，不凭空日志认定算法失败。
- Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。知识库KB-000056已有性能比较方法，不重复记卡。
