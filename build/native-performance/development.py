"""Apply only D37 production changes to the separate development tree."""
from pathlib import Path
import difflib,subprocess
import package as p
MOD,OUT=p.MOD,p.OUT
if __name__=='__main__':
 baseline=MOD/'build/combat-visibility-output/production/src';chosen=p.PACKAGE/'src'
 parts=[]
 for name in ['RealisticVisionMod.as','RVWallSurface.as']:
  before=(baseline/name).read_text(encoding='utf-8-sig').splitlines(True);after=(chosen/name).read_text(encoding='utf-8-sig').splitlines(True)
  parts.extend(difflib.unified_diff(before,after,'a/src/'+name,'b/src/'+name))
 patch=OUT/'development.patch';patch.write_text(''.join(parts),encoding='utf-8')
 subprocess.run(['git','apply','--check',str(patch)],cwd=MOD,check=True)
 subprocess.run(['git','apply',str(patch)],cwd=MOD,check=True)
 folder=OUT/'development-check';folder.mkdir(exist_ok=False)
 with p.run.Registration(owner='RealisticVision / D37 开发源编译',purpose='仅语法检查；未发布authority不安装',run_dir=folder,evidence=folder/'result.json') as rec:
  p.run.runner.compile(MOD/'src/RealisticVisionMod.as',folder/'RealisticVisionMod.swf',[MOD/'src'],stubs=True)
  p.run.save(folder/'result.json',{'compiled':True,'deployed':False,'includes_unpublished_authority':True});rec.outcome='passed'
