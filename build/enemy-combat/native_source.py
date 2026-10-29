from pathlib import Path
M=Path(__file__).resolve().parents[2]
code=(M/'build/frame-attribution/source.py').read_text().replace('frame-attribution-output','enemy-combat-output')
exec(compile(code,str(Path(__file__)),'exec'))
