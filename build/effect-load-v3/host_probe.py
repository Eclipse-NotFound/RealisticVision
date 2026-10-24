"""Bounded read-only host sampling under the same exclusive test lease."""
import json,time,psutil,argparse
import bench
r=bench.r;OUT=bench.OUT
def main(name):
 folder=OUT/name;assert not folder.exists();folder.mkdir()
 with r.Registration(owner='RealisticVision / D43 无游戏负载核对',purpose='exclusive lease, no AIR launched, 3 second CPU sample',run_dir=folder,evidence=folder/'host.json',wait=900) as rec:
  env=r.environment();r.save(folder/'preflight.json',env)
  assert not env['processes'],'Other AIR/Java still active; no quiet host sample'
  before={};start=time.monotonic();psutil.cpu_percent(None)
  for proc in psutil.process_iter(['pid','name','cpu_times','memory_info']):
   try:
    info=proc.info;t=info['cpu_times'];before[proc.pid]=(info['name'],t.user+t.system)
   except (psutil.Error,AttributeError):pass
  time.sleep(3);cpu=psutil.cpu_percent(None);elapsed=time.monotonic()-start;rows=[]
  for proc in psutil.process_iter(['pid','name','cpu_times','memory_info']):
   if proc.pid not in before:continue
   try:
    info=proc.info;t=info['cpu_times'];seconds=t.user+t.system-before[proc.pid][1]
    rows.append({'pid':proc.pid,'name':info['name'],'cpu_seconds':round(seconds,3),'logical_core_percent':round(100*seconds/elapsed,2),'rss_mib':round(info['memory_info'].rss/1024**2,1)})
   except (psutil.Error,AttributeError):pass
  result={'elapsed_seconds':elapsed,'cpu_percent':cpu,'logical_processors':psutil.cpu_count(),'available_gib':psutil.virtual_memory().available/1024**3,'top_cpu':sorted(rows,key=lambda x:x['cpu_seconds'],reverse=True)[:12],'air_launched':False}
  r.save(folder/'host.json',result);rec.outcome='passed';rec.note='read-only sample; no settings or processes changed'
  print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');main(a.parse_args().name)
