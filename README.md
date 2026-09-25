# RealisticVision

A fog-of-war / line-of-sight overhaul for **Fallout Equestria: REMAINS**: unexplored areas go fully dark, what you currently see renders normally, and areas you have left stay dimly remembered — terrain and items persist, enemies don't.

English (this page) · [简体中文](README.zh-CN.md)

## Features

- Real-time vision updates: unexplored = black, in-sight = normal, explored-but-out-of-sight = dimmed memory (scene, terrain and items kept; enemies hidden until seen again).
- Works with destructible walls (vision opens up as walls break) and glass doors / lit doorways.
- Telekinesis-aware: items moved by enemy telekinesis show up live; your own telekinesis works through walls for items but not enemies (`telegrace` gives enemies a grace period when dragged out of sight).
- Optional **shared exploration** integration with [RConnect](https://github.com/Eclipse-NotFound/RConnect) co-op (two-way, per-side toggle).

## Requirements

- Fallout Equestria: REMAINS (1.02).
- The one-time **ModLoader** game patch — see
  [ModLoader Releases](https://github.com/Eclipse-NotFound/ModLoader/releases) → `Remains-GamePatch`.

## Install

1. Download `RealisticVision_v0.30.0.zip` from [Releases](../../releases).
2. Copy the zip's `mods` folder into your game root (next to `pfe.swf`).
3. Restart the game.

## Usage

| Key | Action |
|---|---|
| **F11** | Toggle on/off at runtime (writes back to config) |
| **F12** | Cycle vision mode |
| **F10** | Diagnostics panel (room/visibility counters, telekinesis countdown, current mode) |

Configuration lives in `mods/RealisticVision/release/config.txt` — `enabled`, `mode`, `dim` (memory darkness, default 0.35), `doordim` (light through doors/water, 0.5), `litmin` (visibility threshold), `fadestep` (smoothing), `telegrace` (seconds of enemy grace when dragged out of sight), `base_rooms` (extra safe-house room ids) and `debug`. Changes take effect after a restart; F11/F12 write back to the file.

## Disable / uninstall

Set the mod's switches to `0` in `mods/loader-manifest.txt`, or delete `mods/RealisticVision`.

## Build from source

AS3 source is a single document class (`src/RealisticVisionMod.as`) compiled against game-API stubs via `build/build.sh` (Git Bash + Flex SDK; see the Chinese README for toolchain paths). The release artifact is `release/RealisticVisionMod.swf`.

## Related mods

[ModLoader](https://github.com/Eclipse-NotFound/ModLoader) ·
[RConnect](https://github.com/Eclipse-NotFound/RConnect) (shared exploration partner) ·
[Sandevistan](https://github.com/Eclipse-NotFound/Sandevistan) ·
[MoreSkillsAndWeapons](https://github.com/Eclipse-NotFound/MoreSkillsAndWeapons) ·
[TDFC](https://github.com/Eclipse-NotFound/TDFC) ·
[RandomRooms](https://github.com/Eclipse-NotFound/RandomRooms)

> Fan mod project; not affiliated with the game's authors.
