# RealisticVision —— 开发记忆入口

> 2026-11-02 **v0.34.3-eye-boundary 已部署**：修普通弹体注册点进暗区后整条亮处尾迹提前消失；Bullet/SmartBullet/PhisBullet 改空间软遮罩并刷新动态外框，Part 保持快速路径。视野从真实玩家眼部发出，按眼部位移刷新，墙角分类不再跨不同起点复用。771项受控检查与正式候选原生加载/运行通过；未重测密集战斗帧率。49,048B / `0861FB64…6DD2E30B`；config与宿主未改。源 `build/eye-boundary-output/candidate/src`，可审阅补丁 `build/eye-boundary/production.patch`，备份 `build/backups/before-eye-boundary-20261102-073730`。**保存并重启游戏生效**。[报告](../knowledge/experiments/2026-11-02-eye-boundary.md)。


> 2026-11-02 **v0.34.2-laser-shadow 已部署（修复：激光炮塔光束不受阴影遮盖）**：48,757B，SHA256 `2F44DDD1…4AC151F`；备份`build/backups/before-laserfix-20261102-054800`（v0.34.1 DAC7CB25，config 未改）。用户报告 v0.34 系激光光束穿阴影不暗化。根因：激光弹=Bullet 类实例（在 fx-fast 二值名单内），其 vis 内 `laser` 子对象按射程拉伸（Bullet.as:213-215 `vis.laser.scaleX=距离/100`），中心点判定只看光束原点（炮塔口）——原点亮即整段直绘，远端穿阴影部分不遮暗（长条几何无法用原点代表，属 fx-fast 中心点二值的固有局限，v0.33.16 起存在，密集游玩后暴露）。修复：dispatch 处 `Object(obj.vis).laser == null` 才走瞬态二值，激光弹一律回 `applyWorldVisual` 逐对象软遮罩；一次动态属性查询，普通枪弹/火花不受影响。A/B fxlib342-01（718 间隔/版本）：34.06 vs 33.93=噪声带（测试 LMG 场无激光对象；真实激光场景每炮塔 1-2 发在场、软遮罩开销可忽略）；官方冒烟 init ok v0.34.2-laser-shadow/设置注册/tick 通过。**真机激光穿阴影视觉待用户重启核对**。[报告](../knowledge/experiments/2026-11-02-fx-liberation.md#v0342-laser-shadow-修复)，证据 fire-exhaustive-output/fxlib342-01，实验 build/perf-20261102。

> 2026-11-02 **v0.34.1-door-coverage 已部署（修复：透光门后可视效果未覆盖炮塔）**：48,731B，SHA256 `DAC7CB25…4AD6E0C9`；备份`build/backups/before-doorfix-20261102-054200`（v0.34.0 638AB1B0，config 未改 73B83AB5）。用户报告 v0.34.0 门控缺陷：透光门/水泄漏区（FOV_DIM）的混合包围盒按 ≥80% 加权比例被提升为全可见→摘遮罩直绘，门景暗度渐变丢失（门后炮塔亮显）。修复三处：①enemyState 房内路径 bbox 含 FOV_DIM 瓦片时禁 ≥0.8 提升（保留软遮罩，≤15% 隐藏不变）；②tile 级 fallback 路径同语义；③手臂与全可见单位长枪中心瓦片为 FOV_DIM 时回退 applyWorldVisual 软遮罩（粒子/子弹保持亮/隐二值——首轮"粒子也回退"版本实测同轮 +1.19ms 且粒子语义非主诉，收窄后手臂/长枪仅 O(1) 判断）。代价边界：门多且敌人常处门区的场景软遮罩开销回归（fxlibdoor02 同轮 35.57 vs 33.79=+5.3%，为最坏房型；无门场景零影响——fxCenterDim/dimTiles 均 O(1)/O(bbox瓦片)）。A/B fxlibdoor01/02 两轮（718 间隔/版本，benchmark-eligible）确认无崩溃、方向符合预期；官方冒烟 init ok v0.34.1-door-coverage/设置注册/tick 通过。**真机门后炮塔视觉待用户重启核对**（应恢复门景暗化覆盖）。重启生效。[报告](../knowledge/experiments/2026-11-02-fx-liberation.md#v0341-door-coverage-修复)，证据 fire-exhaustive-output/fxlibdoor01-02，实验 build/perf-20261102。

> 2026-11-02 **v0.34.0-fx-liberation 已部署（帧率解放：半分辨率雾场+遮罩门控+无损候选合并，含 locmem 修复）**：48,554B，SHA256 `638AB1B0…DAE807C8`；回退备份`build/backups/before-fxlib-20261102-014500`（locmem 35243D0F + config 13F5AB06），config 字节级追加`fog_vision_quality=0`/`enemy_mask_fast=1`/`vision_quality_preset=0`（421B，73B83AB5…）。四支柱：①移植普查会话 exact-render 的 coverage-fast+classic-repaint-v2（**遵从其"贴图门控/固定字段不纳入"结论**）；②`FOG_SUB`/`MASK_SUB` 常量→实例`fogSub`（137+31 处），预设 0 时 4 子格=像素量−75%，显示 2x 双线性、`applyVisionScale()` 重建模糊半径/经典矩阵；③敌人 80%/15% 加权面积门控（≥80% 摘遮罩直绘、≤15% 隐藏，仅临界带挂软遮罩）+ state=1 武器摘共享遮罩 + 手臂/长枪中心点二值；④`vision_quality_preset` 0极速(默认)/1平衡/2原版，单项键覆盖预设。**中途合并事件**：首轮基于 fx-fast 构建验证后发现并行会话 01:28 已部署 locmem——以 landmem 源为基线重放全部编辑（改动区零重叠），部署字节复验。六轮三版本同进程 A/B（fxlib01-06，718 间隔/版本）：固定 vs 历任 −1.5%~−4.2%、P95 −9%~−13%、>100 减半/清零、RV −34%；移动持平（噪声带内）；截图固有暗区泄漏 0.07%（与 fx-fast 同级）、亮区结构 83-92% 重合；官方冒烟 init ok v0.34.0/设置注册/tick 通过。仅 current 整窗计时；视觉取舍=雾羽化略粗/门控敌人边界无虚化/手臂长枪二值，preset=2 可全回原路径。[报告](../knowledge/experiments/2026-11-02-fx-liberation.md)，证据 fire-exhaustive-output/fxlib*，实验 build/perf-20261102。重启生效。

> 2026-11-02 **v0.33.17-locmem 已部署（换地图/楼层首房"整间已探索"修复）**：47,862B，SHA256 `35243D0F…97489D29`；回退备份`build/backups/before-locmem-20261102-013447`（旧v0.33.16 47,801B `F3223BF1…43799A` + config）。用户报告：进入新地图/新楼层后到达的第一个房间整间按记忆暗度显示。根因：跨房间记忆`roomMem`按`loc.id`存，而`loc.id`只是Land内坐标（`Land.as:945-957`，跨Land重名），且所有房间恒48×25（`Location.as:265-266`，尺寸校验永远通过）；Land一重建（读档/出口箱下一层/世界地图非base图），新到达房就命中旧同 id 记录恢复`explored[]`。修复：`roomMem`/`rangeMem`改 **Location对象弱键**（`Dictionary(true)`），对齐原版"记忆随Location/Tile实例存活"——重建后自然不命中、缓存Land复用仍保留，并顺带修掉同Land内prob房共用`loc0_0`的撞名。每会话恢复时记一行`roommem restore loc=… explored=…`。验证：候选构建退出0；官方ModLoader隔离副本冒烟 init ok v0.33.17-locmem/设置注册/tick 1–901、requested==ok；部署后回读SHA一致。**未做**真机自然换层复现对照（需专用驱动强制gotoNextLevel）——用户重启后换层核对即可：`RVision.log`出现`roommem restore`说明恢复路径正常、新楼层首房不再整间发暗。注意：与并行普查会话的未部署候选`v0.33.17-exact-render`(47,740B)是不同产物，正式安装只认`v0.33.17-locmem`。**该修复已并入 v0.34.0-fx-liberation。**[报告](../knowledge/experiments/2026-11-02-land-memory.md)，[回执](deployment-v03317-20261102.md)，源build/landmem-fix-20261102/src。

> 2026-11-02 **v0.33.16-fx-fast 已部署（开火卡顿·瞬态特效快速路径）**：47,801B，SHA256 `F3223BF193D60922E31EF88FB2674B9D945A7C21C35A3F0F3E8B21098A43799A`；备份`build/backups/before-fx-fast-20261102-002600`（旧combo-v4 SWF+旧config），config模板字节级追加`fx_vision_quality=0`（新SHA 13F5AB06…34F609）。瞬态特效（Part/子弹/弹壳/火花）改中心点视野查表二值处理：亮区摘遮罩原生直绘、暗区挂常驻空Shape遮罩（无栅格/cacheAsBitmap）；**不碰visible/alpha**——原生`Part.step`的otklad机制会把visible=false的粒子每帧设回true，visible开关与监听顺序不可靠，mask是常驻属性顺序无关。`fx_vision_quality`=0快速(默认)/1=v0.33.15逐特效遮罩原画质。四轮原生A/B（fire-exhaustive链33-36：固定/移动正反序+截图，238间隔/版本，基准=combo-v4冻结源重编译）：整帧均值-3.2%~-9.3%、RV调用-34%~-64%、固定108ms尖峰清除（34正序128ms单帧未在反序复现=噪声）；截图校验暗区泄漏0.07-0.09%（边界中心亮子弹尾迹预期）、亮区96%重合。官方ModLoader冒烟init/设置注册/tick通过。仅测current；classic走同分支未整窗计时；与并行普查会话共享登记无冲突（其50轮条目见下）。重启生效。[报告](../knowledge/experiments/2026-11-02-fx-fast.md)，证据fire-exhaustive-output/33-36，实验build/fx-fast-20261102。

> 2026-11-02 **本体开火全面普查继续（76轮，独立候选，暂不合并部署）**：遵守用户“各自测试”：不发跨会话消息、不写release/config。基线combo-v4 AEA30314/9D8662、关闭LAD。无损coverage+classic省重画独立包v0.33.17-exact-render（47740B/544B8062…72117）通过39/40/47严格图像、36设置及61当前loader原生射击；44/52/54有收益，48固定current不利结果保留，密集交战仍远慢于off。新增贴图上传/固定字段/空罩挂载/延迟矩阵均画面通过但配对性能不稳定，未加入。69重叠合罩1600像素反例；74/76直接Bitmap在真实阴影算法仍36/96组不同。65慢帧桶无明显IO/换页增长；72自有线程WCT仅单节点且观察开销高，未定位等待源，不作收益排名。70–76自有游戏及登记全部结束。报告knowledge/experiments/2026-11-01-fire-exhaustive.md；证据fire-exhaustive-20261101/index-76.json按哈希与压缩回读核对，排除其它会话fx-fast和游戏素材。正确性外框/alpha修复仍独立，不编HEAD生产；正式F3223BF1是其它会话视觉取舍包。本任务目标ACTIVE，剩余非重叠分组/类别与大图原生覆盖、引擎等待，未声称无损空间穷尽。


> 2026-11-01 **用户最新测试范围**：后续RealisticVision性能评估关闭光与暗，只评估RV本体；光与暗算法可以作为独立方向研究，结果分开记录。本轮仅调整测试入口与记录，未启动游戏或更改正式安装。


> 2026-11-01 **开火照明普查完成，未采用/未部署**：正式RV仍combo-v4 AEA30314、LAD0.7仍8ADBA691，准确冻结9D8662宿主/两模组生产源。36原生窗6000采样/5964间隔；前后两次照明分别负责AI曝光与新弹体画面，不可直接删。04移动阴影生成6.742ms，其中矢量转位图6.067ms，光带仅约0.4–0.5ms。光带90000射线/180图通过但只局部提速；绘图树1411图相等但固定79.09→98.41ms；精确轮廓2394原生图+900专项通过，09 current移动68.59→68.76ms无稳定收益，classic移动74.65→69.11有改善但不推广。直接渐变三版有1像素/1级反例；12普通夹具通过不能泛化，14在合法弹体参数f83仍失败。14登记/13自有AIR全部结束，安装配置未改；已归档失败、收尾权限核验与回执补录。后续需降低真实矢量遮罩转位图/显示合成开销，仍未解决全部长帧；不重复已失败路线或混入authority。工具build/shot-light，[报告](../knowledge/experiments/2026-11-01-shot-light.md)，证据shot-light-20261101；外部WIP保留。


> 2026-11-01 **双方开火分配/缩放/组合照明调查完成，未采用/未部署**：准确combo-v4/9D8662宿主，正式仍AEA30314。02移动窗current/classic产生7034/5855张临时差异图，部分40–52MiB内存下降伴随长调用，但清理批次不是最长帧，另有229ms中RV仅8ms。03/04缩放裁切同一f123像素反例否决；05夹具覆盖失败保留，07稳定滤镜后1440帧严格相等、2287次确定不等经完整比较核对。08原生ABBA无确认收益：current59.95→62.26ms、classic63.87→63.59，方向不稳定，候选不部署。06补查正式启用LAD0.7：119间隔内237–238次光照渲染，118–119次晚阶段补绘；仅隔离关闭弹体照明时RV开启均值56.86→52.10ms，真实设置未改，不能直接删补绘或当成无损优化。合计20窗2880采样/2860间隔，自有AIR/登记全部结束。下一步优先审查照明双绘制及曝光时序，不重复失败裁切/见证像素方案；外框/渐入恢复缺陷仍独立待修。KB-000108 r2补覆盖断言。[报告](../knowledge/experiments/2026-11-01-fire-cost.md)，工具build/fire-cost，归档fire-cost-20261101；其他WIP保留。


> 2026-11-01 **精确区域遮罩与墙alpha候选完成，未采用/未部署**：准确combo-v4源/9D8662宿主，正式仍AEA30314。区域候选按每格64位实际内容失效，alpha候选仅单源完整覆盖时比较透明度；两者独立。大小夹具各1202项、alpha47项严格图像对照通过，累计32459次区域复用输入相等。08长窗650秒超时，仅9窗；终段整机CPU约96–98%，部分优势不作发布依据。09复用相同三版字节、反序短窗12窗1440采样/1428间隔完成：current原64.15/区域80.97/alpha63.66ms，classic69.81/79.48/82.87ms；无确认收益，不部署。端点174进程不可读，跨轮不混比；逐进程CPU初采分母错误已明确作废并修正。01/02/05夹具失败保留，修夹具后通过；全部自有AIR/登记结束。下一步分配回收或实际采样覆盖取证，避免未证收益继续叠缓存；原外框/渐入恢复缺陷仍独立待修。[报告](../knowledge/experiments/2026-11-01-local-mask-regions.md)，工具build/local-mask-regions，归档local-mask-regions-20261101；外部WIP保留。

> 2026-11-01 **性能切口普查完成，未实现/部署优化**：正式仍combo-v4 AEA30314；本轮冻结新9D8662宿主，不能与旧CA94绝对计时混比。02两模式固定/受控移动4窗720采样帧、716完整间隔；插桩只用于诊断。74769次显示对象处理同帧重复0，纠正链/层双算假设。进入输入比较的current移动97.56%、classic固定/移动99.37%/99.57%相同；classic每窗比较3573万材质像素而墙轮廓重建0。优先原型：精确区域内容版本→材质alpha改写来源→分配/回收证据；缩放裁切须另做采样等价验证，本轮世界2/3缩放裁切0，不能泛化到用户前台最大化。01保存目录检查失败，02仅修探针路径后复用同RV字节成功；两登记/自有AIR均结束。低CPU长帧、外框/渐入恢复缺陷仍未解决。报告[性能普查](../knowledge/experiments/2026-11-01-performance-survey.md)，工具build/performance-survey，证据performance-survey-20261101；保留他人WIP。

> 2026-11-01 **阴影显示交叉归因完成，未部署**：正式仍combo-v4 AEA30314；冻结当前CA94宿主，4项34窗6086完整间隔。01完整57.67/off37.10ms，跳单位及特效46.93/隐藏雾45.26/同时35.59；两路径各有成本，交互两方向−2.53/+4.68不稳定。共同祖先无滤镜/缓存；显示雾时整个进程约1.9–2.2核，隐藏约1.1–1.24核。02整层cacheAsBitmap原48.18→55.68ms，P95 63→103，12图像对照都有1–2级差，否决。03/04细分随时间波动，不能按总体均值认定具体子层成本；最大794ms中RV2、剩余779ms，一秒采样无法归因，未重现旧5394ms。下一步较密自有句柄采样抓亚秒停顿、补真实最大化呈现路径；原外框/渐入恢复缺陷仍待修。所有自有AIR及4项登记结束；KB-000107 r4补采样边界。[报告](../knowledge/experiments/2026-11-01-composite-followup.md)，工具build/composite-followup；保留他人工作树。

> 2026-11-01 **combo-v4审核完成，未部署修复**：正式RV仍47,534B / AEA30314…9AA557。准确生产源与D56仅主类变化，其他5文件相同；已冻结本轮两版源码。确认外框缓存漏scaleY/子几何（08独立D56 scaleY反例3840像素差）、fadeCount未初始化、关闭时alpha残留0.19921875。40窗7160完整间隔；最大化首轮off34.38/D5649.44/v444.73ms，后续有显著负载波动，不能套用旧小窗“问题均已处理”结论。零敌人扫射也变慢；跳过独立特效CPU3.49→0.80ms但整帧未改善；隐藏fog显示55.32→49.64ms、P95反变差，只有归因价值。5394ms无敌/无弹停顿中RV0ms、剩余阶段5330ms，极端长帧未精确定位。02后置PNG失败后04/08补验；06/07宿主8321→C6漂移被拦，08/09只在副本复用冻结8321；真实/种子CS nativeEnabled均false。所有自有AIR/登记结束。下一步优先修恢复/缓存正确性，再查阴影合成和单位软遮罩整体绘制，不能继续只靠FOV节流或把撤罩诊断当候选。[报告](../knowledge/experiments/2026-11-01-combo-audit.md)。


> 2026-11-01 **v0.33.15-combo-v4已部署**：47,534B，SHA256 `AEA30314…9AA557`；旧v0.33.14备份`build/backups/before-combo-v4*`。增量：1) 单位从全隐→可见过渡加5帧alpha渐入（修复炮塔在阴影边界二分切换）；2) FOV兜底30→90帧（站立开火不再每秒一次~4ms周期尖峰）。移动-4.1%/RV-23%；固定RV-40%。累计D56→v0.33.15：移动约-20%/固定约-15%。用户两个问题均已处理。生产源`build/mask-budget-output/production-combo-v4/src`。[回执](deployment-v03315-20261101.md)。combo_v5 sight采样已否决（RV-12%但整帧+1.7ms且有漏检视觉风险，[报告](../knowledge/experiments/2026-11-01-sight-sampling-rejected.md)）；零影响优化已达边际，RV约3.6ms移动/1.2ms固定。

