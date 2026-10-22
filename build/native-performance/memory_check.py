import fov_check as f
from pathlib import Path
import argparse
source=(Path(__file__).parent/'fov_check.py').read_text(encoding='utf-8')
source=source[source.index('def build('):source.index("if __name__=='__main__':")]
source=source.replace('FovBoundsChecks','MemoryTileChecks').replace('FOV BOUNDS COMPLETE','MEMORY TILES COMPLETE')
exec(source,f.__dict__)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');a=p.parse_args()
 f.build(a.name,'candidate-12') if a.action=='build' else f.run(a.name)
