# 最大化、低开销采样与墙面裁切候选

正式基线为 v0.33.15-combo-v4，AEA30314…9AA557；准确生产源从已冻结
`build/composite-followup-output/baseline/src` 复制。不要从开发 HEAD 构建部署。
`prepare.py` 已执行，只允许第一次使用；历史输出不可覆盖。

- `01-maximized-baseline`：自有 Windows 窗口确为 maximized；该桌面得到的
  客户区为 **1280×729**，不等同于此前 2560×1521 的大尺寸普通窗口。
- CPU 查询仅使用自有进程句柄，100ms 间隔；有 monotonic/UTC 锚点。
  CPU 总时间粒度较粗，接近零必须结合 cycles，不能把 0 个时间刻度说成
  进程绝对没有执行。进程所有线程执行量不能归为某个遮罩或 GPU 开销。
- `02-floor-branch`：`make_candidate.py` 从基线生成，只将默认地板分支放到
  墙材质轮廓外；墙边常亮路径不变。12 组同帧/变换严格相等，但当前配对
  整帧没有改善，不采用。源已冻结在 `floor-candidate/src`。
- `03-merged-large`：`make_merged.py` 从第一候选生成，保留原始裁切图形，
  将墙瓦片范围与材质轮廓的正向矩形相交，取消剩余嵌套硬裁切。需分别
  检查画面及完整帧表现；实测49.21→52.14ms，8图有1级像素差，否决，
  不再扩展状态矩阵。源保留在 `merged-candidate/src`。
- `04-palette-both`：`make_palette.py` 重新从基线派生，只按fieldUpdates
  跳过相同贴图上传。4个current画面/工作图对照通过，省17/27次上传。
  实时PowerShell长管道读JSON引起写文件占用，save错误处理又跳过退出，
  自有进程已核对后结束；此轮全部计时不作验收，失败原件必须保留。
- `05-palette-repeat`：相同两份SWF，修正结果保存为独立快照，fail最终
  总能退出；不在计时中读进度JSON。8窗两模式正反比较，去掉原生函数
  包装和外部CPU采样，仍取完整相邻帧间隔和RV局部计时。
  最终8组画面/工作图相等，但current43.44→44.46ms，classic51.69→62.28ms，
  classic两方向反转，未确认收益，不采用、不部署。所有5项登记结束。

`run.py` 自动登记 game 独占，使用唯一应用 ID、私有桌面、静音和存档副本。
玩家/其它会话进程不被关闭。所有计时通过完整相邻帧间隔验证，并区分 RV、
原生主循环、其它监听和绘制/等待后段。`--solo` 去掉随机单位后仍补六名
狮鹫；零敌人另需 `--zero-enemies`。

`PixelChecks.as` / `MergedPixels.as` 在计时结束后对同一时刻的实际显示树
切换参考/候选层次，保持输入位图完全相同；另取参考重复图以检查对照本身。
它们不代替跨帧缓存失效与状态切换检查。

`--maximize` 检查原生最大化完成。`--native-screen` 只设置大尺寸普通窗口，
两者不可混称。01/02 的 activeSamples 插桩锚点失配，结果是 null；虽然
驱动每帧向自有窗口请求激活，不能称已经逐帧核实。后续修正锚点。

新试验使用唯一目录，例如：

```text
python -X utf8 build/maximized-flow/run.py 03-merged-large --full --plain --native-timing --private-visible --sweep --solo --native-screen --try-candidate --reverse --pixel-checks --merged
python -X utf8 build/maximized-flow/analyze.py 03-merged-large
```

完整开启组合来自本轮冻结安装，排除 RV 原入口和 LightAndDarkness；探针
载入准确 RV 源的测试公开版本。源文件、宿主、配置和启用名单均记录指纹。
这些测试字节不应部署。通过功能与性能后才构建不含插桩的正式候选。
