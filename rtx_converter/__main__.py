import pathlib

from .gui import converter_window


if __name__ == '__main__':
    converter_window(files_root=pathlib.Path(__file__).parent)