> 2026-11-01 **最大化与三种绘制候选验证完成，未采用/未部署**：正式仍combo-v4 AEA30314；冻结CA94宿主。01/02/03/05共24窗8616完整间隔；02地板分支12组图相等，但整帧47.95→48.70ms；03硬裁切合并49.21→52.14ms，8图均有1/255轻微差；05相同贴图门控8组工作图/最终图/重复参考全相等，current43.44→44.46ms、classic51.69→62.28ms且正反方向不一致，均无确认收益。01真正最大化客户区1280×729；off组896ms停顿内7个100ms桶CPU时间无刻度增长、周期非零，证实低执行量但未定位等待源。04读写结果文件占用失败，不纳性能验收；修正唯一快照/finally退出后05相同字节正常完成。5项登记及全部自有AIR结束；KB-000107 r5回流方法。原外框/渐入恢复缺陷仍独立待修，保留他人WIP。[报告](../knowledge/experiments/2026-11-01-maximized-flow.md)，工具build/maximized-flow；后续需分别追查显示成本与呈现/线程等待，不复用本轮失败候选。

> 2026-10-31 **v0.33.14-combo-v3已部署（零视觉影响）**：47,415B，SHA256 `C1CB90C5…DADF8`；旧v0.33.13备份`build/backups/before-combo-v3-20261031-173735`。增量：整数tile key（消除~100次/帧字符串拼接）+ Matrix缓存（消除~100次/帧Matrix分配）+ corner reuse 4→16px（配合motionstep=4.0）。移动-1.7%/RV-9.7%；固定-3.7%/RV-35%。累计D56→v0.33.14：固定约-13%/移动约-16%。生产源`build/mask-budget-output/production-combo-v3/src`。[回执](deployment-v03314-20261031.md)。
> 2026-10-31 **v0.33.13-combo-v2已部署**：47,326B，SHA256 `3F6E6072…6D96D`；旧v0.33.12备份`build/backups/before-combo-v2-20261031-164852`。增量：`motionstep` 2.5→4.0 + `applyWorldVisual` getBounds缓存（transform不变时复用bounds）。移动A/B（active 1280×720六敌）：v0.33.12 normal40.43→v0.33.13 **37.75ms（-6.6%）**、RV6.48→**5.05ms（-22%）**、P95 52→50、>100 1→0；固定41.18→40.32ms无回退。与off差距缩至4.39ms（此前7.07ms）。官方ModLoader smoke通过`v0.33.13-combo-v2`。配置`motionstep=4.0`；后续测试默认关闭LightAndDarknessMod。生产源`build/mask-budget-output/production-combo-v2/src`。[回执](deployment-v03313-20261031.md)。

