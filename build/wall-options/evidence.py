"""Archive completed off/on captures; verify the option cannot brighten air."""
from pathlib import Path
import hashlib,json,re,shutil,statistics
import numpy as np
from PIL import Image,ImageDraw,ImageFont
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/wall-options-output'
DEST=MOD/'knowledge/experiments/wall-options-v0311-20261015'
DEST.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
metrics=[]
for fixture in ['game','game-rock']:
    root=OUT/fixture;src=root/'evidence';target=DEST/fixture;target.mkdir(exist_ok=True)
    result=read(src/'result.json');run=read(root/'last-run.json')
    assert run['exit']==0 and not result.get('error') and all(c['ok'] for c in result['checks'])
    assert 'SURFACE GAME COMPLETE' in (root/'game.log').read_text(encoding='utf-8')
    for path in (OUT/'candidate/src').rglob('*.as'):
        assert (root/'candidate-src'/path.relative_to(OUT/'candidate/src')).read_text(encoding='utf-8')==re.sub(r'\bprivate\b','public',path.read_text(encoding='utf-8'))
    shutil.copyfile(root/'game.log',target/'game.txt');save(target/'last-run.json',run)
    # Preserve the native compact evidence instead of expanding repeated tile
    # snapshots into hundreds of thousands of presentation-only diff lines.
    shutil.copyfile(src/'result.json',target/'result.json')
    alpha=np.array(Image.open(src/'terrain-alpha.png').convert('RGBA'))[:,:,3]
    shutil.copyfile(src/'terrain-alpha.png',target/'terrain-alpha.png')
    tiles=result['states'][0]['tiles'];solid=np.array([t['opac']>=1 and t['zForm']==0 for t in tiles]).reshape(25,48)
    core=[(x*40+20,y*40+20) for y in range(1,24) for x in range(1,47) if solid[y-1:y+2,x-1:x+2].all()]
    coarse=np.zeros((200,384),dtype=bool)
    for t in tiles:
        if t['opac']>=1:coarse[t['y']*8+int(t['zForm'])*2:(t['y']+1)*8,t['x']*8:(t['x']+1)*8]=True
    expanded=np.pad(coarse,8)
    band=np.zeros_like(coarse)
    for dy in range(17):
        for dx in range(17):band|=expanded[dy:dy+200,dx:dx+384]
    band=np.repeat(np.repeat(band,5,0),5,1)
    for mode in ['classic','current']:
        for pos in ['upper','lower']:
            tag=pos+'-'+mode
            images={name:np.array(Image.open(src/(name+'-'+tag+'-fog.png')).convert('RGB')).astype(int) for name in ['baseline','off','on']}
            switch_delta=np.abs(images['on']-images['off']).max(2)
            repair_delta=np.abs(images['off']-images['baseline']).max(2)
            row={'fixture':fixture,'mode':mode,'position':pos,
                 'switch_air_max_difference':int(switch_delta[alpha==0].max()),
                 'switch_changed_opaque_pixels':int(np.count_nonzero((switch_delta>0)&(alpha==255))),
                 'repair_changed_air_pixels':int(np.count_nonzero((repair_delta>1)&(alpha==0))),
                 'repair_outside_wall_band_max':int(repair_delta[~band].max()),
                 'core_points':len(core),
                 'off_core_max':max(int(images['off'][y,x].max()) for x,y in core),
                 'on_core_max':max(int(images['on'][y,x].max()) for x,y in core)}
            assert row['switch_air_max_difference']==0 and row['switch_changed_opaque_pixels']>0,row
            assert row['off_core_max']==0 and row['on_core_max']==0 and row['repair_outside_wall_band_max']<=1,row
            metrics.append(row)
            for name in ['baseline','off','on','native']:
                for suffix in ['-fog','-stage']:
                    path=src/(name+'-'+tag+suffix+'.png')
                    if path.exists():shutil.copyfile(path,target/path.name)
                Image.open(src/(name+'-'+tag+'.png')).crop((160,360,1250,990)).save(target/(name+'-'+tag+'-detail.png'))
checks=read(OUT/'checks/results.json');assert all(r['exit']==0 and r['failed']==0 for r in checks.values())
save(DEST/'checks.json',checks)
for name in checks:shutil.copyfile(OUT/'checks'/(name+'.txt'),DEST/(name+'.txt'))
for variant in ['legacy','repaired']:
    shutil.copyfile(OUT/(variant+'-repro')/'repro.txt',DEST/(variant+'-repro.txt'))
save(DEST/'pixels.json',metrics)
bench=read(OUT/'bench/evidence/result.json');assert read(OUT/'bench/last-run.json')['exit']==0 and not bench.get('error')
for path in (OUT/'candidate/src').rglob('*.as'):
    assert (OUT/'bench/candidate-src'/path.relative_to(OUT/'candidate/src')).read_text(encoding='utf-8')==re.sub(r'\bprivate\b','public',path.read_text(encoding='utf-8'))
