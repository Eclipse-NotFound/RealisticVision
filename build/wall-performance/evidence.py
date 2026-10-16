from pathlib import Path
import hashlib,json,math,re,statistics,shutil
import numpy as np
from PIL import Image
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/wall-performance-output'
EVIDENCE=MOD/'knowledge/experiments/wall-performance-v0321-20261016'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    EVIDENCE.mkdir(exist_ok=True)
    checks=json.loads((OUT/'checks/results.json').read_text())
    assert all(v['exit']==0 and v['failed']==0 for v in checks.values())
    total=sum(v['passed'] for v in checks.values())
    pixels=[]
    for scene in ['game-reuse','game-rock-reuse']:
        folder=OUT/scene/'evidence';result=json.loads((folder/'result.json').read_text())
        assert not result.get('error') and all(c['ok'] for c in result['checks'])
        total+=len(result['checks'])
        for mode in ['classic','current']:
            for position in ['upper','lower']:
                for old,new in [('oldOff','off'),('oldOn','on')]:
                    tag=position+'-'+mode+'-fog'
                    a=np.asarray(Image.open(folder/(old+'-'+tag+'.png')).convert('RGB')).astype(np.int16)
                    b=np.asarray(Image.open(folder/(new+'-'+tag+'.png')).convert('RGB')).astype(np.int16)
                    delta=np.abs(a-b);changed=int(np.any(delta,axis=2).sum());maximum=int(delta.max())
                    assert int(a.min())==0 and int(a.max())==255,'Blank/unrepresentative image'
                    pixels.append(dict(scene=scene,mode=mode,position=position,option=new,changed_pixels=changed,max_delta=maximum))
                    assert changed==0,(scene,tag,new,changed,maximum)
        shutil.copyfile(OUT/scene/'game.log',EVIDENCE/(scene+'.txt'))
        shutil.copyfile(folder/'result.json',EVIDENCE/(scene+'.json'))
        # Representative old/new fog images; every group's statistics are above.
        for name in ['oldOff-upper-current-fog','off-upper-current-fog','oldOn-lower-classic-fog','on-lower-classic-fog']:
            shutil.copyfile(folder/(name+'.png'),EVIDENCE/(scene+'-'+name+'.png'))
    bench=json.loads((OUT/'bench-reuse/evidence/result.json').read_text());metrics=[]
    assert not bench.get('error') and all(c['ok'] for c in bench['checks'])
    for row in bench['timings']:
        values=[a+b for a,b in zip(row['updates'],row['composition'])];ordered=sorted(values)
        assert len(values)==240
        metrics.append(dict(mode=row['mode'],variant=row['variant'],samples=len(values),mean=statistics.mean(values),p95=ordered[math.ceil(len(values)*.95)-1],maximum=max(values)))
    for folder in ['checks','game-reuse','game-rock-reuse','bench-reuse']:
        for src in (OUT/'candidate/src').rglob('*.as'):
            target=OUT/folder/('src' if folder=='checks' else 'candidate-src')/src.relative_to(OUT/'candidate/src')
            expected=re.sub(r'\bprivate\b','public',src.read_text(encoding='utf-8-sig'))
            expected=expected.replace('File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")','new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
            assert target.read_text(encoding='utf-8')==expected,'Test source drift '+str(target)
    production=json.loads((OUT/'production/result.json').read_text());assert production['status']=='PASS'
    candidate=OUT/'candidate/RealisticVisionMod.swf';assert production['sha256']==sha(candidate)
    total+=sum(v['checks'] for v in production['runs'])
    classes=json.loads((OUT/'classes.json').read_text())
    assert set(classes)=={'RealisticVisionMod','RVWallSurface','RVKeybinds','RVExplorationCarrier','modlocales.vision.RVLocale','modlocales.vision.RVLocaleMessages'}
    proof=dict(status='PASS',version='v0.32.1-wall-performance',candidate_sha256=sha(candidate),bytes=candidate.stat().st_size,
        checks_passed=total,pixel_groups_passed=len(pixels),strict_pixel_equality=True,classes=classes,
        source_sha256={p.relative_to(OUT/'candidate/src').as_posix():sha(p) for p in (OUT/'candidate/src').rglob('*.as')})
    for name,value in [('final-checks',proof),('checks',checks),('pixels',pixels),('benchmark',metrics),('benchmark-raw',bench),('production',production)]:
        (EVIDENCE/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'final-checks.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    for name in ['profile-vectors','profile-sparse','profile-wall-cache','bench-final','bench-final-pass']:
        shutil.copyfile(OUT/name/'evidence/result.json',EVIDENCE/(name+'.json'))
    shutil.copyfile(OUT/'runtime-inputs.json',EVIDENCE/'runtime-inputs.json')
    shutil.copyfile(OUT/'classes-raw.txt',EVIDENCE/'classes-raw.txt')
    for name in checks:shutil.copyfile(OUT/'checks'/(name+'.txt'),EVIDENCE/(name+'.txt'))
    for name in ['process-1.txt','process-2.txt','runtime.txt']:shutil.copyfile(OUT/'production'/name,EVIDENCE/('production-'+name))
    # Archive normalized text; byte-for-byte raw AIR logs remain in build output.
    for p in EVIDENCE.glob('*.txt'):
        p.write_text('\n'.join(line.rstrip() for line in p.read_bytes().decode('utf-8').replace('\r','').splitlines()).rstrip()+'\n',encoding='utf-8')
    print(json.dumps(proof,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':run()
