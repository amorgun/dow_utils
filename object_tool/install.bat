@echo off

cd object_tool
python -m venv venv
call "venv/scripts/activate"
@REM pip install -r requirements.txt
pip install pyinstaller==6.9.0