from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/native-performance/development.py').read_text(encoding='utf-8').replace('D37','D41').replace('build/combat-visibility-output/production/src','build/long-frame-output/production/src')
# The development branch has an older scene gate around the same block. Keep
# that unrelated code intact; one line of exact context isolates our additions.
s=s.replace("difflib.unified_diff(before,after,'a/src/'+name,'b/src/'+name)","difflib.unified_diff(before,after,'a/src/'+name,'b/src/'+name,n=1)")
exec(compile(s,str(HERE/'development.py'),'exec'),globals())
