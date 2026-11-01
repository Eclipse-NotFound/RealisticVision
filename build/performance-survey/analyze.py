from pathlib import Path
import json,hashlib,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/performance-survey-output'
name=sys.argv[1];folder=OUT/name
p=folder/'evidence/result.json';data=json.loads(p.read_text('utf8'))
assert data['weapon']=='lmg' and data['audioVolume']==0 and len(data['cases'])==4
result={'run':name,'inputSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'scope':'Diagnostic counters and inclusive instrumented timings; not a performance comparison', 'cases':[]}
for c in data['cases']:
    n=len(c['frames']);s=c['survey'];wall=c['wallSurvey'];assert n==180 and c['activeSamples']==180
    assert s.get('visualCalls',0)==s.get('uniqueVisualCalls',0)+s.get('duplicateVisualCalls',0)
    assert s.get('visualCalls',0)==sum(s.get('source'+str(i),0) for i in range(3))
    assert s.get('worldRefreshCalls',0)+s.get('unitRefreshCalls',0)==s.get('sameVersionReturn',0)+s.get('refreshWork',0)
    assert s.get('inputCompare',0)==s.get('inputUnchanged',0)+s.get('inputChanged',0)
    assert wall.get('terrainCompare',0)==wall.get('terrainSame',0)+wall.get('terrainChanged',0)
    entry={'mode':c['mode'],'variant':c['variant'],'sampleFrames':n,'activeSamples':c['activeSamples'],
           'screen':c['stageScreen'],'settings':c['settings'],'positionsRange':[min(x[0] for x in c['positions']),max(x[0] for x in c['positions'])],
           'counters':s,'perFrame':{k:v/n for k,v in s.items()},'wallCounters':wall,
           'profileMsPerFrame':{k:v/n for k,v in c['profile'].items()},
           'callsPerFrame':{k:v/n for k,v in c['calls'].items()},'retained':c['retained'],
           'playerShotsLowerBound':c['samplePlayerShotsLowerBound'],'enemyShotsLowerBound':c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots']}
    result['cases'].append(entry)
    print(c['mode'],c['variant'],'calls',s.get('visualCalls'), 'duplicates',s.get('duplicateVisualCalls',0),'newRasters',s.get('worldRasterNew',0),
          'refresh',s.get('refreshWork',0),'compareSame',s.get('inputUnchanged',0),'compareChanged',s.get('inputChanged',0),
          'crop',s.get('cropUsed',0),'scaled',s.get('nonUnitTransform',0))
    print('wall',wall,'inclusive ms/frame',entry['profileMsPerFrame'])
(folder/'census.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
print('Counter identity checks passed')
