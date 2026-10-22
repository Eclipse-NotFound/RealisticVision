"""Freeze the selected source. Only the version changes after functional testing."""
from pathlib import Path
import json,shutil,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output'
VERSION='v0.33.5-followup-performance'
if __name__=='__main__':
 source=OUT/'candidate-04/src';target=OUT/'production-input/src';assert not target.exists()
 shutil.copytree(source,target)
 entry=target/'RealisticVisionMod.as';s=entry.read_text(encoding='utf-8-sig');assert s.count('v0.33.4-native-performance')==1
 entry.write_text(s.replace('v0.33.4-native-performance',VERSION),encoding='utf-8',newline='\n')
 data={'candidate':'candidate-04','version':VERSION,'changes_after_candidate':'version only','sources':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*.as')}}
 (OUT/'selected.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
