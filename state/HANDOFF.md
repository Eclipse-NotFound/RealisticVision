# RealisticVision —— 交接文档（HANDOFF）

> 最后更新：2026-08-18（v0.22）
> 用途：项目转移到新对话时，新 agent 先读本文 + `AGENT_SCOPE.md` + `state/current-status.md`。

## 0. 项目一句话

《Fallout Equestria: REMAINS》（1.02，Flash/AIR）的**视野系统模组**：三态视野
（未探索全黑 / 视野内亮 / 记忆区暗色隐藏敌人），含破坏墙、透光门、敌人部分
可见裁剪、念力规则（隔墙抓物品可、抓敌人不可）、多渲染模式切换。

## 1. 当前状态摘要（2026-08-17）

- 版本 **v0.22**，`release/RealisticVisionMod.swf` 已部署（Loader 子域注入，
  由补丁 MainFE 加载）。游戏本体文件**未改动**。
- **污染排查结论（2026-08-18，对照桌面干净备份）**：游戏文件层零污染——
  Location/Tile/Grafon/World 反编译逐行零差异、Rooms 数据/资源/文本一致；
  pfe.swf 差异仅 6 mod 加载器合并（含新出现的 RandomRooms，只追加测试地形）。
  真实污染源为运行时状态：current 模式曾写 t_visi 二元 → **v0.21.1 起只写
  visi、保留游戏 t_visi**（切模式后游戏 10 帧自愈恢复，不再污染原版渲染）。
- 敌人显示（v0.21 重构）：
  - 三态判定（0 全隐/1 全显/2 部分）按 **unitBBox 外扩 1 瓦片**（单瓦片
    敌人如炮塔 phis 38×38 跨边界进入部分可见态，不再二分）；
  - 部分可见用**位图掩膜**（子格 raycast → BitmapData → 放大 smoothing 双
    线性圆滑边界，无硬台阶颗粒）；生命周期：先挂 mask 后填内容、clearMask
    移出图层并 dispose、死亡清扫兜底（v0.5 教训）；hpbar 独立 BitmapData；
  - **子格 castRay 返回 -1（墙瓦片）回退 fov 判定**（墙炮塔掩膜不空）；
  - 尸体（sost==4）保留；友好跳过；敌方武器按 owner 实时状态隐藏/裁剪；
    狮鹫手臂（UnitMerc.arm）用 visObjs[2] 显示树扫描隐藏。
- 三档渲染模式（`config.txt` 的 `mode`，F12 轮换，PipBuck 选项页面板 + F10
  面板 + F12 屏幕提示显示模式名）：
  - `vanilla`（原版）：**纯透传**——模组完全不碰 visi/visLight/lightBmp，
    游戏原样渲染（半格错位掩膜/硬边/已探索常亮）；
  - `classic`（仿原版）：**v7 = 游戏值优先 + 记忆化渐变**。雾层结构复刻
    原版 lightBmp：1px/瓦片 `(spaceX+1)×(spaceY+2)`（富余 1 列 2 行，同
    原版 49×28）、smoothing=true 双线性、半格错位 x=-20/y=-60 写 y+1 行、
    写入范围照抄原版（列 1..spaceX-1、行 2..spaceY）、每帧读游戏 tile.visi。
    规则：`a=游戏值(1-visi)×255` + **memCur 记忆化进度**（视野外渐增/视野内
    渐减，0.1/帧，a = 游戏值 + cur×(max(游戏值,dimA)−游戏值)）——移动时记忆
    边界平滑渐变；**墙恒黑 255（v0.20.1：不读 visi——current 模式写的 visi=1
    残留会让墙亮块并错位渗成墙边亮带）**，墙东/南半渗入邻瓦亮值（原版墙亮
    面）；retDark 纯原版消退。**不变量：只暗化不亮化**（含中途态）。门景
    doorBoost 写 visi 生效；变化才写像素（lastA 缓存，站立零写入）；
  - `current`（平滑阴影）：8×8 子格 raycast 线状阴影 + 渐变（blur 2.5,quality 3
    ≈20px）+ 单侧钳制 + 子格"曾见"历史边界（5px）+ 门景 doordim；**可见墙
    四分格映射**（v0.17.4 复刻原版墙亮，无波痕）；性能：fogCache 缓存 +
    4 角采样分类，站立零 raycast。
