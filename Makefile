WINEPREFIX= ${HOME}/wine_prefixes/dow_utils

.PHONY: wine_prefix screen_editor

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
	cp -r screen_editor/templates screen_editor/static LICENSE dist/screen_editor; \
	cd dist; \
	zip -r screen_editor .;
