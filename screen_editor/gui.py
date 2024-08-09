import json
import logging
import multiprocessing
import pathlib
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import urllib.request
import webbrowser

from .app import start_editor


DEFAULT_PORT = 5055


def start_server(*args, files_root=None, **kwargs):
    logging.getLogger().handlers.append(logging.FileHandler(files_root / 'screen_editor.log', 'w'))
    try:
        start_editor(*args, files_root=files_root, **kwargs)
    except Exception as e:
        logging.exception(f'ERROR')


def select_dir(var, entry):
    dirname = filedialog.askdirectory()
    var.set(dirname)
    entry.xview(tk.END)


def start_window(files_root: pathlib.Path):
    print(f'{files_root=}')
    multiprocessing.set_start_method('spawn')
    data_path = files_root / 'screen_editor_data.json'
    root = tk.Tk()
    root.title('Dawn of War Screen Viewer')
    mainframe = ttk.Frame(root)
    mainframe.grid(column=0, row=0)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    mod_path = tk.StringVar()
    ttk.Label(mainframe, text='Mod path:').grid(column=0, row=0, padx=6, sticky=tk.E)
    mod_path_entry = ttk.Entry(mainframe, width=28, textvariable=mod_path)
    mod_path_entry.grid(column=1, row=0, columnspan=2)
    ttk.Button(mainframe, text='Select', command=lambda: select_dir(mod_path, mod_path_entry)).grid(column=3, row=0)

    ui_mode = tk.StringVar(value='simple')
    ttk.Label(mainframe, text='Mode:').grid(column=0, row=10, sticky=tk.E)
    ttk.Radiobutton(mainframe, text='Simple', variable=ui_mode, value='simple').grid(column=1, row=10)
    ttk.Radiobutton(mainframe, text='Advanced', variable=ui_mode, value='advanced').grid(column=2, row=10)

    screen_dir = tk.StringVar()
    screen_label = ttk.Label(mainframe, text='Screens dir:')
    screen_dir_entry = ttk.Entry(mainframe, width=28, textvariable=screen_dir)
    scrren_select_btn = ttk.Button(mainframe, text='Select', command=lambda: select_dir(screen_dir, screen_dir_entry))

    port = tk.IntVar(value=DEFAULT_PORT)
    port_label = ttk.Label(mainframe, text='Port:')
    port_entry = ttk.Spinbox(mainframe, textvariable=port, from_=1024, to=65535, width=5)
    
    def on_mode_change(name, idx, mode):
        if ui_mode.get() == 'simple':
            screen_label.grid_forget()
            screen_dir_entry.grid_forget()
            scrren_select_btn.grid_forget()
            port_label.grid_forget()
            port_entry.grid_forget()
        else:
            screen_label.grid(column=0, row=1, sticky=tk.E)
            screen_dir_entry.grid(column=1, row=1, columnspan=2)
            scrren_select_btn.grid(column=3, row=1)
            port_label.grid(column=0, row=2, sticky=tk.E)
            port_entry.grid(column=1, row=2, sticky=tk.W)
        start_btn['state'] = 'normal' if can_start() else 'disabled'

    ui_mode.trace_add('write', on_mode_change)

    def start(arg=None):
        path = pathlib.Path(mod_path.get().strip())
        if not path.is_dir():
            messagebox.showerror('No such directory', f'Directory {path} does not exist')
            return
        screen_path = pathlib.Path(screen_dir.get().strip()) if ui_mode.get() == 'advanced' else path / 'Data/art/ui/screens'
        if not screen_path.is_dir():
            messagebox.showerror('No such directory', f'Directory {screen_path} does not exist')
            return
        
        app_port = port.get() if ui_mode.get() == 'advanced' else DEFAULT_PORT

        with data_path.open('w') as f:
            json.dump({
                'mod_path': str(path),
                'screen_dir': screen_dir.get().strip(),
                'ui_mode': ui_mode.get(),
                'port': port.get(),
            }, f, indent=2, ensure_ascii=False)

        process = multiprocessing.Process(
                target=start_server,
                args=(path, screen_path),
                kwargs=dict(
                    port=app_port,
                    use_reloader=False,
                    files_root=files_root,
                ),
                daemon=True,
        )
        process.start()

        def dismiss():
            process.terminate()
            dlg.grab_release()
            dlg.destroy()

        dlg = tk.Toplevel(root)
        text_label = ttk.Label(dlg, text='Starting a web server')
        text_label.grid(column=0, row=1, pady=(10, 0), padx=5)

        num_steps = 15
        pbar = ttk.Progressbar(dlg, orient="horizontal", mode="determinate", maximum=num_steps)
        pbar.grid(column=0, row=10)

        stop_btn = ttk.Button(dlg, text='Cancel', command=dismiss)
        stop_btn.grid(column=0, row=20, pady=10)
        
        server_url = f'http://127.0.0.1:{app_port}/ping'

        def ping_server(step=0):
            force_stop = False
            if not process.is_alive():
                force_stop = True
            success = False
            try:
                resp = urllib.request.urlopen(server_url, timeout=1000)
                success = resp.status == 200
            except urllib.error.URLError:
                pass
            if success:
                text_label['text'] = 'Web server started. Open this link in your browser:'
                link = ttk.Label(dlg, text=f'http://127.0.0.1:{app_port}', foreground='blue', cursor='hand2')
                link.grid(column=0, row=2, padx=6)
                link.bind("<ButtonRelease-1>", lambda e: webbrowser.open(f'http://127.0.0.1:{app_port}'))
                ttk.Label(dlg, text='Close this window to stop the server').grid(column=0, row=3, padx=6)
                stop_btn['text'] = 'Stop'
                pbar.grid_forget()
                return
            steps_done = step + 1
            pbar['value'] = steps_done
            if not force_stop and steps_done < num_steps:
                dlg.after(1000, ping_server, steps_done)
            else:
                text_label['text'] = '    Cannot start the web server.\nCheck scrrent_editor.log for errors.'
                stop_btn['text'] = 'Close'
                pbar.grid_forget()

        ping_server()

        dlg.protocol('WM_DELETE_WINDOW', dismiss)
        dlg.transient(root)
        dlg.resizable(False, False)
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.wait_window()

    start_btn = ttk.Button(mainframe, text='Start', command=start, state='disabled')
    start_btn.grid(column=1, row=11, pady=4, columnspan=2)

    def can_start():
        return mod_path.get().strip() and (ui_mode.get() == 'simple' or screen_dir.get().strip())

    def on_mod_path_set(name, idx, mode):
        start_btn['state'] = 'normal' if can_start() else 'disabled'

    mod_path.trace_add('write', on_mod_path_set)
    screen_dir.trace_add('write', on_mod_path_set)
    
    def show_about():
        def dismiss():
            dlg.grab_release()
            dlg.destroy()

        dlg = tk.Toplevel(root)
        ttk.Label(dlg, text='The source code is available on Github:').grid(pady=(10, 0))
        link = ttk.Label(dlg, text='https://github.com/amorgun/dow_utils/tree/main/screen_editor', foreground='blue', cursor='hand2')
        link.grid(padx=6)
        link.bind("<ButtonRelease-1>", lambda e: webbrowser.open('https://github.com/amorgun/dow_utils/tree/main/screen_editor'))
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
    
    mod_path_entry.focus()
    mainframe.columnconfigure(1, weight=1, minsize=100)
    mainframe.rowconfigure(0, weight=1)
    root.bind("<Return>", lambda _: start() if can_start() else None)
    root.minsize(250, 80)
    root.resizable(False, False)

    if data_path.is_file():
        try:
            with data_path.open('r') as f:
                data = json.load(f)
            mod_path.set(data.get('mod_path', ''))
            if 'ui_mode' in data:
                ui_mode.set(data['ui_mode'])
            screen_dir.set(data.get('screen_dir', ''))
            if 'port' in data:
                port.set(data['port'])
        except json.JSONDecodeError:
            pass

    root.mainloop()


if __name__ == '__main__':
    start_window(pathlib.Path(__file__).parent)
