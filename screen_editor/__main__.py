import argparse
import pathlib

from .app import start_editor


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mod_dir', help='Folder with the mod data', type=pathlib.Path)
    parser.add_argument('screen_dir', help='Folder with .screen files', type=pathlib.Path, default=None, nargs='?')
    args = parser.parse_args()
    screen_dir = args.screen_dir
    start_editor(args.mod_dir, screen_dir, files_root=pathlib.Path(__file__).parent)
