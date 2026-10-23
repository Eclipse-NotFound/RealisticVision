from pathlib import Path
import json,statistics
OUT=Path(__file__).resolve().parents[2]/'build/effect-visibility-output'
for name in ['native-final-02','safe-final-parent','production-final']:
 path=OUT/name/'evidence/result.json'
 if path.exists():
  d=json.loads(path.read_text());print(name,'checks',len(d.get('checks',[])),'cases',len(d.get('cases',[])),'error',d.get('error'))
  for row in d.get('cases',[]):
   if 'frames' in row:
    a=[f['nextInterval'] for f in row['frames'] if 'nextInterval' in f];b=[f['rv'] for f in row['frames']]
    print(row['mode'],row['variant'],len(a),round(statistics.mean(a),2),round(statistics.mean(b),2),row['grounded'])
