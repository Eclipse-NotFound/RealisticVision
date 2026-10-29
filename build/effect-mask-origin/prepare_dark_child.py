"""D56: suppress only an owned zero-output Bitmap child, not native Part.vis."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/dark-child/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''         record.pass=this.worldPass;
         var shape:Shape=record.shape as Shape;'''
new='''         record.pass=this.worldPass;
         var container:DisplayObjectContainer=visual as DisplayObjectContainer;
         var darkChild:Bitmap=null;
         if(drawDark && container!=null && container.numChildren==1 && container.getChildAt(0) is Bitmap && !this.worldVisualHasFilters(visual))
            darkChild=container.getChildAt(0) as Bitmap;
         if(record.darkChild!=null && record.darkChild!==darkChild)this.restoreDarkChild(record);
         if(darkChild!=null){
            if(record.darkChild==null){record.darkChild=darkChild;record.childVisible=darkChild.visible;}
            if(darkChild.visible)darkChild.visible=false;
            // D56_DARK_CHILD
         }
         var shape:Shape=record.shape as Shape;'''
assert s.count(old)==1;s=s.replace(old,new)
where='      private function releaseWorldVisual('
method='''      private function restoreDarkChild(record:Object):void
      {
         if(record.darkChild!=null){
            Bitmap(record.darkChild).visible=record.childVisible;
            record.darkChild=null;
         }
      }

'''
assert s.count(where)==1;s=s.replace(where,method+where)
old='''      private function releaseWorldVisual(visual:DisplayObject,record:Object):void
      {'''
assert s.count(old)==1;s=s.replace(old,old+'\n         this.restoreDarkChild(record);')
p.write_text(s,encoding='utf-8',newline='\n')
