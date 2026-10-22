"""D38 uses D37 as the exact baseline and retains corrected parent capture."""
from pathlib import Path
import re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
source=(MOD/'build/native-performance/measure.py').read_text(encoding='utf-8')
source=source[:source.index("if __name__=='__main__':")]
source=source.replace('native-performance-output','followup-performance-output').replace("MOD/'build/combat-visibility-output/production/src'","MOD/'build/native-performance-output/production/src'")
source=source.replace("if candidate not in ['candidate-01','candidate-02','candidate-03','candidate-04'] and verify:","if verify:")
exec(compile(source,str(HERE/'measure.py'),'exec'),globals())

def public(source,dest,profile=False):
 for p in source.rglob('*.as'):
  q=dest/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True)
  s=re.sub(r'\bprivate\b','public',p.read_text(encoding='utf-8-sig'))
  if profile:
   methods=['prepareOcclusion','computeFov','applyVision','applyVisionClassic','prepareClassicCells','paintClassicDisplay','classicLogicRegion','joinClassicWalls','updateWallSurface','hideEnemies','applyMask','enemyState','fillFogCache','refreshWallField'] if p.name=='RealisticVisionMod.as' else ['update','updateContour','buildContourClip','rebuildFaces','rebuildSamples','rebuildSupport'] if p.name=='RVWallSurface.as' else []
   if methods:s=inv.r.fp.instrument(s,methods)
  q.write_text(s,encoding='utf-8',newline='\n')
inv.r.public=public
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run','analyze']);a.add_argument('name');a.add_argument('--candidate',default='candidate-00');a.add_argument('--verify',action='store_true');a.add_argument('--wide',action='store_true');a.add_argument('--profile',action='store_true');a.add_argument('--live',action='store_true');a.add_argument('--native',action='store_true');x=a.parse_args()
 if x.action=='build':build(x.name,x.candidate,x.verify,x.profile,x.live,x.native,x.wide)
 elif x.action=='run':run(x.name)
 else:inv.analyze(x.name)
