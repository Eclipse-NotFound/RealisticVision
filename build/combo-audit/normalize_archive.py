"""Correct Windows text newlines before committing; preserve original raw hashes."""
from pathlib import Path
import hashlib,json
MOD=Path(__file__).resolve().parents[2];root=MOD/'knowledge/experiments/combo-audit-20261101'
old=(root/'manifest.json').read_bytes()
(MOD/'build/combo-audit-output/archive-manifest-before-newline-fix.json').write_bytes(old)
for p in root.rglob('*'):
    if p.is_file() and (p.suffix in ('.as','.json','.log') or p.name=='.gitattributes'):
        data=p.read_bytes().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        if p.suffix=='.log':data=b'\n'.join(line.rstrip() for line in data.split(b'\n'))
        p.write_bytes(data)
manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(root/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
print('Normalized archive line endings; source hashes and raw results unchanged')
