from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/development.py').read_text(encoding='utf-8').replace('D37','D40').replace('build/combat-visibility-output/production/src','build/long-frame-output/production/src')
exec(compile(s,str(HERE/'development.py'),'exec'),globals())
