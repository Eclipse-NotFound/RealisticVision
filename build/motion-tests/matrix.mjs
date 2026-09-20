import {spawnSync} from 'node:child_process';
const game=process.argv.includes('--game');
const variants=process.argv.slice(2).filter(x=>x!=='--game');
for(const variant of variants){
  const r=spawnSync(process.execPath,[game?'build/motion-tests/run-game.mjs':'build/motion-tests/run.mjs',variant],{encoding:'utf8',timeout:game?180000:90000});
  console.log(variant, r.stdout.trim(),r.stderr.trim());
  if(r.status!==0)process.exit(r.status||1);
}
