WINEPREFIX= ${HOME}/wine_prefixes/dow_utils

.PHONY: wine_prefix screen_editor object_tool rtx_converter

wine_prefix:
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" winecfg; \
	wget https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe -P "$(WINEPREFIX)"
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c "$(WINEPREFIX)/python-3.12.5-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1; 

screen_editor:
	rm -rf dist/screen_editor dist/screen_editor.zip; \
	mkdir -p dist/screen_editor/dow_utils; \
	cp -r lib screen_editor dist/screen_editor/dow_utils; \
	cp screen_editor/pyinstaller_script.py dist/screen_editor; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c screen_editor/install.bat; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c screen_editor/make_exe.bat; \
	rm -rf dist/screen_editor/dow_utils dist/screen_editor/pyinstaller_script.py; \
	cp -r screen_editor/templates screen_editor/static LICENSE screen_editor/vgmstream-win64 dist/screen_editor; \
	cd dist && zip -r screen_editor.zip screen_editor;

object_tool:
	rm -rf dist/object_tool dist/object_tool.zip; \
	mkdir -p dist/object_tool/dow_utils; \
	cp -r lib object_tool dist/object_tool/dow_utils; \
	cp object_tool/pyinstaller_script.py dist/object_tool; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c object_tool/install.bat; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c object_tool/make_exe.bat; \
	rm -rf dist/object_tool/dow_utils dist/object_tool/pyinstaller_script.py; \
	cp -r LICENSE dist/object_tool; \
	cd dist && zip -r object_tool.zip object_tool;

rtx_converter:
	rm -rf dist/rtx_converter dist/rtx_converter.zip; \
	mkdir -p dist/rtx_converter/dow_utils; \
	cp -r lib rtx_converter dist/rtx_converter/dow_utils; \
	cp rtx_converter/pyinstaller_script.py dist/rtx_converter; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c rtx_converter/install.bat; \
	DISPLAY=:0.0 WINEPREFIX="$(WINEPREFIX)" wine cmd /c rtx_converter/make_exe.bat; \
	rm -rf dist/rtx_converter/dow_utils dist/rtx_converter/pyinstaller_script.py; \
	cp -r LICENSE dist/rtx_converter; \
	cd dist && zip -r rtx_converter.zip rtx_converter;
