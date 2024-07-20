import argparse
import json
import hashlib
import pathlib


def make_index(src_folder: pathlib.Path, dst_path: pathlib.Path):
    result = {}

    def walk(path: pathlib.Path, result_data: dict):
        if path.is_dir():
            for child in path.iterdir():
                walk(child, result_data.setdefault(path.name, {}))
        else:
            digest = hashlib.md5()
            with path.open('rb') as f:
                while chunk := f.read(8192):
                    digest.update(chunk)

            result_data[path.name] = {
                'HASH': digest.hexdigest(),
                'SIZE': path.stat().st_size,
                # 'IS_FILE': True,
            }

    walk(src_folder, result)

    with dst_path.open('w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='Original folder', type=pathlib.Path)
    parser.add_argument('output', help='Result file with the index', type=pathlib.Path)
    args = parser.parse_args()
    make_index(args.folder, args.output)
