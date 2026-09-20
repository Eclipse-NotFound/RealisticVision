"""Archive completed motion investigations and generate an offline comparison page."""
from pathlib import Path
import hashlib, json, shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/motion-test-output'
DEST=ROOT/'knowledge/experiments/current-motion-20260920'
DEST.mkdir(parents=True,exist_ok=True)
if (DEST/'fingerprints.json').exists():raise SystemExit('Evidence already archived; choose a new destination.')
analysis=json.loads((OUT/'analysis.json').read_text())
shutil.copy2(OUT/'analysis.json',DEST/'analysis.json')
for p in OUT.iterdir():
    if not p.is_dir() or not (p/'motion.json').exists():continue
    d=DEST/p.name;d.mkdir(exist_ok=True)
    shutil.copy2(p/'motion.json',d/'motion.json')
    if (p/'run.log').exists():
        lines=(p/'run.log').read_text().splitlines()
        (d/'results.txt').write_text('\n'.join(x for x in lines if 'MOTION' in x or x.startswith('[RVision]'))+'\n')
for variant in ['game-baseline','game-fast-sync']:
    for f in range(24):
        # Exact world-space crop, no resampling. Both cases use the same viewport.
        img=Image.open(OUT/variant/f'frame-{f:02}.png')
        img.crop((880,80,1800,520)).save(DEST/variant/f'motion-{f:02}.png')
for variant in ['baseline','profile','fast-rays','fast-sync','hires','no-clamp','coverage','corner-history',
                'game-baseline','game-fast-rays','game-fast-sync','game-hires','game-coverage','game-corner-history']:
    for f in [1,7]:
        if (OUT/variant/f'frame-{f:02}.png').exists():shutil.copy2(OUT/variant/f'frame-{f:02}.png',DEST/variant/f'frame-{f:02}.png')
for v in ['baseline','corner-history']:
    Image.open(OUT/v/'frame-07.png').crop((420,320,850,460)).save(DEST/v/'speckles.png')
lines=(OUT/'game/bench.log').read_text().splitlines()
(DEST/'benchmark-results.txt').write_text('\n'.join(x for x in lines if x.startswith('CASE ') or 'MOTION_' in x)+'\n')
fingerprints={p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest().upper()
              for p in [ROOT/'src/RealisticVisionMod.as',ROOT/'release/RealisticVisionMod.swf',ROOT/'release/config.txt',ROOT.parents[1]/'pfe.swf']}
