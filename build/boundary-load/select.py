from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/boundary-load-output'
if __name__=='__main__':
 dst=OUT/'production-input/src';assert not dst.exists();shutil.copytree(OUT/'candidate-03/src',dst)
 p=dst/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig');assert s.count('v0.33.6-long-frame')==1
 p.write_text(s.replace('v0.33.6-long-frame','v0.33.7-boundary-performance'),encoding='utf-8',newline='\n')
 (OUT/'selected.json').write_text(json.dumps({'candidate':'candidate-03','version':'v0.33.7-boundary-performance','difference':'version only','sources':{p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
