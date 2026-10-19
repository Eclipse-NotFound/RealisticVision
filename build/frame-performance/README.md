# D31 完整视野与单位遮罩性能验证

基线固定为已安装 D29 `2E7150CF…8907A10`，准确生产源来自 `build/wall-performance-output/candidate/src`。本目录不写 release、不改用户存档。HEAD 另有未发布 authority 工作；`src/RVWallSurface.as` 也有其他会话的阶梯修复，不能整包编译 HEAD 当本次候选。

`prepare.py` 从冻结D29依次应用 `optimize.py`、`sparse_sight.py`、`view_cache.py`。六项改动是同色墙格批量填充、classic遮罩阈值运算、相同输入复用遮罩、瓦片可见性分类缓存、大图按需读取视野格子，以及常亮关闭时稳定墙面缓存范围。没有降采样或降低更新频率。已淘汰的paletteMap和colorTransform两个current方案留在trial-01/02，像素一致但更慢；常亮开启路径不扩大墙面缓存，因为viewport-checks-02出现10组像素差。

用 Codex runtime Python 从游戏根运行 `mods/RealisticVision/build/frame-performance/run.py`。每次实验使用新名字，已冻结证据不可覆盖：

```text
run.py freeze
prepare.py
run.py checks --name checks-final
viewport.py build --name viewport-checks-03
viewport.py run --name viewport-checks-03
run.py build --name final-large-verify --large --verify
run.py build --name final-large-trial --large
run.py campaign --name final-large-verify,final-large-trial
package.py
analyze.py --name final-large-trial
evidence.py
```

以上是复现步骤，已有名字的成功运行与生产包已经冻结，不要照抄覆盖。`final-large-trial`现已成功完成，其余最终原生轮已完成或取消，本轮没有待运行的AIR。未来确有复验需要时使用新名字；运行前必须取得 RConnect 主会话新的明确交接，并通过6GiB可用内存门槛，单次资源观察不等于获得窗口。`environment.json`每10秒记录AIR/Java及可用内存，不能据此排除所有外部负载。完成或无法启动立即交回，再离线分析。

早先因资源不足保存过停点，后于2026-10-19 12:09获得新窗口并完成最后一轮。四组更新加绘制平均减少5.6%–14.2%、P95均下降，但classic最大值243→266ms、仍有长帧；具体数据见报告末节及analysis-final.json，不等于完整游戏FPS。PID60112退出0、描述符删除，窗口已交回，未部署。

`analyze.py`只接受成功退出、无插桩、无像素核验的完整配对轮，输出更新、绘制及逐样本相加总耗时的均值、中位数、P95和最大值；P95使用排序后`floor(.95*(n-1))`。旧`trial-04`尚无新格式构建清单，不能直接套完整命令；统计函数已逐项复算并严格匹配其`analysis-initial.json`，没有改写旧证据。

`checks-final` 对照旧源码的160移动帧、288随机场与重新挂载、512同色墙情况、48,000个大小场景判定；另沿用柔化/射线/共享探索检查。`viewport-checks-03`独立核对192组缩放、移动、原地破坏、探索和半透明材质变化的屏幕图像。全部使用真实AIR位图，不用Python模拟像素。

`final-large-trial`同进程、相同位置输入、旧新次序交替，每组120样本；含完整RV更新及单独雾层绘制，无诊断计时包装、无取图。空场景和96单位压力场是可控工作负载，不等于完整游戏帧率。额外的`final-small-trial`、`final-large-profile`、`final-live`已编译但取消运行，不计入最终实测；不因文件存在便称已通过。

`final-large-verify`只读复制CS 0.7和固定工厂地图，192×75原生Location，移动镜头下核对32个时点的雾层、墙场、视野、探索、敌人资格、遮罩和最终雾层合成。此模式含逐像素验证，耗时不作速度证据。

`FrameProbe`的`--live`模式可保留原生世界循环和原场景单位，连续执行旧/新/新/旧/关闭五窗；每窗排除前30帧、记录180帧间隔及RV更新耗时。世界继续演进，这种测试只作运行观察。已运行的`live-final`属于第一组四项优化，且与其他编译重叠；不能混为最终六项候选或独占FPS实测。

`package.py` 只改版本标记为 v0.32.2-frame-performance，冻结到 `build/frame-performance-output/production`，并让**准确生产字节**通过两个独立进程的设置、改键和心跳检查。六个生产类应与 D29 相同，禁止携带探针、存根或 authority 类。

所有启动使用唯一 AIR AppID、隐藏窗口和自己的存储，退出后删除自有描述符；玩家及其他会话进程不操作。正式安装另需复核当前安装、保护其他并行工作、按发布门禁保存回退并验证，不能直接运行历史 D29 部署脚本。
