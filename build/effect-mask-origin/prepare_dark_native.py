"""Limit the display-only suppression to native Part.initBlit children."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
dest=OUT/'candidates/dark-native/src';assert not dest.exists();shutil.copytree(OUT/'candidates/dark-child/src',dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='kind=name=="fe.graph::Part" || name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet";'
new='kind=name=="fe.graph::Part" ? 2 : (name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet");'
assert s.count(old)==1;s=s.replace(old,new)
old='if(kind && obj.vis != null)this.applyWorldVisual(obj.vis);'
new='if(kind && obj.vis != null)this.applyWorldVisual(obj.vis,kind===2 && Object(obj)["blitData"]!=null);'
assert s.count(old)==1;s=s.replace(old,new)
old='private function applyWorldVisual(visual:DisplayObject):void'
assert s.count(old)==1;s=s.replace(old,'private function applyWorldVisual(visual:DisplayObject, nativeBlit:Boolean=false):void')
s=s.replace('if(drawDark && container!=null && container.numChildren==1','if(nativeBlit && drawDark && container!=null && container.numChildren==1')
p.write_text(s,encoding='utf-8',newline='\n')
