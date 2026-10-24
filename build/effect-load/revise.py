from pathlib import Path
import shutil,json,subprocess
MOD=Path(__file__).resolve().parents[2];OLD=MOD/'build/effect-load-output';OUT=MOD/'build/effect-load-v2-output';HERE=MOD/'build/effect-load-v2'
assert not OUT.exists() and not HERE.exists();OUT.mkdir();HERE.mkdir()
for name in ['baseline','candidate']:shutil.copytree(OLD/name,OUT/name)
shutil.copyfile(OLD/'inputs.json',OUT/'inputs.json')
for f in (MOD/'build/effect-load').iterdir():
 if f.is_file() and f.name not in ['setup.py','candidate.py','revise.py','finalize.py','closeout.py','review.py']:
  s=f.read_text(encoding='utf-8').replace('effect-load-output','effect-load-v2-output')
  (HERE/f.name).write_text(s,encoding='utf-8',newline='\n')
# The package adapter derives its source root through a generated wrapper.
p=HERE/'package.py';s=p.read_text().replace(".replace('v0.33.8-effect-visibility'", ".replace('v0.33.8-effect-visibility'");p.write_text(s,encoding='utf-8')
p=OUT/'candidate/src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
s=s.replace('         var uniform:int=this.worldUniform(x0,y0,x1,y1);','''         var key:String=x0+","+y0+","+x1+","+y1;
         var raster:Object=this.worldMasks[key];
         var uniform:int=raster!=null && raster.lastFov==this.fovVersion?3:this.worldUniform(x0,y0,x1,y1);''')
s=s.replace('         var key:String=x0+","+y0+","+x1+","+y1;\n         var raster:Object=uniform==1?this.worldDark:this.worldMasks[key];','         if(uniform==1)raster=this.worldDark;')
begin=s.index('         var combined:int=0;',s.index('private function worldUniform'))
end=s.index('         if(combined==2)',begin)
s=s[:begin]+'''         var area:Rectangle=new Rectangle(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB);
         var combined:int=2;
         if(this.cfgMode=="classic"){
            this.classicLogicRegion(new Rectangle(x0,y0,x1-x0+1,y1-y0+1));
            // Native alpha hit testing answers "any dark pixel?" directly.
            // Avoid an AS loop and temporary bitmap for every queried tile.
            if(this.fogCache.hitTest(this.fogPoint,MASK_LIT_A,area))return 3;
         } else {
            if(!this.currentSight.hitTest(this.fogPoint,1,area))return 1;
            for(var y:int=y0;y<=y1;y++)for(var x:int=x0;x<=x1;x++){
               var index:int=x+y*this.spaceX,kind:int=int(this.worldCellKinds[index]);
               if(kind==0){
                  this.worldCellPixels.copyPixels(this.currentSight,new Rectangle(FOG_PAD+x*MASK_SUB,FOG_PAD+y*MASK_SUB,MASK_SUB,MASK_SUB),this.fogPoint);
                  kind=this.worldCellPixels.getColorBoundsRect(0xff000000,0xff000000,false).isEmpty()?2:3;
                  this.worldCellKinds[index]=kind;
               }
               if(kind==3)return 3;
            }
         }
'''+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
# Undo only our unapplied-to-production development delta before merging v2.
subprocess.run(['git','apply','--reverse','--check',str(OLD/'development.patch')],cwd=MOD,check=True)
subprocess.run(['git','apply','--reverse',str(OLD/'development.patch')],cwd=MOD,check=True)
(OLD/'performance-decision.json').write_text(json.dumps({'accepted':False,'reason':'两轮classic完整帧均值回退（83.383→87.688、79.964→81.992ms），不部署；保留全部证据。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v1 preserved and rejected; v2 prepared')
