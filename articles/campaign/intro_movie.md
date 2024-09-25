# Using custom cinematics

1. Convert video
```bash
ffmpeg -i "my_custom_intro.webm" -c:v mpeg4 -tag:v DXGM -q:v 5  -r 29.97 -pix_fmt yuv420p -an "My_Mod/Movies/custom_intro.avi"
```

2. Create `My_Mod/Movies/custom_intro.lua` file
```lua
-- custom_intro.lua
movie = "custom_intro.avi"
audio = "speech/nis/custom_intro"
maintainAspect = false
```

3. Extract audio
```bash
ffmpeg -i "my_custom_intro.webm" -ar 44100 "ModTools/DataGeneric/My_Mod/Sound/custom_intro.wav"
```

4. Convert audio to .fda using Relic Audio Editor  
Refer to this [Audio Editor tutorial](https://dow.finaldeath.co.uk/rdnwiki/www.relic.com/rdn/wiki/DOWAudioEditor%26v=3w6.html)

5. Create `_default.rat` inside `My_Mod/Data/sound` folder.  
You can copy it from the DXP2 mod.

6. Ensure there are converted .fda and .rat files inside `My_Mod/Data/sound/speech/nis` folder.

7. Edit `My_Mod/Data/Scenarios/sp/kaurava.mmcamp`
```lua
-- kaurava.mmcamp
MapFile = "my_map"
AISettingsFile = "Settings"
```

8. Create  to `My_Mod/Data/Scenarios/sp/my_map.map`  
You can copy it from `DXP2/Data/Scenarios/sp/kaurava.map`

9. Set intro movie path
```lua
-- my_map.map
IntroMovie = "custom_intro"
```

10. Edit intro subtitles
Subtitles are configured in `IntroMovieText` section of `My_Mod/Data/Scenarios/sp/my_map.map` file.
```lua
-- my_map.map
IntroMovieText =
{
	{
		Text = "$5200152",
		Start = 0.28,
		End = 12.16,
	},
}
```

There are also `OutroMovie` sections in the .map file as well as `IntroMovie` and `OutroMovie` in each of the .race files so you can change them as well.
