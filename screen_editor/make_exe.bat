@echo off

call "screen_editor/venv/scripts/activate"
pyinstaller --onefile --noconsole --name screen_editor --distpath "dist/screen_editor" --collect-data werkzeug "dist/screen_editor/pyinstaller_script.py"