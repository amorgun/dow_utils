# Dawn of War Screen Editor
A tool for an interactive preview of `.screen` files.  
It launches a local web server so you can view the files in your browser.

# Download application
See the [latest release](https://github.com/amorgun/dow_utils/releases/tag/SE0.4).
Get `screen_editor.zip` from there.

# Run
You can run pre-build `.exe` or run it from the source code.  
Usually your selected mod folder should be inside your `Dawn of War Soulstorm` installation folder (e.g. `C:/Steam/steamapps/common/Dawn of War Soulstorm/My_Mod`).  
In case your mod is packed in `.sga` you must extract `.screen` files (usually located in `art/ui/screens`) using [Corsix's Mod Studio](https://modstudio.corsix.org/) before running this tool.

## Running from the source code
### Requirements
1. 
```bash
git clone git@github.com:amorgun/dow_utils.git
pip install -r dow_utils/screen_editor/requirements.txt
```
2. Get [vgmstream-cli](https://github.com/vgmstream/vgmstream) and put it into `dow_utils/screen_editor` folder

### GUI
```bash
python3 -m dow_utils.screen_editor.gui
```

### CLI
```bash
python3 -m dow_utils.screen_editor <path_to_mod>
```

# Antivirus issues
This tool uses [PyInstaller](https://github.com/pyinstaller/pyinstaller/tree/develop) to build exe files and some antivirus software flags it as a virus.  
You can read the detailed explanation [here](https://github.com/pyinstaller/pyinstaller/blob/develop/.github/ISSUE_TEMPLATE/antivirus.md).  
You can either add the `.exe` to the exceptions or run it from the source code.