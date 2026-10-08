# RealisticVision — line of sight and exploration fog

**English** · [简体中文](README.zh-CN.md)

Unexplored areas stay dark, your current view is clear, and places you leave become dim memories. Enemies disappear when they leave your sight. For a stronger sense of stealth and exploration.

**[Download v0.30.1 — RealisticVision_v0.30.1.zip](https://github.com/Eclipse-NotFound/RealisticVision/releases/download/v0.30.1/RealisticVision_v0.30.1.zip)** · [Release notes / other versions](https://github.com/Eclipse-NotFound/RealisticVision/releases)

Use the download link above, or open the release page, expand **Assets**, and select that filename. **Source code** and the green **Code → Download ZIP** button are development files, not the installable package.

## What changes?

- Three visibility states: unexplored, visible now, and remembered.
- Broken walls, doors and glass affect sight. Memory retains terrain and items, not hidden enemies.
- Switch between vanilla and two mod vision modes, and adjust remembered-area brightness.
- Optional shared exploration with RConnect, controlled independently by each player.

## Install

For **Windows / Remains 1.02**.

1. Save and close the game. In your Steam Library, right-click Remains → **Manage → Browse local files**. The game folder contains `pfe.swf` and `application.xml`.
2. If this is your first mod from this collection, complete the [ModLoader first-time setup](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.md#first-install), including the game patch and scanner. Skip this if already installed.
3. Extract the ZIP and **merge its `mods` folder into the game folder**. Avoid a nested `mods/mods` folder. On a first installation, copy `default-config/RealisticVision/config.txt` into `mods/RealisticVision/release/config.txt`. Do not overwrite an existing configuration when updating.
4. Double-click **`mods/ModLoader/RemainsModScanner.exe`** inside the game folder. Wait for it to finish, close its message, then launch the game normally.

Check that this file exists: `mods/RealisticVision/release/RealisticVisionMod.swf`. Enter an exploration area to see the effect; use F11 to compare enabled and disabled views.

[Folder diagram, updating and recovery](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.md)

## Your first session

| Control | Action |
|---|---|
| F11 | Enable/disable the effect |
| F12 | Cycle vanilla, classic and current vision modes |
| PipBuck → Settings → Mods (`模组`) → vision settings | Adjust brightness and other options |

The mode name appears briefly when you switch. Mode and enable settings persist; saved in-game settings take priority over the installation template.

## Updates, removal and compatibility

Before updating, save and close the game, back up `mods/RealisticVision`, merge the new files, run the scanner and restart. Preserve your configuration. To disable the mod temporarily, move its folder outside `mods` as a backup, scan again and restart.

This guide covers v0.30.1 on Remains 1.02. Safe areas may retain the vanilla view. Increasing memory brightness does not reveal hidden enemies. Performance in busy scenes depends on your machine and other mods.

## Need help?

Check the folder location, run the scanner, and fully restart the game. See the [installation troubleshooting guide](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.md#troubleshooting) for common problems.

If it still fails, [report an issue](https://github.com/Eclipse-NotFound/RealisticVision/issues) with your game version, mod version, other installed mods, steps to reproduce, and what you expected versus what happened. Include a screenshot or exact error if available; a personal save is not needed for an initial report.

<details>
<summary>Development resources (not needed to install)</summary>

This page describes the downloadable release; repository source may be ahead. See [src](src/) for implementation, with design, validation and version records in the project tree.

</details>

[Browse the mod collection](https://github.com/Eclipse-NotFound/ModLoader#choose-mods) · [First-time installation guide](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.md)

An unofficial fan project. You need your own copy of the game.
