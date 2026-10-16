"""Run the final frozen validation sequentially, with no overlapping AIR jobs."""
import hashlib
import run,production
assert hashlib.sha256((run.OUT/'candidate/src/RVWallSurface.as').read_bytes()).hexdigest()=='62f22cc918368aeed59e70112d94dfcdab8de63c91a9249e888322513e47c895'
print('D29 FINAL independent regression checks',flush=True)
run.checks()
for name in ['bench-reuse','game-reuse','game-rock-reuse']:
    print('D29 FINAL '+name,flush=True)
    run.run_game(name)
print('D29 FINAL exact production bytes, two processes',flush=True)
production.run()
print('D29 FINAL RUNTIME VALIDATION PASS',flush=True)
