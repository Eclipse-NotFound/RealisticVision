@echo off
setlocal
set ROOT=%~dp0..
set SDK=D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk
set JAVA_HOME=D:\Program Files\Adobe Animate 2024\jre
set PATH=%JAVA_HOME%\bin;%PATH%
set AIR_HOME=%SDK%
call "%SDK%\bin\amxmlc.bat" -swf-version=32 -static-link-runtime-shared-libraries=true -debug=false -optimize=true -warnings=true -external-library-path+="%ROOT%\build\GameStubs.swc" -source-path+="%ROOT%\src" -output "%ROOT%\build\RealisticVisionMod_test.swf" "%ROOT%\src\RealisticVisionMod.as"
echo AMXMLC_EXIT=%errorlevel%
endlocal
