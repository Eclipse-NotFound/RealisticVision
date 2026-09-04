# RealisticVision 架构参考（关键机制 / 配置 / 常用操作）

> 2026-08-27 自 state/HANDOFF.md §1/§3/§4/§7 迁入（原文在 git 历史）。
> 反映 v0.24.x 时点；现行状态见 state/MEMORY.md，版本流水见 state/journal.md。

## 注入与构建

- 游戏 pfe.swf（SWF41）文档类 MainFE 已被补丁加载模组（`app:/mods/<M>/release/<M>Mod.swf`，调文档类**静态** `init(main)`）。**改动游戏文件前必须反编译核对线上加载器清单**（2026-08-17 时为 5 个：Sandevistan/RConnect/RealisticVision/MoreSkills&Weapons/TDFC），任何 pfe.swf 修改需多方协调；历史合并备份 `pfe_1.02_before_rvision_merge_20260815.swf`。
- 构建：flexsdk 4.16.1 不接受裸 SWF 作库 → `build/stubs/` 手写游戏 API 存根 → acompc 打包 GameStubs.swc → amxmlc `-swf-version=32 -external-library-path+=GameStubs.swc`。运行时 fe.* 经父 ApplicationDomain 解析到游戏真实类。**存根勿随 release 发布**。
- **sealed 类陷阱**：对密封类（Box/Bullet/Weapon…）动态 bracket 访问不存在成员抛 #1069；对动态对象写属性在运行时对 sealed 类抛 #1056（历史事故：掩膜 Shape 的 mouseEnabled 赋值崩溃导致联机宿主卡死）。

## 渲染管线（三模式，v0.17.4 定型）

自建雾层（Sprite+Bitmap）插在 `grafon.visLight` 之后同一层级：

- **vanilla（透传）**：完全不碰 visi/visLight/lightBmp，游戏原样渲染（原版半格错位掩膜/硬边/已探索常亮）；进入透传瞬间调 `grafon.setLight()` 恢复掩膜。
- **classic（仿原版，v7 = 游戏值优先 + 记忆化渐变；v0.26.0 恢复位移架构）**：`visLight.visible=false`，雾层 1px/瓦片、smoothing 双线性、**原版位移显示**（x=-半格、y=-1 格半，写 (tx, ty+1) 行，位图 (spaceX+1)×(spaceY+2) 富余行列保持黑——同原版 lightBmp 边缘恒黑）；规则 `a=游戏值(1-visi)×255` + memCur 记忆化渐变（0.1/帧；v0.25.5 起目标统一 dimA）；**v0.26.0 起墙与地板同管线**：游戏 visi 场经位移马赛克自然产生原版墙内明暗（贴亮区墙行亮、结构内部黑、40px 线性过渡坡——原版基准截图剖面实测），墙专用层与协调值全部退役；**不变量：只暗化不亮化**；门景 doorBoost 写 visi 生效；变化才写像素（站立零写入）。
- **current（平滑阴影）**：`visLight.visible=false`，`tile.visi` 写二元（探索过=1/未探索=0，D15），自建雾层全权接管：8×8 子格 raycast 线状阴影 + 渐变（blur 2.5,q3 ≈20px）+ 单侧钳制 max(raw,blurred) + 子格"曾见"历史边界（5px）+ 门景 doordim；可见墙四分格映射（TL=自身/TR=东/BL=南/BR=东南 visi）。

- 游戏逻辑可见性：current 模式 visi≥0.8 才算可见（checkPort）；classic/vanilla 走原版语义。
- 三态数组：fov[]（VISIBLE/DIM/NONE，含透光门/水）、explored[]（长期）、visCur[]（淡入）、seenSub[]（子格级曾见历史）。
- current 性能（v0.17.1 + v0.24.x）：fogCache 缓存 + 每瓦片 4 角采样分类（全暗 fillRect / 全亮免 raycast / 混合才完整 8×8 raycast）；fov 重算最小间隔 3 帧（墙破坏不受限）；模糊+钳制拆帧；站立零 raycast。
- 子格亮度 = max(lit×距离衰减, 记忆暗色 0.35)；fogRaw→blur→fogBmp（source≠dest，勿自应用 applyFilter）。

