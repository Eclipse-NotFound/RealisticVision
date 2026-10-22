"""Exact moving-viewport regression against the D38 production helper."""
from pathlib import Path
import argparse,importlib.util,re
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/long-frame-output'
spec=importlib.util.spec_from_file_location('d39trace',HERE/'trace.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);r=t.r
def run(name,candidate):
 folder=OUT/name;assert not folder.exists();folder.mkdir()
 with r.Registration(owner='RealisticVision / D39 视口缓存回归',purpose=name,run_dir=folder,evidence=folder/'result.json') as rec:
  src=folder/'src';r.public(OUT/candidate/'src',src)
  p=src/'BaselineWallSurface.as';p.write_text(re.sub(r'\bprivate\b','public',(OUT/'candidate-00/src/RVWallSurface.as').read_text(encoding='utf-8-sig')).replace('RVWallSurface','BaselineWallSurface'),encoding='utf-8')
  s=(MOD/'build/wall-performance/EquivalenceChecks.as').read_text(encoding='utf-8')
  s=s.replace('var a:BitmapData=new BitmapData(600,480,false,0xffffff)', '''for each(var fieldName:String in ["sampleStarts","samplePixels","sampleAlphas","sampleCells"])
            if(String(oldSurface[fieldName])!=String(surface[fieldName]))throw new Error("sample table mismatch "+fieldName+" "+label);
         var a:BitmapData=new BitmapData(600,480,false,0xffffff)''')
  at=s.index('         for each(var zoom:Number')
  extra='''         for each(var enabled:Boolean in [false,true]){
            bright=enabled;known=true;intensity=.35;
            for(var step:int=0;step<80;step++){
               var vx:int=step%3,vy:int=int(step/3)%3;
               if(step%7==0){tiles[3+3*10].opac=step%14==0?0:1;tiles[4+2*10].zForm=step%3;}
               if(step%9==0)pixels.fillRect(new Rectangle(140,80,10,15),step%18==0?0:0x80ffffff);
               compare("moving cache, tile/alpha change "+enabled+"/"+step,new Rectangle(vx,vy,7+step%2,5+step%2),[.658333,.75,1,1.25][step%4]);
            }
         }
         bright=false;known=true;compare("before interrupted geometry scan");
         tiles[3+3*10].opac=tiles[3+3*10].opac?0:1;
         var originalGet:Function=loc.getTile;
         loc.getTile=function(x:int,y:int):Object{if(x==6&&y==6)throw new Error("expected fixture interruption");return originalGet(x,y);};
         var interrupted:int=0;
         for each(var tested:* in [oldSurface,surface])try{
            tested.update(tested===surface?fog:oldFog,tested===surface?base:oldBase,{visFront:front},loc,new Rectangle(0,0,10,8),function(x:int,y:int):Boolean{return true;},function(...args):Number{return .35;},false);
         }catch(expected:Error){interrupted++;}
         if(interrupted!=2)throw new Error("missing interrupted scans");
         loc.getTile=originalGet;compare("geometry retry after interrupted scan");
'''
  s=s[:at]+extra+s[at:];(src/'EquivalenceChecks.as').write_text(s,encoding='utf-8')
  r.runner.compile(src/'EquivalenceChecks.as',folder/'EquivalenceChecks.swf',[src])
  code,log=r.air(folder,'EquivalenceChecks.swf',rec,180)
  (folder/'checks.log').write_text(log,encoding='utf-8');print('\n'.join(log.splitlines()[-8:]),flush=True)
  r.save(folder/'result.json',{'candidate':candidate,'exit':code,'summary':log.splitlines()[-8:]})
  assert code==0 and 'failed=0' in log;rec.outcome='passed'
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');a.add_argument('--candidate',default='candidate-02');x=a.parse_args();run(x.name,x.candidate)
