import multiprocessing
import pathlib
import sys

from dow_utils.rtx_converter.gui import converter_window


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    elif __file__:
        app_path = __file__
    files_root = pathlib.Path(app_path).parent
    converter_window(files_root)
