"""Archive the accepted soft-edge design; never overwrite the previous investigation."""
import hashlib,json,math,shutil,statistics
from pathlib import Path
from PIL import Image,ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/motion-test-output'
DEST=ROOT/'knowledge/experiments/current-soft-v0290'
if (DEST/'fingerprints.json').exists():raise SystemExit('Evidence already archived')
DEST.mkdir(parents=True,exist_ok=True)
def load(name):return json.loads((OUT/name/'motion.json').read_text())
def summary(d):
    costs=sorted(f['ms'] for f in d['frames'])
    return dict(updates=d['updates'],frozen=d['maxFrozen'],mean=round(statistics.mean(costs),2),p95=costs[math.ceil(len(costs)*.95)-1],maximum=max(costs),mutations=d.get('mutations',0))
data={}
base=load('game-baseline')
for name in ['game-baseline','game-soft-medium','game-soft-wide']:
    d=load(name)
    assert all(base[k]==d[k] for k in ['tiles','room','width','height','dist1','dist2'])
    folder=DEST/name;folder.mkdir(exist_ok=True)
    (folder/'motion.json').write_text(json.dumps(d,indent=2)+'\n')
    for f in range(24):shutil.copy2(OUT/name/f'frame-{f:02}.png',folder/f'frame-{f:02}.png')
    data[name]=d
bench={}
for name in sorted(p.name for p in OUT.glob('bench-soft-*')):
    bench[name]=summary(load(name))
    (DEST/(name+'.json')).write_text(json.dumps(load(name),indent=2)+'\n')
def edge(im,y,threshold):
    for x in range(310,810):
        a,b=im.getpixel((x,y)),im.getpixel((x+1,y))
        if a>=threshold>b:return x+(a-threshold)/(a-b)
    raise ValueError((y,threshold))
spatial={}
for name,index in [('baseline',1),('soft-medium',0),('soft-wide',0)]:
    d=load(name);assert d['frames'][index]['eye']==204
    im=Image.open(OUT/name/f'frame-{index:02}.png').convert('L')
    shutil.copy2(OUT/name/f'frame-{index:02}.png',DEST/(name+'-edge.png'))
    metrics={}
    for threshold in [16,128]:
        points=[(y,edge(im,y,threshold)) for y in range(90,215)]
        ym=statistics.mean(y for y,x in points);xm=statistics.mean(x for y,x in points)
        slope=sum((y-ym)*(x-xm) for y,x in points)/sum((y-ym)**2 for y,x in points)
        metrics['rms_'+str(threshold)]=round(math.sqrt(statistics.mean((x-xm-slope*(y-ym))**2 for y,x in points)),3)
    metrics['band_10_90_px']=round(statistics.median((edge(im,y,25.5)-edge(im,y,229.5))/math.sqrt(1+(196/230)**2) for y in range(90,215)),2)
    spatial[name]=metrics