## 敌人显示（三态）

- 每帧按敌人包围盒瓦片与 fov 交集分三态（0 全隐 / 1 全显 / 2 部分），判定按 **unitBBox 外扩 1 瓦片**（单瓦片敌人如炮塔跨边界进部分可见态，不再二分）。
- 部分可见：**矢量 Shape 掩膜 + 模糊位图填充 + cacheAsBitmap**（v0.24.2 Shape 回归 + v0.24.4 补 cache——**alpha 掩膜的硬性要求：掩膜与被掩膜对象都必须 cacheAsBitmap=true**）；子格 5px（MASK_SUB=8 与雾层一致）；模糊按模式对齐雾层边界宽度（classic BlurFilter(6,6,2)≈40px / current (4,4,3)≈32px；config：maskblur_classic/maskblur_current）。
- 生命周期：先挂 mask 后填内容、clearMask 移出图层并 dispose、死亡清扫兜底删除 unitVis 条目（v0.5 教训）；hpbar 独立掩膜（copyFrom）。
- 子格 castRay 返回 -1（墙瓦片）回退 fov 判定（墙炮塔掩膜不空）；尸体（sost==4）保留；友好跳过；敌方武器按 owner 实时状态隐藏/裁剪；狮鹫手臂（UnitMerc.arm，internal）用 visObjs[2] 显示树扫描隐藏。

## 念力

- Q/右键输入拦截（复刻游戏抓取目标选择，不可见敌人 stopImmediatePropagation）；帧尾 backstop（不可见敌人 teleObj → dropTeleObj）；拖出视野 3 秒宽限（telegrace；v0.6.3 起被抓敌人无豁免）。

## 其他机制

- FOV 触发：玩家位移>0.5px / 结构哈希变化（opac+phis）/ 15 帧兜底。
- 安全基地：`loc.base` 或 `base_rooms=` 配置 → normalMode（恢复原版光照）。
- 看门狗：onFrame try/catch，连续 30 帧错误自动禁用（写回 config）。
- 调试：F10 面板（三态计数/念力倒计时/帧耗时/mode）、F11 总开关、F12 模式、屏幕提示。

## 配置（release/config.txt）

```text
enabled=1       总开关（F11）
mode=current    vanilla / classic / current（F12 轮换）
dim=0.35        记忆区暗度
doordim=0.5     透光门/水后视野亮度（门景）
litmin=0.6      可见阈值
fadestep=0.1    淡入步长
telegrace=3     念力拖敌出视野宽限（秒）
base_rooms=     额外安全基地房间 id（逗号分隔）
maskblur_classic / maskblur_current   敌人掩膜模糊宽度（0=硬边回退）
debug=0
autotest=0      自动化验证埋点（默认关；开=每 300 帧 auto st 统计 + 事件日志，
                见 knowledge/experiments/2026-08-27-autotest-verification.md）
```

## 常用操作

```bash
# 构建（本机实测路径，2026-08-27：flexsdk 在 Sandevistan 仓库工具目录，java 用 Animate 自带 JRE）
cd mods/RealisticVision/build && cmd //c build_test.bat   # 测试版 → build\RealisticVisionMod_test.swf
# 或 bash build.sh（脚本内旧 SDK 路径需先改，产物直接覆盖 release\）
# 验证产物仅含模组类（期望只输出 RealisticVisionMod；ffdec exe 启动器找不到 JRE，必须 java -jar）
"/d/Program Files/Adobe Animate 2024/jre/bin/java.exe" -jar \
  "/d/RemainsMod/mods/Sandevistan/build/tools/ffdec/ffdec.jar" -dumpAS3 <swf>
# 检查线上 pfe.swf 加载器（其他开发者是否改过）
java -jar <ffdec>/ffdec.jar -selectclass MainFE -export script /tmp/x <游戏根>/pfe.swf
grep -oE "app:/mods/[A-Za-z]+/release/[A-Za-z]+Mod.swf" /tmp/x/scripts/MainFE.as
```
