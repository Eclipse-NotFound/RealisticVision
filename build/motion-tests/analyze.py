"""Analyze AIR captures. Fixed-step replay costs are NOT live FPS measurements."""
import json, math, statistics
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/motion-test-output'

def pct(values,q):
    values=sorted(values)
    return values[max(0,math.ceil(len(values)*q)-1)] if values else None

def summarize(data):
    f=data['frames'];r=[x for x in f if x['rays']>0] # fovVersion also changes for wall-mask refreshes.
    return {'frames':len(f),'updates':data['updates'],'frozen':data['maxFrozen'],
            'mean_ms':round(statistics.mean(x['ms'] for x in f),2),'p95_ms':pct([x['ms'] for x in f],.95),
            'max_ms':max(x['ms'] for x in f),'over_33ms':sum(x['ms']>1000/30 for x in f),
            'rebuild_mean_ms':round(statistics.mean(x['ms'] for x in r),2) if r else None,
            'rays_per_rebuild':round(statistics.mean(x['rays'] for x in r),1) if r else None,
            'boundary_tiles':round(statistics.mean(x['tiles'] for x in r),1) if r else None,
            'phase_sum_ms':{key:sum(x['perf'].get(key,0) for x in f) for key in ['computeFov','fillFogCache','refreshWallField','structHash','hideEnemies','applyVision']}}

def edge_at(img,y,threshold=16):
    for x in range(300,800):
        a,b=img.getpixel((x,y)),img.getpixel((x+1,y))
        if a>=threshold and b<threshold:return x+(a-threshold)/max(1,a-b)
    return None

def spatial(img,eye=204):
    pts=[(y,edge_at(img,y)) for y in range(90,215)]
    pts=[(y,x) for y,x in pts if x is not None]
    ym=statistics.mean(y for y,x in pts);xm=statistics.mean(x for y,x in pts)
    slope=sum((y-ym)*(x-xm) for y,x in pts)/sum((y-ym)**2 for y,x in pts)
    residual=[x-(xm+slope*(y-ym)) for y,x in pts]
    # Single opaque wall, analytic tangent from player eye to its top-left corner.
    # >5 world pixels into the never-seen shadow, away from wall and framebuffer borders.
    leaked=[]
    for y in range(90,215):
        tangent=400+(240-y)*(400-eye)/230
        for x in range(math.ceil(tangent+5),math.ceil(tangent+25)):
            leaked.append(img.getpixel((x,y)))
    return {'edge_residual_rms_px':round(math.sqrt(statistics.mean(v*v for v in residual)),3),
            'edge_residual_range_px':round(max(residual)-min(residual),3),
            'deep_shadow_max_brightness':max(leaked),'deep_shadow_pixels_above_2':sum(v>2 for v in leaked)}

report={}
for folder in sorted(OUT.iterdir()):
    p=folder/'motion.json'
    if not p.exists():continue
    d=json.loads(p.read_text());report[folder.name]=summarize(d)
    if not folder.name.startswith('game') and (folder/'frame-01.png').exists() and folder.name!='gate1':
        report[folder.name]['spatial']=spatial(Image.open(folder/'frame-01.png').convert('L'),d['frames'][1]['eye'])

for candidate in ['profile','fast-rays']:
    pairs=[]
    for f in range(24):
        a=Image.open(OUT/'baseline'/f'frame-{f:02}.png').convert('RGB')
        b=Image.open(OUT/candidate/f'frame-{f:02}.png').convert('RGB')
        pairs.append(ImageChops.difference(a,b).getbbox() is None)
    report[candidate]['exact_baseline_frames']=sum(pairs)

# Input equivalence across independently booted real-game replays; compare opacity and native illumination.
games=[p for p in OUT.iterdir() if (p.name.startswith('game-') or p.name.startswith('bench-')) and (p/'motion.json').exists()]
base=json.loads((OUT/'game-baseline/motion.json').read_text()) if (OUT/'game-baseline/motion.json').exists() else None
for p in games:
    if base:
        d=json.loads((p/'motion.json').read_text())
        report[p.name]['identical_room_input']=all(d[k]==base[k] for k in ['tiles','room','dist1','dist2','width','height'])
        report[p.name]['native_mutations']=d['mutations']

if (OUT/'game-fast-rays/frame-01.png').exists():
    report['game-fast-rays']['exact_baseline_frames']=sum(
        ImageChops.difference(Image.open(OUT/'game-baseline'/f'frame-{f:02}.png').convert('RGB'),
                              Image.open(OUT/'game-fast-rays'/f'frame-{f:02}.png').convert('RGB')).getbbox() is None
        for f in range(24))

for variant in ['baseline','corner-history']:
    if not (OUT/variant/'frame-07.png').exists():continue
    b=Image.open(OUT/variant/'frame-07.png').convert('L');values=[]
    # Intersection of occluded regions over the entire visited route (eyes x=200..228).
    for x in range(480,901):
        upper=240-230*(x-400)/200
        lower=440-30*(x-440)/(440-228)
        for y in range(280,440):
            if upper+8<y<lower-8:values.append(b.getpixel((x,y)))
    report[variant]['never_seen_interior']={'pixels_above_2':sum(v>2 for v in values),'max_brightness':max(values)}

(OUT/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
