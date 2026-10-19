# D30 阶梯阴影修复

候选从已部署 D29 冻结生产源派生，仅修改 `contourRole` 对半高格顶部空气的判定和版本号。`inputs.json` 固定六份基础源；不把 HEAD 的 authority 或并行性能开发带入候选。

在 RealisticVision 目录使用 Codex runtime Python，命令入口：

```text
python -B -X utf8 build/stair-shadow/run.py prepare
python -B -X utf8 build/stair-shadow/run.py checks --name checks-final
python -B -X utf8 build/stair-shadow/run.py regression
python -B -X utf8 build/stair-shadow/run.py compile-game --name reproduction
python -B -X utf8 build/stair-shadow/run.py run-game --name reproduction
python -B -X utf8 build/stair-shadow/run.py build
python -B -X utf8 build/stair-shadow/production.py
```

已冻结的检查/截图不得覆盖，复验须给新输出目录或复制工具后改变输出根。只用唯一 AIR ID、隐藏窗口和独立存储；玩家游戏保持原状。构建和测试不写 release。

`checks-red` 是修复前的真实失败证据（28通过、12失败）；`checks-green` 为最初同输入绿灯（40通过）；最终专项增加视口、亚像素缩放、破坏检查。`regression` 保留 D29 的严格差分，但将原动态测试的半高格改为完整墙，用于断言本次修复影响范围外逐像素不变；半高格正确性由专项独立断言，而非强求错误像素一致。

原生夹具使用 `Tile.dec("C," / "C;" / "C:" / "C,F" / "C;F" / "C:F")`。后缀会重设 opac，因此两种实际游戏状态都必须覆盖。清空旧墙时显式清 opac；`dec(" ")` 本身不会清它。初次 `diagnostic` 金属夹具第二组受此污染，不能作为修复证据；保留其记录以解释排查过程。

`reproduction` 记录原版 visLight、禁用 helper 的原雾、旧版与候选，两模式、常亮开关及移动后的亮/暗位置。图像审计仅允许 alpha=0 的半高实体上方发生变化。运行耗时不是性能基准，本轮不报告 FPS 收益。

`reproduction-isolation` 在相同输入下追加保持base.mask和显示层次、仅隐藏airPixels/wallPixels的图像。它用来区分修补层覆盖与带mask/不带mask的绘图差异；最初无mask参考严格比较的18通过/8失败必须保留，不能改为容差通过。准备并运行新名字的原生夹具后，执行：

```text
python -B -X utf8 build/stair-review/analyze.py build/stair-shadow-output/reproduction-isolation
python -B -X utf8 build/stair-shadow/evidence.py
python -B -X utf8 build/stair-shadow/cleanup.py
```

独立审计工具退出码仍按无mask参考的严格结果给出；需分别查看isolation_passed/failed及修正区外、材质像素。实际隔离结果为OFF四组零差异、ON四组仍有1/255差异。证据打包要求区外和材质零变化、错误黑条消失、OFF隔离零差异，并校验输入图像指纹；ON失败原样保留为STRICT_ON_ISOLATION_NOT_MET，不等于放宽容差后的全绿验收。

清理脚本仅在测试描述符已移除且素材与保留来源SHA256一致后删除本轮重复运行素材，记录`runtime-cleanup.json`。候选、源码、图像、日志及恢复来源继续保留。再次运行原生夹具前须用新的输出目录执行compile-game恢复素材；不要覆盖已冻结证据。
