"""Apply only the verified production delta; retain the separate authority WIP."""
import difflib,json,subprocess
import package
r=package.run;MOD=package.MOD;OUT=package.OUT
proof=json.loads((OUT/'verified.json').read_text())
assert proof['status']=='PASS' and proof['swf']==r.sha(package.PACKAGE/'RealisticVisionMod.swf')
before=MOD/'build/effect-load-v3-output/production-final/src/RealisticVisionMod.as'
after=package.PACKAGE/'src/RealisticVisionMod.as';target=MOD/'src/RealisticVisionMod.as'
assert r.sha(before)=='563c3833fd58429c4a00d251f17ad4c26e916213af4259d3f066bfbf302af74e'
def development(text):
    # HEAD has an unpublished authority recorder. An active lease must still
    # receive every original write, including nativeOnClear restoration.
    # The tested production file has no recorder and is never changed here.
    conditions=['!u.vis.cacheAsBitmap','u.vis.mask!==s2','!u.hpbar.cacheAsBitmap','u.hpbar.mask!==s3',
        'u.vis.mask != null','u.vis.cacheAsBitmap','u.hpbar.mask != null','u.hpbar.cacheAsBitmap',
        'u.vis.visible','u.hpbar.visible','!u.vis.visible','visual.visible','!visual.cacheAsBitmap',
        'visual.mask!==shape','wpn.vis.visible != visB','visual.cacheAsBitmap!==useCache']
    for condition in conditions:text=text.replace('if('+condition+')','if(this.authorityView.active || '+condition+')')
    writes={
        'u.vis.cacheAsBitmap=true;':'this.authorityView.write(u.vis,"cacheAsBitmap",true);',
        'u.vis.mask=s2;':'this.authorityView.write(u.vis,"mask",s2);',
        'u.hpbar.cacheAsBitmap=true;':'this.authorityView.write(u.hpbar,"cacheAsBitmap",true);',
        'u.hpbar.mask=s3;':'this.authorityView.write(u.hpbar,"mask",s3);',
        'u.vis.mask = null;':'this.authorityView.write(u.vis,"mask",null,true);',
        'u.vis.cacheAsBitmap = false;':'this.authorityView.write(u.vis,"cacheAsBitmap",false,true);',
        'u.hpbar.mask = null;':'this.authorityView.write(u.hpbar,"mask",null,true);',
        'u.hpbar.cacheAsBitmap = false;':'this.authorityView.write(u.hpbar,"cacheAsBitmap",false,true);',
        'u.vis.visible = false;':'this.authorityView.write(u.vis,"visible",false);',
        'u.hpbar.visible = false;':'this.authorityView.write(u.hpbar,"visible",false);',
        'u.vis.visible = true;':'this.authorityView.write(u.vis,"visible",true,true);',
        'u.prior = 0;':'this.authorityView.write(u,"prior",0);',
        'u.prior = 1;':'this.authorityView.write(u,"prior",1,true);',
        'visual.visible=false;':'this.authorityView.write(visual,"visible",false);',
        'visual.mask=record.mask;':'this.authorityView.write(visual,"mask",record.mask,true);',
        'visual.cacheAsBitmap=record.cache;':'this.authorityView.write(visual,"cacheAsBitmap",record.cache,true);',
        'visual.cacheAsBitmap=true;':'this.authorityView.write(visual,"cacheAsBitmap",true);',
        'visual.mask=shape;':'this.authorityView.write(visual,"mask",shape);',
        'wpn.vis.mask = null;':'this.authorityView.write(wpn.vis,"mask",null,true);',
        'wpn.vis.cacheAsBitmap = false;':'this.authorityView.write(wpn.vis,"cacheAsBitmap",false,true);',
        'wpn.vis.visible = visB;':'this.authorityView.write(wpn.vis,"visible",visB,visB);',
        'visual.cacheAsBitmap=raster.fullyDark?record.cache:true;':'this.authorityView.write(visual,"cacheAsBitmap",raster.fullyDark?record.cache:true);',
        'visual.cacheAsBitmap=useCache;':'this.authorityView.write(visual,"cacheAsBitmap",useCache);'
    }
    for old,new in writes.items():text=text.replace(old,new)
    return text
patch=''.join(difflib.unified_diff(development(before.read_text(encoding='utf-8-sig')).splitlines(True),development(after.read_text(encoding='utf-8-sig')).splitlines(True),fromfile='a/src/RealisticVisionMod.as',tofile='b/src/RealisticVisionMod.as'))
path=OUT/'development-source.patch';path.write_text(patch,encoding='utf-8',newline='\n')
subprocess.run(['git','apply','--check','--ignore-space-change',str(path)],cwd=MOD,check=True)
original=r.sha(target)
subprocess.run(['git','apply','--ignore-space-change',str(path)],cwd=MOD,check=True)
r.save(OUT/'source-merge.json',{'before':original,'after':r.sha(target),'production_source':r.sha(after),'patch':r.sha(path),'scope':'D43 to D44 delta adapted to existing HEAD recorder. Active authority keeps every original write; production remains the separately tested six-class package.'})
print('Verified production delta merged into development source')
