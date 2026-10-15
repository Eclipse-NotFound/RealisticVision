"""Archive completed runs, assert pixel boundaries, and make a local comparison."""
from pathlib import Path
import hashlib,json,re,shutil,statistics
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from prepare import MOD,OUT,FROZEN_SHA

DEST=MOD/'knowledge/experiments/wall-surface-v0310-20261015'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
DEST.mkdir(parents=True,exist_ok=True)
assert digest(OUT/'baseline/src/RealisticVisionMod.as')==FROZEN_SHA
assert digest(MOD/'src/RVWallSurface.as')==digest(OUT/'candidate/src/RVWallSurface.as')
metrics=[]
for fixture in ['game','game-rock']:
    root=OUT/fixture;src=root/'evidence';target=DEST/fixture;target.mkdir(exist_ok=True)
    data=read(src/'result.json');assert not data.get('error') and all(x['ok'] for x in data['checks'])
    assert 'SURFACE GAME COMPLETE' in (root/'game.log').read_text(encoding='utf-8')
    for filename in ['RealisticVisionMod.as','RVWallSurface.as']:
        assert (root/'candidate-src'/filename).read_text(encoding='utf-8')==re.sub(r'\bprivate\b','public',(OUT/'candidate/src'/filename).read_text(encoding='utf-8')),filename
    for f in src.glob('*.png'):
        if f.name.endswith('-fog.png') or f.name=='terrain-alpha.png':shutil.copyfile(f,target/f.name)
    shutil.copyfile(root/'game.log',target/'game.txt');shutil.copyfile(root/'last-run.json',target/'last-run.json')
    save(target/'result.json',data)
    alpha=np.array(Image.open(src/'terrain-alpha.png').convert('RGBA'))[:,:,3]
    tiles=data['states'][0]['tiles'];solid=np.array([t['opac']>=1 and t['zForm']==0 for t in tiles]).reshape(25,48)
    core=[(x*40+20,y*40+20) for y in range(1,24) for x in range(1,47) if solid[y-1:y+2,x-1:x+2].all()]
    assert len(core)>0
    for mode in ['classic','current']:
        for pos in ['upper','lower']:
            name=pos+'-'+mode
            base=np.array(Image.open(src/('baseline-'+name+'-fog.png')).convert('RGB')).astype(int)
            cand=np.array(Image.open(src/('candidate-'+name+'-fog.png')).convert('RGB')).astype(int)
            delta=np.abs(cand-base).max(2)
            row={'fixture':fixture,'mode':mode,'position':pos,'air_pixels':int(np.count_nonzero(alpha==0)),
                 'air_max_difference':int(delta[alpha==0].max()),'core_points':len(core),
                 'core_max_brightness':max(int(cand[y,x].max()) for x,y in core),
                 'changed_wall_pixels':int(np.count_nonzero(delta[alpha>0]))}
            assert row['air_max_difference']==0 and row['core_max_brightness']==0 and row['changed_wall_pixels']>0,row
            metrics.append(row)
            for variant in ['baseline','candidate','native']:
                im=Image.open(src/(variant+'-'+name+'.png'))
                im.crop((160,360,1250,990)).save(target/(variant+'-'+name+'-detail.png'))
checks=read(OUT/'checks/results.json');assert all(r['exit']==0 and r['failed']==0 for r in checks.values())
for f in (OUT/'checks').glob('*.log'):
    if f.name in ['SurfaceChecks.log','SoftHarness.log','SharedExplorationHarness.log']:shutil.copyfile(f,DEST/(f.stem+'.txt'))
save(DEST/'checks.json',checks);save(DEST/'pixels.json',metrics)
bench=read(OUT/'bench/evidence/result.json');assert not bench.get('error')
save(DEST/'benchmark-raw.json',bench);shutil.copyfile(OUT/'bench/game.log',DEST/'benchmark.txt')
timings=[]
for row in bench['timings']:
    total=[a+b for a,b in zip(row['updates'],row['composition'])]
    timings.append({'variant':row['variant'],'mode':row['mode'],'samples':len(total),
        'update_mean_ms':round(statistics.mean(row['updates']),2),'draw_mean_ms':round(statistics.mean(row['composition']),2),
        'total_mean_ms':round(statistics.mean(total),2),'median_ms':statistics.median(total),
        'p95_ms':sorted(total)[int(len(total)*.95)-1],'max_ms':max(total)})
save(DEST/'benchmark.json',timings)
inputs={str(f.relative_to(MOD)):digest(f) for f in [MOD/'src/RealisticVisionMod.as',MOD/'src/RVWallSurface.as',
        OUT/'candidate/src/RealisticVisionMod.as',OUT/'candidate/RealisticVisionMod.swf',MOD/'release/RealisticVisionMod.swf',MOD/'release/config.txt']}