save(DEST/'benchmark-raw.json',bench);shutil.copyfile(OUT/'bench/game.log',DEST/'benchmark.txt')
timings=[]
for row in bench['timings']:
    values=[a+b for a,b in zip(row['updates'],row['composition'])]
    timings.append({'mode':row['mode'],'variant':row['variant'],'samples':len(values),
                    'mean_ms':round(statistics.mean(values),2),'p95_ms':sorted(values)[int(len(values)*.95)-1],
                    'max_ms':max(values)})
save(DEST/'benchmark.json',timings)
paths=['src/RVWallSurface.as','build/wall-options-output/candidate/src/RealisticVisionMod.as','release/config.txt']
# Binary fingerprints are supplied by a separate, read-only hash command. Keep
# that inspection distinct from artifact writes under the workspace SWF guard.
fingerprints={p:digest(MOD/p) for p in paths};fingerprints.update(read(OUT/'binary-fingerprints.json'));save(DEST/'fingerprints.json',fingerprints)
save(DEST/'source-fingerprints.json',{str(p.relative_to(MOD)):digest(p) for folder in [OUT/'candidate/src',MOD/'build/wall-options'] for p in folder.rglob('*') if p.is_file() and p.suffix in ['.as','.py','.json']})
preview=Image.new('RGB',(1040,690),'#10161c');draw=ImageDraw.Draw(preview);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for i,(variant,label) in enumerate([('baseline','当前安装'),('off','候选 · 常亮关闭（仍修复阴影溢出）'),('on','候选 · 常亮开启')]):
    draw.text((12,230*i+4),label,font=font,fill='white')
    preview.paste(Image.open(OUT/'game-rock/evidence'/(variant+'-upper-classic.png')).crop((200,600,1240,800)),(0,230*i+30))
preview.save(DEST/'preview.png')
(DEST/'comparison.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>墙边常亮开关与阴影修复</title><style>
*{box-sizing:border-box}body{margin:0;background:#111820;color:#e8edf3;font:16px/1.7 "Segoe UI","Microsoft Yahei",sans-serif}main{max-width:1800px;margin:auto;padding:28px}
h1{font-size:28px;margin:0 0 10px}p{color:#b5c2d0}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}label{display:flex;gap:8px;align-items:center}
select,button{font:inherit;background:#233140;color:#fff;border:1px solid #4b6074;border-radius:6px;padding:6px 12px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
figure{margin:0;background:#090e13;border:1px solid #324454;border-radius:8px;overflow:hidden}figcaption{padding:10px;font-weight:600}.image{overflow:auto}img{width:100%;display:block}.zoom img{width:auto;max-width:none}small{color:#9dacba}a{color:#95c9ff}
@media(max-width:1000px){.grid{grid-template-columns:1fr}main{padding:16px}}
</style><main><h1>常亮可以关闭，墙边阴影仍会修正</h1><p>关闭时，已探索墙面随视野变暗；开启时保留亮面。两种设置都修正岩壁透明凹口处的方格黑影，深处墙芯继续保持黑暗。</p>
<div class="controls"><label>材质<select id="material"><option value="game-rock">岩壁与半高墙</option><option value="game">金属训练房</option></select></label>
<label>模式<select id="mode"><option value="classic">仿原版</option><option value="current">平滑阴影</option></select></label>
<label>位置<select id="position"><option value="upper">上层 · 下方为记忆区</option><option value="lower">梯子下方</option></select></label>
<label>画面<select id="view"><option value="detail">局部对照</option><option value="stage">最终游戏画面</option></select></label><button id="zoom">查看原始像素</button></div>
<div class="grid"><figure><figcaption>当前安装</figcaption><div class="image"><img id="baseline" alt="旧版墙面与阴影"></div></figure>
<figure><figcaption>候选 · 常亮关闭</figcaption><div class="image"><img id="off" alt="常亮关闭但保留阴影修复"></div></figure>
<figure><figcaption>候选 · 常亮开启</figcaption><div class="image"><img id="on" alt="常亮开启并保留阴影修复"></div></figure></div>
<p><small>同场景、同路线的独立测试实例；岩壁使用原生材质和一处半高墙，并非用户存档复刻。候选尚未部署。<a href="preview.png">局部预览</a> · <a href="../2026-10-15-wall-bright-option.md">验证与性能记录</a></small></p></main>
<script>const el=id=>document.getElementById(id);function update(){for(const variant of ['baseline','off','on'])el(variant).src=el('material').value+'/'+variant+'-'+el('position').value+'-'+el('mode').value+'-'+el('view').value+'.png';}
for(const id of ['material','mode','position','view'])el(id).addEventListener('change',update);el('zoom').onclick=()=>{document.body.classList.toggle('zoom');el('zoom').textContent=document.body.classList.contains('zoom')?'缩放到页面':'查看原始像素'};update();</script></html>''',encoding='utf-8')
print(json.dumps({'checks':checks,'pixels':metrics,'timings':timings,'comparison':str(DEST/'comparison.html')},ensure_ascii=False,indent=2))
