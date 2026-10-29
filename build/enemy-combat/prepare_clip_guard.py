from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];O=M/'build/enemy-combat-output';D=O/'candidates/unit_clip_guard/src'
assert not D.exists();shutil.copytree(O/'candidates/unit_clip_refresh/src',D)
p=D/'RealisticVisionMod.as';s=p.read_text()
old='''         if(matrix.a==1 && matrix.d==1 && matrix.b==0 && matrix.c==0'''
new='''         // Rotated native weapon caches differ at the sampling boundary;
         // retain their original full mask until that path is proven equivalent.
         if(visual.rotation==0 && matrix.a==1 && matrix.d==1 && matrix.b==0 && matrix.c==0'''
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
