import enum
import io
import pathlib
import struct

from ..chunky import ChunkReader


@enum.unique
class RgdDataType(enum.IntEnum):
    FLOAT = 0
    INTEGER = 1
    BOOL = 2
    STRING = 3
    WSTRING = 4
    TABLE = 100
    NO_DATA = 254


class RgdParser:
    def __init__(self, dict_path: str | pathlib.Path = None):
        self.dict_path = dict_path or pathlib.Path(__file__).parent / 'RGD_DIC.TXT'
        self.hash_dict = self.read_hash_dict(self.dict_path)

    def parse(self, reader: ChunkReader) -> dict:
        reader.skip_relic_chunky()
        current_chunk = reader.read_header('DATAAEGD')
        unk, data_size = reader.read_struct('<2L')
        return self.read_entry(reader, RgdDataType.TABLE, data_size)

    def parse_bytes(self, data: bytes) -> dict:
        with io.BytesIO(data) as f:
            reader = ChunkReader(f)
            return self.parse(reader)

    def read_entry(self, reader: ChunkReader, type_: RgdDataType, data_size: int) -> float | int | bool | dict:
        match type_:
            case RgdDataType.TABLE:
                num_entries = reader.read_one('<L')
                entries = []
                header_size = 4 + num_entries * 12
                for _ in range(num_entries):
                    hash_, entry_type_, offset = reader.read_struct('<3L')
                    entry_type_ = RgdDataType(entry_type_)
                    entries.append((self.hash_dict[hash_], entry_type_, offset))
                entries.sort(key=lambda x: x[2])
                result = {}
                if not num_entries:
                    return result
                assert entries[0][2] == 0
                for idx, (name, entry_type_, offset) in enumerate(entries):
                    entry_end = entries[idx + 1][2] if idx < len(entries) - 1 else data_size - header_size
                    result[name] = self.read_entry(reader, entry_type_, entry_end - offset)
                return dict(sorted(result.items()))
            case RgdDataType.STRING:
                return str(reader.read_one(f'{data_size}s'), 'ascii').rstrip('\0')
            case RgdDataType.WSTRING:
                return str(reader.read_one(f'{data_size}s'), 'utf16').rstrip('\0')
            case RgdDataType.FLOAT:
                fmt = '<f'
            case RgdDataType.INTEGER:
                fmt = '<L'
            case RgdDataType.BOOL:
                fmt = '<B'
            case _:
                raise Exception(type_)
                reader.skip(data_size)
                return type_
        result = reader.read_one(fmt)
        reader.skip(data_size - struct.calcsize(fmt))
        return result

    def read_hash_dict(self, path: str | pathlib.Path) -> dict:
        res = {}
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line[0] == '#':
                    continue
                key, val = line.split('=', 1)
                res[int(key, 16)] = val
        return res


def load_rgd(reader: ChunkReader | None = None, path: str | None = None) -> dict:
    if reader is None:
        assert path is not None
        reader = ChunkReader(open(path, 'rb'))
    return RgdParser().parse(reader)
