import argparse
import json
import pathlib

from ..lib.rsh import load_rsh

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Original .rsh file', type=pathlib.Path)
    parser.add_argument('output', help='Result .json file', type=pathlib.Path)
    args = parser.parse_args()
    parsed = load_rsh(path=args.input)
    with open(args.output, 'w') as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)
