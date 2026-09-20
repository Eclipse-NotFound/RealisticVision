// Checks the archived investigation's claims, not a production-release gate.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import crypto from 'node:crypto';
const base='knowledge/experiments/current-motion-20260920';
const a=JSON.parse(fs.readFileSync(path.join(base,'analysis.json'),'utf8'));
assert.equal(a.baseline.updates,20);assert.ok(a.baseline.frozen>=2);
assert.equal(a.gate1.updates,0);assert.equal(a['fast-sync'].updates,60);assert.equal(a['fast-sync'].frozen,0);
assert.equal(a['fast-rays'].exact_baseline_frames,24);assert.equal(a['game-fast-rays'].exact_baseline_frames,24);
assert.equal(a['corner-history'].never_seen_interior.pixels_above_2,0);assert.equal(a.baseline.never_seen_interior.pixels_above_2,808);
assert.ok(a.hires.spatial.edge_residual_rms_px<a.baseline.spatial.edge_residual_rms_px*.6);
assert.ok(a.coverage.spatial.edge_residual_rms_px>a.baseline.spatial.edge_residual_rms_px*.85);
assert.ok(a['no-clamp'].spatial.deep_shadow_pixels_above_2>a.baseline.spatial.deep_shadow_pixels_above_2*10);
const games=Object.entries(a).filter(([k])=>k.startsWith('game-')||k.startsWith('bench-'));
for(const [name,result] of games){assert.equal(result.identical_room_input,true,name+' input');assert.equal(result.native_mutations,0,name+' native mutation');}
const fingerprints=Object.fromEntries(Object.entries(JSON.parse(fs.readFileSync(path.join(base,'fingerprints.json'),'utf8'))).map(([k,v])=>[k.replaceAll('\\','/'),v]));
for(const file of ['src/RealisticVisionMod.as','release/RealisticVisionMod.swf','release/config.txt'])assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex').toUpperCase(),fingerprints[file],file);
const gameSWF=path.resolve('../..','pfe.swf').replaceAll('\\','/');assert.equal(crypto.createHash('sha256').update(fs.readFileSync(gameSWF)).digest('hex').toUpperCase(),fingerprints[gameSWF]);
console.log('INVESTIGATION_EVIDENCE PASS: motion failure reproduced, temporal experiment green, cache frames identical, phantom memory eliminated, rejected AA tradeoffs measured, '+games.length+' same-input game cases, production files unchanged.');
