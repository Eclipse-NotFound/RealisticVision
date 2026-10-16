"""Archive final checked outputs; source equality is mandatory before copying."""
from pathlib import Path
import json,re,hashlib,shutil,statistics
from PIL import Image,ImageDraw,ImageFont
import numpy as np
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/wall-restore-output'
DEST=MOD/'knowledge/experiments/wall-restore-v0320-20261016'
DEST.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def match(folder):
    for p in (OUT/'candidate/src').rglob('*.as'):
        s=re.sub(r'\bprivate\b','public',p.read_text(encoding='utf-8-sig'))
        if p.name=='RealisticVisionMod.as':s=s.replace('File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")','new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
        assert (folder/p.relative_to(OUT/'candidate/src')).read_text(encoding='utf-8')==s,p

metrics=[];scene_checks=0
for name in ['game','game-rock']:
    root=OUT/name;src=root/'evidence';target=DEST/name;target.mkdir(exist_ok=True)
    match(root/'candidate-src');r=read(src/'result.json')
    assert read(root/'last-run.json')['exit']==0 and not r.get('error') and all(c['ok'] for c in r['checks'])
    scene_checks+=len(r['checks'])
    for a,b in [(root/'game.log',target/'game.txt'),(src/'result.json',target/'result.json'),(src/'terrain-alpha.png',target/'terrain-alpha.png')]:shutil.copyfile(a,b)
    alpha=np.array(Image.open(src/'terrain-alpha.png').convert('RGBA'))[:,:,3]
    h,w=alpha.shape;solid=np.zeros((h//40,w//40),bool)
    for t in r['states'][0]['tiles']:solid[t['y'],t['x']]=t['opac']>=1 and t['zForm']==0
    core=[(x*40+20,y*40+20) for y in range(1,solid.shape[0]-1) for x in range(1,solid.shape[1]-1) if solid[y-1:y+2,x-1:x+2].all()]
    padded=np.pad(solid,2);near=np.zeros_like(solid)
    for dy in range(5):
        for dx in range(5):near|=padded[dy:dy+solid.shape[0],dx:dx+solid.shape[1]]
    near=np.repeat(np.repeat(near,40,0),40,1)
    for mode in ['classic','current']:
        for pos in ['upper','lower']:
            tag=pos+'-'+mode
            pictures={v:np.array(Image.open(src/(v+'-'+tag+'-fog.png')).convert('RGB')).astype(int) for v in ['legacy','baseline','off','on']}
            delta=np.abs(pictures['off']-pictures['legacy']).max(2)
            air=np.abs(pictures['off']-pictures['on']).max(2)
            row={'fixture':name,'mode':mode,'position':pos,'material_max_old_wall_difference':int(delta[alpha>0].max()),
                'material_pixels_over_one':int(np.count_nonzero((alpha>0)&(delta>1))),
                'switch_air_max_difference':int(air[alpha==0].max()),
                'corrected_air_pixels':int(np.count_nonzero((alpha==0)&(delta>1))),
                'distant_floor_max_difference':int(delta[~near].max()),'core_points':len(core),
                'off_core_max':max(int(pictures['off'][y,x].max()) for x,y in core),
                'on_core_max':max(int(pictures['on'][y,x].max()) for x,y in core)}
            # Native jagged edges rasterized through different positive mask
            # partitions can differ by a few 8-bit levels. Keep both the maximum
            # and the affected count; do not hide them behind a mean metric.
            assert row['material_max_old_wall_difference']<=3 and row['material_pixels_over_one']<=100,row
            assert row['switch_air_max_difference']<=3,row
            # A solid metal face need not have any visible transparent notch.
            # Rock is the positive contour fixture; metal also checks no-op areas.
            if name=='game-rock':assert row['corrected_air_pixels']>0,row
            assert row['distant_floor_max_difference']<=1,row
            assert row['off_core_max']==0 and row['on_core_max']==0,row
            metrics.append(row)
            for variant in pictures:
                Image.open(src/(variant+'-'+tag+'.png')).crop((160,360,1250,990)).save(target/(variant+'-'+tag+'-detail.png'))
                shutil.copyfile(src/(variant+'-'+tag+'-fog.png'),target/(variant+'-'+tag+'-fog.png'))
                if variant in ['off','on']:shutil.copyfile(src/(variant+'-'+tag+'-stage.png'),target/(variant+'-'+tag+'-stage.png'))

checks=read(OUT/'checks-candidate/results.json');assert all(v['exit']==0 and v['failed']==0 for v in checks.values())
match(OUT/'checks-candidate/src')
save(DEST/'checks.json',checks);save(DEST/'pixels.json',metrics)
for name in checks:shutil.copyfile(OUT/'checks-candidate'/(name+'.txt'),DEST/(name+'.txt'))
shutil.copyfile(OUT/'checks-baseline/RestoreChecks.txt',DEST/'old-repro.txt')
match(OUT/'bench/candidate-src');bench=read(OUT/'bench/evidence/result.json');assert not bench.get('error')
save(DEST/'benchmark-raw.json',bench)
timings=[]
for row in bench['timings']:
    v=[a+b for a,b in zip(row['updates'],row['composition'])]
    timings.append({'mode':row['mode'],'variant':row['variant'],'samples':len(v),'mean_ms':round(statistics.mean(v),2),'p95_ms':sorted(v)[int(len(v)*.95)-1],'max_ms':max(v)})
save(DEST/'benchmark.json',timings)
production=read(OUT/'production/result.json');assert production['status']=='PASS' and production['sha256']==sha(OUT/'candidate/RealisticVisionMod.swf')
save(DEST/'production.json',production)
for name in ['process-1.txt','process-2.txt','runtime.txt']:shutil.copyfile(OUT/'production'/name,DEST/name)
save(DEST/'source-fingerprints.json',{str(p.relative_to(MOD)):sha(p) for p in (OUT/'candidate/src').rglob('*.as')})
save(DEST/'final-checks.json',{'candidate_sha256':production['sha256'],'candidate_bytes':(OUT/'candidate/RealisticVisionMod.swf').stat().st_size,
    'isolated_checks':sum(v['passed'] for v in checks.values()),'scene_checks':scene_checks,'production_checks':sum(v['checks'] for v in production['runs']),
    'pixel_groups':len(metrics),'deployed':False})
(DEST/'comparison.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>恢复旧版墙内阴影 · v0.32.0 候选</title><style>*{box-sizing:border-box}body{margin:0;background:#101820;color:#e7edf3;font:16px/1.7 "Segoe UI","Microsoft Yahei",sans-serif}main{max-width:1900px;margin:auto;padding:26px}h1{font-size:28px}p{color:#b7c6d2}a{color:#94caff}.controls{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}select,button{font:inherit;color:#eef5fc;background:#223241;padding:6px;border:1px solid #52708a;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}figure{margin:0;border:1px solid #395165;background:#080d12;border-radius:8px;overflow:hidden}figcaption{padding:10px;font-weight:600}.image{overflow:auto}img{width:100%;display:block}.zoom img{width:auto;max-width:none}@media(max-width:850px){.grid{grid-template-columns:1fr}}</style>
<main><h1>旧版墙芯与渐变，保留透明凹口修复</h1><p>默认关闭“已探索墙边常亮”。墙的亮边随视野变暗，厚墙深处沿用旧版原生阴影。开启常亮只改变墙材质，空气和地板不随开关改变。<strong>候选尚未部署。</strong></p>
<div class="controls"><label>材质 <select id="material"><option value="game-rock">岩壁与半高墙</option><option value="game">金属训练房</option></select></label><label>模式 <select id="mode"><option value="classic">仿原版</option><option value="current">平滑阴影</option></select></label><label>位置 <select id="position"><option value="upper">上层</option><option value="lower">梯子下方</option></select></label><label>画面 <select id="view"><option value="detail">局部画面</option><option value="fog">纯阴影</option></select></label><button id="zoom">原始像素</button></div>
<div class="grid"><figure><figcaption>旧版墙面参考 · 含原来的凹口溢出</figcaption><div class="image"><img id="legacy" alt="旧版墙面参考"></div></figure><figure><figcaption>当前 v0.31.1 · 常亮关闭</figcaption><div class="image"><img id="baseline" alt="当前版本"></div></figure><figure><figcaption>候选 · 默认关闭常亮</figcaption><div class="image"><img id="off" alt="候选默认阴影"></div></figure><figure><figcaption>候选 · 开启常亮</figcaption><div class="image"><img id="on" alt="候选可选常亮"></div></figure></div>
<p>同场景、同路线的独立 AIR 实例。旧墙面参考保留后续改键、语言与场景兼容，只保留 v0.30.1 的墙面渲染路径；并非整包回滚。岩壁为受控材质场景，并非玩家存档复刻。<a href="../2026-10-16-wall-render-restore.md">验证与性能记录</a></p></main>
<script>const el=id=>document.getElementById(id);function update(){for(const v of ['legacy','baseline','off','on'])el(v).src=el('material').value+'/'+v+'-'+el('position').value+'-'+el('mode').value+'-'+el('view').value+'.png';}for(const id of ['material','mode','position','view'])el(id).onchange=update;el('zoom').onclick=()=>document.body.classList.toggle('zoom');update();</script></html>''',encoding='utf-8')
for log in DEST.rglob('*.txt'):
    # Canonical archive formatting only; raw AIR stdout stays in build output.
    log.write_text('\n'.join(line.rstrip() for line in log.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':checks,'scene_checks':scene_checks,'pixels':metrics,'timings':timings},ensure_ascii=False,indent=2))