fingerprints['experiment_scripts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in Path(__file__).parent.iterdir() if p.is_file()}
(DEST/'fingerprints.json').write_text(json.dumps(fingerprints,indent=2))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>current 阴影跑动与像素边界调查</title><style>
:root{font-family:system-ui,"Microsoft YaHei",sans-serif;color:#dfe7ee;background:#10151b;color-scheme:dark}body{margin:0 auto;max-width:1220px;padding:32px 24px 64px}h1{font-size:30px;margin-bottom:12px}h2{font-size:21px;margin-top:36px}p{line-height:1.75;color:#b7c5d2}.tag{color:#90ddca;font-size:13px;letter-spacing:1px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:#1b232c;border:1px solid #33404d;border-radius:12px;padding:16px;min-width:0}canvas,img{max-width:100%;background:#000;display:block;border-radius:6px}h3{margin:0 0 12px;font-size:17px}.row{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:16px 0}input{flex:1;min-width:200px}button,select{padding:9px 14px;background:#263844;border:1px solid #547182;border-radius:6px;font:inherit;color:inherit}small{display:block;color:#a8b9c9;margin-top:10px;line-height:1.6}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;border-bottom:1px solid #34434e;padding:12px 8px}a{color:#a7d9f4}.stat{color:#90ddca;font-variant-numeric:tabular-nums}.warn{color:#f6ca85}.badge{font-size:12px;color:#8ecfc0}li{line-height:1.85} .pixel{image-rendering:pixelated;width:100%}@media(max-width:750px){.grid{grid-template-columns:1fr}body{padding:18px}table{font-size:12px}}
</style><body><div class="tag">REALISTICVISION · v0.28.2 · 2026-09-20</div>
<h1>跑动时的停顿，与阴影边缘的颗粒</h1>
<p>已复现三个独立问题：<b>约 10 次/秒的边界更新</b>、<b>5 像素采样与硬钳制形成的台阶</b>、<b>角点历史索引错误形成的亮点</b>。此页是调查证据与实验对照；正式模组保持原样。</p>
<h2>① 同一跑动路线，边界是否跟得上</h2>
<p>完整 1.02 训练房，玩家每步向右 4 像素。下方按目标 30 帧/秒回放实际绘图结果，<b>不是实时游戏帧率录像</b>。两图采用相同世界坐标裁切，可暂停逐帧看。</p>
<div class="row"><button id="play">暂停</button><input id="frame" type="range" min="0" max="23" value="0" aria-label="回放帧"><span id="position" class="stat"></span></div>
<div class="grid"><div class="card"><h3>现版 · 三帧计算一次，下一帧显示</h3><canvas id="old" width="920" height="440"></canvas><small id="oldState"></small></div><div class="card"><h3>实验 · 缓存遮挡 + 每帧同步显示</h3><canvas id="new" width="920" height="440"></canvas><small id="newState"></small></div></div>
<p>现版 90 次移动仅更新 30 次；同步实验更新 90 次。仅把计算频率改成每帧、保留原来的显示条件，会使持续移动期间 <b class="warn">一直等不到显示机会</b>（小场景实测 60 帧更新 0 次）。</p>
<h2>② 同一斜边，不同抗锯齿实验</h2>
<div class="row"><select id="edgeChoice" aria-label="边缘方案"><option value="hires">2.5 像素采样</option><option value="no-clamp">移除硬钳制</option><option value="coverage">边界四点覆盖率</option><option value="corner-history">仅修正角点历史</option></select><span id="edgeNote"></span></div>
<div class="grid"><div class="card"><h3>现版 · 5 像素采样</h3><canvas id="edgeOld" width="840" height="480"></canvas></div><div class="card"><h3 id="edgeTitle">实验</h3><canvas id="edgeNew" width="840" height="480"></canvas></div></div>
<small>同眼位、同输入，截取单墙角上侧斜边并放大 2 倍。测量的是直线拟合后的边缘起伏，数值越低越平滑。放开钳制带来的偏移和漏光不能算成功。</small>
<h2>③ 阴影里的规律亮点，来自错误的记忆位置</h2>
<div class="grid"><div class="card"><h3>现版</h3><img class="pixel" src="baseline/speckles.png" alt="现版下侧阴影内的小亮点"></div><div class="card"><h3>仅修正角点索引</h3><img class="pixel" src="corner-history/speckles.png" alt="修正后阴影内亮点消失"></div></div>
<p>四角射线采样的位置是子格 0 和 7，历史却写到 0 和 1。单变量修正后，已确认从未看见过的阴影内部，异常亮像素从 <b>808 → 0</b>。台阶仍存在，说明它是另一个问题。</p>
<h2>④ 同一游戏进程内，交替复测的计算成本</h2>
<table><thead><tr><th>方案</th><th>边界更新 / 90 步</th><th>平均每步</th><th>95% 的调用不超过</th><th>判断</th></tr></thead><tbody>
<tr><td>现版</td><td>30</td><td>8.9–9.7 ms</td><td>21–22 ms</td><td>停顿节奏稳定复现</td></tr>
<tr><td>仅缓存遮挡数据</td><td>30</td><td>6.9–7.0 ms</td><td>13–14 ms</td><td>画面逐像素一致，但仍三帧更新</td></tr>
<tr><td>缓存 + 每帧同步</td><td>90</td><td>13.0–14.0 ms</td><td>16–17 ms</td><td>时间连续性改善，须进一步压低成本</td></tr>
<tr><td>全图 2.5px 采样</td><td>30</td><td>24.9 ms</td><td>55 ms</td><td>台阶减半，但代价过高</td></tr>
<tr><td>边界四点覆盖率</td><td>30</td><td>14.0 ms</td><td>38 ms</td><td>当前实现改善很小，不推荐</td></tr></tbody></table>
<small>每方案 90 步；现版、缓存、同步有首尾交替复测。采用正式版相同的优化编译设置。计时覆盖模组处理，排除截图编码；不包含游戏物理、其他模组和最终屏幕合成。同步实验有一次 72 ms 尖峰，复测最大 19 ms，不能声称长期稳定帧率。训练房视距很大，其他房间成本需另测。</small>
<h2>推荐实施顺序</h2><ol><li><b>先修正确性：</b>角点历史索引；确保显示任务不会被连续计算饿死。</li><li><b>先省成本再提高刷新：</b>缓存遮挡数据，同步更新显示与敌人掩膜；继续减少完全亮、完全暗区域及未变墙体的重复工作。</li><li><b>抗锯齿单独设计：</b>优先在遮挡轮廓处计算连续覆盖率或到边缘的距离，完整保留黑区和墙内原版渐变；不直接放大整图或取消保护。</li></ol>
<p>尚未完成：新抗锯齿算法、完整战斗性能、门水破墙与换房回归、真实存档长时间跑动。本轮未部署实验方案。</p>
<p><a href="../2026-09-20-current-motion-investigation.md">详细调查报告</a> · <a href="analysis.json">测量数据</a> · <a href="benchmark-results.txt">复测结果</a></p>
<script>
const data=__DATA__,oldFrames=__OLD__,newFrames=__NEW__;
const seq={};for(const name of ['game-baseline','game-fast-sync'])seq[name]=Array.from({length:24},(_,i)=>{const x=new Image();x.src=`${name}/motion-${String(i).padStart(2,'0')}.png`;return x});
let playing=true,index=0,last=0;const slider=document.getElementById('frame');
function draw(){slider.value=index;document.getElementById('position').textContent=`第 ${index+1} / 24 帧 · 玩家 X=${oldFrames[index].x}`;
for(const [id,name,frames] of [['old','game-baseline',oldFrames],['new','game-fast-sync',newFrames]]){const c=document.getElementById(id).getContext('2d'),im=seq[name][index];if(im.complete&&im.naturalWidth)c.drawImage(im,0,0);document.getElementById(id+'State').textContent=frames[index].changed?'这一帧边界已更新':'这一帧边界保持原样';}}
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暂停':'播放';};slider.oninput=()=>{playing=false;document.getElementById('play').textContent='播放';index=+slider.value;draw();};
function loop(t){if(playing&&t-last>=1000/30){index=(index+1)%24;last=t;}draw();requestAnimationFrame(loop);}requestAnimationFrame(loop);
const notes={hires:'起伏 RMS：1.30 → 0.63 px；计算成本显著增加','no-clamp':'起伏 RMS：1.30 → 0.33 px；未见黑区出现漏光',coverage:'起伏 RMS：1.30 → 1.27 px；收益很小','corner-history':'修复亮点，斜边台阶基本不变'};
function edge(){const v=document.getElementById('edgeChoice').value;document.getElementById('edgeNote').textContent=notes[v];document.getElementById('edgeTitle').textContent=document.getElementById('edgeChoice').selectedOptions[0].textContent;
for(const [id,name] of [['edgeOld','baseline'],['edgeNew',v]]){const im=new Image();im.onload=()=>{const c=document.getElementById(id).getContext('2d');c.imageSmoothingEnabled=false;c.drawImage(im,350,20,420,240,0,0,840,480);};im.src=`${name}/frame-01.png`;}}
document.getElementById('edgeChoice').onchange=edge;edge();
</script></body></html>'''
page=page.replace('__DATA__',json.dumps(analysis,ensure_ascii=False)).replace('__OLD__',(OUT/'game-baseline/motion.json').read_text()).replace('__NEW__',(OUT/'game-fast-sync/motion.json').read_text())
page=page.replace('oldFrames=','oldFramesData=').replace('newFrames=','newFramesData=')
page=page.replace('const seq={};','const oldFrames=oldFramesData.frames,newFrames=newFramesData.frames;const seq={};')
(DEST/'comparison.html').write_text(page,encoding='utf-8')
print(DEST/'comparison.html')
