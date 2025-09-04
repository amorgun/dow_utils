@echo off

call "rtx_converter/venv/scripts/activate"
pyinstaller --onefile --noconsole --name rtx_converter --distpath "dist/rtx_converter" --collect-data werkzeug "dist/rtx_converter/pyinstaller_script.py"