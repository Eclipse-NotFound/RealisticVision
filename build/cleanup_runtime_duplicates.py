"""Remove only hash-identical runtime copies, retaining a local restore source."""
from pathlib import Path
from collections import defaultdict,Counter
import argparse,hashlib,json,os,re,shutil,subprocess

MOD=Path(__file__).resolve().parents[1]
BUILD=MOD/'build'
RECORD=MOD/'state/cleanup-2026-10-16'
PREFERRED=['build/wall-performance-output/runtime-inputs',
           'build/wall-restore-output/game-rock','build/wall-options-output/game-rock',
           'build/motion-test-output/game']

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def path(rel):
    p=MOD/rel
    assert p.resolve().is_relative_to(BUILD.resolve()) and p.resolve()!=BUILD.resolve(),rel
    assert '.git' not in p.parts and not p.is_symlink(),rel
    return p

def snapshot(p):
    st=p.stat()
    return dict(size=st.st_size,sha256=sha(p),inode=st.st_ino,links=st.st_nlink,mtime_ns=st.st_mtime_ns)

def save(name,value):
    RECORD.mkdir(exist_ok=True)
    (RECORD/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def rank(p):
    rel=p.relative_to(MOD).as_posix()
    return (next((i for i,prefix in enumerate(PREFERRED) if rel.startswith(prefix+'/')),99),rel)

def plan():
    assert not (RECORD/'plan.json').exists(),'Do not overwrite a reviewed plan'
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=MOD).decode('utf-8').split('\0'))
    roots=sorted({p.parent for p in BUILD.rglob('pfe.swf')})
    groups=defaultdict(list);inventory={}
    for root in roots:
        files=[p for p in root.iterdir() if p.is_file() and
               re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name)]
        if (root/'Rooms').is_dir():files.extend(p for p in (root/'Rooms').rglob('*') if p.is_file())
        for p in files:
            rel=p.relative_to(MOD).as_posix();path(rel)
            if rel in tracked:continue
            item=snapshot(p);inventory[rel]=item
            groups[(p.relative_to(root).as_posix(),item['size'],item['sha256'])].append(p)
    remove=[];keepers={}
    for (_,size,digest),items in groups.items():
        if len(items)<2:continue
        items.sort(key=rank);source=items[0].relative_to(MOD).as_posix();keepers[source]=inventory[source]
        for p in items[1:]:
            rel=p.relative_to(MOD).as_posix()
            remove.append(dict(path=rel,source=source,**inventory[rel]))
    # Bytecode is reproducible; preserve every other non-asset file.
    for p in BUILD.rglob('*.pyc'):
        rel=p.relative_to(MOD).as_posix();path(rel)
        if '__pycache__' in p.parts and rel not in tracked:remove.append(dict(path=rel,source=None,**snapshot(p)))
    assert all(r['path'] not in tracked for r in remove)
    protected={p:sha(MOD/p) for p in tracked if p and (MOD/p).is_file()}
    for p in BUILD.rglob('*.as'):
        protected[p.relative_to(MOD).as_posix()]=sha(p)
    for p in BUILD.rglob('RealisticVisionMod*.swf'):
        protected[p.relative_to(MOD).as_posix()]=sha(p)
    for p in (MOD/'release').iterdir():
        if p.is_file():protected[p.relative_to(MOD).as_posix()]=sha(p)
    for p in list((BUILD/'backups').rglob('*'))+list((BUILD/'backup').rglob('*'))+list(BUILD.glob('*backup*.swf')):
        if p.is_file():protected[p.relative_to(MOD).as_posix()]=sha(p)
    removed_links=Counter(r['inode'] for r in remove)
    freed={r['inode']:r['size'] for r in remove if removed_links[r['inode']]==r['links']}
    result=dict(scope=str(MOD),removed=remove,keepers=keepers,protected=protected,
                logical_bytes=sum(r['size'] for r in remove),unique_file_bytes=sum(freed.values()),
                disk_free_before=shutil.disk_usage(BUILD).free)
    save('plan.json',result)
    print(json.dumps({k:result[k] for k in ['logical_bytes','unique_file_bytes','disk_free_before']},indent=2))
    print('Planned files:',len(remove),'retained restore sources:',len(keepers),'protected fingerprints:',len(protected))

def verify(data):
    for rel,digest in data['protected'].items():assert (MOD/rel).is_file() and sha(MOD/rel)==digest,'Protected file changed: '+rel
    for rel,item in data['keepers'].items():assert sha(path(rel))==item['sha256'],'Restore source changed: '+rel

def apply(data):
    assert not (RECORD/'receipt.json').exists(),'Do not overwrite cleanup history'
    targets={r['path'] for r in data['removed']}
    assert len(targets)==len(data['removed']) and not targets.intersection(data['keepers'])
    verify(data)
    # Validate every resolved destination and its bytes before any deletion.
    for row in data['removed']:
        p=path(row['path']);st=p.stat()
        assert st.st_size==row['size'] and st.st_mtime_ns==row['mtime_ns'] and st.st_ino==row['inode'],'File drift: '+str(p)
        assert sha(p)==row['sha256'],'Content drift: '+str(p)
        if row['source']:assert data['keepers'][row['source']]['sha256']==row['sha256']
    done=[]
    try:
        for row in data['removed']:
            p=path(row['path']);p.unlink();done.append(row['path'])
        # Remove only now-empty directories. Never recursively delete a tree.
        parents={path(rel).parent for rel in done}
        for folder in sorted(parents,key=lambda p:len(p.parts),reverse=True):
            while folder!=BUILD and folder.is_relative_to(BUILD):
                path(folder.relative_to(MOD).as_posix())
                try:folder.rmdir()
                except OSError:break
                folder=folder.parent
        verify(data)
        assert all(not path(row['path']).exists() for row in data['removed'])
        save('receipt.json',dict(status='PASS',files_removed=len(done),logical_bytes=data['logical_bytes'],
            unique_file_bytes=data['unique_file_bytes'],disk_free_after=shutil.disk_usage(BUILD).free,
            restore_sources=len(data['keepers']),protected_fingerprints=len(data['protected'])))
    except BaseException as error:
        save('partial.json',dict(status='PARTIAL',removed=done,error=repr(error)));raise
    print('CLEANUP PASS',len(done),'files;',data['unique_file_bytes'],'unique file bytes reclaimed')

def restore(data,prefix):
    restored=0
    for row in data['removed']:
        if not row['source'] or not row['path'].startswith(prefix):continue
        dest=path(row['path']);source=path(row['source'])
        if dest.exists():assert sha(dest)==row['sha256'];continue
        assert sha(source)==row['sha256'];dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as output,source.open('rb') as input_:shutil.copyfileobj(input_,output)
        assert sha(dest)==row['sha256'];restored+=1
    print('Restored runtime copies:',restored)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply','verify','restore']);p.add_argument('--prefix',default='build/');a=p.parse_args()
    if a.action=='plan':plan()
    else:
        data=json.loads((RECORD/'plan.json').read_text(encoding='utf-8'));assert data['scope']==str(MOD)
        if a.action=='apply':apply(data)
        elif a.action=='restore':restore(data,a.prefix)
        else:verify(data);print('Protected files and restore sources match')
