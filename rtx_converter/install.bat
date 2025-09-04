@echo off

cd rtx_converter
python -m venv venv
call "venv/scripts/activate"
pip install -r requirements.txt
pip install pyinstaller==6.9.0