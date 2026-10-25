"""Summarize both complete comparisons; keep per-run estimates separate."""
from pathlib import Path
import json

MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/candidate-comparison-output'
REPORT=MOD/'knowledge/experiments/2026-10-25-candidate-comparison.md'
names=['comparison-01','comparison-04']
labels={'off':'关闭RV','normal':'D44正式基线','candidate':'D50 all','ray':'D51 v2'}
results=[]
tables=[]
for name in names:
    folder=OUT/name
    analysis=json.loads((folder/'analysis.json').read_text())
    assert analysis['verified']
    data=json.loads((folder/'evidence/result.json').read_text())
    build=json.loads((folder/'build.json').read_text())
    environment=json.loads((folder/'environment-active.json').read_text())
    assert not environment['processes']
    changes={}
    for mode,candidate in [('classic','candidate'),('current','ray')]:
        base=analysis['groups'][mode+'/normal']['nextInterval']
        trial=analysis['groups'][mode+'/'+candidate]['nextInterval']
        changes[mode]={'baseline':base,'candidate':trial,'meanChangePercent':100*(trial['mean']/base['mean']-1)}
    longframes=[]
    for index,case in enumerate(data['cases']):
        for frame in case['frames']:
            if frame.get('nextInterval',0)>100:
                longframes.append({'window':index,'mode':case['mode'],'variant':case['variant'],**frame})
    results.append({'name':name,'groups':analysis['groups'],'targetChanges':changes,'longFrames':longframes,
                    'availableGiB':environment['available']/1024**3,'hostCpuSnapshot':environment['hostCpu'],
                    'selected':analysis['selected'],'buildSamples':build['samples'],'scene':data['scene']})
    lines=[f'### {name}', '', f"每窗预热{build['warmup']}帧、采样{build['samples']}帧；每条件{2*(build['samples']-1)}个有效完整间隔。启动可用内存{environment['available']/1024**3:.2f} GiB、CPU两秒快照{environment['hostCpu']}%；未发现其它AIR或Java。CPU快照不代表整轮机器负载。",'',
           '| 模式 | 条件 | 均值 / P95 / 最大值（ms） | >100ms | RV自身均值（ms） |',
           '|---|---|---|---|---|']
    for mode in ['current','classic']:
        for variant in ['off','normal','candidate','ray']:
            group=analysis['groups'][mode+'/'+variant];v=group['nextInterval']
            lines.append(f"| {mode} | {labels[variant]} | {v['mean']:.2f} / {v['p95']} / {v['max']} | {v['>100']} | {group['rv']['mean']:.2f} |")
    tables.append('\n'.join(lines))

