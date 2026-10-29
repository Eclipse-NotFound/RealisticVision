from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];O=M/'build/enemy-combat-output';D=O/'candidates/unit_guard_final/src'
assert not D.exists();shutil.copytree(O/'candidates/unit_clip_guard/src',D)
p=D/'RealisticVisionMod.as';s=p.read_text().replace('''         } else {
            for each(var draw:Object in [rec.bodyDraw,rec.barDraw])''','''         } else if(rec.bodyDraw!=null || rec.barDraw!=null){
            for each(var draw:Object in [rec.bodyDraw,rec.barDraw])''')
s=s.replace('''         for each(var draw:Object in [rec.bodyDraw,rec.barDraw])if(draw!=null){''','''         if(rec.bodyDraw!=null || rec.barDraw!=null)for each(var draw:Object in [rec.bodyDraw,rec.barDraw])if(draw!=null){''')
p.write_text(s,encoding='utf-8')
