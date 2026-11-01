# RV v0.33.17-landmem build (stub-SWC route, mirrors wall-surface/run.py compile recipe)
$ErrorActionPreference = 'Stop'
$MOD  = 'D:\Program Files\Steam\steamapps\common\Remains\mods\RealisticVision'
$GAME = 'D:\Program Files\Steam\steamapps\common\Remains'
$HERE = "$MOD\build\landmem-fix-20261102"
$JAVA = 'D:\Program Files\Adobe Animate 2024\jre\bin\java.exe'
$SDK  = "$GAME\mods\Sandevistan\build\tools\flexsdk"
$AIR  = "$GAME\mods\Sandevistan\build\tools\airsdk\frameworks\libs\air\airglobal.swc"
$STUB = "$MOD\build\GameStubs.swc"

$cfg = @'
<flex-config><compiler><external-library-path><path-element>__AIR__</path-element><path-element>__STUB__</path-element></external-library-path><source-path><path-element>__SRC__</path-element></source-path><debug>false</debug><optimize>true</optimize><omit-trace-statements>false</omit-trace-statements><theme/></compiler><target-player>32.0</target-player><swf-version>32</swf-version><use-network>false</use-network><static-link-runtime-shared-libraries>true</static-link-runtime-shared-libraries></flex-config>
'@
$cfg = $cfg.Replace('__AIR__',$AIR).Replace('__STUB__',$STUB).Replace('__SRC__',"$HERE\src")
[IO.File]::WriteAllText("$HERE\out\landmem.compiler.xml",$cfg)

& $JAVA '-Dfile.encoding=UTF-8' -jar "$SDK\lib\mxmlc.jar" "+flexlib=$SDK\frameworks" "-load-config=$HERE\out\landmem.compiler.xml" "-output=$HERE\out\RealisticVisionMod.swf" "$HERE\src\RealisticVisionMod.as" 2>&1 | Tee-Object -FilePath "$HERE\out\compile.log"
if ($LASTEXITCODE -ne 0) { throw "BUILD FAILED" }
(Get-FileHash "$HERE\out\RealisticVisionMod.swf" -Algorithm SHA256).Hash
(Get-Item "$HERE\out\RealisticVisionMod.swf").Length
