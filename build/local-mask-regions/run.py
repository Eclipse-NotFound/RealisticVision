"""Pinned isolated native combat runner, new outputs only."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/local-mask-regions-output'
sys.path.insert(0,str(HERE));sys.path.insert(1,str(MOD/'build/maximized-flow'))
source=MOD/'build/maximized-flow/run.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==json.loads((OUT/'inputs.json').read_text())['runtime_runner']
s=source.read_text('utf8').replace('build/maximized-flow-output','build/local-mask-regions-output').replace('RealisticVision / 最大化与重画复用','RealisticVision / 精确区域遮罩')
if '--alpha-candidate' in sys.argv:s=s.replace("('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')","('candidate',OUT/'alpha-candidate/src'),('vector',OUT/'alpha-candidate/src')")
if '--three-way' in sys.argv:
 assert '--candidate' in sys.argv and '--alpha-candidate' not in sys.argv
 s=s.replace("('vector',OUT/'candidate/src')","('vector',OUT/'alpha-candidate/src')")
 s=s.replace("['off','normal','candidate','vector','vector','candidate','normal','off']","['normal','candidate','vector','vector','candidate','normal']")
 s=s.replace("['off','vector','candidate','normal','normal','candidate','vector','off']","['vector','candidate','normal','normal','candidate','vector']")
s=s.replace('from cpu_sampler import OwnedCpuSampler','from oracle import instrument as verify_regions\nfrom cpu_sampler import OwnedCpuSampler')
marker=" s=(HERE/'SavedFireProbe.as').read_text()"
assert s.count(marker)==1
s=s.replace(marker,marker+'''
 if '--three-way' in sys.argv:
  order="['vector','candidate','normal','normal','candidate','vector']" if '--reverse' in sys.argv else "['normal','candidate','vector','vector','candidate','normal']"
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off','normal','normal','off']",order)
 if '--verify-regions' in sys.argv:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off','normal','normal','off']","['candidate']")
  s=s.replace('SAMPLE_COUNT=360','SAMPLE_COUNT=180').replace('WARMUP_COUNT=90','WARMUP_COUNT=45')
  s=s.replace('row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);','row.regionHits=rv.regionHits;row.regionVerified=rv.regionVerified;if(rv.regionHits<100||rv.regionHits!=rv.regionVerified)throw new Error("region oracle coverage");row.profile=rv.profile;row.calls=rv.calls;result.cases.push(row);')
''')
marker='  if plain:\n'
assert s.count(marker)==1
s=s.replace(marker,"  if '--verify-regions' in sys.argv and variant!='rv':s=verify_regions(s)\n"+marker)
s=s.replace(" groups={}\n", " if '--three-way' in sys.argv:assert {c['variant'] for c in data['cases']}=={'normal','candidate','vector'}\n groups={}\n")
s=s.replace("rec.note='LMG原生射击和计时完成；插桩归因不作最终发布收益'","rec.note='精确局部版本：相同组合原生轻机枪/六狮鹫；oracle仅功能，plain用于整帧对照'")
(OUT/'generated-runner.py').write_text(s,'utf8',newline='\n')
exec(compile(s,str(source),'exec'),{'__name__':'__main__','__file__':str(HERE/'run.py')})
