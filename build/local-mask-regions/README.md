# 精确区域遮罩与墙面alpha候选

继续2026-11-01性能普查。基于准确combo-v4生产源建立独立实验，不覆盖历史证据。
本目录脚本不是部署入口，候选必须先通过对应功能与干净完整帧对照。

- `prepare.py`：只执行一次，冻结生产源、当前宿主及组合，保留正式配置和存储。
- `candidate.py`：只执行一次。current在原逻辑像素写入时构建两个32位数，精确表示每格64像素；classic对已经生成的原输入按需建立同样记录。只让内容未变的区域提前返回，保留光栅、坐标和关联历史。
- `check.py <新目录> [--large]`：真实更新函数与基线差分；比较当前全部逻辑格、原输入、雾图、探索及敌人/特效实际绘制。大场景增加视口移动和视口外墙光。
- `oracle.py`：仅测试构建使用。每次提前返回都从原位图完整复制/阈值化并比较；不得据此测性能。
- `alpha.py`：独立候选，不叠加区域版本。一个无变换材质源完整覆盖贴片时只复制/比较alpha；组合、变换及不完整覆盖走原路径，回退强制刷新过期RGB快照。
- `alpha_check.py <新目录>`：原helper逐像素对照，包括RGB/alpha改变、复合源、scrollRect、小数平移、常亮和重置。
- `run.py`：指纹核对后复用既有隔离、登记、静音、原生射击运行器；新输出位于local-mask-regions-output。

```text
python -X utf8 build/local-mask-regions/check.py 03-regions
python -X utf8 build/local-mask-regions/run.py 04-native-oracle --full --solo --sweep --both --no-cpu --private-visible --maximize --plain --moving --verify-regions
python -X utf8 build/local-mask-regions/check.py 05-large-regions --large
python -X utf8 build/local-mask-regions/alpha_check.py 06-alpha-checks
python -X utf8 build/local-mask-regions/check.py 07-large-regions --large
```

功能证据：03的1202项检查、3494次复用相等；04原生交战current11734/classic12673次复用均与原输入一致。01因夹具以实例访问静态常量编译失败；02因Grafon替身缺生产已读取的visFront字段失败，均未改候选，失败保留。

05缺大场景原生space二维入口，修夹具后07通过1202项/4558次复用。06通过47项严格像素检查/107次alpha路径，包含多源、透明度/颜色修改、回退、常亮和变换。

干净计时使用`--plain`且不含`--verify-regions`。`--candidate --three-way`比较baseline、region candidate、alpha vector三个版本的正反次序。固定与受控移动、两模式及变换分开记录，不把操作数下降当作整帧收益。三个准确源各保存在输出目录。

08长窗超时；09用`--short --reverse --reuse-from=08-three-way-moving`复用同字节完整完成12窗。两项候选无确认收益，不采用、不部署。详见[报告](../../knowledge/experiments/2026-11-01-local-mask-regions.md)。`analyze.py <目录>`只接受正常终态；失败轮必须显式`--partial=result-9-605784.json`，生成带不完整标记的诊断统计。`archive.py`只在最后测试退出后运行，冻结证据且排除玩家存储与游戏素材。
