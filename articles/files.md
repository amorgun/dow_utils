# List of file extensions used by DoW

| **Extention** | **Description** | **Category** | **Tools (Open Source 😊 / Closed Source🔒)** | **Example paths** | **Other links**| 
| ---- | ---- | ---- | ---- | ---- | ---- |
| [**Common**](#Common) |
| .sga | Archives with compressed game data | Binary | [Corsix's Mod Studio😊](https://modstudio.corsix.org/) | `DXP2Data.sga` | [Format description](https://github.com/ModernMAK/Relic-Game-Tool/wiki/SGA-Archive) |
| .rgd | Compiled attribute data. You can see it as a binary JSON (?**R**elic **G**ame **D**ata) | [Relic Chunky](#relic-chunky) | [Corsix's Mod Studio😊](https://modstudio.corsix.org/) | `attrib/ebps/races/guard/troops/guard_infantry_kasrkin_sergeant_advance_sp.rgd` | [C# parser](https://github.com/jbelford/Dawn-of-War-UMG/blob/761b7383a6a0c1e64b0b096fc94d265da33e96a4/src/DowUmg/FileFormats/RgdReader.cs#L68) |
| [**Models**](#Models) |
| .whm | Model data files - contain meshes, texture references, animations and markers. | [Relic Chunky](#relic-chunky) | [Blender DoW addon😊](https://github.com/amorgun/blender_dow), [Relic 3DS Max Scripts🔒](https://forums.revora.net/topic/116206-tutorial-install-and-set-up-3ds-max-2008/) | `art/ebps/races/space_marines/troops/space_marine.whm` | |
| .whe | Model attributes files - contain FX, events, actions and animation tree. | [Relic Chunky](#relic-chunky) | [Object Editor🔒](https://forums.revora.net/topic/113849-object-editor-tutorial/), [Object Tool😊](https://github.com/amorgun/dow_utils/tree/main/object_tool) | `art/ebps/races/space_marines/troops/space_marine.whe` | |
| .sgm | Model data files used by Object Editor. Contains the same data as `.whm`. | [Relic Chunky](#relic-chunky) | [Object Editor🔒](https://forums.revora.net/topic/113849-object-editor-tutorial/), [Blender DoW addon😊](https://github.com/amorgun/blender_dow), [Relic 3DS Max Scripts🔒](https://forums.revora.net/topic/116206-tutorial-install-and-set-up-3ds-max-2008/) | | |
| .ebp | Model attributes files used by Object Editor. Contains the same data as `.whe`. | [Relic Chunky](#relic-chunky) | [Object Editor🔒](https://forums.revora.net/topic/113849-object-editor-tutorial/), [Object Tool😊](https://github.com/amorgun/dow_utils/tree/main/object_tool) | | | 
| [**Textures**](#Textures) |
| .rsh | Default textures for a model. Contains albedo, specularity and self-illumination layers. | [Relic Chunky](#relic-chunky) | [Blender DoW addon😊](https://github.com/amorgun/blender_dow), [DoW Texture Tool🔒](https://skins.hiveworldterra.co.uk/Downloads/detail_DawnOfWarTextureTool.html) | `art/ebps/races/space_marines/texture_share/space_marine_unit.rsh` | [[How-to] create a rsh file with specular mapping](https://web.archive.org/web/20140916035059/http://forums.relicnews.com/showthread.php?200685-How-to-create-a-rsh-file-with-specular-mapping) | 
| .wtp | Teamcolor information for a model. Describes areas colored into each of the teamcolors and badge and banner positions. | [Relic Chunky](#relic-chunky) | [Blender DoW addon😊](https://github.com/amorgun/blender_dow), [DoW Texture Tool🔒](https://skins.hiveworldterra.co.uk/Downloads/detail_DawnOfWarTextureTool.html) | `art/ebps/races/space_marines/texture_share/space_marine_unit_default.wtp` | [Skinning 4 Dummies](https://skins.hiveworldterra.co.uk/Article/view_Skinning4Dummies.html) |
| .rtx | Textures with a baked-in teamcolor. Used in single-player campaign and in skirmish/multiplayer when team-colouring is turned off.| [Relic Chunky](#relic-chunky) | [DoW Texture Tool🔒](https://skins.hiveworldterra.co.uk/Downloads/detail_DawnOfWarTextureTool.html) | `art/ebps/races/space_marines/texture_share/space_marine_unit_default_0.rtx` | |
| .teamcolour | Color schemes. Lists the exact color used along with the banner and badge links. | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `art/team_colours/chaos_marine_race/deathguard.teamcolour` | | |
| [**Images**](#Images) |
| .dds | Common image file format. DoW supports DXT1, DXT3 and DXT5. | Binary | [GIMP😊](https://www.gimp.org/), [Photoshop🔒](https://www.adobe.com/products/photoshop.html), [ImageMagick😊](https://imagemagick.org/index.php) | `Scenarios/loading/chaos_race_02.dds` | [Wikipedia](https://en.wikipedia.org/wiki/DirectDraw_Surface) | 
| .tga | Common image file format. All .tga files need to be 32 bit, with the alpha transparency layer on, DoW doesn't support color maps or RLE compression. | Binary | [GIMP😊](https://www.gimp.org/), [Photoshop🔒](https://www.adobe.com/products/photoshop.html), [ImageMagick😊](https://imagemagick.org/index.php) | `art/banners/guard_race/cadian101.tga` | [Wikipedia](https://en.wikipedia.org/wiki/Truevision_TGA) | 
| [**Maps**](#Maps) |
| .sgb | Map files | [Relic Chunky](#relic-chunky) | [Dow Advanced Map Editor😊](https://bitbucket.org/dark40k/dowadvmapeditor/), [Mission Editor🔒](https://www.moddb.com/games/dawn-of-war-dark-crusade/downloads/dark-crusade-mod-tools) | `Scenarios/mp/2p_absolute_zero.sgb` | | 
| [**Sound**](#Sound) |
| .fda | Compressed sound files | [Relic Chunky](#relic-chunky) | [DoW Mod Tools🔒 (encoding)](https://www.mediafire.com/file/lpizd73o8wxl703/DoW_Modtools_setup_v1.7z/file), [vgmstream😊 (decoding)](https://github.com/vgmstream/vgmstream) [Relic Audio Converter🔒](https://www.moddb.com/games/dawn-of-war/downloads/relic-audio-converter) | `speech/races/space_marines/force_commander/attack/403150.fda`, `sound/button_menu.fda` | [Using the Audio Editor](https://dow.finaldeath.co.uk/rdnwiki/www.relic.com/rdn/wiki/DOWAudioEditor%26v=3w6.html) | 
| .rat | Configuration for sound file playback (**R**elic **A**udio **T**ool) | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `speech/races/space_marines/force_commander/attack/_default.rat` | | 
| .con | Somehow used for marking directories with audio files | Empty | | `speech/races/space_marines/force_commander/attack.con` | | 
| [**UI**](#UI) |
| .screen | UI lauout for the majority of the game menus| [Lua](#lua) | [Screen viewer😊](https://github.com/amorgun/dow_utils/tree/main/screen_editor), [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `art/ui/screens/mainmenu.screen` | | 
| .styles | Common styles shared between `.screen` files | [Lua](#lua) | [Screen viewer😊](https://github.com/amorgun/dow_utils/tree/main/screen_editor), [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `art/ui/styles/uistyles.styles` | 
| .colours | Common colours shared between `.screen` files | [Lua](#lua) | [Screen viewer😊](https://github.com/amorgun/dow_utils/tree/main/screen_editor), [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `art/ui/styles/colourtable.colours` | |  
| [**Scripts**](#Scripts) |
| .lua | Generic file with code or config data | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `camera_me.lua`, `art/ebps/races/space_marines/troops/space_marine.lua` | |
| .scar | Lua scripts (**Sc**ripting **A**t **R**elic) | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `scar/winconditions/annihilate.scar` | |
| .nis | Ingame cinematics (**N**on **I**nteractive **S**equences) | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Scenarios/sp/cinematic.nis` | |
| [**Metamap**](#Metamap) |
| .mmcamp | The root file for describing metamap. Soulstorm uses the hardcoded `kaurava.mmcamp` | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Scenarios/sp/kaurava.mmcamp` | |
| .map | Metamap config. Lists all used races, territories and planets. | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Scenarios/sp/kaurava.map` | |
| .ter | Single territory config. Describes parent planet, resource production, honour guard and lists adjacent territories. | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Scenarios/sp/cape_of_despair.ter` | |
| .race | Race config. Describes a colour scheme, commander models and wargear options. Must have a corresponding .rgd file in `attrib/racebps`  |[Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Scenarios/sp/races/chaos_marine_race.race` | |
| .gfx | UI used in metamap screens | SWF | [jpexs-decompiler😊](https://github.com/jindrapetrik/jpexs-decompiler) | `art/ui/swf/metamap.gfx`| [Wikipedia](https://en.wikipedia.org/wiki/Scaleform_GFx), [Scaleform Reference Documentation](https://help.autodesk.com/view/SCLFRM/ENU/?guid=__cpp_ref_00004_html) |
| [**AI**](#AI) |
| .ai | Files for controlling the AI (**A**bominable **I**ntelligence)| [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `ai/default.ai` | [*.AI files.](https://dow.finaldeath.co.uk/rdnwiki/www.relic.com/rdn/wiki/DOWScar/AI/AIFiles&v%3D1csc.html), [Docs](https://dow.finaldeath.co.uk/rdnwiki/www.relic.com/rdn/wiki/DOWScar/AI%26v=19p.html) |
| [**Font**](#Text) |
| .ttf | Fonts files. Cannot be overridden by mods, must be inside the `engine` folder. | TrueType | | `fonts/engo.ttf` | [Wikipedia](https://en.wikipedia.org/wiki/TrueType) |
| .fnt | Text style presets (used fonts and sizes for different screen resolutions). | [Lua](#lua)  | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `fonts/albertus extra bold16.fnt` | |
| [**Localization**](#Localization) |
| .ucs | Translation data | Plain text | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `Locale/English/DXP2_VO.ucs` | [List of reserved UCS Ranges](https://forums.revora.net/topic/109906-ucs-ranges-for-all-projects/) |
| [**Other**](#Other) |
| .module | Mod config | Plain text (ini) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `DXP2.module` | |
| .events | The same format as `.whe` events section | [Relic Chunky](#relic-chunky) | | `art/events/assault_cannon_fx.events` | |
| .avi | Movies. Use DivX format. | Binary | [FFmpeg😊](https://www.ffmpeg.org/) | `Movies/ss_guard_race_outro.avi` | [Wikipedia](https://en.wikipedia.org/wiki/DivX) |
| .turn | Some configs for unit turning behaviour  | [Lua](#lua) | [Notepad++😊](https://notepad-plus-plus.org/), [VS Code😊](https://code.visualstudio.com/) | `game/turningbehaviors/infantry.turn`, `game/turningbehaviors/vehicles.turn` | |

# Relic Chunky
Relic Chunky files are a binary file structure developed by Relic Entertainment for use in their games. You can find some info on the format [here](https://web.archive.org/web/20250506215716/https://scratchpad.fandom.com/wiki/Relic_Chunky_files).  
Usually you need a specialized tool to edit any given chunky format, like Blender for models or Map Editor for maps. 
For editing an arbitrary chunky file you can use [FFE](https://bitbucket.org/dark40k/dowadvfileeditor/src/master/) or any of the hex editors, like [ImHex](https://github.com/WerWolv/ImHex). You can view chunky files using `ChunkyViewerCSharp.exe` from [ModTools](https://www.mediafire.com/file/lpizd73o8wxl703/DoW_Modtools_setup_v1.7z/file).


# Lua
Lua is a programming language. DoW uses it for scripting and storing data. Consult its Reference Manual [here](https://www.lua.org/manual/5.1/manual.html) on the language syntax.

# References
1. [Basics of Modding DoW1: The files](https://forums.revora.net/topic/110825-basics-of-modding-dow1-the-files/)
2. [Dawn of War File Formats](https://dow.finaldeath.co.uk/rdnwiki/www.relic.com/rdn/wiki/DOWFileFormats.html)