import multiprocessing
import pathlib
import sys

from dow_utils.object_tool.convert.gui import start_window


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    elif __file__:
        app_path = __file__
    files_root = pathlib.Path(app_path).parent
    start_window(files_root)
