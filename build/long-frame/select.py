from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/long-frame-output'
if __name__=='__main__':
 dst=OUT/'production-input/src';assert not dst.exists();shutil.copytree(OUT/'candidate-04/src',dst)
 p=dst/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig');assert s.count('v0.33.5-followup-performance')==1
 p.write_text(s.replace('v0.33.5-followup-performance','v0.33.6-long-frame'),encoding='utf-8',newline='\n')
 (OUT/'selected.json').write_text(json.dumps({'candidate':'candidate-04','version':'v0.33.6-long-frame','after_tests':'version only','sources':{p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
