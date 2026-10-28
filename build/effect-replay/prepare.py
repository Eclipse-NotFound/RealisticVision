"""Create D55 tools without modifying any frozen D54 input or output."""
from pathlib import Path
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=MOD/'build/effect-replay-output';OUT.mkdir(exist_ok=True)
assert not (HERE/'SavedReplayProbe.as').exists()
s=(MOD/'build/sustained-fire/SavedProbe.as').read_text().replace('sustained-fire-output','effect-replay-output').replace('D54','D55')
s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['capture']")
s=s.replace('rv.d53SkipEffects=p.variant==\'noeffects\';','rv.d53SkipEffects=true;')
s=s.replace('private function inputFrame(e:Event):void {','private function inputFrame(e:Event):void {\n   if(replaying){wc["w"].ctr.clearAll();return;}')
s=s.replace('private function step(e:Event):void {','private function step(e:Event):void {\n   if(replaying){try{replayStep();}catch(replayError:Error){fail(replayError);}return;}')
s=s.replace('if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;','if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;\n    if(!replaying){freezeReplay(w);return;}')
at=s.rfind('\n }');assert at>0
s=s[:at]+(HERE/'Replay.as.inc').read_text()+s[at:]
(HERE/'SavedReplayProbe.as').write_text(s,encoding='utf-8',newline='\n')
s=(MOD/'build/sustained-fire/run.py').read_text().replace("OUT=MOD/'build/sustained-fire-output'","OUT=MOD/'build/effect-replay-output'").replace("SEED=OUT/'player-seed'","SEED=MOD/'build/sustained-fire-output/player-seed'").replace('D54','D55')
a=s.index(" s=(HERE/'SavedProbe.as')");b=s.index(" (folder/'CombatRenderProbeMod.as')",a)
s=s[:a]+''' s=(HERE/'SavedReplayProbe.as').read_text()
 s=s.replace('SWEEP=false','SWEEP=true').replace('SOLO=false','SOLO=true').replace('SHOW_WINDOW=false','SHOW_WINDOW=true')
 s=s.replace('EXPERIMENT=false','EXPERIMENT=true')
 if '--validate' in sys.argv:s=s.replace('REPLAY_VALIDATE=false','REPLAY_VALIDATE=true')
 if '--diagnostic' in sys.argv:s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','normal','fixed','fixed','normal','off']")
''' +s[b:]
a=s.index(' if candidate:sources.append');b=s.index('\n for variant,source in sources:',a)
s=s[:a]+" sources.append(('candidate',MOD/'build/sustained-fire-output/candidates'/('pixel-cache' if '--pixel-cache' in sys.argv else 'integer-v2')/'src'))"+s[b:]
a=s.index(" data=json.loads((folder/'evidence/result.json')");s=s[:a]+'''
 data=json.loads((folder/'evidence/result.json').read_text())
 assert data['weapon']=='lmg' and data['audioVolume']==0 and data['windowVisible']
 assert data['replay']['count']>10 and data['capture']['attacks']>10
 if '--validate' in sys.argv:
  assert data['exactFrames']==60
  result={'exactFrames':data['exactFrames'],'replay':data['replay'],'environment':eligibility}
 else:
  groups={}
  for c in data['replayCases']:
   assert c['fingerprint']==data['replayCases'][0]['fingerprint'],'Replay input differs'
   groups.setdefault(c['variant'],[]).extend(c['frames'])
  def stats(v):
   v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
  result={'environment':eligibility,'replay':data['replay'],'groups':{k:{f:stats([x[f] for x in a if f in x]) for f in ['interval','rv','restore']} for k,a in groups.items()}}
 r.save(folder/'analysis.json',result);print(json.dumps(result));rec.outcome='passed';rec.note='固定真实特效受控回放；不是完整游戏性能验收'
'''
(HERE/'run.py').write_text(s,encoding='utf-8',newline='\n')
ignore=MOD/'.gitignore';text=ignore.read_text()
if 'build/effect-replay-output/' not in text:ignore.write_text(text.rstrip()+'\nbuild/effect-replay-output/\n',encoding='utf-8',newline='\n')
