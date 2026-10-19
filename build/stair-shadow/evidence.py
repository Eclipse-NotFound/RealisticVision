"""Package completed D30 evidence; no game/installation mutations."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image,ImageChops
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/stair-shadow-output'
DEST=MOD/'knowledge/experiments/stair-shadow-v0322-20261019'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    DEST.mkdir(exist_ok=True)
    capture=OUT/'reproduction-isolation'
    result=json.loads((capture/'evidence/result.json').read_text(encoding='utf-8'))
    review=json.loads((OUT/'review-rv3/reproduction-isolation.json').read_text(encoding='utf-8'))
    # Keep the first strict comparison, including its eight failures. Removing
    # the helper also removes base.mask, so that reference changes two variables.
    # The additional capture holds base.mask/display ancestry fixed and hides
    # only the overlays. Preserve every strict result, including ON failures;
    # packaging evidence must not relabel those as tolerance-based passes.
    assert len(result['checks'])==96 and all(c['ok'] for c in result['checks'])
    expected={(v,m,p) for v in ['off','on'] for m in ['classic','current'] for p in ['lower','upper']}
    assert {(p['variant'],p['mode'],p['position']) for p in review['pairs']}==expected
    assert len(review['pairs'])==8 and len(review['isolation_checks'])==8
    assert all(p['changed_outside_cut_air']==0 and p['changed_material_pixels']==0
               and p['old_black_air']>0 and p['new_black_air']==0 for p in review['pairs'])
    assert all(p['cut_air_overlay_mismatch']==0 and p['cut_air_overlay_max_delta']==0
               for p in review['pairs'] if p['variant']=='off')
    assert review['result_sha256']==sha(capture/'evidence/result.json')
    for pair in review['pairs']:
        for name,digest in pair['input_sha256'].items():
            assert sha(capture/'evidence'/name)==digest,'Stale pixel audit: '+name
    residual_path=OUT/'review-rv3/reproduction-isolation-residual-comparison.json'
    residual=json.loads(residual_path.read_text(encoding='utf-8'))
    for name,digest in residual['input_sha256'].items():
        assert sha(capture/'evidence'/name)==digest,'Stale residual audit: '+name
    assert len(residual['pairs'])==4 and all(
        p['target_positive']['pixels']==p['target_positive']['final_output_unchanged_from_old']
        and p['common_air_final_output_changes']==0 and p['common_air_delta_changes']==0
        for p in residual['pairs'])
    for folder in ['checks-red','checks-green','checks-final','regression','production']:
        for p in (OUT/folder).glob('*'):
            if p.suffix in ['.txt','.json']:
                q=DEST/folder/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    for p in (capture/'evidence').iterdir():
        if p.suffix in ['.png','.json']:shutil.copyfile(p,DEST/p.name)
    shutil.copyfile(capture/'game.log',DEST/'native-game.txt')
    shutil.copyfile(OUT/'review-rv3/reproduction.json',DEST/'first-strict-pixels.json')
    shutil.copyfile(OUT/'review-rv3/reproduction-detailed.json',DEST/'first-strict-pixels-detailed.json')
    shutil.copyfile(OUT/'review-rv3/reproduction-isolation.json',DEST/'independent-pixels.json')
    shutil.copyfile(OUT/'review-rv3/reproduction-isolation-detailed.json',DEST/'independent-pixels-detailed.json')
    shutil.copyfile(residual_path,DEST/'residual-comparison.json')
    shutil.copyfile(capture/'last-run.json',DEST/'native-last-run.json')
    for name in ['runtime-cleanup-plan.json','runtime-cleanup.json']:
        if (OUT/name).exists():shutil.copyfile(OUT/name,DEST/name)
    # Preserve the initial capture alongside the final causal isolation run.
    initial=DEST/'initial-capture';initial.mkdir(exist_ok=True)
    for p in (OUT/'reproduction/evidence').iterdir():
        if p.suffix in ['.png','.json']:shutil.copyfile(p,initial/p.name)
    shutil.copyfile(OUT/'reproduction/game.log',initial/'native-game.txt')
    fixture=capture/'evidence'
    terrain=Image.open(fixture/'terrain-alpha.png').convert('RGBA')
    background=Image.new('RGBA',terrain.size,(135,141,145,255));background.alpha_composite(terrain)
    background=background.convert('RGB');box=(280,585,720,810)
    cards=[]
    for mode,label in [('classic','仿原版'),('current','平滑阴影')]:
        row=[]
        for variant,title in [('oldOff','修复前'),('off','修复后'),('native','原版光照参考')]:
            name=f'off-upper-{mode}-native.png' if variant=='native' else f'{variant}-upper-{mode}-fog.png'
            fog=Image.open(fixture/name).convert('RGB')
            image=ImageChops.multiply(background,fog).crop(box)
            name=f'compare-{mode}-{variant}.png';image.save(DEST/name)
            row.append(f'<figure><figcaption>{title}</figcaption><img src="{name}" alt="{label}：{title}"></figure>')
        cards.append(f'<section><h2>{label}</h2><div class="row">'+''.join(row)+'</div></section>')
    (DEST/'comparison.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>阶梯阴影修复对照 · v0.32.2</title><style>body{font:16px/1.7 system-ui;margin:32px auto;padding:0 24px;max-width:1460px;background:#171c22;color:#e6eaf0}h1{font-size:28px}h2{font-size:20px;margin-top:34px}p{color:#bcc9d8;max-width:960px}.row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:0;background:#222b34;border:1px solid #3d4958;border-radius:8px;overflow:hidden}figcaption{padding:10px 14px}img{width:100%;display:block}.badge{color:#9edac2}a{color:#a6ceff}@media(max-width:900px){.row{grid-template-columns:1fr}} </style>
<h1>阶梯上方的黑色横条已修复</h1><div class="badge">v0.32.2 阶梯候选 · 尚未部署</div>
<p>原生材质、相同位置的实际 AIR 渲染。修复保留台阶上方原有雾效，墙内凹口继续防止阴影溢出。下图关闭“已探索墙边常亮”；开启时也已做像素核对。</p>
<p>这是可重复的原生训练房阶梯夹具，不是用户原存档。左组和右组分别覆盖两种原生台阶标记；灰色背景用于看清墙材质与阴影。</p>
<p>严格隔离核对：默认关闭常亮的4组空气像素完全一致；开启常亮的4组仍有34–70个像素相差1/255，该零差异检查保留失败记录。8组均没有改变墙面材质或修正区外像素，原先每组500个错误全黑空气像素均消失。下方原版列仅作光照参考。</p>'''+''.join(cards)+
        '<p>独立复核发现，旧版在同一空气区域也存在相同的隐藏图层参考差异，实际新旧画面却完全一致。该参照会改变少量合成取整，不能直接把失败判作新的阴影溢出；目标区域负1差异未逐点归因，完整记录保留。</p><p><a href="../2026-10-19-stair-shadow.md">完整原因、验证与限制</a> · <a href="independent-pixels.json">独立像素检查</a></p></html>',encoding='utf-8')
    manifest={'candidate':{'version':'v0.32.2-stair-candidate','bytes':(OUT/'candidate/RealisticVisionMod.swf').stat().st_size,'sha256':sha(OUT/'candidate/RealisticVisionMod.swf')},
        'sources':{p.relative_to(OUT/'candidate/src').as_posix():sha(p) for p in (OUT/'candidate/src').rglob('*.as')},
        'regression':json.loads((OUT/'regression/results.json').read_text()),'stair_checks':44,'native_checks':len(result['checks']),
        'pixel_checks':{'status':'PASS' if review['isolation_failed']==0 else 'VISIBLE_STAIR_FIX_VERIFIED_WITH_STRICT_REFERENCE_DIFFERENCES',
                        'pairs':8,'outside_cut_air_mismatches':sum(p['changed_outside_cut_air'] for p in review['pairs']),
                        'material_mismatches':sum(p['changed_material_pixels'] for p in review['pairs']),
                        'overlay_isolation_passed':review['isolation_passed'],'overlay_isolation_failed':review['isolation_failed'],
                        'unmasked_reference_strict_passed':review['passed'],'unmasked_reference_strict_failed':review['failed'],
                        'unmasked_reference_max_delta':max(p['max_air_delta_to_original_fog'] for p in review['pairs'])},
        'residual_audit':'residual-comparison.json',
        'production':json.loads((OUT/'production/result.json').read_text()),'classes':['RealisticVisionMod','RVWallSurface','modlocales.vision.RVLocale','RVExplorationCarrier','RVKeybinds','modlocales.vision.RVLocaleMessages']}
    (DEST/'final-checks.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
