# D33 运动与战斗性能调查

正式发布以 `motion-performance-output/merged-settings/` 为准，继承 D34 v0.33.0 的设置。早期 `production/` 是 v0.32.4 Object 缓存候选，存在长帧回退且缺少 D34，禁止部署。

## 改动与边界

- 墙体轮廓线性读取 alpha，按格边界读取高度，以整数向量保存完全相同的连续矩形。材质 alpha 或地形高度变化使缓存失效；视口、房间和开关仍按原路径更新。
- classic 四角及所有启用边的修正均为零时，跳过重复写回的 64 个像素。
- 不降低采样分辨率、刷新频率或柔化质量。不改变视野、探索、单位资格和原生亮度记录。
- `src` 含独立 authority 开发，不能直接整包编译部署。正式候选从已安装 D34 的准确源快照局部合并。

## 工具

Python 使用本机可导入 psutil 的 Codex runtime；构建器复用本模组 `build/wall-surface/run.py`。所有游戏测试用唯一 AIR ID、独立存储与后台桌面，接入共享 `game` 登记，清理仅限本轮进程。后台桌面需系统允许相应创建权限，失败不退回前台。

- `run.py`：历史 D32 对照、构建、运行与组件检查；不要重新 freeze 覆盖历史输入。
- `optimize.py`：Object 缓存、无缓存扫描、紧凑整数缓存三个候选变换。
- `merged.py freeze`：核对安装与 D34 源指纹，新建组合快照。
- `merged.py checks-build/checks-run --name <新名>`：192 组视口、68 项材质、16 项单位遮罩检查。
- `merged.py settings-build/settings-run`：D34 的 90 项设置、16 项柔化、21 项共享探索检查。
- `merged.py build --name <新名> [--verify|--live|--profile]`，随后 `run --name <同名>`：192×75 连续场景测试。冻结目录不可重编；重复测试必须新目录。
- `merged.py analyze --name <新名>`：同输入交替对照，RV 更新加离屏雾层绘制；不是整帧 FPS。输出同时保留最大值、P95、超预算次数和测试窗口内外部 AIR/Java 观察。
- `package.py build/check`：准确生产包编译、类清点、36 项两进程设置验收。
- `deploy.py`：只接受人工核验后固定证据的 `verified.json`；备份、并发指纹、原子替换、正式路径启动，失败只回退本轮 RV。

LIVE 使用原生世界循环，按 baseline/candidate/candidate/baseline 顺序分别测两模式。测试驱动在独立世界生成原生 raider1（smg10），每步移动玩家 12px 在其旁往返，每 6 步扣动一次扳机；敌人无敌只用于保持负载。必须观察实际攻击与 Bullet 对象；随机场景和先后次序意味着它只能补充实战行为与开销证据，不能取代同输入对照。非自动武器每帧按住会维持 t_auto；UnitDamager陷阱也可能带 currentWeapon，早期零攻击窗口不属于战斗验证。

最终结论、未通过轮次和部署状态见 `knowledge/experiments/2026-10-21-motion-performance.md`。