- 敌人掩膜子格 5px（MASK_SUB=8，与雾层一致）。
- **验证状态**：全部功能未经用户最终确认（用户此前确认过的：v0.4.1 敌人
  "明处显示暗处不显示"语义、v0.10 渐变可见性、classic 最接近原版观感）。
  每次修改后请用户在游戏内实测（F10 面板、F12 模式、PipBuck 面板）。

## 2. 目录结构

```text
mods/RealisticVision/
├─ AGENT_SCOPE.md        权限边界（必读；本模组 READ-WRITE，其他区域只读）
├─ README.md             模组说明/构建/部署
├─ src/RealisticVisionMod.as   全部源码（单文件，~2330 行）
├─ build/
│  ├─ build.sh           构建（Git Bash）：stubs SWC + mxmlc
│  ├─ build.bat          （同功能 bat 版，可能有 errorlevel 坑，优先 bash）
│  ├─ stubs/             游戏公共 API 编译期存根（勿随 release 发布）
│  ├─ GameStubs.swc      构建中间产物
│  └─ patched/           MainFE_merged.as + pfe_merged.swf（三方合并补丁，已部署）
├─ release/              RealisticVisionMod.swf + config.txt
├─ design/vision-system.md   架构设计（v0.2 起有修订记录）
├─ decisions/decisions.md    决策记录 D1-D20（D19 教训：平滑来自光源模型而非空间滤波）
├─ state/current-status.md   当前状态（每轮更新）
└─ knowledge/            模组专属发现（光照管线/掩膜错位/念力机制/构建实验）
```

## 3. 关键机制（必须理解的架构）

### 注入与构建
- 游戏 pfe.swf（SWF41）文档类 MainFE 已被补丁加载模组（`app:/mods/<M>/release/<M>Mod.swf`，
  调文档类**静态** `init(main)`）。**2026-08-17 核对：线上 MainFE 现有 5 个
  加载器**——Sandevistan / RConnect / RealisticVision（rvLoader，部署完好）/
  **MoreSkills&Weapons / TDFC**（其他开发者新加，未与我们合并过）。
  **改动游戏文件前必须反编译核对加载器清单，任何 pfe.swf 修改需五方协调**；
  历史合并备份：`pfe_1.02_before_rvision_merge_20260815.swf`（游戏根，仅三方）。
- 构建：flexsdk 4.16.1 不接受裸 SWF 作库 → `build/stubs/` 手写游戏 API 存根 →
  acompc 打包 SWC → amxmlc `-swf-version=32 -external-library-path+=GameStubs.swc`
  编译。运行时 fe.* 经父 ApplicationDomain 解析到游戏真实类。
- **sealed 类陷阱**：对密封类（Box/Bullet/Weapon…）动态 bracket 访问不存在成员
  抛 #1069；对动态对象（`*`/Dictionary 值）写属性在运行时对 sealed 类抛 #1056
  （历史事故：掩膜 Shape 的 mouseEnabled 赋值崩溃导致联机宿主卡死）。

