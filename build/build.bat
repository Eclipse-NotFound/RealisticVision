@echo off
rem RealisticVision build script (ASCII only, CRLF line endings required)
rem 1) compile game API stubs -> GameStubs.swc
rem 2) compile mod against stubs (external) -> release/RealisticVisionMod.swf
rem At runtime fe.* resolves to game classes via parent ApplicationDomain.
setlocal
set ROOT=%~dp0..
set SDK=C:\Users\micha\Documents\_sandevistan_dev\flexsdk
set AIR_HOME=%SDK%
set SRC=%ROOT%\src
set STUBS=%ROOT%\build\stubs
set OUT=%ROOT%\release

if not exist "%OUT%" mkdir "%OUT%"

call "%SDK%\bin\acompc.bat" -source-path+="%STUBS%" -include-classes fe.World fe.Pt fe.Obj fe.loc.Location fe.loc.Tile fe.graph.Grafon fe.unit.Unit fe.unit.UnitPlayer fe.weapon.Weapon -output "%ROOT%\build\GameStubs.swc"
if errorlevel 1 (
  echo.
  echo BUILD FAILED (stubs)
  exit /b 1
)

call "%SDK%\bin\amxmlc.bat" -swf-version=32 -static-link-runtime-shared-libraries=true -debug=false -optimize=true -warnings=true -external-library-path+="%ROOT%\build\GameStubs.swc" -source-path+="%SRC%" -output "%OUT%\RealisticVisionMod.swf" "%SRC%\RealisticVisionMod.as"
if errorlevel 1 (
  echo.
  echo BUILD FAILED (mod)
  exit /b 1
)

echo.
echo BUILD OK: %OUT%\RealisticVisionMod.swf
endlocal
