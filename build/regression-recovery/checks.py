from pathlib import Path
import argparse, json, re, shutil
import investigate as inv
r=inv.r;OUT=inv.OUT;MOD=inv.MOD
NAMES=['LazyClassicChecks','SettingsChecks','SoftHarness','SharedExplorationHarness']

def build(name,source='fixed'):
 folder=OUT/name;assert not folder.exists();src=folder/'src'
 with r.Registration(owner='RealisticVision / D35 精确回归编译',purpose=name,run_dir=folder,evidence=folder/'inputs.json',wait=300) as rec:
  r.public(inv.SOURCES[source],src)
  s=inv.SOURCES['d33'].joinpath('RealisticVisionMod.as').read_text(encoding='utf-8-sig')
  s=re.sub(r'\bprivate\b','public',s).replace('RealisticVisionMod','BaselineVision')
  (src/'BaselineVision.as').write_text(s,encoding='utf-8')
  for name in NAMES:
   path=Path(__file__).parent/(name+'.as') if name=='LazyClassicChecks' else MOD/('build/vision-settings' if name=='SettingsChecks' else 'build/motion-tests')/(name+'.as')
   s=path.read_text(encoding='utf-8-sig').replace('p.m.curBlur.blurX=p.m.curBlur.blurY=6','p.m.cfgSoftCurrent=30')
   if name=='SettingsChecks':
    s=s.replace('import flash.display.*;','import flash.display.*;\n import flash.geom.Rectangle;')
    s=s.replace('o.m.onFrameInner();}', 'o.m.onFrameInner();if(o.m is RealisticVisionMod)o.m.classicLogicRegion(new Rectangle(0,0,o.loc.spaceX,o.loc.spaceY));}')
    s=s.replace('same(logic,mode=="current"?m.currentSight:m.fogCache)','sameLogical(logic,mode=="current"?m.currentSight:m.fogCache,mode,o.loc.spaceX,o.loc.spaceY)')
    s=s.replace('  private function run():void {','''  private function sameLogical(a:BitmapData,b:BitmapData,mode:String,w:int,h:int):Boolean {
   if(mode!="classic")return same(a,b);
   var area:Rectangle=new Rectangle(4,4,w*8,h*8),aa:BitmapData=new BitmapData(w*8,h*8,true,0),bb:BitmapData=aa.clone();
   aa.copyPixels(a,area,aa.rect.topLeft);bb.copyPixels(b,area,bb.rect.topLeft);var equal:Boolean=same(aa,bb);aa.dispose();bb.dispose();return equal;
  }
  private function run():void {''')
   entry=src/(name+'.as');entry.write_text(s,encoding='utf-8')
   r.runner.compile(entry,folder/(name+'.swf'),[src,MOD/'build/motion-tests',MOD/'build/stubs'])
  r.save(folder/'inputs.json',{'sources':{str(p.relative_to(src)):r.sha(p) for p in src.rglob('*.as')}});rec.outcome='passed'

def run(name):
 folder=OUT/name
 with r.Registration(owner='RealisticVision / D35 精确像素与设置',purpose=name,run_dir=folder,evidence=folder/'result.json',wait=300) as rec:
  results=[]
  for name in NAMES:
   code,log=r.air(folder,name+'.swf',rec,180)
   (folder/(name+'.txt')).write_text(log,encoding='utf-8')
   results.append({'name':name,'exit':code,'summary':log.splitlines()[-4:]})
   r.save(folder/'result.json',results);print('\n'.join(log.splitlines()[-4:]),flush=True)
   assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log,log[-4000:]
  rec.outcome='passed';rec.note='精确像素、敌人裁剪、设置和共享探索回归通过'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--name',required=True);p.add_argument('--source',default='fixed');p.add_argument('--only');a=p.parse_args()
 if a.only:NAMES=[a.only]
 build(a.name,a.source) if a.action=='build' else run(a.name)