### 渲染管线
- 自建雾层（Sprite+Bitmap）插在 `grafon.visLight` 之后同一层级。**v0.17.1 起
  按模式区分，v0.17.4 最终定型**：
  - **vanilla（透传）**：完全不碰 visi/visLight/lightBmp，游戏原样渲染
    （原版掩膜半格错位/硬边/已探索常亮）；进入透传瞬间调 `grafon.setLight()`
    恢复掩膜；
  - **classic（仿原版，v4 雾场自渲染）**：`visLight.visible=false`（雾场取代
    游戏掩膜），`tile.visi` 交还游戏（原版 lighting()/lighting2() 管理）；
    雾场 = 可见区复刻游戏 visi（`alpha=(1-max(visi,dimF))×255`，40px 原版
    亮度 + 记忆暗色下限 → 光缘环终点 166 与记忆区连续）+ 可见墙四分格映射
    （TL=自身/TR=东/BL=南/BR=东南 visi，原版半格错位墙亮）+ fov==NONE 区
    按 seenSub 曾见历史子格化（5px 边界，光缘/前沿带逐子格 raycast）；
    门景 doordim 由 doorBoost 写 visi 生效；
  - **current（平滑阴影）**：`visLight.visible=false`，`tile.visi` 写**二元**
    （探索过=1/未探索=0，D15），自建雾层全权接管（8×8 子格 raycast + blur
    2.5,quality 3 ≈20px 渐变 + 单侧钳制 max(raw,blurred) + 可见墙四分格
    映射按 br 点亮）。
- 游戏逻辑可见性：current 模式 `tile.visi` 二元（`checkPort` 要求 visi≥0.8）；
  classic/vanilla 走原版语义（游戏 lighting() 自己维护，已探索常亮）。
- 三态：fov[]（VISIBLE/DIM/NONE，逻辑用，含透光门/水）、explored[]（长期）、
  visCur[]（current 淡入）、seenSub[]（子格级"曾见"历史，记忆区↔未探索
  边界 5px 粒度）。
- current 性能（v0.17.1）：最终 alpha 场缓存 fogCache，仅 FOV 重算时更新；
  每瓦片 4 角采样分类——全暗整块 fillRect、全亮免 raycast 只算距离衰减、
  FOV_DIM/明暗混合才完整 8×8 raycast；每帧 copyPixels + blur（站立零 raycast）。
- 子格亮度 = max(lit×距离衰减, 记忆暗色 0.35)；fogRaw→blur→fogBmp
  （source≠dest，勿自应用 applyFilter）。

### 敌人显示
- 每帧按敌人包围盒瓦片与 fov 交集分三态：0 全隐（vis+hpbar 隐藏、prior=0
  杀标签）、1 全显（visDetails 恢复血条）、2 部分（矢量矩形掩膜 Shape，**5px**
  子格 raycast 裁剪，MASK_SUB=8 与雾层一致；掩膜必须移出图层防白块）。
- 尸体（sost==4）保留；友好（fraction==F_PLAYER/npc）跳过；敌方武器按 owner
  实时状态隐藏/裁剪；狮鹫手臂（UnitMerc.arm，internal）用 visObjs[2] 显示树
  扫描隐藏。
- 念力：Q/右键输入拦截（复刻游戏抓取目标选择，不可见敌人 stopImmediatePropagation）；
  帧尾 backstop（不可见敌人 teleObj → dropTeleObj）；拖出视野 3 秒宽限
  （telegrace，期间敌人按视野规则显示——v0.6.3 起被抓敌人无豁免）。

### 其他
- FOV 触发：玩家位移>0.5px / 结构哈希变化（opac+phis，isRelight 被游戏提前
  清零读不到）/ 15 帧兜底。
- 安全基地：`loc.base` 或 `base_rooms=` 配置 → normalMode（恢复原版光照）。
- 看门狗：onFrame try/catch，连续 30 帧错误自动禁用（写回 config）。
- 调试：F10 面板（三态计数/念力倒计时/帧耗时/mode）、F11 总开关、F12 模式、
  屏幕提示、trace（RVision 前缀）。

## 4. 配置（release/config.txt）

```text
enabled=1       总开关（F11）
mode=current    vanilla=原版 / classic=仿原版 / current=平滑阴影（F12 轮换）
dim=0.35        记忆区暗度
doordim=0.5     透光门/水后视野亮度（门景，比记忆区亮）
litmin=0.6      可见阈值
fadestep=0.1    淡入步长
telegrace=3     念力拖敌出视野宽限（秒）
base_rooms=     额外安全基地房间 id（逗号分隔）
debug=0
```

