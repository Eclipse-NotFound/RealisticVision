// Full 1.02 copied-resource replay. Fixed input steps, not a live-game FPS benchmark.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
import {transform} from './variants.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),mod=path.resolve(here,'../..'),game=path.resolve(mod,'../..');
const variant=process.argv[2]||'profile';if(!/^[a-z0-9-]+$/.test(variant))throw Error('Invalid variant');
const out=path.join(mod,'build/motion-test-output/game'),result=path.join(mod,'build/motion-test-output/game-'+variant);fs.mkdirSync(out,{recursive:true});fs.mkdirSync(result,{recursive:true});
const sdk=process.env.RV_FLEX_SDK||'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk';const java=process.env.RV_JAVA||'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
for(const name of fs.readdirSync(game)){
  if(!/^(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf$|^(text_.*|lang|launcher_text)\.xml$/.test(name))continue;
  if(!fs.existsSync(path.join(out,name)))fs.copyFileSync(path.join(game,name),path.join(out,name));
}
if(!fs.existsSync(path.join(out,'Rooms')))fs.cpSync(path.join(game,'Rooms'),path.join(out,'Rooms'),{recursive:true});
fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),transform(fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8'),variant));
function compile(args){const r=spawnSync(java,['-Xmx384m','-jar',path.join(sdk,'lib/mxmlc.jar'),'+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=false','-optimize=true','-omit-trace-statements=false','-static-link-runtime-shared-libraries=true',...args],{cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});if(r.status!==0)throw Error(r.stdout+r.stderr);}
compile([`-source-path=${out}`,`-external-library-path+=${mod}/build/GameStubs.swc`,'-output',path.join(out,'MotionMod.swf'),path.join(out,'RealisticVisionMod.as')]);
const boot=path.join(out,'bootstrap');fs.mkdirSync(boot,{recursive:true});
for(const name of ['GameMotionProbe.as','MotionCapture.as'])fs.copyFileSync(path.join(here,name),path.join(boot,name));
fs.writeFileSync(path.join(boot,'RealisticVisionMod.as'),'package {import flash.display.Sprite;public class RealisticVisionMod extends Sprite {public static var probe:GameMotionProbe;public static function init(main:*):void{probe=new GameMotionProbe(main);}}}');
const injected=path.join(out,'mods/RealisticVision/release');fs.mkdirSync(injected,{recursive:true});
compile([`-source-path=${boot}`,'-output',path.join(injected,'RealisticVisionMod.swf'),path.join(boot,'RealisticVisionMod.as')]);
const descriptor=path.join(out,'app-motion-game-test.xml');
fs.writeFileSync(descriptor,`<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-motion-game-${variant}</id><versionNumber>1.0</versionNumber><filename>MotionGameProbe</filename><initialWindow><content>pfe.swf</content><visible>false</visible><width>1280</width><height>720</height><renderMode>direct</renderMode></initialWindow></application>`);
const r=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),descriptor],{cwd:out,encoding:'utf8',timeout:150000,maxBuffer:48*1024*1024});fs.unlinkSync(descriptor);
const log=(r.stdout||'')+(r.stderr||'');fs.writeFileSync(path.join(result,'run.log'),log);
for(const rawLine of log.split(/\r?\n/)){
  const line=rawLine.trimEnd();
  if(line.startsWith('PNG ')){const [,name,data]=line.split(' ');fs.writeFileSync(path.join(result,name+'.png'),Buffer.from(data,'hex'));}
  else if(line.startsWith('DATA '))fs.writeFileSync(path.join(result,'motion.json'),line.slice(5));
  else if(line.includes('MOTION_GAME'))console.log(line);
}
if(r.error)console.error(r.error.message);
process.exit(r.status===0&&log.includes('MOTION_GAME COMPLETE')?0:1);