inputs['installed_pfe.swf']=digest(MOD.parents[1]/'pfe.swf');inputs['frozen_production_source']=FROZEN_SHA
save(DEST/'fingerprints.json',inputs)

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
preview=Image.new('RGB',(1040,690),'#111820');draw=ImageDraw.Draw(preview)
for i,(variant,label) in enumerate([('native','原版参照'),('baseline','当前安装 · 仿原版'),('candidate','候选 · 已探索墙边常亮')]):
    draw.text((12,i*230+4),label,font=font,fill='#eef3fb')
    im=Image.open(OUT/'game-rock/evidence'/(variant+'-upper-classic.png')).crop((200,600,1240,800))
    preview.paste(im,(0,i*230+30))
preview.save(DEST/'preview.png')
(DEST/'comparison.html').write_text('''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RealisticVision · 常亮墙边候选</title><style>
*{box-sizing:border-box}body{margin:0;background:#10161c;color:#e6ebf2;font:16px/1.65 "Segoe UI","Microsoft Yahei",sans-serif}
main{max-width:1500px;margin:auto;padding:28px}h1{font-size:28px;margin:0 0 8px}p{color:#aebbc9;margin:8px 0 18px}
.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin:20px 0}label{display:flex;gap:8px;align-items:center}
select,button{background:#202b37;color:#f2f6fb;border:1px solid #3d5064;border-radius:7px;padding:9px 12px;font:inherit;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#080c10;border:1px solid #30404e;border-radius:10px;overflow:hidden}
figcaption{padding:10px 15px;font-weight:600}.image{overflow:auto}img{display:block;width:100%;height:auto}.zoom img{width:1090px;max-width:none}
#native{margin-top:20px;max-width:1090px}small{color:#9aabba}a{color:#97cfff}@media(max-width:850px){.grid{grid-template-columns:1fr}main{padding:16px}}
</style><main><h1>已探索墙边，保留一圈亮面</h1><p>离开当前视野后，墙边仍可见；往墙内逐渐变暗。地板雾效继续由各模式决定。</p>
<div class="controls"><label>材质<select id="material"><option value="game-rock">岩壁与半高墙</option value="game">原训练房金属墙</option></select></label>
<label>模式<select id="mode"><option value="classic">仿原版</option><option value="current">平滑阴影</option></select></label>
<label>位置<select id="position"><option value="upper">回到上层 · 下方为记忆区</option><option value="lower">梯子下方 · 上方为记忆区</option></select></label>
<button id="zoom">查看原始像素</button><button id="reference">显示原版参照</button></div>
<div class="grid"><figure><figcaption>当前安装</figcaption><div class="image"><img id="baseline" alt="当前安装的墙面和阴影"></div></figure>
<figure><figcaption>候选 · 已探索墙边常亮</figcaption><div class="image"><img id="candidate" alt="候选的常亮墙边"></div></figure></div>
<figure id="native" hidden><figcaption>同场景原版参照</figcaption><div class="image"><img id="original" alt="原版照明参照"></div></figure>
<p><small>取自隔离游戏实例，同场景、同路线对照。岩壁使用原生 G 材质并设置一处半高墙，用于检查凹凸边缘；不是用户存档的精确复刻。此页为候选，正式安装尚未替换。<br>
八组图像中，墙体图像以外的雾层差异为 0；各组 156 个深墙芯采样保持全黑。<a href="preview.png">打开局部对照图</a></small></p></main>
<script>
const byId=id=>document.getElementById(id);
function update(){const key=byId('material').value+'/'+'';const suffix='-'+byId('position').value+'-'+byId('mode').value+'-detail.png';
 byId('baseline').src=key+'baseline'+suffix;byId('candidate').src=key+'candidate'+suffix;byId('original').src=key+'native'+suffix;}
['material','mode','position'].forEach(id=>byId(id).addEventListener('change',update));
byId('zoom').onclick=()=>{document.body.classList.toggle('zoom');byId('zoom').textContent=document.body.classList.contains('zoom')?'缩放到页面':'查看原始像素'};
byId('reference').onclick=()=>{byId('native').hidden=!byId('native').hidden;byId('reference').textContent=byId('native').hidden?'显示原版参照':'收起原版参照'};update();
</script></html>''',encoding='utf-8')
print(json.dumps({'checks':checks,'pixel_cases':len(metrics),'benchmark':timings,'artifact':str(DEST/'comparison.html')},ensure_ascii=False,indent=2))
