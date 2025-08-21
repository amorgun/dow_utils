# Object tool
A tool for manipulating Dawn of War object configs.

# Commands
## Convert
Supported formats:
- From: `.whe`, `.json`, `.lua`
- To: `.whe`, `.json`, `.ebp`, `.lua`

### Use cases:
- **Convert `.whe` to `.ebp`**  
    If you want to edit an existing `.whe` in the Object Editor you need to convert it to `.ebp` first
    ```bash
    python3 -m dow_utils.object_tool.convert dreadnought.whe dreadnought.ebp
    ```
- **Edit .whe without the Object Editor**  
    In case you need to change multiple `.whe` files programmatically you can convert them to `json` format.  
    It's also useful if you want to store a human-readable version of`.whe` in VCS or if you simply like me don't like Object Editor.
    ```bash
    # Contert to .json
    python3 -m dow_utils.object_tool.convert dreadnought.whe dreadnought.json
    
    # Edit converted .json here

    # Then convert it back to .whe
    python3 -m dow_utils.object_tool.convert dreadnought.json dreadnought_edited.whe
    ```

# Download application
See the [**latest release**](https://github.com/amorgun/dow_utils/releases/tag/OT0.4).
Get `object_tool.zip` from there.

# Run
You can run pre-build `.exe` or run it from the source code.  

## Running from the source code
### Requirements
```bash
git clone git@github.com:amorgun/dow_utils.git
```

### GUI
```bash
python3 -m dow_utils.object_tool.convert.gui
```

### CLI
```bash
python3 -m dow_utils.object_tool.convert <source_path> <converted_path>
```


# Antivirus issues
This tool uses [PyInstaller](https://github.com/pyinstaller/pyinstaller/tree/develop) to build exe files and some antivirus software flags it as a virus.  
You can read the detailed explanation [here](https://github.com/pyinstaller/pyinstaller/blob/develop/.github/ISSUE_TEMPLATE/antivirus.md).  
You can either add the `.exe` to the exceptions or run it from the source code.