"""Read installed files/registry; write only this experiment's receipt."""
from pathlib import Path
import ast,hashlib,json,sqlite3,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/shot-light-output';HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((OUT/'inputs.json').read_text())
for rel,h in inputs['files'].items():assert sha(OUT/rel)==h,rel
candidates=[]
for name in ['candidate','raster-candidate','geometry-candidate','direct-candidate','direct-full-candidate','direct-circle-candidate']:
 for rel,h in json.loads((OUT/name/'sources.json').read_text()).items():assert sha(OUT/name/'src'/rel)==h,(name,rel)
 candidates.append(name)
for p in HERE.glob('*.py'):ast.parse(p.read_text('utf8'),filename=str(p))
expected={
 'mods/RealisticVision/release/RealisticVisionMod.swf':'aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557',
 'mods/RealisticVision/release/config.txt':'0f27e923eb3af5cc99f45064fd3ea93df8afe4107cdbc58b305a915f425bf47e',
 'mods/LightAndDarkness/release/LightAndDarknessMod.swf':'8adba6914df5aada4df12a646b6c22df4b95b9630a55dd05ca7f713621c7e3ef'}
installed={rel:sha(GAME/rel) for rel in expected};assert installed==expected
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import gone
db=GAME/'shared-knowledge/knowledge-validation/coordination/test-runs.sqlite3'
with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as con:
 rows=[json.loads(r[0]) for r in con.execute('select payload from runs where payload like ?',('%shot-light-output%',))]
assert len(rows)==14,len(rows)
records=[]
for r in rows:
 assert Path(r['runDir']).resolve().is_relative_to(OUT.resolve())
 assert r['state'] in ('passed','failed') and r['ended'],r['purpose']
 children=[{'pid':c['pid'],'token':c['token'],'gone':gone(c)} for c in r['children']]
 assert all(c['gone'] for c in children),children
 records.append({'id':r['id'],'purpose':r['purpose'],'state':r['state'],'ended':r['ended'],'children':children})
windows=frames=intervals=0
for p in OUT.glob('[0-9][0-9]-*/evidence/result.json'):
 data=json.loads(p.read_text());assert not data.get('error'),p
 windows+=len(data['cases'])
 for c in data['cases']:frames+=len(c['frames']);intervals+=sum('nextInterval' in f for f in c['frames'])
assert (windows,frames,intervals)==(36,6000,5964)
receipt={'deployed':False,'installedUnchanged':installed,'currentHost':sha(GAME/'pfe.swf'),
 'frozenInputsVerified':len(inputs['files']),'candidateSourcesVerified':candidates,'windows':windows,'sampleFrames':frames,'completeIntervals':intervals,'registrations':records}
(OUT/'final-checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
print(json.dumps({'installedUnchanged':True,'windows':windows,'sampleFrames':frames,'completeIntervals':intervals,'registrationsEnded':len(records),'ownedAirGone':sum(len(r['children']) for r in records),'deployed':False}))
