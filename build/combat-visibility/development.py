"""Compile development source for syntax only; never install this artifact."""
import package as p

def main():
    folder=p.OUT/'development-check'
    with p.run.Registration(owner='RealisticVision / D36 开发源编译',purpose='仅语法检查，含未发布authority，不部署',run_dir=folder,evidence=folder/'result.json',wait=300) as record:
        folder.mkdir(exist_ok=False)
        source=p.MOD/'src'
        p.run.runner.compile(source/'RealisticVisionMod.as',folder/'development-only.swf',[source],stubs=True)
        p.run.save(folder/'result.json',{'status':'PASS','scope':'Compile only; authority runtime not tested; not for deployment','sources':{f.relative_to(source).as_posix():p.run.sha(f) for f in source.rglob('*.as')}})
        record.outcome='passed'
        record.note='开发源编译通过；生产使用独立冻结六类包'
    print('DEVELOPMENT COMPILE PASS')

if __name__=='__main__':main()
