// Full 1.02 game in a copied asset root and a separate AIR app id. No user saves/mod releases.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url)),mod=path.resolve(here,'../..'),game=path.resolve(mod,'../..');
const out=path.join(mod,'build/wall-test-output/game');fs.mkdirSync(out,{recursive:true});
const sdk=process.env.RV_FLEX_SDK||'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk';
const java=process.env.RV_JAVA||'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
for(const name of fs.readdirSync(game)) {
  if(!/^(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf$|^(text_.*|lang|launcher_text)\.xml$/.test(name))continue;
  if(!fs.existsSync(path.join(out,name)))fs.copyFileSync(path.join(game,name),path.join(out,name));
}
fs.cpSync(path.join(game,'Rooms'),path.join(out,'Rooms'),{recursive:true});
const exposed=fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8').replace(/\bprivate\b/g,'public');
fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),exposed);
function compile(args){const r=spawnSync(java,['-Xmx384m','-jar',path.join(sdk,'lib/mxmlc.jar'),'+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=true','-static-link-runtime-shared-libraries=true',...args],{cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});if(r.status!==0)throw Error(r.stdout+r.stderr);}
compile([`-source-path=${out}`,`-external-library-path+=${mod}/build/GameStubs.swc`,'-output',path.join(out,'WallMod.swf'),path.join(out,'RealisticVisionMod.as')]);
const boot=path.join(out,'bootstrap');fs.mkdirSync(boot,{recursive:true});
fs.copyFileSync(path.join(here,'GameProbe.as'),path.join(boot,'GameProbe.as'));
fs.writeFileSync(path.join(boot,'RealisticVisionMod.as'),'package { import flash.display.Sprite; public class RealisticVisionMod extends Sprite { public static var probe:GameProbe; public static function init(main:*):void { probe=new GameProbe(main); } } }');
const injected=path.join(out,'mods/RealisticVision/release');fs.mkdirSync(injected,{recursive:true});
compile([`-source-path=${boot}`,'-output',path.join(injected,'RealisticVisionMod.swf'),path.join(boot,'RealisticVisionMod.as')]);
const descriptor=path.join(out,'app-wall-game-test.xml');
fs.writeFileSync(descriptor,`<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-wall-game-probe</id><versionNumber>1.0</versionNumber><filename>WallGameProbe</filename><initialWindow><content>pfe.swf</content><visible>true</visible><width>1280</width><height>720</height><renderMode>direct</renderMode></initialWindow></application>`);
const r=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),descriptor],{cwd:out,encoding:'utf8',timeout:85000,maxBuffer:20*1024*1024});
const log=(r.stdout||'')+(r.stderr||'');fs.writeFileSync(path.join(out,'game.log'),log);
fs.unlinkSync(descriptor);
for(const line of log.split(/\r?\n/)){if(line.startsWith('PNG ')){const [,name,data]=line.split(' ');fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(data,'hex'));}else if(line.includes('GAME_PROBE'))console.log(line);}
if(r.error)console.error(r.error.message);
process.exit(r.status===0 && log.includes('GAME_PROBE PASS')?0:1);
