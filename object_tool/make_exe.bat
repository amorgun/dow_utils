@echo off

call "object_tool/venv/scripts/activate"
pyinstaller --onefile --noconsole --name object_tool --distpath "dist/object_tool" "dist/object_tool/pyinstaller_script.py"