> 2026-10-31 **v0.33.12-combo已部署**：47,195B，SHA256 `26456B67…46FB255`；旧v0.33.11备份`build/backups/before-combo-20261031-155952`。组合：墙面输入门控（输入不变跳`updateWallSurface`，每30帧兜底，像素等价）+ 四角射线复用（`fillFogCache`，|Δeye|≤4px/≤2帧，分类差异0.0035%，有近似）+ P1清理 + `motionstep=2.5`（可配置0.25恢复旧频率）。active 1280×720六敌A/B：固定normal38.86→35.03ms（-9.9%）、RV2.80→1.79、>100 1→0；移动normal48.44→43.82ms（-9.5%）、RV8.71→6.19、P95 66→55、>100 3→1；逐窗两轮方向一致。官方ModLoader路径smoke：`init ok v0.33.12-combo`、tick1/181、settings registered。视觉：墙体/角点近似与2.5px更新滞后，采样截图无明显异常，未做严格像素/视频验收；**用户2026-10-31明确接受视觉损失**。后续性能测试默认关闭LightAndDarknessMod（mask-budget/run.py默认排除，`--allow-lightanddarkness`可恢复）。回退用备份SWF。准确生产源`build/mask-budget-output/production-combo/src`。[部署回执](deployment-v03312-20261031.md)，[报告](../knowledge/experiments/2026-10-31-combo-deployment.md)。

> 2026-10-29 **D59扫射/交战卡顿只读排查与方案，未改模组/未部署，正式仍D56**：确认D56–D58固定位置协议漏掉移动态：固定位置current每120帧仅4次视野重算、RV 3.29ms；D44受控移动profile约13ms/帧（applyVision4.98、updateWallSurface2.45、hideEnemies5.13，refreshMask 97次/帧）。六敌small-02撤RV遮罩43.66/60.38→33.70/33.24ms（仅诊断），但D56后current与off差已约4.8ms，继续缩遮罩几何上限低。方案P0类别归因→P1零画质清理→P2移动态刷新节流/脏区→P3遮罩结构/特效分级（需画质拍板）→P4长帧归因。P0已完成：active 1280×720通道绕过启动阻塞，固定normal 51.29/RV3.72ms、移动normal 49.97/RV8.20ms（off 38.80/34.72）；六类中仅unit body mask固定/移动4/4窗一致（约-3.4ms），Part数量最多但两窗方向不一致；撤罩不降RV AS3、变化在绘制后段。移动态profile：updateWallSurface 2.73ms/帧、fillFogCache约2.03ms/帧平均、refreshMask仅0.85ms/帧，故P2.1掩膜节流上限<0.5ms。P2-A墙面门控+P1清理候选已A/B：固定约-0.5~-0.7ms（RV1.70ms）、移动无确认收益，未达明显收益，未采用/未部署。三方向尝试完成：方向1 FOV阈值2.5px固定-0.84ms、移动帧持平/RV-1.47但P95变差；方向2 身体mask 80/20阈值固定-0.59ms、移动+12.85ms回退；方向3 最小组合因存档依赖#1009失败，去RConnect/ContinuousScene各约0-1ms、长帧样本极少。无可部署候选。其他未检查方向调查：applyWorldVisuals约99.5次visual/帧、链132.5节点/帧、层275子对象/帧，扫描约0.4ms/帧、逐visual工作是大头；fillFogCache 3.4ms/次且95%帧调用为最大未处理项。按建议实现的visfast/fulldark均无收益：固定normal43.72/visfast47.61/fulldark49.30ms，移动46.18/47.68/48.53ms，未部署。角点验证：85742个复用瓦片仅3个分类不一致/2个分支不同（0.0035%），分类近乎等价；复测方向不一致（18:-1.27ms；20:+0.73ms、RV+1.56、>100 3→6），未证实收益。长窗TDFC排除：normal65.30 vs 全组合67.44、其它监听5.33 vs7.59，但RV/off环境差异大、长帧均5次，TDFC非尖峰主因。下一步更干净角点配对或MSW/FirearmAttachments长窗排除，或接受画质取舍。[corner-verify-longwindow](../knowledge/experiments/2026-10-30-corner-verify-longwindow.md)，[corner-reuse](../knowledge/experiments/2026-10-30-corner-reuse.md)，[visfast/fulldark](../knowledge/experiments/2026-10-30-visfast-fulldark.md)。

> 2026-10-29 **D58继续优化，未采用/未部署，正式仍D56**：拆分aux/vector因B190并行不排名；30/60帧校准未支持固定33ms等待主因；小数裁切前两组通过但固定视野f482反例否决。支持区缓存1446严格检查通过，09/10共24战斗窗4296间隔，current均值低3.92%/1.85%但局部CPU不稳、classic两轮回退，不发布。10个实验全部结束，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-29-combat-split.md)，工具build/combat-split。

> 2026-10-29 **D57六敌交战调查结束，未采用/未部署，正式仍D56**：身体裁切1531项、alpha裁切722项+原生60帧、减少临时对象723项均有功能证据，但整帧收益不稳定或回退。纠正菜单显示层残留、原生后固定狮鹫姿态及kol_shoot计数；纠正后68窗11692完整间隔（含内存归因）。长帧分布原生/RV/其它监听/绘制后等待；部分内存骤降不证明全由RV分配。22个实验均结束，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-29-enemy-combat.md)；工具build/enemy-combat，经验KB-000123 r4。

> 2026-10-29 **D56 v0.33.11已部署**：current保留原采样格并缩小特效遮罩，真实内容变化时刷新目标关联；classic保持旧路径。发现旧跨帧关联残留，最终721项对照通过，准确包36设置及原生240帧/119次开火通过。三组current配对平均约低7%–12%，最终48.51→42.55ms、P95 65→56ms，仍有102ms长帧。准确包BD64B5BB…CE4A9AD（46441B），生产源build/effect-mask-origin-output/production/src，不含authority；旧638E已备份。29轮自有实例/登记全部结束，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-29-effect-mask-origin.md)。

