// Runs the real mod methods in an isolated, invisible AIR fixture.
// Only access modifiers change in the temporary copy; production method bodies are intact.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const mod=path.resolve(here,'../..'), game=path.resolve(mod,'../..');
const out=path.join(mod,'build/wall-test-output');
fs.mkdirSync(out,{recursive:true});
const imagePrefix=process.argv.includes('--baseline')?'baseline-':'candidate-';
const sdk=process.env.RV_FLEX_SDK || 'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk';
const java=process.env.RV_JAVA || 'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
const source=process.argv.includes('--baseline')
  ? spawnSync('git',['show','8748feb:src/RealisticVisionMod.as'],{cwd:mod,encoding:'utf8'}).stdout
  : fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8');
if(!source.includes('class RealisticVisionMod')) throw Error('Missing mod source');
fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),source.replace(/\bprivate\b/g,'public'));
const result=spawnSync(java,['-Xmx384m','-Dsun.io.useCanonCaches=false','-jar',path.join(sdk,'lib/mxmlc.jar'),
  '+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=true',
  '-static-link-runtime-shared-libraries=true',`-source-path=${out},${here},${mod}/build/stubs`,
  '-output',path.join(out,'WallHarness.swf'),path.join(here,'WallHarness.as')],
  {cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});
if(result.status!==0){process.stdout.write(result.stdout||''); process.stderr.write(result.stderr||'');process.exit(2);}
fs.writeFileSync(path.join(out,'app-wall-test.xml'),`<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-wall-fixture</id><versionNumber>1.0</versionNumber><filename>WallHarness</filename><initialWindow><content>WallHarness.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>`);
const run=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),path.join(out,'app-wall-test.xml')],{cwd:out,encoding:'utf8',timeout:45000});
const log=(run.stdout||'')+(run.stderr||'');
fs.unlinkSync(path.join(out,'app-wall-test.xml'));
fs.writeFileSync(path.join(out,process.argv.includes('--baseline')?'baseline.log':'candidate.log'),log);
for(const line of log.split(/\r?\n/)) {
  if(line.startsWith('PNG ')) {const [,name,data]=line.split(' ');fs.writeFileSync(path.join(out,imagePrefix+name+'.png'),Buffer.from(data,'hex'));}
  else if(line.trim()) console.log(line);
}
if(run.error) console.error(run.error.message);
process.exit(run.status===0 && log.includes('WALL_TESTS PASS')?0:1);
