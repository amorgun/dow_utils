import argparse
import re
import json
import pathlib


def compare_indexes(path_before: pathlib.Path, path_after: pathlib.Path, dst_path: pathlib.Path, ignore_patterns=list[str]):
    diff = []

    with path_before.open('r') as f:
        index_before = json.load(f)

    with path_after.open('r') as f:
        index_after = json.load(f)

    def walk(curr_path: str, data_before: dict, data_after: dict):
        if data_before is None:
            diff.append(('ADDED', curr_path))
            return
        if data_after is None:
            diff.append(('REMOVED', curr_path))
            return
        if 'HASH' in data_before or 'HASH' in data_after:
            if data_before.get('HASH') != data_after.get('HASH'):
                diff.append(('CHANGED', curr_path))
            return
        for key in sorted(data_before.keys() | data_after.keys()):
            walk(f'{curr_path}/{key}', data_before.get(key), data_after.get(key))

    walk('', index_before, index_after)

    with dst_path.open('w') as f:
        for diff, path in diff:
            for pattern in ignore_patterns:
                if re.fullmatch(pattern, path):
                    break
            else:
                f.write(f'{diff:<7} {path}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('before', help='Index before', type=pathlib.Path)
    parser.add_argument('after', help='Index after', type=pathlib.Path)
    parser.add_argument('output', help='Result file with the diff', type=pathlib.Path)
    args = parser.parse_args()
    compare_indexes(args.before, args.after, args.output, ignore_patterns=[
        # '/Data/Scenarios/*.ter',  # files that set up campaign skirmish battles and hold other territory info like what honor guard and how much planetary requisition it gives
        r'/Data/Scenarios/.*\.sgb',
        r'.*\.dds',  # images
        r'.*\.tga',  # images
        r'.*\.rsh',  # textures
        r'.*\.rtx',  # textures
        r'.*\.fda',  # sound effects from dawn of war 1
        r'.*\.rat',  # Relic Audio Tool, sound files round 1, sound effects.
    ])
