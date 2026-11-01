"""Reuse the proven isolated runner; save its exact generated source for audit."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(1,str(MOD/'build/maximized-flow'))
from instrument import replace_once
source=MOD/'build/maximized-flow/run.py'
pins=json.loads((MOD/'build/performance-survey-output/inputs.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==pins['runtime_runner']
s=source.read_text('utf8').replace('build/maximized-flow-output','build/performance-survey-output')
s=s.replace('from cpu_sampler import OwnedCpuSampler','from instrument import instrument as census_main, helper as census_helper\nfrom cpu_sampler import OwnedCpuSampler')
s=s.replace('RealisticVision / 最大化与重画复用','RealisticVision / 性能切口普查')
s=replace_once(s,"sources=[('rv',BASE),('candidate',OUT/'candidate/src'),('vector',OUT/'candidate/src')]","sources=[('rv',BASE)]")
s=replace_once(s,'  if plain:\n','  s=census_main(s)\n  if plain:\n')
s=replace_once(s,"p.write_text(s,encoding='utf-8')", "p.write_text(s,encoding='utf-8')\n  helper=src/'RVWallSurface.as';helper.write_text(census_helper(helper.read_text()),encoding='utf-8')")
s=s.replace("rec.note='LMG原生射击和计时完成；插桩归因不作最终发布收益'","rec.note='两模式固定/受控移动计数完成；含诊断开销，不作性能收益验收'")
s=replace_once(s,"code,log=r.air(folder,'pfe.swf',rec,timeout=650)","code,log=r.air(folder,'pfe.swf',rec,timeout=650)")
(MOD/'build/performance-survey-output/generated-runner.py').write_text(s,'utf8',newline='\n')
exec(compile(s,str(source),'exec'),{'__name__':'__main__','__file__':str(HERE/'run.py')})
