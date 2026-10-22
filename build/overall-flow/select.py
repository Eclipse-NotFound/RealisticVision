from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/overall-flow-output'
if __name__=='__main__':
 dst=OUT/'production-input/src';assert not dst.exists();shutil.copytree(OUT/'candidate-05/src',dst)
 p=dst/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig');assert s.count('v0.33.6-long-frame')==1
 p.write_text(s.replace('v0.33.6-long-frame','v0.33.7-classic-scan'),encoding='utf-8',newline='\n')
 (OUT/'selected.json').write_text(json.dumps({'candidate':'candidate-05','version':'v0.33.7-classic-scan','after_tests':'version only; deployment still requires review','sources':{p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
