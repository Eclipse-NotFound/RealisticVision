# D38 继续优化

准确基线为D37 v0.33.4的六类生产源，正式SHA187D287B…4111272。所有输出在忽略目录`build/followup-performance-output`，历史输出不能覆盖。不要从含authority的开发src整包部署。

候选00冻结基线；01把classic精确逻辑查询对齐4×4格；02缓存支持形状，实测无稳定收益，舍弃；03连续行段生成墙面支持区与补集、复用两个mask的几何；04合01与03。

`measure.py`继承D37保留父子层级取图：`*-parent --verify`才是像素验收；`*-visible`无截图用于同输入更新/独立软件draw计时。D38所有候选都继承lazy逻辑场，验证时双方补齐可查询区域，不能沿用D37按01～04候选编号跳过的分支。旧exact-01-parent失败因此保留，exact-01b-parent是修正后证据。

最终：`checks.py build/run checks-final --candidate candidate-04`；`measure.py`的`wide-final-parent --verify --wide`与`exact-final-parent --verify`；`validate.py performance`；`validate.py weapon`。`--candidate`、`--verify`、`--wide`只用于build。真实武器回归仍保留D35泄露反例，主性能基线是D37。

`select.py`仅冻结04与新版本号；`package.py build/check`检验准确六类字节和实际设置；`development.py`只合生产差异、编译开发树但不安装；`review.py`钉住源码/像素/性能/环境证据；`deploy.py`核对当前187D、备份D37、原子替换RV并从正式路径独立启动验证，失败回滚；`finalize.py`归档原始证据和记忆；`closeout.py`隔离暂存，保留四项外部authority改动。

AIR/JVM按官方共享game登记顺序，唯一应用ID、私有桌面、独立存储。完整战斗窗口不是确定性输入，off是同CS场景原生渲染；不把独立更新/软件draw当游戏FPS。最终性能发布只引用同一轮数据，P95、最大值和长帧如实保留。
