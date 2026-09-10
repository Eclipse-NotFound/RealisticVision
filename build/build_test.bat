@echo off
rem Test build with autotest instrumentation (ASCII only, CRLF required)
rem Output goes to build\RealisticVisionMod_test.swf - release\ is NOT touched.
setlocal
set ROOT=%~dp0..
set SDK=D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk
set JAVA_HOME=D:\Program Files\Adobe Animate 2024\jre
set PATH=%JAVA_HOME%\bin;%PATH%
set AIR_HOME=%SDK%
set SRC=%ROOT%\src
set STUBS=%ROOT%\build\stubs
set OUT=%ROOT%\build

call "%SDK%\bin\acompc.bat" -source-path+="%STUBS%" -include-classes fe.World fe.Pt fe.Obj fe.loc.Location fe.loc.Tile fe.graph.Grafon fe.unit.Unit fe.unit.UnitPlayer fe.unit.Pers fe.weapon.Weapon -output "%ROOT%\build\GameStubs.swc"
if errorlevel 1 (
  echo.
  echo BUILD FAILED: stubs
  exit /b 1
)

call "%SDK%\bin\amxmlc.bat" -swf-version=32 -static-link-runtime-shared-libraries=true -debug=false -optimize=true -warnings=true -external-library-path+="%ROOT%\build\GameStubs.swc" -source-path+="%SRC%" -output "%OUT%\RealisticVisionMod_test.swf" "%SRC%\RealisticVisionMod.as"
if errorlevel 1 (
  echo.
  echo BUILD FAILED: mod
  exit /b 1
)

echo.
echo BUILD OK: %OUT%\RealisticVisionMod_test.swf
endlocal
