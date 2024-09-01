import pathlib

from ...lib.formats import whe

FILE_READERS = {
    '.whe': whe.read_whe,
    '.json': whe.read_json,
    '.lua': whe.read_lua,
}

FILE_WRITERS = {
    '.json': whe.write_json,
    '.lua': whe.write_lua,
    '.whe': lambda data, filename: whe.write_format(data, filename, whe.ExportFormat.WHE),
    '.ebp': lambda data, filename: whe.write_format(data, filename, whe.ExportFormat.EBP),
}


def convert(src: pathlib.Path, dst: pathlib.Path):
    file_reader = FILE_READERS[src.suffix]
    parsed = file_reader(src)
    file_writer = FILE_WRITERS[dst.suffix]
    file_writer(parsed, dst)
