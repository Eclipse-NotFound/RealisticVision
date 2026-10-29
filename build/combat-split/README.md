# D58：拆分开销与支持区结果复用

本轮全部10个实验已结束，没有采用/部署新候选，正式保持D56。
support虽然通过1446项画面检查，但09/10反向完整战斗的classic均回退，
current局部CPU也不稳定；不得把本目录的候选SWF放入release。

基线为正式 D56 v0.33.11-effect-clip，准确生产源由上一轮冻结源复制。
不从含 authority 的开发 HEAD 打包。报告和最终采用状态见
`../../knowledge/experiments/2026-10-29-combat-split.md`。

所有输出写入忽略目录 `../combat-split-output/`，名称必须新建。
`prepare*.py` 是已经执行的历史生成器，不要覆盖既有输出或现行驱动。

`run.py <新名字> --candidate --source=support --pair --sweep --solo
--private-visible --native-screen --full --plain --both --native-timing`
使用原生菜单退出、玩家轻机枪和六个狮鹫 SMG，实际最大化尺寸，独立
桌面可见、静音、唯一 AIR ID 和共享测试登记。solo 仅移除随机原生单位，
不是零敌人。每窗预热90、采样180，末帧不参与完整间隔。
`--reverse --reuse-from=<已完成轮次>` 先核对源码，再复用准确 SWF 和依赖。

不加 `--pair` 时三路对照 normal/aux/vector；01有并行试玩，不作性能排名。
`--rate-calibration --short` 仅在自有实例临时改变 stage 帧率，不能发布。
02没有支持固定33ms等待是主要瓶颈；剩余区间不等于GPU独占耗时。

`fractional_check.py` 是连续独立显示树的严格 ARGB 对照。
03/04 小数位移裁切通过，但05固定视野失败于 f482，06分对象复现；
此候选不安全，未合并。普通 LMG 不主动震镜头，不能当作扫射根因。

`--source=support --identity-blit --integer --opaque --fractional-stress
--support-cache` 是07动态输入验证；再加 `--steady-field --keep-masks`
是08持续缓存、全亮/全暗/混合和两模式切换验证。两组各723项通过。
缓存只保存固定支持区的透明性，m2e实际改写前失效；保留每个对象的
实时滤镜检查。完整帧计时不增加support命中计数，窗口结束后只记录
含有效缓存的栅格数。图像测试中的扫描次数下降不是帧率改善结论。

候选均独立从D56派生：aux、vector、fractional、support互不混合。
玩家存档种子和 Local Store 不入库；原始证据归档采用内容去重和gzip，
实际采用/部署以报告及部署回执为准，不凭某次图像通过安装。
