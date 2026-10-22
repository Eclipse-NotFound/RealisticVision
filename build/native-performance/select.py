"""Freeze the accepted candidate and its version; does not install it."""
from pathlib import Path
import argparse,json,shutil,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate');a=p.parse_args()
 source=OUT/a.candidate/'src';target=OUT/'production-input/src';assert not target.exists()
 shutil.copytree(source,target)
 entry=target/'RealisticVisionMod.as';s=entry.read_text(encoding='utf-8-sig');assert s.count('v0.33.3-combat-visibility')==1
 entry.write_text(s.replace('v0.33.3-combat-visibility','v0.33.4-native-performance'),encoding='utf-8')
 data={'candidate':a.candidate,'version':'v0.33.4-native-performance','changes_after_candidate':'version only','sources':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*.as')}}
 (OUT/'selected.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