analysis={'benchmark':bench,'spatial':spatial,'source_sha256':hashlib.sha256((ROOT/'src/RealisticVisionMod.as').read_bytes()).hexdigest().upper()}
(DEST/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
for source,dest in [(OUT/'soft-medium-checks/run.log','soft-checks.txt'),(ROOT/'build/wall-test-output/candidate.log','walls.txt'),(ROOT/'build/wall-test-output/edges/candidate.log','edges.txt'),(ROOT/'build/wall-test-output/seams/candidate.log','seams.txt'),(OUT/'game/bench-soft.log','benchmark.txt')]:
    (DEST/dest).write_text('\n'.join(s for s in source.read_text().splitlines() if not s.startswith(('PNG ','DATA ')))+'\n')
old=ROOT/'knowledge/experiments/classic-seams-v0282'
new=ROOT/'build/wall-test-output/game'
old_scene=json.loads((old/'seams-data.json').read_text())
new_scene=json.loads((new/'seams-data.json').read_text())
regression={}
for pos in ['lower','upper']:
    a=next(s for s in old_scene['states'] if s['mode']=='classic' and s['position']==pos)
    b=next(s for s in new_scene['states'] if s['mode']=='classic' and s['position']==pos)
    assert a==b,'Classic inputs differ'
    name=f'seams-{pos}-classic-fog.png'
    assert ImageChops.difference(Image.open(old/name).convert('RGB'),Image.open(new/name).convert('RGB')).getbbox() is None
    name=f'seams-{pos}-current-fog.png'
    ia,ib=Image.open(old/name).convert('L'),Image.open(new/name).convert('L')
    state=next(s for s in new_scene['states'] if s['mode']=='current' and s['position']==pos)
    largest=0
    for tile in state['tiles']:
        if tile['opac']>=1:
            box=(tile['x']*40,tile['y']*40,(tile['x']+1)*40,(tile['y']+1)*40)
            largest=max(largest,ImageChops.difference(ia.crop(box),ib.crop(box)).getextrema()[1])
    assert largest==0,'Current walls differ'
    regression[pos]=dict(classic_identical_input=True,classic_pixel_differences=0,current_wall_max_difference=largest)
(DEST/'full-game-regression.json').write_text(json.dumps(regression,indent=2)+'\n')
rows=''.join(f'<tr><td>{n.replace("bench-soft-", "")}</td><td>{v["updates"]}/90</td><td>{v["mean"]} ms</td><td>{v["p95"]} ms</td><td>{v["maximum"]} ms</td></tr>' for n,v in bench.items())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>current 柔和阴影候选</title>
<style>:root{color-scheme:dark;font:16px/1.65 system-ui,"Microsoft YaHei";background:#111821;color:#e1e9ef}body{max-width:1200px;margin:auto;padding:32px 24px 70px}h1{font-size:30px}h2{font-size:22px;margin-top:36px}p,small{color:#bbc9d4}.tag{color:#8edac6}button,select{font:inherit;color:inherit;background:#243745;border:1px solid #577081;border-radius:6px;padding:6px 15px}.row{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:18px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{border:1px solid #364652;background:#1b2732;padding:14px;border-radius:10px;min-width:0}h3{font-size:17px;margin:0 0 10px}canvas{display:block;width:100%;background:black}input{flex:1;min-width:180px}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #354652}a{color:#a4d6f5}@media(max-width:760px){.grid{grid-template-columns:1fr}body{padding:16px}}</style>
<body><div class="tag">REALISTICVISION · v0.29.0 候选 · 未部署</div><h1>随跑动更新，边缘柔和过渡</h1>
<p>保留 current 的投影轮廓，地板改为连续灰度渐变。墙内黑芯和原版亮面独立保留，敌人遮挡与探索记录不使用柔化后的地板亮度。默认建议采用<b>适中柔化</b>；较宽档用于比较。</p>
<h2>跑动对照</h2><p>同一训练房、同一路线，每步向右 4 像素。旧版 90 步更新 30 次，两档候选均更新 90 次。此处是实际阴影绘图的 24 帧循环回放，不是实时游戏帧率录像。</p>
<div class="row"><button id="play">播放</button><select id="choice" aria-label="柔化宽度"><option value="game-soft-medium">适中柔化 · 推荐</option><option value="game-soft-wide">较宽柔化</option></select><input id="frame" aria-label="回放帧" type="range" min="0" max="23" value="8"><span id="position"></span></div>
<div class="grid"><div class="card"><h3>正式 v0.28.2</h3><canvas id="old" width="920" height="440"></canvas><small id="oldState"></small></div><div class="card"><h3 id="newTitle">适中柔化</h3><canvas id="new" width="920" height="440"></canvas><small id="newState"></small></div></div>
<h2>同眼位的斜边细节</h2><p>以下保持眼位 X=204，放大两倍比较。地板边缘允许有意的柔和过渡；墙内黑芯仍保持全黑。</p>
<div class="grid"><div class="card"><h3>正式版</h3><canvas id="edgeOld" width="840" height="480"></canvas></div><div class="card"><h3>所选候选</h3><canvas id="edgeNew" width="840" height="480"></canvas></div></div><p id="edgeMetrics"></p>
<h2>验证与处理成本</h2><p>墙形 39 项、classic 小墙 10 方向、接缝 8 项通过；另检查门、水、破墙、短视距、换房与模式切换。千条射线的缓存结果与实时查询一致。两档柔化的逻辑视野及探索记录完全相同，敌人掩膜在不可见样本上的透明度均为零。</p>
<table><thead><tr><th>交替测试</th><th>更新次数</th><th>平均处理</th><th>95% 调用不超过</th><th>最大一次</th></tr></thead><tbody>__ROWS__</tbody></table>
<p>同一隔离游戏进程、相同输入、每例 90 步，正式优化编译，计时不含截图。测的是模组处理成本，未包含游戏战斗、其他模组和屏幕合成；短测中的偶发峰值不能排除，尚未做用户存档的长时间实战验收。</p>
<p><a href="../2026-09-20-current-soft-candidate.md">修复说明</a> · <a href="analysis.json">测量数据</a> · <a href="soft-checks.txt">遮挡与刷新验证</a></p>
<script>const data=__DATA__,metrics=__METRICS__;const seq={};for(const name of Object.keys(data))seq[name]=Array.from({length:24},(_,i)=>{const im=new Image();im.src=`${name}/frame-${String(i).padStart(2,'0')}.png`;return im});
const q=id=>document.getElementById(id);let frame=8,playing=false,last=0;
function draw(){q('frame').value=frame;q('position').textContent=`第 ${frame+1}/24 帧`;q('newTitle').textContent=q('choice').selectedOptions[0].textContent;for(const [id,name] of [['old','game-baseline'],['new',q('choice').value]]){const im=seq[name][frame];if(im.complete&&im.naturalWidth)q(id).getContext('2d').drawImage(im,880,80,920,440,0,0,920,440);q(id+'State').textContent=data[name].frames[frame].changed?'本帧阴影已更新':'本帧阴影沿用旧画面';}}
q('play').onclick=()=>{playing=!playing;q('play').textContent=playing?'暂停':'播放'};q('frame').oninput=()=>{frame=+q('frame').value;playing=false;q('play').textContent='播放';draw()};
function edges(){const v=q('choice').value.replace('game-','');for(const [id,name] of [['edgeOld','baseline'],['edgeNew',v]]){const im=new Image();im.onload=()=>{const c=q(id).getContext('2d');c.imageSmoothingEnabled=false;c.drawImage(im,350,20,420,240,0,0,840,480)};im.src=name+'-edge.png'}q('edgeMetrics').textContent=`暗边起伏 RMS：${metrics.baseline.rms_16} → ${metrics[v].rms_16} 像素；所选柔化的 10%–90% 过渡宽度约 ${metrics[v].band_10_90_px} 世界像素。`;}
q('choice').onchange=()=>{draw();edges()};edges();function loop(t){if(playing&&t-last>=1000/30){frame=(frame+1)%24;last=t}draw();requestAnimationFrame(loop)}requestAnimationFrame(loop);
</script></body></html>'''
page=page.replace('__ROWS__',rows).replace('__DATA__',json.dumps(data)).replace('__METRICS__',json.dumps(spatial))
(DEST/'comparison.html').write_text(page,encoding='utf8')
files=[ROOT/'src/RealisticVisionMod.as',ROOT/'build/RealisticVisionMod_test.swf',ROOT/'release/RealisticVisionMod.swf',ROOT/'release/config.txt',ROOT.parents[1]/'pfe.swf']
fingerprints={str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p):hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in files}
fingerprints['evidence']={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in DEST.rglob('*') if p.is_file()}
(DEST/'fingerprints.json').write_text(json.dumps(fingerprints,indent=2)+'\n')
print(json.dumps(analysis,indent=2))
