from pathlib import Path
import difflib,subprocess,re
import package as p
MOD,OUT=p.MOD,p.OUT
if __name__=='__main__':
 before=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig').splitlines(True)
 after=(p.PACKAGE/'src/RealisticVisionMod.as').read_text(encoding='utf-8-sig').splitlines(True)
 target=MOD/'src/RealisticVisionMod.as';original=target.read_text(encoding='utf-8-sig');merged=original
 # The development tree alone routes display writes through its unpublished
 # authority adapter. Keep that route while merging the verified production delta.
 def adapter(text):
  text=text.replace('if((needFov || this.frameCount % 3 == 0)', 'if((this.authorityView.active || needFov || this.frameCount % 3 == 0)')
  for obj,field,value in [('u.vis','cacheAsBitmap','true'),('u.vis','mask','s2'),('u.hpbar','cacheAsBitmap','true'),('u.hpbar','mask','s3'),('c','visible','false'),('c','visible','true')]:
   text=re.sub(re.escape(obj)+r'\.'+field+r'\s*=\s*'+value+r';','this.authorityView.write('+obj+',"'+field+'",'+value+(',true' if obj=='c' and value=='true' else '')+');',text)
  text=text.replace('visual.cacheAsBitmap=raster.fullyDark?record.cache:true;visual.mask=shape;','this.authorityView.write(visual,"cacheAsBitmap",raster.fullyDark?record.cache:true);this.authorityView.write(visual,"mask",shape);')
  text=text.replace('visual.mask=record.baseMask;visual.cacheAsBitmap=record.cache;','this.authorityView.write(visual,"mask",record.baseMask,true);this.authorityView.write(visual,"cacheAsBitmap",record.cache,true);')
  return text
 hunks=list(difflib.unified_diff(before,after,n=1))[2:];old=[];new=[]
 def merge_hunk():
  global merged
  if not old:return
  a=adapter(''.join(old));b=adapter(''.join(new));count=merged.count(a)
  repeated_reset=a=='         this.classicCells=null;\n         this.restoreWeaponVisuals();\n'
  assert count==1 or (repeated_reset and 1<=count<=3),('development anchor mismatch',count,a[:450])
  merged=merged.replace(a,b,1)
 for line in hunks:
  if line.startswith('@@'):
   merge_hunk();old=[];new=[]
  else:
   if line[0] in ' -':old.append(line[1:])
   if line[0] in ' +':new.append(line[1:])
 merge_hunk()
 # applyMask now attaches and records display writes after every refresh call,
 # including cache hits; refreshMask must remain independent of a unit.
 obsolete='            if(this.authorityView.active) this.rebindAuthorityMask(w,u,rec);\n'
 assert merged.count(obsolete)==1;merged=merged.replace(obsolete,'',1)
 patch=OUT/'development.patch';patch.write_text(''.join(difflib.unified_diff(original.splitlines(True),merged.splitlines(True),'a/src/RealisticVisionMod.as','b/src/RealisticVisionMod.as',n=3)),encoding='utf-8')
 subprocess.run(['git','apply','--check',str(patch)],cwd=MOD,check=True)
 subprocess.run(['git','apply',str(patch)],cwd=MOD,check=True)
 folder=OUT/'development-check';folder.mkdir(exist_ok=False)
 with p.run.Registration(owner='RealisticVision / D42 开发树',purpose='syntax only; authority never deployed',run_dir=folder,evidence=folder/'result.json',wait=300) as rec:
  p.run.runner.compile(MOD/'src/RealisticVisionMod.as',folder/'RealisticVisionMod.swf',[MOD/'src'],stubs=True)
  p.run.save(folder/'result.json',{'compiled':True,'deployed':False});rec.outcome='passed'