> 2026-10-29 **D55同批特效回放完成，未采用/未部署，正式仍D44**：stable-v4通过1081项+原生60帧，重画2703→829，但完整扫射45.49→46.04ms未改善。identity-blit原生60帧通过、首轮current约快3.7%，反向current持平/classic变慢，扩展位图检查又在f121失败。原D47 identity也有原生47像素反例。21轮全部结束，完整扫射共24窗4296间隔/3161次开火；主src/release不改，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-effect-replay.md)，工具build/effect-replay。

> 2026-10-28 **D54最大化持续扫射已复现额外成本，未修复/未部署，正式仍D44**：用户已确认正式启动器、current、轻机枪整个持续扫射、最大化窗口。只读存档副本+原生keyAttack、容量内补弹、单人固定位置，独立私有桌面实际visible=true。28拆分正常53.96/禁鼠标54.17/计算后撤罩48.51/跳过特效46.11ms，支持动态特效绘制线索；撤罩不是修复。integer-v2通过721+888严格检查但27整帧回退；预绘共享通过721但整体收益不稳定，直接Bitmap两版f121差异，均不采用。候选v0.33.11-trailing-cache未部署，不能安装。主src/release不变，自有AIR全退出，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-sustained-fire.md)，工具build/sustained-fire。

> 2026-10-28 **D53单人轻机枪调查，未修复/未部署，正式仍D44**：按用户current/LMG补32窗、7168完整间隔、3060次真实开火；均有B190并行，帧数据仅诊断。early-dark候选361严格图像/13281阳性通过，无明确整帧收益，未采用。首次开火先开RV93ms、换新进程先关RV仍87ms，支持继续定位非RV的首次开火环节，不足以认定加载/绘制根因。训练房未稳定复现持续明显卡顿。已询问实际入口：正式v0.33.10还是独立B190 v0.30.2，尚待答复；未改试玩。全部本轮自有AIR退出，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-solo-fire.md)，工具build/solo-fire。

> 2026-10-25 **D52独立战斗复验完成，未采用，正式仍D44**：用户“可进行测试”已撤回此前性能暂停。D50 all及D51 v2两轮32窗、6688完整帧间隔，调换模式/候选次序并复用相同冻结字节；均未证明稳定完整战斗收益，不合并或部署。两次构建后预检失败均未启动AIR，修正后新目录通过；旧暂停标记改名保留。所有自有AIR与描述符退出，正式638E/config5136不变。详见[报告](../knowledge/experiments/2026-10-25-candidate-comparison.md)，证据candidate-comparison-d52-20261025。

> 2026-10-25 **D51功能完成，性能仍暂缓，正式仍D44**：独立候选candidate-v2用原遮光快照证明空矩形后省略逐格射线，墙/门/水/异常值回退；21129条射线及134827项检查、192×75原生64次严格画面全部通过。原生回放快速路径368918次、循环33896533→29561650，只是步骤计数，未证明帧率收益。用户保留试玩的选择有效，无独立计时/部署。自有AIR均退出。详见[报告](../knowledge/experiments/2026-10-25-ray-clearance.md)，证据ray-clearance-d51-20261025。

> 2026-10-25 **D50功能完成，独立计时暂缓，正式仍D44**：classic私有插值raw候选6529+64检查通过，亮度0.6普通房间战斗均值51.89→50.79ms，current52.87→53.48ms；单轮小收益未采用。all再缓存私有墙场，6529局部+64原生+59397临界尺寸/设置/模式/换房检查严格相同，尚无性能数据。用户选择保留player-1/player-2、先做代码和画面检查；暂停独立计时，不关试玩。所有自有AIR退出。详见[报告](../knowledge/experiments/2026-10-25-classic-inputs.md)，证据classic-inputs-d50-20261025。

> 2026-10-25 **D49结束，正式仍D44**：雾层同值setter跳过通过414项严格画面检查；完整战斗current61.47→61.77ms、classic65.70→66.44ms，>100ms未降，不采用。原始D44嵌套热点：current fillFogCache4.56ms，classic classicLogicRegion3.46ms，滤镜树0.02–0.04ms；不能相加或当性能验收。下一步检查classic原始插值工作图复用，仍只按旧查询范围发布，不扩大fogCache范围。所有本轮AIR已退出；详见[报告](../knowledge/experiments/2026-10-25-fog-setters.md)，证据fog-setters-d49-20261025。

> 2026-10-25 **D48结束，正式仍D44**：共享4×4格模糊场的shared/shared-v2各通过361+888项，但直接引用大位图的reference两版均在帧164出现24像素差异，淘汰。首轮计时受自有去重IO干扰，仅诊断；shared-v2干净12窗current68.08→70.00ms、classic71.89→71.51ms且最大408ms，无稳定收益，不采用。所有本轮AIR/队列结束。下一步检查ensureFog/RVWallSurface每帧重复设置相同显示属性是否造成大雾层重建，不叠加本轮候选。详见[报告](../knowledge/experiments/2026-10-25-shared-mask.md)，证据shared-mask-d48-20261025。

> 2026-10-25 **D47结束，正式仍D44**：2864个完整间隔已区分原生函数/其它监听/RV/剩余，六敌场景RV约13–14ms；318ms峰值发生于关闭RV且无弹体，不能把剩余全部归GPU。恒亮实际范围撤mask候选通过1309项，但12战斗窗current67.69→68.16ms、classic70.75→69.25ms，尾部不一致，无稳定收益，不采用。所有本轮AIR和队列结束；下一步验证相邻动画共用模糊场，先证明局部边界等价。详见[报告](../knowledge/experiments/2026-10-25-frame-attribution.md)，证据frame-attribution-d47-20261025；方法已补KB-000107 r3，目标仍未完成。

> 2026-10-25 **D46结束，正式仍D44**：清理观察四窗2156配对帧，28个实际释放帧41–93ms，505ms峰值发生时没有释放，不支持集中释放主因，未做分帧释放。相同输入分类复用carry通过361+888检查、阳性40453次，但12战斗窗整体无稳定收益（current63.75→63.52ms、classic60.23→61.89ms），未采用。所有本轮AIR和队列结束，不再追加争占测试。下一步区分RV调用外的宿主/绘制/调度开销，避免继续只减局部CPU。详见[报告](../knowledge/experiments/2026-10-25-mask-lifecycle.md)，证据mask-lifecycle-d46-20261025；目标尚未解决。

> 2026-10-25 **D45结束，三候选均未采用，正式仍D44**：tileclip有19像素差异；precise及cacheoff严格图像通过，但完整战斗性能未达标。四轮64窗包含40窗受限分组诊断，不能算生产验收；源指纹、实际14项加载与真实开火已核对。cacheoff的classic均值66.81→76.15ms、>100ms次数20→58，拒绝部署。旧mask计数含Shape反向链接，已纠正。两簇长停顿从60帧清理点开始，仍只是关联；下一步测释放数量/像素量。所有本轮AIR和队列结束。详见[报告](../knowledge/experiments/2026-10-25-mask-area.md)，工具build/mask-area，冻结证据knowledge/experiments/mask-area-d45-20261025。

> 2026-10-25 **D44 v0.33.10已部署**：跳过相同mask/cache/visible写入，完全透明支持区用空遮罩，复用临时矩形。1284项/组及完整14模组24战斗窗通过；四组均值减少约16%–19%，P95及>100ms次数均下降，仍未达到同组合关闭RV的流畅度。准确包638E2D40…FE343710（46110B），生产源build/combat-render-output/production-final2/src，不含authority；正式init/设置注册/tick1/181/361通过，旧BF4A已备份。开发线保留active authority记录调用，单独编译通过，未将其发布。详见[报告](../knowledge/experiments/2026-10-25-combat-render-attribution.md)。

> 2026-10-24 **D43 v0.33.9已部署**：在独立特效的原有采样中判断全亮/全暗，跳过不需要的模糊及辅助图，不重复classic采样；边界与宽滤镜沿用原算法。1131项/组、36原生六敌战斗窗与正式启动通过。SHA bf4ac9cd87272b03fae7ec22ee67d045f037362f412ee801cad3f9ba9fe3afef，45826B；准确源build/effect-load-v3-output/production-final/src，不含authority。两版失败方案与环境异常保留；受控测试RV更新current约少20%、classic约少6%，完整帧基本持平，最长帧未解决，测试调度策略未部署。[报告](../knowledge/experiments/2026-10-24-effect-load.md)。

> 2026-10-23 **D42 v0.33.8已部署**：按世界位置裁切原生弹体/激光/粒子、狮鹫独立手臂和身体外敌方武器；明区原生绘制、全零支持区空遮罩。1000项/组及12完整组合跑动射击窗、正式init/注册/tick1/181/361通过。SHA 0dbe0d7a95b8e496fb393d7fcd75f88d60c34a1d0fabb33266b122e3fa04f2bf，45600B；准确源build/effect-visibility-output/production-final/src。尚未达原版流畅度、第三方自有遮罩优先。[报告](../knowledge/experiments/2026-10-23-effect-visibility.md)。

