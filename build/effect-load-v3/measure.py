from pathlib import Path
from environment_guard import classify
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/overall-flow/measure.py').read_text(encoding='utf-8').replace('overall-flow-output','effect-load-v3-output').replace('candidate-00','baseline')
at=s.rindex("\nif __name__=='__main__':")
s=s[:at]+"\nsaved_environment=inv.r.environment\ninv.r.environment=lambda:classify(saved_environment())\nsaved_air=inv.r.air\ndef bounded_air(folder,entry,rec,timeout=600,seed_store=None):\n return saved_air(folder,entry,rec,600,seed_store)\ninv.r.air=bounded_air\n"+s[at:]
exec(compile(s,str(HERE/'measure.py'),'exec'),globals())
