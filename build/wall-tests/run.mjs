// Runs the real mod methods in an isolated, invisible AIR fixture.
// Only access modifiers change in the temporary copy; production method bodies are intact.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const mod=path.resolve(here,'../..'), game=path.resolve(mod,'../..');
const edges=process.argv.includes('--edges');
const seams=process.argv.includes('--seams');
if(edges && seams)throw Error('Choose either --edges or --seams');
if(process.argv.includes('--seam-probes') && !seams)throw Error('--seam-probes requires --seams');
const harness=seams?'WallSeamHarness':edges?'WallEdgeHarness':'WallHarness';
const revisionArg=process.argv.indexOf('--revision');
const revision=revisionArg>=0?process.argv[revisionArg+1]:(process.argv.includes('--baseline')?'8748feb':null);
if(revisionArg>=0 && !/^[0-9a-f]{7,40}$/.test(revision||''))throw Error('--revision requires a commit hash');
if(process.argv.includes('--seam-probes') && !revision)throw Error('--seam-probes requires a pre-v0.28.2 --revision (old wall display tree)');
if(process.argv.includes('--probes') && (!edges || !revision))throw Error('--probes requires --edges and a pre-fix --revision');
const out=path.join(mod,'build/wall-test-output',seams?'seams':edges?'edges':'');
fs.mkdirSync(out,{recursive:true});
const imagePrefix=revision?'baseline-':'candidate-';
const sdk=process.env.RV_FLEX_SDK || 'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk';
const java=process.env.RV_JAVA || 'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
const source=revision
  ? spawnSync('git',['show',revision+':src/RealisticVisionMod.as'],{cwd:mod,encoding:'utf8'}).stdout
  : fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8');
if(!source.includes('class RealisticVisionMod')) throw Error('Missing mod source');
fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),source.replace(/\bprivate\b/g,'public'));
const result=spawnSync(java,['-Xmx384m','-Dsun.io.useCanonCaches=false','-jar',path.join(sdk,'lib/mxmlc.jar'),
  '+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=true',
  `-define=CONFIG::edgeProbes,${process.argv.includes('--probes')}`,
  `-define=CONFIG::seamProbes,${process.argv.includes('--seam-probes')}`,
  '-static-link-runtime-shared-libraries=true',`-source-path=${out},${here},${mod}/build/stubs`,
  '-output',path.join(out,harness+'.swf'),path.join(here,harness+'.as')],
  {cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});
if(result.status!==0){process.stdout.write(result.stdout||''); process.stderr.write(result.stderr||'');process.exit(2);}
fs.writeFileSync(path.join(out,'app-wall-test.xml'),`<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-wall-fixture${seams?'-seams':edges?'-edges':''}</id><versionNumber>1.0</versionNumber><filename>${harness}</filename><initialWindow><content>${harness}.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>`);
const run=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),path.join(out,'app-wall-test.xml')],{cwd:out,encoding:'utf8',timeout:45000});
const log=(run.stdout||'')+(run.stderr||'');
fs.unlinkSync(path.join(out,'app-wall-test.xml'));
fs.writeFileSync(path.join(out,revision?'baseline.log':'candidate.log'),log);
for(const line of log.split(/\r?\n/)) {
  if(line.startsWith('PNG ')) {const [,name,data]=line.split(' ');fs.writeFileSync(path.join(out,imagePrefix+name+'.png'),Buffer.from(data,'hex'));}
  else if(line.trim()) console.log(line);
}
if(run.error) console.error(run.error.message);
process.exit(run.status===0 && log.includes(seams?'WALL_SEAM_TESTS PASS':edges?'WALL_EDGE_TESTS PASS':'WALL_TESTS PASS')?0:1);
