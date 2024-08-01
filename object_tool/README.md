# Object tool
A command-line tool for manipulating Dawn of War object configs.

# Installation
```
git clone git@github.com:amorgun/dow_utils.git
```

# Commands
## Convert
Supported formats:
- From: `.whe`, `.json`
- To: `.whe`, `.json`, `.ebp`

### Use cases:
- **Convert `.whe` to `.ebp`**  
    If you want to edit an existing `.whe` in the Object Editor you need to convert it to `.ebp` first
    ```bash
    python3 -m dow_utils.object_tool convert dreadnought.whe dreadnought.ebp
    ```
- **Edit .whe without the Object Editor**  
    In case you need to change multiple `.whe` files programmatically you can convert them to `json` format.  
    It's also useful if you want to store a human-readable version of`.whe` in VCS or if you simply like me don't like Object Editor.
    ```bash
    # Contert to .json
    python3 -m dow_utils.object_tool convert dreadnought.whe dreadnought.json
    
    # Edit converted .json here

    # Then convert it back to .whe
    python3 -m dow_utils.object_tool convert dreadnought.json dreadnought_edited.whe
    ```