import argparse
import pathlib

from .converters import convert


def convert_file(args):
    return convert(args.input, args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert object data between different formats')
    parser.add_argument('input', help='Original file', type=pathlib.Path)
    parser.add_argument('output', help='Converted file', type=pathlib.Path)
    parser.set_defaults(func=convert_file)
    args = parser.parse_args()
    args.func(args)