> 2026-10-23 **D41 v0.33.7已部署**：复用身体/血条/武器遮罩图形，classic仅补算未缓存视野区，current局部清理并保留静止墙光失效。747项/组、12原生战斗窗与正式init/注册/tick1/181/361通过。准确包6dbbae60eb09…（44604B），生产源build/boundary-load-output/production/src。密集移动更新classic约11%下降、current约3%–4%；完整帧classic60.2→57.2ms，current基本持平54.7→55.3ms，未达原版，长帧未全解。[报告](../knowledge/experiments/2026-10-23-boundary-load.md)。

> 2026-10-23 **D40整体性能试验完成，未发布**：六候选中05 classic合并逐格扫描通过96组严格图像与36设置；局部CPU略降，24原生跑动射击窗整体收益未稳定。正式仍D39 83D8…205C7E65，src/release未改。847ms长帧中RV22ms；另有内存下降相关峰值，根因未完全定位。外部高频监测证据标无效性能验收。[报告](../knowledge/experiments/2026-10-23-overall-flow.md)；候选/数据build/overall-flow-output，勿据功能通过自动部署。

> 2026-10-22 **D39 v0.33.6已部署**：定位镜头跨墙面缓存边界的集中重建；复用重叠世界区域轮廓、预计算精确采样模板并保留异常失效。414项/组、96组严格图像及完整组合12窗通过；准确包83d8e590…205c7e65（44427B），正式init/注册/tick1/181/361通过。仍有非RV长更新的长帧，不声称全部卡顿消除；[报告](../knowledge/experiments/2026-10-22-long-frame-triggers.md)。生产源build/long-frame-output/production/src，无authority；D38备份见部署回执。

> 2026-10-22 **D38 v0.33.5已部署**：classic按4×4格复用精确逻辑采样；两模式墙面支持区/补集一次生成。同输入更新下降classic约20.5%～21.6%；current约8.5%～9.0%，4987项/组、12原生射击窗及正式init/注册/tick1/181/361通过。准确包6593EE35…8FD6EC06（43818B）；[报告](../knowledge/experiments/2026-10-22-followup-performance.md)含完整帧间隔和长帧边界。生产源build/followup-performance-output/production/src，无authority；D37备份保留，正常重启生效。

> 2026-10-22 **D37 v0.33.4已部署**：保持D36画面，classic视口合成/变化格重算、材质复制计划复用、FOV保守遍历及current本地子格缓存。8191项/组、12原生射击窗、准确包设置与正式init/注册/tick1/181/361通过。战斗帧间隔classic66.85→40.75ms、current45.87→37.48ms，同场off约33.3ms，仍未完全达原版。准确包187D287B…4111272（43816B），冻结生产源见本轮证据production/src，无authority；[报告](../knowledge/experiments/2026-10-22-native-performance.md)详录取图纠正/长帧边界与D36备份。

> 2026-10-22 **D36 v0.33.3已部署**：原生手持武器漏扫childObjs导致记忆区泄露，现按所属单位每帧裁切并独立遮罩；806泄露像素归零，1848项和8原生射击窗通过。current软遮罩改批量处理，画面严格相同；实际耗时和长帧边界见[报告](../knowledge/experiments/2026-10-22-combat-visibility.md)。准确包AB461FF3…2F23871（42400B），生产源build/combat-visibility-output/production/src，无authority。正式init/设置注册/tick1/181/361通过；备份D35见deployment/receipt.json。

> 2026-10-21 **D35先回退，再修复并部署v0.33.2**：22:17恢复下午前D32；23:35准确安装7852F61E…BE86764（41,630B）。自定义亮度不再重复整图合成/地形扫描；显示与逻辑隔离、设置、阶梯和防溢出保留。1731项检查及8个原生射击窗口通过，正式路径init/设置注册/tick1/181/361通过。D32配对四组更新加绘制均值低3.8%～21.6%，current默认组最大值仍83→125ms，不能承诺无卡顿。生产源build/regression-recovery-output/production-singlepass/src，不含authority；回退备份before-settings-recovery-20261021-233515-ab290b为D32。详见[报告](../knowledge/experiments/2026-10-21-settings-performance-recovery.md)。

> 2026-10-21 **D33合入D34，v0.33.1已部署**：墙轮廓线性扫描/紧凑缓存与classic零修正跳过；完整保留视野设置、阶梯与防溢出。471项/组通过，正式路径init/设置注册/tick1/181/361通过。SHA F2B8A973D9D2A374C9BD8F5DA9D29040266954C8F139B8C85BFA0AAAA749A561。大图配对更新加绘制均值下降6.9%–15.4%，持续射击classic更新约降18.3%、current基本持平；最大长帧未全面改善，不宣称卡顿全解。准确源build/motion-performance-output/merged-settings/production/src，不含authority。详见[报告](../knowledge/experiments/2026-10-21-motion-performance.md)。

> 2026-10-21 **D34 v0.33.0已部署**：已探索区亮度、分模式柔化与0.5–3倍房间视距；默认画面与D32严格相同，251项通过，正式路径init/设置注册/tick1/181/361通过。SHA 8D4A19634770ACCA0B66C8C684955855EF4725E80FBDFF329451D69710C55BF1。准确源build/vision-settings-output/candidate/src，不含authority及未发布D33候选；后续性能合并不可覆盖设置。详见[报告](../knowledge/experiments/2026-10-21-vision-settings.md)。


> 2026-10-19 15:26:52 **D32 v0.32.3阶梯与性能合并已部署**：准确包76314B81…AF5C46B7（37,775B），D31六项优化保留，仅合D30高度条件。299项功能通过；8组每组500错误黑空气像素归零，墙材质/修正区外差0，ON参考1级残差保留。正式新init/设置注册/tick1/181/361通过，PID35268与描述符已清理，窗口交回RConnect。旧DECCA备份保留，用户正常重启生效。详见[部署回执](deployment-v0323-2026-10-19.md)及[报告](../knowledge/experiments/2026-10-19-stair-performance-merge.md)。

> 2026-10-19 **D30阶梯候选已由D32合并部署**：原325A0DDC…F6770A92基于D29，不直接安装；局部helper高度条件已合入D31生产线并以76314B81…AF5C46B7完成新组合验证。原299项与独立严格18/8、隔离4/4保留历史，ON负1残差逐点原因未尽证。详见[原阶梯报告](../knowledge/experiments/2026-10-19-stair-shadow.md)。

> 2026-10-19 13:27:40 **v0.32.2已部署**：用户明确部署并确认新测试窗口后，准确安装DECCA3E0…C4A0B10CA（37,760B）。正式路径独立实例确认新版init、设置注册及tick1/181/361；18项保护指纹不变，PID93512与描述符已清理，窗口已交回RConnect。D29单模组备份已保存，用户正常保存并重启生效。详见[部署回执](deployment-v0322-2026-10-19.md)。

> 2026-10-19 D31 **已部署版本的验收依据**：保持原画面的六项优化已完成。55项聚合检查、48,000次分类、192组位图、32组192×75原生像素及准确包两进程20项设置检查通过。最终大图四场景各120配对样本，更新加绘制平均减少5.6%–14.2%、P95均下降，但classic最大值243→266ms，长帧仍存在，非完整游戏FPS。准确安装v0.32.2-frame-performance，SHA256 DECCA3E0E1142EB8FAF7E0E776F2B94FC67DCE1C5503DE7FBA7B810C4A0B10CA。源码提交25143cd，生产源固定build/frame-performance-output/production/src，不含authority或并行阶梯修复，不能直接编译HEAD替换。无需重跑已完成或取消轮次；详见[报告](../knowledge/experiments/2026-10-19-frame-performance.md)和[工具](../build/frame-performance/README.md)。

> 2026-10-16 16:06:22 D29 **已部署**：v0.32.1-wall-performance，36,992B，SHA256 `2E7150CF415355C2D7B809689AAC3C4CA0BACBB5F6D8770066A6E887D8907A10`。保持D28原生墙芯/渐变和防溢出；常亮默认关闭并保留保存值。复用墙边采样、光照缓冲区与常亮墙面图；336项、68组人工差分与16组原生雾层严格相同，准确生产字节及正式路径启动通过。相比D28同进程平均渲染开销减少约4%–9%，非完整FPS，长帧/密集联机仍有边界。仅改RV，authority WIP保留。详见[报告](../knowledge/experiments/2026-10-16-wall-performance.md)和[回退记录](deployment-v0321-2026-10-16.md)。

> 2026-10-15 22:27:59 D27 **已部署**：设置新增“已探索墙边常亮”（默认开、即时保存）；关闭后墙面随视野变暗，classic/current的透明凹口与墙边阴影修复始终生效。正式安装v0.31.1-wall-options-candidate，35,017B，SHA256 `BAA48289D9CF86F64CFF53B4734032AD29C89C3AC1704DB2D89038D4B8DB4275`。精确安装验收候选，保留改键与场景兼容；212项开发检查、8组图像、20项生产字节设置检查和正式路径init/设置注册/tick1/181/361通过。备份和单模组回退见[部署回执](deployment-v0311-2026-10-15.md)。平均额外渲染约9.8～13.7ms；大型全模组战斗未验。需保存并重启游戏生效。

