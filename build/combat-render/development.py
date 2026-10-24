"""Syntax-check the development integration; this binary is never released."""
import package
r=package.run;MOD=package.MOD;OUT=package.OUT
folder=OUT/'development-check';assert not folder.exists();folder.mkdir()
sources={p.relative_to(MOD/'src').as_posix():r.sha(p) for p in (MOD/'src').rglob('*.as')}
with r.Registration(owner='RealisticVision / D44 开发线语法',purpose='Retain unpublished authority recorder; compile only',run_dir=folder,evidence=folder/'build.json',resource='game',wait=900) as rec:
    r.runner.compile(MOD/'src/RealisticVisionMod.as',folder/'DevelopmentOnly.swf',[MOD/'src'],stubs=True)
    assert all(r.sha(MOD/'src'/p)==digest for p,digest in sources.items()),'Source changed during compile'
    r.save(folder/'build.json',{'status':'PASS','sources':sources,'scope':'Compile only; active authority runtime remains separate, not included in release','binary':r.sha(folder/'DevelopmentOnly.swf')})
    rec.outcome='passed'
print('Development syntax PASS; production still uses production-final2')
