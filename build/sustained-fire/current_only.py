from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/sustained-fire-output/candidates'
source=OUT/'trailing-v2/src';dest=OUT/'trailing-current/src';assert not dest.exists()
s=(source/'RealisticVisionMod.as').read_text()
base=(MOD/'build/combat-render-output/production-final2/src/RealisticVisionMod.as').read_text()
start=base.index('         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)')
end=base.index('         if(shape.parent!==visual.parent)',start)
old=base[start:end]
start=s.index('         // Keep the old sampling lattice;')
end=s.index('         if(shape.parent!==visual.parent)',start)
optimized=s[start:end].replace('Keep the old sampling lattice; test whether unused outer tiles\n         // can be omitted without changing Flash\'s cached alpha rendering.','Keep the cached bitmap origin fixed. Only trim trailing blank support\n         // in current mode; moving the origin changes subpixel mask sampling.')
s=s[:start]+'         if(this.cfgMode=="current")\n         {\n'+optimized+'         }\n         else\n         {\n'+old+'         }\n'+s[end:]
shutil.copytree(source,dest);(dest/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
print('Prepared current-only candidate; classic restores the exact D44 graphics branch')