> 2026-10-15 菜单改键已安装：本模组改键候选已随统一六客户端安装并从正式路径读回，七模组23项联合两进程346项通过。当前正式SHA256 E99608088A8B00B4442BC3AEF52D8035336F0123EA5A96D55503C90B1F6E0808。入口「模组→对应模组→快捷键」，保存后重启游戏加载新版；本机偏好即时保存。备份/回退及权限见[keybind-deployment-2026-10-15.md](keybind-deployment-2026-10-15.md)。下方候选及旧安装记忆保留历史；未发布WIP没有带入本次安装。

> 2026-10-15 菜单改键候选完成，未部署：调试、总开关、渲染模式三项可在「视野系统→快捷键」修改并即时保存，提示文字同步。准确生产线候选E9960808…1F6E0808，排除墙面候选与authority WIP；最终七模组346项和公共39项通过。详情见[keybind-integration-2026-10-15.md](keybind-integration-2026-10-15.md)。

> 2026-10-15 D26历史墙面候选（已由上方D27替代），**未部署**：用户确认“已探索墙边常亮”，D26 更新旧 D22 的记忆墙压暗要求。classic/current 共用实际材质轮廓，墙内约12px亮面、至32px渐隐；墙芯/未探索背面/地板雾效及敌人视野保持各自规则。候选 v0.31.0-wall-surface-candidate，29,879B，SHA256 `6DE9C96EBF48E7CB9E01479DD5661E21625625E2EE9C1B6F9E5F640B7518E06D`。当时正式安装为 v0.30.5-scene；当前安装见顶部改键部署。历史报告与对照：[已探索墙面](../knowledge/experiments/2026-10-15-explored-wall-surface.md)。

> 2026-10-15 16:18:17 当前安装已随 ContinuousScene 0.5 更新为 **v0.30.5-scene**，SHA256 `B7695DF82AA45FDB783C4EB88AFFCB0C34A7674E3A052D2FD128867172A83A49`。来源为冻结的0735491生产线加CS兼容补丁，未发布authority接口或既有WIP；不要用HEAD直接覆盖。详见[本轮部署记录](deployment-scene-v05-20261015.md)。当前回退仅经 `ContinuousScene/build/upgrade-v05.ps1 -Action Rollback`；下方旧部署与回退说明保留作历史，既有开发内容不变。

> 2026-10-14 23:10 ContinuousScene预绘兼容已升级：**v0.30.4-scene**，SHA256 `89B391BCE114534D6F2C0147BD4B136602168EE4362AA36F6F0C37ECD47173B5`。大图视野快照在有可见单位需要时才复制，场变化即时失效；原视野、遮罩和小房间保留。42项视野、48项场景、15项安装启动通过。仍由0735491生产线叠加补丁，不发布authority接口/WIP。当前回退归ContinuousScene/build/rollback-v03.ps1；详见[本轮部署记录](deployment-scene-v03-20261014.md)。下方0.30.3为历史。

> 2026-10-14 ContinuousScene兼容已安装：**v0.30.3-scene**，SHA256 `ED76EC15666FD8CD50ACF0149F7EC32F2602D2E68D753580A0EC5814B95A2E99`。用户明确允许必要兼容修改。大场景雾绘图、模糊和显示裁切按镜头范围，小房间范围/逻辑视野/共享探索保留。安装包从原安装线0735491叠加补丁构建，不包含HEAD的authority接口和下述既有WIP；切勿用HEAD未经核验直接覆盖。37项视野、全模组44项和正式原生启动通过。详见[兼容部署记录](deployment-scene-20261014.md)，配置未改，备份归ContinuousScene统一管理。

> 2026-10-12 后续：RConnect主会话按既有独立接口授权增加readNative：在AIR帧完成后采样时临时撤回RV显示字段/掩膜，再在finally恢复本机图像与层次。RV003配B149实际vision d48ad492e649主86/0加76/0：真实墙前/墙后敌人、正常及抛错后的掩膜/显示/层次精确恢复，发布不带宿主隐藏结果；148身体专项主157/0加89/0。独立小检查增加5项但临时启动被本地护栏拦截未执行；原15项绿灯仅属于RV002。完整最终冻结和压力仍需核验。安装release、旧共享探索API均未改。

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

> 2026-10-16 构建清理完成：删除1,409份重复运行素材/字节码，独立文件大小约2.09GB；1,427个文件指纹核对通过。当前安装、生产源、验证图与回退备份保留；重跑旧实验前按[恢复说明](../build/CLEANUP.md)补齐素材。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current 三模式。入口 RealisticVisionMod，源码 src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组 loader。

## 2. 用户偏好与协作约定

- 2026-11-01用户明确：后续RV性能测试必须关闭LightAndDarkness，优先最小依赖组合，对比RV关闭/current/classic；必要依赖保持一致并列明。核对实际加载日志，不能只关弹体照明；收益只归于RV。光与暗算法研究可另行进行，不混入RV本体评估，也不改玩家正式加载名单。
- 模式标识不常驻右上角，只在切换模式时于左上角短暂提示；本次沿用3秒时长。
- 共享探索任务的新授权：宿主/加入者双向，各自控制接收，关闭后保留共享区域；RV 按自身设置显示。允许同时修改 RV 接口，禁止对 RConnect/RV 相互引入硬性依赖。本轮已获“替换正式版本”授权并完成部署。
- 用户已明确“认可你的设计，请继续”：落实 current 投影轮廓配连续地板渐变、适中/宽两档比较、刷新与错误亮点修复。不是尚待定案的讨论。本轮用户进一步明确“部署”，已完成正式替换与独立启动检查。
- D25：允许地板边缘有限柔和过渡，不把边界外所有非黑像素自动判错；柔化不扩大逻辑视野或探索。默认推荐适中约28px，宽档约41px供比较，均是斜边实测10%–90%范围。
- D28新决定：保留已探索墙边常亮选项、默认关闭。关闭恢复v0.30.1原生墙芯和渐变，透明凹口独立修复；开启才保留D26亮面。开关只改材质，原地板/原版记录/地图传送/敌人视野保持隔离。历史D26/D27默认开启已被替代。
- 同场景、同输入对照，实际 AIR 复现；不能把固定步算法耗时当完整游戏FPS。用户精确存档、相机/历史与战斗验收仍需区分。
- 不写其他模组、不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，不恢复旧记忆播种/墙面受光传播。a583f1a念力守卫保留。

## 3. 当前状态

- 当前安装 **v0.34.3-eye-boundary**，49,048B / `0861FB64…6DD2E30B`；准确生产源 `build/eye-boundary-output/candidate/src`，保留 v0.34.2 的门区、激光与跨地图记忆修复。771项针对性检查及正式包冒烟通过；无需追加未请求的性能普查。本轮已结束，等待正常重启后的实际游玩反馈。详情见顶部新条目。

- 历史安装 **v0.33.17-locmem**，47,862B，SHA256 `35243D0F…97489D29`；准确生产源 `build/landmem-fix-20261102/src`（自fx-fast冻结派生）。修跨地图/楼层首房"整间已探索"：房间记忆改按Location对象弱键。冒烟 init/设置注册/tick1–901 通过；真机换层核对待用户重启后确认。回退备份`build/backups/before-locmem-20261102-013447`。重启生效。

- 前一安装 **v0.33.16-fx-fast**，47,801B，SHA256 `F3223BF1…43799A`；准确生产源 `build/fx-fast-20261102/src`（自production-combo-v4冻结派生）。新增：瞬态特效中心点视野快速路径，`fx_vision_quality=0`默认（1=v0.33.15逐特效遮罩原画质）。四轮A/B整帧-3.2%~-9.3%、RV-34%~-64%、固定108ms尖峰清除；跨边界特效失去羽化渐变（配置可回退）。回退备份`build/backups/before-fx-fast-20261102-002600`。

- 前一安装 **v0.33.15-combo-v4**，47,534B，SHA256 `AEA30314…9AA557`；准确生产源 `build/mask-budget-output/production-combo-v4/src`。新增：单位渐入修复+FOV兜底90帧。移动-4.1%/RV-23%；固定RV-40%（vs v0.33.14）。累计D56→v0.33.15：移动约-20%/固定约-15%。motionstep=4.0。后续测试默认关闭LightAndDarknessMod。


- D32阶梯与性能版已合并部署76314B81…AF5C46B7：新组合299项功能通过，8组每组500错误黑空气像素归零；墙材质和修正区外严格不变。正式路径启动通过，测试窗口已交回RConnect，无待跑RV实例。

- D31 v0.32.2 DECCA3E0…C4A0B10CA为本次合并基线与回退备份，六项性能优化在D32完整保留。原平均更新加绘制减少5.6%–14.2%是D31相对D29的实测，不是本次新增收益，classic残余长帧仍在。

- D29旧基线2E7150CF…8907A10已由D31替代并留作本次单模组回退。D29既有336项与16组原生雾层差0是历史证据；当前无本轮RV测试实例，窗口已归还RConnect。

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