## 5. 已知问题 / 待办

- **验证未完成（v0.21/0.21.1 未实测）**：① 炮塔部分可见/敌人边界无颗粒
  ② **切模式后原版渲染自愈（current→vanilla/classic 后移动几步，无残留
  黑/亮）** ③ 位图掩膜无白块/闪烁 ④ classic 各项（记忆渐变/墙恒黑/无亮边）。
  机制已离线验证，待游戏内实测。
- **敌人掩膜二值限制**：Flash mask 是二值的，5px 子格是锯齿上限（无法软裁剪）；
  若仍嫌锯齿可用位图掩膜方案（历史上有白块生命周期风险，需严格挂载同步）。
- **classic 已知小差异**：模组 fov 光源点/半径测量与原版 lightBmp 略有不同
  （~半格），光缘最外圈 ~12-28px 过渡位置有微小偏移（接受）。
- **current 全亮瓦片近似**：4 角采样判定"全亮"时内部凹形阴影偶发被当全亮
  （模糊掩盖，接受）。
- **classic 光缘衰减步进**：游戏 visi 是 40px 瓦片值，光缘环内衰减呈 40px
  台阶（原版同款）；20px 模糊部分软化，若仍显眼可加大 blur 半径。
- Sats 扫描器把记忆区（visi=1 二元）当可见——原版语义，接受。
- 抓取暗区敌人瞬间 alarma() 已触发（输入层拦截已做，帧尾 backstop 兜底）。

## 6. 跨模组事项（重要）

- **线上加载器（2026-08-17 核对）**：pfe.swf MainFE 现有 5 个模组加载器
  （Sandevistan / RConnect / RealisticVision / MoreSkills&Weapons / TDFC）。
  新会话若发现新模组行为异常（如光照/显示冲突），可先确认对方是否也操作了
  visi/visLight/掩膜；RV 只在 current 模式写 tile.visi（二元），classic/vanilla
  透传。**勿修改其他模组文件**；pfe.swf 改动需五方协调。
- **共享知识库**：已贡献 `knowledge-validation/conflicts/grafon-drawallobjs-callchain.md`
  （结论：setLight 不调用 drawAllObjs，原 fact 文件表述有误——由 Sandevistan
  维护者自行修正，勿直接改其文件）。
- **交叉 bug 已修**：#1056（掩膜 Shape mouseEnabled）——联机开发者（RConnect）
  上报，已修复并反馈；对方"setLight→drawAllObjs"归因不成立（已核实）。
- **hpbar 规则**：血条只在受伤/护甲/精英/首领时显示（游戏 visDetails）——
  修复时用"隐藏时压暗 + 恢复时 visDetails 重算"，勿无条件 hpbar.visible=true
  （历史教训）。
- 其他模组目录不得修改；改动 pfe.swf 前必须检查/合并。

## 7. 常用操作

```bash
# 构建
cd mods/RealisticVision/build && bash build.sh

# 验证产物仅含模组类
ffdec-cli -dumpAS3 release/RealisticVisionMod.swf   # 期望只输出 RealisticVisionMod 0

# 检查线上 pfe.swf 加载器（其他开发者是否改过）
ffdec-cli -selectclass MainFE -export script /tmp/x <游戏根>/pfe.swf
grep -oE "app:/mods/[A-Za-z]+/release/[A-Za-z]+Mod.swf" /tmp/x/scripts/MainFE.as

# 重新生成三方合并补丁
# 以当前线上 pfe.swf 为基础，改 build/patched/MainFE_merged.as（追加/保留加载器），
# ffdec-cli -replace in.swf out.swf MainFE MainFE_merged.as
```

## 8. 权限提醒

- 只改 `mods/RealisticVision/`；shared-knowledge 谨慎写（先搜索、按 README 规则）；
  game-reference/游戏文件只读；其他模组不读不改（除交叉问题已解决的历史）。
- 部署（覆盖游戏文件）需用户明确授权；本轮从未改动游戏本体。
