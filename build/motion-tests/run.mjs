// Investigation only: copied source, isolated AIR identity, no release writes.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {transform} from './variants.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),mod=path.resolve(here,'../..'),game=path.resolve(mod,'../..');
const variant=process.argv[2]||'baseline';
if(!/^[a-z0-9-]+$/.test(variant))throw Error('Invalid variant');
const out=path.join(mod,'build/motion-test-output',variant);fs.mkdirSync(out,{recursive:true});
const sdk=process.env.RV_FLEX_SDK||'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk';
const java=process.env.RV_JAVA||'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
let source=transform(fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8'),variant);
fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),source);
const r=spawnSync(java,['-Xmx384m','-jar',path.join(sdk,'lib/mxmlc.jar'),'+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=false','-optimize=true','-omit-trace-statements=false','-static-link-runtime-shared-libraries=true',`-source-path=${out},${here},${mod}/build/stubs`,'-output',path.join(out,'MotionHarness.swf'),path.join(here,'MotionHarness.as')],{cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});
if(r.status!==0)throw Error(r.stdout+r.stderr);
const descriptor=path.join(out,'app-motion-test.xml');
fs.writeFileSync(descriptor,`<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-motion-fixture-${variant}</id><versionNumber>1.0</versionNumber><filename>MotionHarness</filename><initialWindow><content>MotionHarness.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>`);
const run=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),descriptor],{cwd:out,encoding:'utf8',timeout:60000,maxBuffer:32*1024*1024});
fs.unlinkSync(descriptor);
const log=(run.stdout||'')+(run.stderr||'');fs.writeFileSync(path.join(out,'run.log'),log);
for(const line of log.split(/\r?\n/)){
  if(line.startsWith('PNG ')){const [,name,data]=line.split(' ');fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(data,'hex'));}
  else if(line.startsWith('DATA '))fs.writeFileSync(path.join(out,'motion.json'),line.slice(5));
  else if(line.trim())console.log(line);
}
if(run.error)console.error(run.error.message);
// RED is a valid investigation result; --assert is the future regression gate.
process.exit(run.status===0 && log.includes('MOTION COMPLETE') && (!process.argv.includes('--assert')||!log.includes('MOTION RED'))?0:1);
