from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
if __name__=='__main__':
 dest=OUT/'candidate-08/src';assert not dest.exists();shutil.copytree(OUT/'candidate-07/src',dest)
 p=dest/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig')
 base=(MOD/'build/combat-visibility-output/production/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
 start='      private function updateWallSurface(';end='      /** Read light'
 s=s[:s.index(start)]+base[base.index(start):base.index(end)]+s[s.index(end):]
 p.write_text(s,encoding='utf-8')
