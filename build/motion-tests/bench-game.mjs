// Same process, same room, alternate order, no PNG encoding inside benchmark trials.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
import {transform} from './variants.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),mod=path.resolve(here,'../..'),game=path.resolve(mod,'../..');
const out=path.join(mod,'build/motion-test-output/game'),sdk=process.env.RV_FLEX_SDK||'D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk',java=process.env.RV_JAVA||'D:/Program Files/Adobe Animate 2024/jre/bin/java.exe';
const variants=['baseline','profile','fast-rays','fast-sync','hires','coverage','corner-history'];
function compile(args){const r=spawnSync(java,['-Xmx384m','-jar',path.join(sdk,'lib/mxmlc.jar'),'+configname=air',`+flexlib=${sdk}/frameworks`,'-swf-version=32','-debug=false','-optimize=true','-omit-trace-statements=false','-static-link-runtime-shared-libraries=true',...args],{cwd:out,env:{...process.env,AIR_HOME:sdk},encoding:'utf8',timeout:60000});if(r.status!==0)throw Error(r.stdout+r.stderr);}
for(const variant of variants){
  fs.writeFileSync(path.join(out,'RealisticVisionMod.as'),transform(fs.readFileSync(path.join(mod,'src/RealisticVisionMod.as'),'utf8'),variant));
  compile([`-source-path=${out}`,`-external-library-path+=${mod}/build/GameStubs.swc`,'-output',path.join(out,'MotionMod-'+variant+'.swf'),path.join(out,'RealisticVisionMod.as')]);
}
const boot=path.join(out,'bootstrap');fs.copyFileSync(path.join(here,'MotionCapture.as'),path.join(boot,'MotionCapture.as'));
let probe=fs.readFileSync(path.join(here,'GameMotionProbe.as'),'utf8');
probe=probe.replace('private var phase:int=0,ticks:int=0,settled:int=0;',`private var phase:int=0,ticks:int=0,settled:int=0; private var index:int=0,classes:Object={},loaders:Array=[];
private var plan:Array=["baseline","profile","fast-rays","fast-sync","hires","coverage","corner-history","fast-sync","fast-rays","baseline","profile"];`);
probe=probe.replace('modClass=mod.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod") as Class;','modClass=mod.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod") as Class;');
// Keep initial loading/startup identical; load each experiment into a sibling domain after entering the room.
probe=probe.replace('MotionCapture.run(w,modClass,gameMain.stage.frameRate);\n          NativeApplication.nativeApplication.exit(0);','loadCase(w);');
probe=probe.replace('    private function tick(e:Event):void {',`    private function loadCase(w:*):void {
      if(index>=plan.length){trace("MOTION_BENCH COMPLETE");NativeApplication.nativeApplication.exit(0);return;}
      var name:String=plan[index++];
      function execute(cls:Class):void {
        try{trace("CASE "+name+"-"+index);MotionCapture.run(w,cls,gameMain.stage.frameRate,false);setTimeout(function():void{loadCase(w);},100);}
        catch(e:Error){trace("MOTION_GAME ERROR "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
      }
      if(classes[name]){execute(classes[name]);return;}
      var loader:Loader=new Loader();loaders.push(loader);
      var ctx:LoaderContext=new LoaderContext(false,new ApplicationDomain(gameMain.loaderInfo.applicationDomain));ctx.allowCodeImport=true;
      loader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void{classes[name]=loader.contentLoaderInfo.applicationDomain.getDefinition("RealisticVisionMod");execute(classes[name]);});
      loader.load(new URLRequest("app:/MotionMod-"+name+".swf"),ctx);
    }
    private function tick(e:Event):void {`);
fs.writeFileSync(path.join(boot,'GameMotionProbe.as'),probe);
const injected=path.join(out,'mods/RealisticVision/release');
compile([`-source-path=${boot}`,'-output',path.join(injected,'RealisticVisionMod.swf'),path.join(boot,'RealisticVisionMod.as')]);
const descriptor=path.join(out,'app-motion-bench-test.xml');
fs.writeFileSync(descriptor,'<?xml version="1.0"?><application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-motion-game-bench</id><versionNumber>1.0</versionNumber><filename>MotionBench</filename><initialWindow><content>pfe.swf</content><visible>false</visible><width>1280</width><height>720</height><renderMode>direct</renderMode></initialWindow></application>');
const r=spawnSync(path.join(game,'adl64.exe'),['-runtime',path.join(game,'runtimes/air/win64'),descriptor],{cwd:out,encoding:'utf8',timeout:150000,maxBuffer:20*1024*1024});fs.unlinkSync(descriptor);
const log=(r.stdout||'')+(r.stderr||'');fs.writeFileSync(path.join(out,'bench.log'),log);let label;
for(const rawLine of log.split(/\r?\n/)){
  const line=rawLine.trimEnd();
  if(line.startsWith('CASE ')){label=line.slice(5);console.log(line);}
  else if(line.startsWith('DATA ')){
    if(!/^[a-z0-9-]+$/.test(label))throw Error('Invalid case');
    const dest=path.join(mod,'build/motion-test-output','bench-'+label);fs.mkdirSync(dest,{recursive:true});fs.writeFileSync(path.join(dest,'motion.json'),line.slice(5));
  }else if(line.includes('MOTION_'))console.log(line);
}
if(r.error)console.error(r.error.message);
process.exit(r.status===0&&log.includes('MOTION_BENCH COMPLETE')?0:1);
