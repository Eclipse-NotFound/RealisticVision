"""Archive compact evidence, without game assets, private saves or binaries."""
from pathlib import Path
import hashlib,json
from run import MOD,OUT

DEST=MOD/'knowledge/experiments/frame-performance-v0322-20261019'

def archive():
    DEST.mkdir(parents=True,exist_ok=True)
    files=[]
    for name in ['inputs.json','analysis-initial.json','analysis-final.json','window-01-preflight.json','window-01-not-started.json']:
        if (OUT/name).exists():files.append(OUT/name)
    for name in ['profile-03','trial-01','trial-02','trial-03','trial-04','large-final-verify','live-final',
                 'large-profile-01','large-view-verify','large-view-profile',
                 'large-sparse-profile','large-sparse-verify','large-sparse-trial',
                 'final-large-verify','final-large-profile','final-large-trial','final-live','final-small-trial']:
        for rel in ['evidence/result.json','last-run.json','build-inputs.json','launch-state.json','environment.json']:
            p=OUT/name/rel
            if p.exists():files.append(p)
    for name in ['checks-04','checks-05','checks-final']:
        for h in ['MaskChecks','SightChecks','SoftHarness','SharedExplorationHarness']:
            p=OUT/name/(h+'.txt')
            if p.exists():files.append(p)
    for name in ['viewport-checks-02','viewport-checks-03']:
        for rel in ['ViewportChecks.txt','last-run.json']:
            p=OUT/name/rel
            if p.exists():files.append(p)
    for rel in ['source-manifest.json','classes.json','options/result.json',
                'options/process-1.txt','options/process-2.txt','options/runtime.txt']:
        p=OUT/'production'/rel
        if p.exists():files.append(p)
    manifest=[]
    for source in files:
        rel=source.relative_to(OUT);dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        original=source.read_bytes()
        if source.suffix=='.json':dest.write_text(json.dumps(json.loads(original.decode('utf-8-sig')),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        else:dest.write_text('\n'.join(line for line in original.decode('utf-8-sig').splitlines() if line.strip())+'\n',encoding='utf-8')
        manifest.append({'source':str(source.relative_to(MOD)),'source_sha256':hashlib.sha256(original).hexdigest(),
                         'archive':str(rel),'archive_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    (DEST/'archive-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Archived',len(manifest),'evidence files to',DEST)

if __name__=='__main__':archive()
