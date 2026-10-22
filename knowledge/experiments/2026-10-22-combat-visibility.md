被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-22 武器泄露与战斗开销修复

用户反馈v0.33.2在战斗仍有轻微卡顿，且记忆区域有独立武器露出。本轮准确生产基线7852F61E…BE86764；实际配置current、dim约0.6、soft_current25、viewscale1、wallbright0。未写玩家配置或存档，未操作玩家实例。采用登记、独立AIR ID、私有桌面；测试开始时玩家运行的功能复现不作为计时。后续确认玩家实例退出才采集性能。

## 根因与修复

原生UnitRaider.currentWeapon位于childObjs，由Unit.step更新，并不在Location.firstObj。旧版只扫描房间链，因此真实身体有mask而武器无mask；完整安装组合最小复现两模式各6帧均泄露806像素。候选每帧沿单位真实附件处理Weapon，复用所属单位已算出的状态，武器拥有独立Shape，避免与身体争用同一mask。只在遮罩输入更新时复制graphics；不再给这些武器重新分类或等三帧扫描。原生已隐藏状态、死亡和模式恢复独立处理。

计时归因中current的软遮罩后处理在120帧累计414–476ms。批量paletteMap和threshold替换两次getVector、逐像素循环与setVector，保留完全相同的整数透明度映射。未降低分辨率/更新频率，未变更探索、墙影、视距及地板柔化；RVWallSurface生产源指纹不变。

## 实证与边界

- 完整组合真实武器52项：两模式泄露像素806→0；隐藏/恢复、同场更新、重新挂载、原生hidden、死亡、停用、换房通过。原生武器本次remVisual/addVisual复用了同一vis，测试仅验证重新挂载，不冒充替换新对象的实测。重建不同vis的释放分支有代码但未由这次原生动作触发。
- 1536项显示/逻辑缓存与破墙；90项设置；16项运动/射线（含1000射线）；21项共享探索；65组批量位图（全256透明度和64模糊场）严格相等。
- 大图192×75、96单位：32检查点的雾图、墙图、逻辑场、单位mask及合成图严格相同。此前普通人工Unit未带真实武器，不能覆盖此次附件缺陷；本轮另有真实武器测试补上。
- 准确生产包两进程36项设置/改键保存通过。总计1848项/组检查，另有8个真实射击窗口，每窗120采样，原生攻击与弹丸均存在。
- 没有玩家截图对应存档/移动历史，不声称整张用户图复原；软取图不是GPU呈现认证。UnitMerc的internal arm、任意模组装饰和名称提示不在此次武器像素认证范围。没有改变念力玩法。

## 性能

无插桩/无逐帧取图的同进程交替对照，每组每版120帧。下表是RV更新加独立雾图draw，单位ms；不是完整FPS。[汇总](combat-visibility-v0333-20261022/performance.json)、[原始样本](combat-visibility-v0333-20261022/timing-02/evidence/result.json)和[环境采样](combat-visibility-v0333-20261022/timing-02/environment.json)均保留。秒级观察无其他AIR/JVM，不排除短进程和其他系统负载。

| 模式/记忆亮度 | D35均值/P95/最大 | D36均值/P95/最大 |
|---|---|---|
| classic 0.35 | 49.35/91/116 | 50.133/92/170 |
| classic 0.6 | 67.442/117/151 | 68.167/117/190 |
| current 0.35 | 38.325/56/100 | 37.275/60/126 |
| current 0.6 | 37.992/62/75 | 37.042/59/122 |

current两组均值降低约2.5%–2.7%；classic增加0.73–0.78ms（约1.1%–1.6%），包含每帧新增的真实附件处理。P95并非全面改善，四组最大值均上升；不能声称消除了长帧或证明其根因已修复。保留候选的依据是武器错误被实际修正、current平均开销小幅下降且画面不变；本次性能优化只是有限改进。

真实战斗A/B/B/A每模式4窗，原生世界继续演进，非确定性重放；只能辅助观察，不将独立窗口差值视为精确收益。整帧尖峰与RV独占更新分开记录，不承诺所有卡顿消失。

真实战斗current两窗RV平均更新约19.60ms，基线约19.63ms，基本持平；classic约37.55ms，基线约37.35ms。此次没有证明真实战斗中的卡顿已明显改善。完整组合用于武器功能复验；战斗计时仅CS与动态RV，不能外推为完整模组组合的FPS。

## 失败和中断保留

regress-full-01的app:写PNG被AIR拒绝，改为受限本实验nativePath；regress-full-02驱动访问classic不存在的currentSight触发1009，补齐仅测试的控制场后regress-full-03通过。不是生产崩溃。timing-01因工具会话更新中断停在case1，运行器和子进程均退出后按官方登记恢复；半轮数据作废，timing-02完整重测。排队过程中遇到CS中断登记，核对无存活进程后调用recover时该记录已被对方恢复，未做二次写入或停止他方进程。

## 部署

持续本机授权，发布门禁通过后只替换RV。版本v0.33.3-combat-visibility，42400B，SHA256 `ab461ff3bdf77544bfb3e7f45b67265429d52280721fa8b8321ba92be2f23871`。正式路径独立启动确认init、新版本、设置注册及tick1/181/361；保护指纹和真实配置前后相同。备份 `build\backups\before-combat-visibility-20261022-182545-6d09e8\RealisticVisionMod.before.swf` 为D35；回滚需核对当前仍为本轮包，再原子恢复此备份，正常重启生效。

准确生产源 `build/combat-visibility-output/production/src`，仅六类、无authority或fe.*存根。开发src同步本轮变更并保留既有authority记账，单独编译确认语法，未把该独立接口带入安装；它的新增武器协作行为未在本轮联机验收。四项外部WIP保留。

本轮技能实证为可复现视觉错误、真实附件测试缝隙、严格像素与计时分离、登记等待和一次中断核对、准确包部署；不覆盖只读无法复现分支或所有客户端环境。经验查询返回partial（无关写作原件缺失）；已回读KB-000106，复用实际配置覆盖和测量边界，不解释为完整经验库均已搜索。
