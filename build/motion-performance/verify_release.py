"""Pin the reviewed candidate and evidence; no build or deployment side effects."""
import json,re
import package
run=package.run
OUT=run.OUT

def read(rel):return json.loads((OUT/rel).read_text())

def main():
    assert not (OUT/'verified.json').exists()
    manifest=read('production/manifest.json')
    assert manifest['version']==package.VERSION and run.sha(package.PACKAGE/'RealisticVisionMod.swf')==manifest['swf']
    for rel,digest in manifest['sources'].items():assert run.sha(package.PACKAGE/'src'/rel)==digest
    for rel,digest in manifest['test_sources'].items():
        path=OUT/'candidate/src'/rel;assert run.sha(path)==digest
        expected=re.sub(r'\bprivate\b','public',path.read_text(encoding='utf-8-sig'))
        assert (OUT/'verify-final/candidate-src'/rel).read_text(encoding='utf-8-sig')==expected,rel
        actual=(package.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig')
        assert actual.replace(package.VERSION,'v0.33.0-vision-settings')==path.read_text(encoding='utf-8-sig'),rel
    classes=[line.split()[0] for line in (package.PACKAGE/'classes.txt').read_text().splitlines() if line.strip()]
    assert set(classes)=={'RealisticVisionMod','RVWallSurface','modlocales.vision.RVLocale','RVExplorationCarrier','RVKeybinds','modlocales.vision.RVLocaleMessages'}
    expected={'ViewportChecks':192,'EquivalenceChecks':68,'MaskChecks':16}
    checks=read('checks-01/checks.json')
    for c in checks:
        assert c['exit']==0
        if c['name']=='ViewportChecks':assert 'comparisons=192 failures=0' in (OUT/'checks-01/ViewportChecks.txt').read_text()
        else:assert c['passed']==expected[c['name']]
    settings=read('settings-checks/checks.json');assert [c['passed'] for c in settings]==[90,16,21] and all(c['exit']==0 for c in settings)
    exact=read('production/settings.json');assert len(exact)==2 and all(c['exit']==0 and c['passed']==18 for c in exact)
    native=read('verify-final/evidence/result.json');assert len(native['checks'])==32 and all(c['exact'] for c in native['checks']) and 'error' not in native
    assert read('verify-final/last-run.json')['exit']==0
    live=read('live-04/evidence/result.json');assert len(live['cases'])==8 and all(c['attackStarts']>0 and c['maxProjectiles']>0 for c in live['cases'])
    performance=read('trial-01/analysis.json');assert all(c['total'][1]['mean']<c['total'][0]['mean'] and c['total'][1]['p95']<=c['total'][0]['p95'] for c in performance['rows'])
    # Maxima are deliberately not hidden behind a pass flag. See reviewed limits.
    host=read('verify-final/build.json')['files']['pfe.swf'];assert run.sha(run.GAME/'pfe.swf')==host
    evidence=['inputs.json','production/manifest.json','production/settings.json','production/classes.txt','checks-01/checks.json',
              'checks-01/ViewportChecks.txt','checks-01/EquivalenceChecks.txt','checks-01/MaskChecks.txt','settings-checks/checks.json',
              'settings-checks/SettingsChecks.txt','settings-checks/SoftHarness.txt','settings-checks/SharedExplorationHarness.txt',
              'verify-final/build.json','verify-final/evidence/result.json','verify-final/last-run.json',
              'trial-01/build.json','trial-01/evidence/result.json','trial-01/analysis.json',
              'live-04/build.json','live-04/evidence/result.json','live-04/live-analysis.json']
    result={'status':'PASS','version':package.VERSION,'swf':manifest['swf'],'host':host,'count':471,
            'evidence':{rel:run.sha(OUT/rel) for rel in evidence},
            'reviewed_limits':['Paired means and P95 improve; isolated maxima still regress in some conditions.',
                               'Native sustained-fire classic update improves; current update is effectively flat.',
                               'Long frame intervals remain; no complete FPS, full-mod or multiplayer claim.']}
    run.save(OUT/'verified.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
