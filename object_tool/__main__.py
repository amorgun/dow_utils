import argparse
import pathlib

from .convert import convert


def convert_file(args):
    return convert(args.input, args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    parser_convert = subparsers.add_parser('convert', help='Convert object data between different formats')
    parser_convert.add_argument('input', help='Original file', type=pathlib.Path)
    parser_convert.add_argument('output', help='Converted file', type=pathlib.Path)
    parser_convert.set_defaults(func=convert_file)
    args = parser.parse_args()
    args.func(args)
