import io
import struct

from ..chunky import ChunkReader, ChunkHeader


def write_dds(
    src: io.BufferedIOBase,
    dst: io.BufferedIOBase,
    data_size: int,
    width: int,
    height: int,
    num_mips: int,
    image_format: int,
):
    _DOW_DXT_FLAGS = 0x000A1007  # _DEFAULT_FLAGS | _dwF_MIPMAP | _dwF_LINEAR
    _ddsF_FOURCC = 0x00000004
    _DOW_DDSCAPS_FLAGS = 0x401008 # _ddscaps_F_TEXTURE | _ddscaps_F_COMPLEX | _ddscaps_F_MIPMAP_S
    fourCC = {8: b'DXT1', 10: b'DXT3', 11: b'DXT5'}[image_format]
    header = struct.Struct('<4s 7l 44x 2l 4s 20x 2l 12x').pack(
        b'DDS ', 124, _DOW_DXT_FLAGS, height, width, data_size, 0, num_mips, 
        32, _ddsF_FOURCC, fourCC,  # pixel format
        _DOW_DDSCAPS_FLAGS, 0,  # ddscaps
    )
    dst.write(header)
    dst.write(src.read(data_size))


def write_tga(
    src: io.BufferedIOBase,
    dst: io.BufferedIOBase,
    data_size: int,
    width: int,
    height: int,
    grayscale: bool = False
):
    # See http://www.paulbourke.net/dataformats/tga/
    header = struct.Struct('<3B 2HB 4H2B').pack(
        0,  # ID length
        0,  # file contains no color map
        3 if grayscale else 2,  # uncompressed grayscale image
        0, 0, 32,  # Color Map Specification
        0, 0, width, height, 8 if grayscale else 32, 0,  # Image Specification.
    )
    dst.write(header)
    dst.write(src.read(data_size))



def header_to_dict(header: ChunkHeader, parent_dict: dict = None) -> dict:
    res = {
        'typeid': header.typeid,
        'name': header.name,
    }
    if header.typeid.startswith('FOLD'):
        res['children'] = []
    else:
        res['data'] = {}
    if parent_dict is not None:
        parent_dict['children'].append(res)
    return res


def load_rtx(reader: ChunkReader | None = None, path: str | None = None, img_bytes: bool = False) -> dict:
    if reader is None:
        assert path is not None
        reader = ChunkReader(open(path, 'rb'))
    reader.skip_relic_chunky()
    current_chunk = reader.read_header('FOLDTXTR')
    return CH_FOLDTXTR(reader, current_chunk, img_bytes=img_bytes)


def CH_FOLDTXTR(reader: ChunkReader, parent_chunk: ChunkHeader, img_bytes: bool = False) -> dict:
    result = header_to_dict(parent_chunk)
    current_chunk = reader.read_header('DATAHEAD')
    curr_data = header_to_dict(current_chunk, result)['data']
    curr_data['image_type'], curr_data['num_images'] = reader.read_struct('<2l')
    current_chunk = reader.read_header('FOLDIMAG')
    foldimag_data = header_to_dict(current_chunk, result)
    current_chunk = reader.read_header('DATAATTR')
    curr_data = header_to_dict(current_chunk, foldimag_data)['data']
    curr_data['image_format'], curr_data['width'], curr_data['height'], curr_data['num_mips'] = reader.read_struct('<4l')
    result['format_str'] = 'tga' if curr_data['image_format'] in (0, 2) else 'dds'
    current_chunk = reader.read_header('DATADATA')
    if img_bytes:
        reader.skip(current_chunk.size)  # dds data
    else:
        data = io.BytesIO()
        if result['format_str'] == 'tga':
            write_tga(reader.stream, data, current_chunk.size, curr_data['width'], curr_data['height'])
        else:
            write_dds(reader.stream, data, current_chunk.size, curr_data['width'], curr_data['height'], curr_data['num_mips'], curr_data['image_format'])
        result['image_bytes'] = data.getbuffer()
    curr_data = header_to_dict(current_chunk, foldimag_data)['data']
    return result