- **D61 v0.33.13-combo-v2 已部署**（2026-10-31 16:48:52，47,326B，`3F6E6072…6D96D`）：motionstep 4.0 + getBounds 缓存。移动较v0.33.12再-6.6%、RV-22%；固定无回退；与off差距4.39ms。官方ModLoader smoke通过。停点=玩家重启后实际体验；异常回滚用`before-combo-v2-20261031-164852`。后续测试默认关闭LightAndDarknessMod。

- **D60 v0.33.12-combo 已部署**（2026-10-31 15:59:52，47,195B，`26456B67…46FB255`）：墙面输入门控、四角射线复用、P1清理、`motionstep=2.5`（可改0.25）。active A/B固定-9.9%、移动-9.5%，RV 1.79/6.19ms；官方ModLoader smoke通过。**用户2026-10-31接受视觉损失**；后续性能测试默认关闭LightAndDarknessMod（mask-budget/run.py默认排除，`--allow-lightanddarkness`可恢复）。停点=玩家重启后实际体验；异常时用`build/backups/before-combo-20261031-155952`回滚。下方D59及更早为历史。

- D59方案与P0已完成，正式仍D56。P0用active 1280×720可见窗口通道绕过此前AIR启动阻塞，固定/移动各16窗六类归因：移动RV 8.20ms vs 固定3.72ms；仅unit body mask在固定/移动4/4窗方向一致（约-3.4ms），Part数量最多但两窗方向不一致，撤罩不降RV AS3、主要变化在绘制后段。移动态profile：updateWallSurface 2.73ms/帧、fillFogCache约2.03ms/帧平均、applyWorldVisuals 1.85、refreshMask 0.85；P2.1节流上限<0.5ms，不满足明显收益条件，P2改为先做像素等价的updateWallSurface增量/复用，其次fillFogCache脏区。未实现/未部署，下方历史停点保留。

- D58已结束，正式仍D56；拆分分配、帧率校准、小数位移及支持区缓存的证据/否决理由见顶部报告。没有合格部署候选。后续只选独立变量验证，不把少扫描等同整帧提升。

- D57已结束并释放全部测试登记，正式仍D56。下一步定位原生更新/绘制后等待的具体长帧触发，暂不复用被否决候选。独立生产源与authority开发线继续隔离；下方保留历史停点。

- D56已部署并结束本轮测试；用户保存重启生效。下一步测密集敌人原生战斗的剩余长帧，不把本轮7%–12%外推所有场景。生产私有源与开发authority线分开，四项外部WIP保留；下方是历史停点。

- D55：本轮实验已结束，持续扫射问题仍未解决。保存的identity原生像素反例是后续检查入口；stable-v4整帧未获益，不要打包或部署。真实入口/武器/最大化条件已明确，无需再问；下方历史停点保留。

- D54：正式最大化窗口持续射击问题仍未解决；无需再问启动入口/武器/是否持续/窗口状态。所有本轮测试已结束，勿安装忽略目录production的未采用v0.33.11。优先区分同输入绘制成本，保留原生开枪实测作验收；下方是历史停点。

- D52：用户已恢复独立性能测试，旧暂停不再约束后续；32窗/6688间隔已完整核对。D50 all、D51 v2功能证据保留，但本轮无稳定整帧收益，未合并/部署，不再凭局部步骤减少推进。工具build/candidate-comparison，准确性能字节已冻存；comparison-02/03为启动前预检失败，01/04是有效样本。正式仍D44生产源，无authority。当前无RV实例或排队。整体卡顿未解决；下一步应先用可检验假设区分完整帧剩余的原生/绘制/调度开销，不继续堆未证实的微优化。下方均为历史停点。

- D51与D50均功能通过、性能待定，未合并或部署。用户保留试玩、只做代码和画面检查的选择继续有效；两个输出目录均有PERFORMANCE-PAUSED.json。D51准确候选build/ray-clearance-output/candidate-v2/src，首稿未测试即因行宽改变风险淘汰。rays-01为夹具中断不对称失败，rays-02及native-large-01已结束且严格通过。没有可采用的D51时间数据；恢复独立计时后先核对环境/组合，再用无测试计数的生产源对D44做完整战斗复验。目标未完成。下方为历史停点。

- D50：raw/all均待判定，未部署；用户明确保留试玩、只做代码和画面检查，独立计时暂停标志build/classic-inputs-output/PERFORMANCE-PAUSED.json。不要重跑已结束all-plan或覆盖all-native-01；all-native-functional-02只做像素，不可用于计时。四尺寸转换测试已通过，新路径仅小房间且主要用于非默认亮度。待用户明确恢复独立性能测试后，重新核对试玩/登记/包组合，在新目录测all并复验。正式准确源仍D44；目标未完成。下方为历史停点。

- D49已结束，无RV测试占用；guard无收益不采用。基线仍准确D44。下一步先核对classicLogicRegion的重复raw/visibility/wall插值：私有工作图可扩大预计算，但fogCache只能按旧查询确切范围发布，避免D40显示副作用；current另看fillFogCache。D49profile含计时插桩，仅定位。CS请求后续窗口，已停止追加游戏，归档等待既有测试。下方为历史停点。

- D48已结束，无RV游戏实例/排队；所有共享场候选不采用，准确正式源仍D44。新方向：ensureFog重复写scrollRect/colorTransform/blendMode和RVWallSurface重复挂air/base mask及setChildIndex；只是源码发现，性能原因未证实。下一轮从D44独立验证同值设置跳过，保留第三方状态变化恢复和实际画面。D48原图/错误/受干扰计时均保留，不重跑旧目录。下方为历史停点。

- D47已结束，没有RV运行/排队；identity不采用，安装仍D44。原生包装已确认RV额外开销主要在自身与尚未完全归因的剩余区间。下一步从准确D44源评估相邻动画共用模糊视野场；局部裁切/房间边缘/宽滤镜/cache语义未证明等价前不推进生产。不要重复D45/D46/D47已否定的微优化。下方为历史停点。

- D46已结束，当前无RV测试或队列，carry不采用，安装仍D44。下一步区分完整帧中RV调用以外的成本，并量化动态遮罩绘制/分配；集中清理已有反证，不重复D45/D46失败候选。保持画质和刷新率。下方均为历史停点。

- D45已结束，三候选不采用，当前没有RV测试或队列。下一步基于D44准确源验证集中释放与长帧的关联，再决定是否分帧释放；不降低画质/刷新率，不重跑覆盖D45已结束目录。目标尚未解决。下方为历史停点。

- D42已完成验证、部署及收尾，当前无待跑RV实例；以下均为历史停点，不自动重跑。后续反馈以D42准确生产源为基线，不能混入D40候选或authority。

- D40已结束并保留候选，不自动重跑/部署；正式仍D39。后续针对原生跑动的非RV长停顿作低开销归因，详见顶部报告；不可把局部CPU下降当整体成功。

- D39已部署并完成归档；测试退出。已减少缓存边界重建开销，剩余偶发长帧需另行针对驱动、宿主计算或绘制取证；不使用旧EXIT_FRAME分段归因。

- D38实现、验证、部署已完成；全部本轮测试实例退出。最终candidate-04合01+03，02无稳定收益已淘汰；同输入开销继续降低，仍不承诺所有战斗达到原版。exact-01-parent为继承工具错误，修正后另名复验，不重跑覆盖历史。authority仍独立未发布。


- 阶梯最小修复已冻结：src/RVWallSurface.as仅增加半高格顶部空气条件；准确生产源build/stair-shadow-output/candidate/src。统一发布应合入最新D31生产源，不用含authority的HEAD整包；无待跑阶梯AIR。

- D32部署及收尾已完成，准确源和包位于build/stair-shadow-output/merged-v0323/candidate，回执与日志在state/deployment-v0323。RConnect已收到新安装指纹，后续联机组合应使用76314B；不要重跑冻结部署或旧回退覆盖后续工作。

- D31最终补测报告已提交fc06aed；全局台账现已追加最终性能与部署索引，旧待测行保留为历史。此前审批服务容量失败的补记停点解除，无需重跑测试。

- D31 final-large-trial已完成并归档：PID60112退出0、test.xml删除。16次环境采样可用内存6.093–8.113GiB，未观察到其它AIR/Java，不能排除所有后台负载。32组final-large-verify已成功；profile/small/live仍取消。本轮已交回窗口，没有待跑的AIR；禁止覆盖冻结证据。

- D29历史准确生产源与字节在build/wall-performance-output/candidate；当前D31在build/frame-performance-output/production。禁止用含authority的HEAD整包部署，禁止重建覆盖冻结候选。D28旧候选/实验保留。

- D27已按本对话“部署”指令替换release，精确对应 `build/wall-options-output/candidate/RealisticVisionMod.swf`；回执 `state/deployment-v0311-2026-10-15.md`，部署日志 `state/deployment-v0311/`。工具 `build/wall-options/README.md`；画面实证 `knowledge/experiments/wall-options-v0311-20261015/`。对照页标记已部署，历史开发报告保持原验收时点；浏览器交互未验。
- 候选来源固定为v0.30.5-scene基础快照，并叠加本轮已正式安装的改键源码（主文件83F27414…BD3F58C8，另固定RVKeybinds与语言目录）；源码位于本轮installed-keys/src，不自动跟随外部生成目录。原完整候选不含新改键，不能再用；新的D27包保留改键且不含authority WIP。head-check仍不是部署包。

