from pathlib import Path
import difflib,subprocess
import package as p
MOD,OUT=p.MOD,p.OUT
if __name__=='__main__':
 before=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig').splitlines(True)
 after=(p.PACKAGE/'src/RealisticVisionMod.as').read_text(encoding='utf-8-sig').splitlines(True)
 patch=OUT/'development.patch';patch.write_text(''.join(difflib.unified_diff(before,after,'a/src/RealisticVisionMod.as','b/src/RealisticVisionMod.as',n=1)),encoding='utf-8')
 subprocess.run(['git','apply','--check',str(patch)],cwd=MOD,check=True)
 subprocess.run(['git','apply',str(patch)],cwd=MOD,check=True)
 folder=OUT/'development-check';folder.mkdir(exist_ok=False)
 with p.run.Registration(owner='RealisticVision / D43 开发树',purpose='syntax only; production excludes authority',run_dir=folder,evidence=folder/'result.json',wait=300) as rec:
  p.run.runner.compile(MOD/'src/RealisticVisionMod.as',folder/'RealisticVisionMod.swf',[MOD/'src'],stubs=True)
  p.run.save(folder/'result.json',{'compiled':True,'deployed':False});rec.outcome='passed'
