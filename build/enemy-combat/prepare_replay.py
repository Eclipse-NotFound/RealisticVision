from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[1]
s=(M/'build/effect-mask-origin/run.py').read_text().replace('effect-mask-origin-output','enemy-combat-output').replace('RealisticVision / D56','RealisticVision / D57')
s=s.replace("BASE=MOD/'build/combat-render-output/production-final2/src'","BASE=OUT/'baseline/src'")
s=s.replace("s=s.replace('EXPERIMENT=false','EXPERIMENT=true')","s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace('NATIVE_CHILD:Boolean=false','NATIVE_CHILD:Boolean=true')")
s=s.replace("  s=s[:pos]+'\\n public var d53SkipEffects", "  s=s[:pos]+'\\n public var d53SkipEffects")
at="  s=s.replace('// D56_LOCAL','trailingHits++;')"
assert s.count(at)==1
s=s.replace(at,"  if variant=='candidate':s=s[:pos]+'\\npublic var nativeAlphaMarker:Boolean=true;public var alphaHits:int=0;\\n'+s[pos:]\n  s=s.replace('// D57_ALPHA_CLIP','alphaHits++; // D57_ALPHA_CLIP')\n"+at)
s=s.replace("assert data['optimizedCalls']>0,'Candidate fast path was not exercised'","assert data['optimizedCalls']>0,'Candidate fast path was not exercised'\n  assert data['alphaHits']>100,'No actual native alpha crop'")
s=s.replace("result={'exactFrames':data['exactFrames']","result={'alphaHits':data.get('alphaHits'),'exactFrames':data['exactFrames']")
(H/'replay.py').write_text(s,encoding='utf-8')
s=(M/'build/effect-mask-origin/SavedReplayProbe.as').read_text().replace('effect-mask-origin-output','enemy-combat-output').replace('D56','D57')
s=s.replace('w.mm.active=false;var saved:', 'w.mm.mainMenuOff();var saved:')
s=s.replace("NATIVE_CHILD && 'restoreDarkChild' in m","NATIVE_CHILD && 'nativeAlphaMarker' in m")
s=s.replace('result.exactFrames=60;result.optimizedCalls=', 'result.alphaHits=compareMod.alphaHits;result.exactFrames=60;result.optimizedCalls=')
s=s.replace("host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D57 COMPLETE');", "host.stage.removeEventListener(Event.ENTER_FRAME,inputFrame);host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D57 COMPLETE');")
(H/'SavedReplayProbe.as').write_text(s,encoding='utf-8')