- 共享探索接口：src/RVExplorationCarrier.as 发布 active/capture/merge，独立记忆按 Location 实例隔离；子格/瓦片/墙光仅参与记忆显示，不写原版字段或本地 FOV/currentSight。未安装 RConnect 时原功能照常。契约 design/shared-exploration-api.md；验证 knowledge/experiments/2026-09-20-shared-exploration-api.md。
- 历史共享探索候选 build/shared-exploration/RealisticVisionMod.swf；独立回归 build/shared-exploration/run_checks.py。RConnect侧联测日志在其M31报告/JSON。当前正式版已叠加v0.30.1提示修改，不能再拿旧共享探索候选覆盖。
- 本轮候选开发、两档实际绘图、回归和测试编译完成。说明：knowledge/experiments/2026-09-20-current-soft-candidate.md；对照页 current-soft-v0290/comparison.html，可逐帧切换适中/宽档。已按用户要求部署适中档。部署回执2026-09-20-v0290-deployment.md，证据deployment-v0290/。正式路径独立实例确认新版标记、MSW设置注册与17条心跳至2881；测试PID51952已关闭、描述符已删除，用户实例未操作。
- 浏览器URL策略拒绝自动打开本地HTML，未绕过。脚本语法已检查、原始PNG已目检，但浏览器交互未实测；给用户文件链接即可，不宣称页面已打开。
- 原调查 ef82898/37f3284 与讨论534865e保留；当前motion-tests旧变体固定读取37c25ba，新soft-*读取当前源码。不要让历史实验改用新源码，或覆盖current-motion-20260920证据。

## 5. 已知问题与边界

- D35解决自定义亮度的重复计算回退；平均改善不能当作长帧全解。current默认大图最大83→125ms，射击整帧峰值259ms而RV更新最大26ms；具体慢帧与全组合长期联机尚未完全归因。

- D33仍有偶发长帧：配对classic最大135→328ms（其中绘图254ms），原生current整帧最大95→138ms，而RV更新最大33→30ms。部分开销改善不等于完整FPS达标，全模组/联机密集混战未验证。


- D30常亮ON隔离参考仍有34–70px的1/255差异；隐藏容器会改变既有绘图取整，不能将其直接判作泄漏。目标负1逐点原因未尽证；严格失败保留，用户精确存档与全模组组合未在本轮覆盖。

- D31最终四组平均更新加绘制分别38.867→34.683、59.542→51.658、97.792→83.900、109.208→103.100ms；classic最大值243→266ms，长帧原因未定位。D32已完成阶梯组合验证；本次未追加性能、玩家精确存档或长期密集联机结论。

- D29最终同进程240帧：关闭常亮classic18.73→18.05ms、current20.89→19.72ms；开启32.21→30.17ms、35.44→32.28ms。P95和峰值本轮均下降，开启仍有75–96ms长帧；不能换算完整战斗FPS。真实大图/玩家存档与密集联机未验。

- D27最终同进程三组轮换回放：classic基线/关闭/开启均值8.17/17.92/20.58ms，P95 12/25/29ms；current 9.31/20.68/23.04ms，P95 11/24/29ms。平均额外约9.8～13.7ms，最大53ms；不是完整战斗FPS。整张最终输出分支无收益已撤回，采用局部内容比较缓存；大型连续场景、全模组负载与用户存档未验。

- 候选仍为5px逻辑采样及四角快速分类，不是连续多边形可见性重写。未覆盖任意窄缝/全部缩放相位、用户精确存档、长时间战斗和六模组共同负载。单位掩膜零泄漏断言针对采样点，不是任意亚像素几何证明。
- 一次67ms峰值未定位；宽/适中间约零点几毫秒差视为噪声，不据此选档。完整训练房视距3000/10000，与普通房不同。
- classic既有40px粗格掠角（一个方向与连续切线差21px）、薄墙可见侧约20px渐变仍保留。旧 F12 app:/ 保存错误已由 ModSettings 迁移修复，配置写入本端应用存储。SATS记忆扫描/抓暗敌瞬间报警等旧限制保留。
- 同尺寸resetRoom清黑共用三图、fogBlurPending及原版墙角相位等旧修复保留；新currentSightData随房间清空重建。

## 6. 下一步

- 最新接续（2026-11-01）：回到不加载LightAndDarkness的RV本体开火/移动/交战对照，比较关闭/current/classic及长帧分布。上轮照明调查保留为独立研究，不能据其改善宣称RV提速；以下旧版本行动仅作历史。
- 当前D42 v0.33.8需用户正常保存并重启加载。原生特效与狮鹫泄露已修复；后续长帧仍需实测归因。下方旧版本行动仅留历史，不据此回退当前安装。

- 用户正常保存并重启加载v0.33.2；若仍反馈高速/混战停顿，按实际保存的设置和完整组合慢帧采样，不仅测默认值或按平均值优化。D35安全回退基线为D32，路径见顶部报告。


- 阶梯修复已交获授权的统一发布会话合入D31并做组合验证；保留功能与严格图像诊断的不同结论，不直接部署325A旧生产线整包。

- D32合并、验证及部署完成；用户保存并正常重启生效。后续联机组合由RConnect以最新安装字节继续，保留authority工作，不复用已交回窗口。

1. D32 v0.32.3已按本轮授权部署，用户保存并正常重启生效，无需重复部署。
2. 本次备份为build/backups/before-stair-merge-20261019-152652-78efec/RealisticVisionMod.before.swf，原DECCA3E0…C4A0B10CA。仅当安装仍为76314B81…AF5C46B7时可按deployment-v0323-2026-10-19.md单独恢复；不覆盖后续组合。
3. 后续优先核对RConnect隔离组合与真实大场景/战斗；本轮单模组实测不代替联机门槛。保留D29严格等价于D28的视觉目标、D22记录隔离、D24/D25地板与念力守卫，不减少刷新。
4. 用户游戏不自动关闭；部署后需保存并正常重启。此前回滚点与stash保留。

## 7. 深入了解与复验

- D35入口：knowledge/experiments/2026-10-21-settings-performance-recovery.md、build/regression-recovery/README.md。1731检查、8战斗窗、原始性能、失败与部署证据均保留；KB-000056用于测量方法；本轮非默认参数回退与局部缓存经验已回流KB-000106修订1。

- D31入口：knowledge/experiments/2026-10-19-frame-performance.md、build/frame-performance/README.md；准确生产源与包位于build/frame-performance-output/production，证据归档frame-performance-v0322-20261019。禁止用含authority与阶梯WIP的HEAD整包覆盖。

- D29最新入口：knowledge/experiments/2026-10-16-wall-performance.md、state/deployment-v0321-2026-10-16.md、build/wall-performance/README.md；KB-000102记录本轮精确调用护栏经验。

- 本轮入口：`knowledge/experiments/2026-10-15-wall-bright-option.md`、D27、`build/wall-options/README.md`；最终指纹/图像/日志在wall-options-v0311-20261015。D26旧记录仍留原址。SDK在本区 `mods/Sandevistan/build/tools/`，仅只读使用。

- 历史D32发布：state/deployment-v0323-2026-10-19.md与state/deployment-v0323/；D31回执保留历史。准确安装76314B81…AF5C46B7，正式启动和299项组合功能通过。工具build/stair-merge/，证据knowledge/experiments/stair-performance-v0323-20261019/。
- 新候选：2026-09-20-current-soft-candidate.md / current-soft-v0290/ / D25。新SoftHarness.as与motion-tests/README.md列完整命令，--checks专项、soft-medium/soft-wide、run-game和bench-game --soft。
- 原调查：2026-09-20-current-motion-investigation.md / current-motion-20260920/。证实三帧+次帧约10Hz、只提频会饿死显示、max硬钳制台阶、角点误写亮点。全图2.5px成本高，四点积分收益小。
- 既有classic修复：2026-09-19-classic-wall-seam-fix.md / classic-seams-v0282/ / D24；部署2026-09-19-v0282-deployment.md。D22/D23旧报告与念力交接见journal。
- 构建只用build/build_test.bat（旧build.bat/build.sh会写release）。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk，Java D:/Program Files/Adobe Animate 2024/jre，FFDec同tools/ffdec。
- AIR使用独立app id和资源副本，禁止写真实pfe存储；性能试验顺序，优化编译debug=false/optimize=true并保留trace。完整游戏共享输出目录的脚本也顺序，限时150秒并核对成功退出。普通沙箱AIR/FFDec可能初始化失败，走工具审核，不凭空日志认定算法失败。
- Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。知识库KB-000056已有性能比较方法，不重复记卡。

缓存验证工具的旧算法已固定到提交d634b5769f9af1949d2114b4643d37d97af8f7b6及规范化源码SHA f2e1b49c…，避免后续HEAD变化变成新算法自比。执行实际取源/指纹检查，并与已验证02中的原始源码逐字一致；本次仅修未来构建工具，已部署SWF与02证据不变。
