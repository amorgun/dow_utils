import json
import pathlib
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import webbrowser

# from tkinterdnd2 import DND_FILES, TkinterDnD

from .converters import convert, FILE_READERS, FILE_WRITERS


def start_window(files_root: pathlib.Path):
    data_path = files_root / 'object_tool_data.json'
    initialdir = None
    # root = TkinterDnD.Tk(className='Object Tool - Convert')
    root = tk.Tk(className='Object Tool - Convert')
    root.title('Dawn of War Object Tool - Convert')
    mainframe = ttk.Frame(root)
    mainframe.grid(column=0, row=0)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    file_path = tk.StringVar()
    ttk.Label(mainframe, text='File:').grid(column=0, row=0, padx=6, sticky=tk.E)
    file_path_entry = ttk.Entry(mainframe, width=28, textvariable=file_path)
    file_path_entry.grid(column=1, row=0, columnspan=2)
    # ttk.Label(mainframe, text='You cant drag a file here').grid(column=0, row=1, columnspan=2, padx=3, sticky=tk.E)

    def set_filename(filename: str):
        file_path.set(filename)
        file_path_entry.xview(tk.END)

    # root.drop_target_register(DND_FILES)
    # root.dnd_bind('<<Drop>>', lambda e: print(e))

    def select_file():
        filename = filedialog.askopenfilename(initialdir=initialdir, filetypes=[('Object file', ' '.join(fmt for fmt in FILE_READERS))])
        if filename:
            set_filename(filename)

    ttk.Button(mainframe, text='Select', command=select_file).grid(column=3, row=0)

    convert_to = tk.StringVar()
    convert_to.set(next(iter(FILE_WRITERS)))

    ttk.Label(mainframe, text='Convert to:').grid(column=0, row=1, padx=6, sticky=tk.E)
    tk.OptionMenu(mainframe, convert_to, *list(FILE_WRITERS)).grid(column=1, row=1, sticky=tk.W)

    def start(arg=None):
        path = pathlib.Path(file_path.get().strip())
        if not path.is_file():
            messagebox.showerror('No such file', f'File {path} does not exist')
            return
        
        dst_path = path.with_suffix(convert_to.get())
        
        if dst_path.is_dir():
            messagebox.showerror('Cannot convert', f'{dst_path.name} is a directory')
            return

        if dst_path.is_file():
            res = messagebox.askokcancel('File exists', f'Do you want to overwrite file {dst_path.name}?')
            if not res:
                return

        nonlocal initialdir
        initialdir = str(path.parent)
        with data_path.open('w', encoding='utf8') as f:
            json.dump({
                'initialdir': initialdir,
                'format': convert_to.get(),
            }, f, indent=2, ensure_ascii=False)
        try:
            convert(path, dst_path)
        except Exception as e:
            messagebox.showerror('Cannot convert', f'Error: {e}')
            raise
        messagebox.showinfo('Success', f'Converted file is saved to {dst_path}')

    start_btn = ttk.Button(mainframe, text='Convert', command=start, state='disabled')
    start_btn.grid(column=1, row=11, pady=4, columnspan=2)

    def can_start():
        return file_path.get().strip()

    def on_file_path_set(name, idx, mode):
        start_btn['state'] = 'normal' if can_start() else 'disabled'

    file_path.trace_add('write', on_file_path_set)
    
    def show_about():
        def dismiss():
            dlg.grab_release()
            dlg.destroy()

        dlg = tk.Toplevel(root)
        ttk.Label(dlg, text='Object Tool v0.4').grid(pady=(10, 0))
        ttk.Label(dlg, text='The source code is available on Github:').grid()
        link = ttk.Label(dlg, text='https://github.com/amorgun/dow_utils/tree/main/object_tool', foreground='blue', cursor='hand2')
        link.grid(padx=6)
        link.bind("<ButtonRelease-1>", lambda e: webbrowser.open('https://github.com/amorgun/dow_utils/tree/main/object_tool'))
        ttk.Label(dlg, text='Go leave a star there!').grid(pady=(0, 10))
        ttk.Button(dlg, text='Ok', command=dismiss).grid()
        dlg.protocol('WM_DELETE_WINDOW', dismiss)
        dlg.transient(root)
        dlg.resizable(False, False)
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.wait_window()

    menubar = tk.Menu(root, tearoff=False)
    root['menu'] = menubar
    menubar.add_command(label="About",command=show_about)
    
    file_path_entry.focus()
    mainframe.columnconfigure(1, weight=1, minsize=100)
    mainframe.rowconfigure(0, weight=1)
    root.bind("<Return>", lambda _: start() if can_start() else None)
    root.minsize(250, 80)
    root.resizable(False, False)

    if data_path.is_file():
        try:
            with data_path.open('r', encoding='utf8') as f:
                data = json.load(f)
            initialdir = data.get('initialdir')
            convert_to.set(data.get('format', convert_to.get()))
        except json.JSONDecodeError as e:
            pass

    root.mainloop()


if __name__ == '__main__':
    start_window(pathlib.Path(__file__).parent)