assert json.loads((OUT/'comparison-04/repeat-input-check.json').read_text())['identical']
summary={'runs':results,'adopted':False,'formal':'D44 v0.33.10-render-cache','reason':'Neither candidate has a consistent full-frame improvement across both comparisons; no merge or deployment.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
total=sum(sum(v['nextInterval']['n'] for v in result['groups'].values()) for result in results)
maxframe=max((f for result in results for f in result['longFrames']),key=lambda f:f['nextInterval'])
text=f'''被测技能：remains-auto-testing、remains-runtime-debug、remains-mod-build、remains-mod-memory
技能归属：工作区级（Remains）
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# D52：恢复独立测试后复验两个性能候选

## 结论

用户2026-10-25明确“可进行测试”，此前保留试玩导致的独立计时暂停已经撤回。两份旧暂停标记改名保存，历史报告未改。两轮共32战斗窗口、{total}个有效完整帧间隔完成；D50 all和D51 v2均未证明稳定的完整战斗收益，不合并、不部署。正式保持D44 v0.33.10（638E2D40…FE343710）。战斗卡顿目标尚未解决。

## 输入与方法

- D44取准确生产源build/combat-render-output/production-final2/src；D50 all和D51 candidate-v2分别独立派生，源指纹见resumed.json。没有authority、射线命中计数或原生主帧插桩。
- 真实48×25训练房，6名佣兵、原生AI/武器/弹体/粒子，角色位置按相同步进控制；记忆亮度0.6、current柔化25、常亮关闭。帧率上限30，不能外推任意房间/设置或用户存档的数值。
- 完整当前安装组合加探针，RV由独立子域加载并手动调用。两轮实际requested/ok、16窗次序、真实开火/弹体、完整采样、退出码0及所有冻结输入均核对。
- 第一轮每模式off/D44/D50/D51/D51/D50/D44/off，current在前；第二轮classic在前，每模式off/D51/D50/D44/D44/D50/D51/off。第二轮直接复用第一轮三个RV测试包，全部宿主及其它模组SWF逐字节相同，仅探针改变次序及采样长度。
- 每组经共享测试登记独占运行，启动前检查其它AIR/Java及可用内存；计时期间没有本会话编译、归档、去重或高频监测。仍有原生随机动画/AI、运行时回收与系统调度波动，因此保留两轮及每窗结果，不挑选有利窗口或跨轮拼接收益。
- D50 all此前6529局部+64原生+59397临界尺寸/设置/模式/换房严格检查；D51此前134827断言（21129条射线）+64原生大图严格检查，本轮源未变。这是复用的功能证据，不冒充本轮重新执行；没有新画面算法改动。

## 完整战斗结果

{chr(10).join(tables)}

## 判读与长帧

D50的目标是classic小房间私有插值复用，D51的目标是current空矩形射线捷径。两者局部步骤/耗时的减少均不能代替完整帧收益。未受对应改动影响的模式也出现相近幅度波动，这是本轮的对照警示；最大值偶尔下降也不足以判为修复。

D50 all的classic整帧均值两轮分别增加2.45%、1.41%，P95也都增加；虽然RV自身均值各少约1ms，不能据此发布。D51的current整帧均值第一轮增加0.98%、第二轮减少0.92%，方向反转，尚无稳定收益。两轮均使用非默认记忆亮度0.6；未证明默认设置或大图的表现。

本轮最长采样间隔{maxframe['nextInterval']}ms出现在{maxframe['mode']}/{labels[maxframe['variant']]}，对应RV调用{maxframe['rv']}ms。调用之外还包含原生更新、其他监听、显示绘制和调度，未逐项计时，不能直接说全部是显卡或垃圾回收。各个>100ms帧已保留在summary.json；没有用缺少新证据的推测解释其根因。

## 失败与修正

comparison-02完成构建后、AIR启动前被字节一致检查拒绝：同源重新编译的三个RV SWF指纹变化。没有将它当性能样本。源码逐文件一致，未进一步定位二进制差异来源；之后改为复用comparison-01冻结测试字节，避免重构建差异成为复测变量。

comparison-03同样没有启动AIR：排除新探针的路径判断使用正斜杠，实际清单是Windows反斜杠，因此误把预期变化的探针判成漂移。改为Path.parts判断，comparison-04独立目录完整通过。两个失败构建与登记保留；没有覆盖或复用失败结果，没有关闭护栏。

## 交付与接续

本轮只新增测试工具和证据，未改生产源码或release。自有AIR退出、测试描述符清理；其它会话实例未操作，4项authority外部WIP保留。报告与冻结证据见candidate-comparison-d52-20261025，源和二进制指纹见archive.json/build.json。

这两项优化不再仅凭此前功能通过或局部计数推进发布。后续若研究更长视距/大图，必须独立验证对应工作负载，不把本轮小房间结论扩成所有场景的性能证明。整体卡顿仍需对完整帧中尚未分清的原生/绘制/调度部分进一步归因；先提出可检验的触发条件，再新增候选。
'''
REPORT.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'pairedFrames':total,'targetChanges':{r['name']:r['targetChanges'] for r in results},'adopted':False},ensure_ascii=False))
