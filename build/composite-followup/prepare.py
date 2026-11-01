"""Freeze a new, non-production diagnostic, leaving combo-audit evidence intact."""
from pathlib import Path
import json, shutil, hashlib

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]; GAME=MOD.parents[1]
OUT=MOD/'build/composite-followup-output'
assert not OUT.exists(), 'Do not overwrite frozen evidence'
OUT.mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(MOD/'release/RealisticVisionMod.swf')=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
assert sha(GAME/'pfe.swf')=='ca94af17ed56b273138789661bf725538e5cb7c161cf282ab8c4aa582f88b9b0'
for variant in ('baseline','candidate'):
    shutil.copytree(MOD/'build/combo-audit-output/candidate/src',OUT/variant/'src')
frozen=OUT/'frozen'; frozen.mkdir()
shutil.copyfile(GAME/'pfe.swf',frozen/'pfe.swf')
for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
    c=line.split('|')
    if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):
        shutil.copytree(GAME/'mods'/c[0]/'release',frozen/'mods'/c[0]/'release')
(OUT/'inputs.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()},indent=2)+'\n')
s=(MOD/'build/combo-audit/run.py').read_text(encoding='utf-8').replace("build/combo-audit-output", "build/composite-followup-output")
s=s.replace("from air_test_process import HiddenProcess", "from air_test_process import HiddenProcess\nfrom cpu_sampler import OwnedCpuSampler")
s=s.replace("r.HiddenProcess=Recorded", """ def close(self):
  if hasattr(self,'cpu_sampler'):
   r.save(self.cpu_output,self.cpu_sampler.stop())
   del self.cpu_sampler
  super().close()
r.HiddenProcess=Recorded""")
s=s.replace("super().__init__(*a,**kw);r.save", "super().__init__(*a,**kw);self.cpu_output=run/'cpu-samples.json';self.cpu_sampler=OwnedCpuSampler(self._process,self.pid);self.cpu_sampler.start();r.save")
s=s.replace("owner='RealisticVision / combo-v4审核'", "owner='RealisticVision / 阴影交叉归因'")
s=s.replace(" r.runtime(folder)\n", " r.runtime(folder)\n shutil.copyfile(OUT/'frozen/pfe.swf',folder/'pfe.swf')\n")
s=s.replace("(OUT/reuse if reuse else GAME)/'mods'", "(OUT/reuse if reuse else OUT/'frozen')/'mods'")
# Diagnostic controls have no setter toggling: the normal attachment obeys
# d60HideFog directly. A fresh instance is constructed for every test window.
s=s.replace("public var d53SkipEffects:Boolean=false;", "public var d53SkipEffects:Boolean=false;public var d60SkipHide:Boolean=false;public var d60HideFog:Boolean=false;")
s=s.replace("  if plain:\n", "  s=s.replace('this.hideEnemies(w,loc,needFov);','if(!d60SkipHide)this.hideEnemies(w,loc,needFov);').replace('this.fogVis.visible = true;','this.fogVis.visible = !d60HideFog;')\n  if plain:\n")
(HERE/'run.py').write_text(s,encoding='utf-8')
s=(MOD/'build/combo-audit/SavedFireProbe.as').read_text(encoding='utf-8').replace('build/combo-audit-output','build/composite-followup-output')
s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']", "['off','normal','skip-hide','hide-fog','both','both','hide-fog','skip-hide','normal','off']")
s=s.replace("rv.cfgWallBright=false;", "rv.d60SkipHide=p.variant=='skip-hide'||p.variant=='both';rv.d60HideFog=p.variant=='hide-fog'||p.variant=='both';rv.cfgWallBright=false;")
s=s.replace("trace('D58 START '", "row.anchorStart={utcMs:new Date().time,timerMs:getTimer()};trace('D58 START '")
s=s.replace("var now:int=getTimer();", "if(age==WARMUP_COUNT-1)row.treeStart=displaySnapshot(w);var now:int=getTimer();")
s=s.replace("if(age>=WARMUP_COUNT&&last)", "if(age==WARMUP_COUNT)row.sampleStart={utcMs:new Date().time,timerMs:now};if(age>=WARMUP_COUNT&&last)")
s=s.replace("if(VISUAL||index==0)", "row.sampleEnd={utcMs:new Date().time,timerMs:getTimer()};row.treeEnd=displaySnapshot(w);if(VISUAL||index==0)")
s=s.replace("  private function undo():void {", (HERE/'DisplaySnapshot.as').read_text(encoding='utf-8')+'\n  private function undo():void {')
(HERE/'SavedFireProbe.as').write_text(s,encoding='utf-8')
s=(MOD/'build/combo-audit/native_check.py').read_text(encoding='utf-8').replace('camera-adaptive-quality-20261101','camera-unit-vis-20261101').replace('8321e4e7068672b2afa1fb17da3d8c21d9e95074a76354aece8b10894e025643','ca94af17ed56b273138789661bf725538e5cb7c161cf282ab8c4aa582f88b9b0').replace('build/combo-audit-output','build/composite-followup-output')
(HERE/'native_check.py').write_text(s,encoding='utf-8')
print('Frozen v4 and current CA94 host; generated new diagnostic')
