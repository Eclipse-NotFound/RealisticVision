#!/bin/bash
# RealisticVision build script
# 1) compile game API stubs -> build/GameStubs.swc
# 2) compile mod against stubs (external) -> release/RealisticVisionMod.swf
# At runtime fe.* resolves to game classes via parent ApplicationDomain.
set -e

SDK="C:/Users/micha/Documents/_sandevistan_dev/flexsdk"
export AIR_HOME="$SDK"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src"
STUBS="$ROOT/build/stubs"
OUT="$ROOT/release"

mkdir -p "$OUT"

echo "[1/2] building GameStubs.swc ..."
"$SDK/bin/acompc.bat" \
  -source-path+="$STUBS" \
  -include-classes fe.World fe.Pt fe.Obj fe.loc.Location fe.loc.Tile fe.graph.Grafon fe.unit.Unit fe.unit.UnitPlayer fe.unit.Pers fe.weapon.Weapon \
  -output "$ROOT/build/GameStubs.swc"

echo "[2/2] compiling RealisticVisionMod.swf ..."
"$SDK/bin/amxmlc.bat" \
  -swf-version=32 \
  -static-link-runtime-shared-libraries=true \
  -debug=false \
  -optimize=true \
  -warnings=true \
  -external-library-path+="$ROOT/build/GameStubs.swc" \
  -source-path+="$SRC" \
  -output "$OUT/RealisticVisionMod.swf" \
  "$SRC/RealisticVisionMod.as"

echo "BUILD OK: $OUT/RealisticVisionMod.swf"
