"""Port only D36 changes into development source; keep authority work isolated."""
from pathlib import Path
import prepare,optimize
MOD=Path(__file__).resolve().parents[2]
p=MOD/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig')
assert 'private var weaponVisuals:' not in s
s=optimize.transform(prepare.transform(s))
# Development-only authority bookkeeping remains in that source branch. It is
# absent from the independently frozen and verified production snapshot.
begin=s.index('      private function applyUnitWeapons(');end=s.index('      private function setWeaponVis(',begin)
part=s[begin:end]
for old,new in [
 ('visual.visible=false;','this.authorityView.write(visual,"visible",false);'),
 ('visual.visible=record.visible;','this.authorityView.write(visual,"visible",record.visible,true);'),
 ('visual.mask=record.mask;','this.authorityView.write(visual,"mask",record.mask,true);'),
 ('visual.cacheAsBitmap=record.cache;','this.authorityView.write(visual,"cacheAsBitmap",record.cache,true);'),
 ('visual.cacheAsBitmap=true;visual.mask=shape;','this.authorityView.write(visual,"cacheAsBitmap",true);this.authorityView.write(visual,"mask",shape);')]:
 part=part.replace(old,new)
s=s[:begin]+part+s[end:]
p.write_text(s,encoding='utf-8')
