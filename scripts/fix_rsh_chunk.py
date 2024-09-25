import argparse
import pathlib

from ..lib.chunky import ChunkReader, ChunkHeader, ChunkWriter


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


def force_write(writer: ChunkWriter, data: bytes):
    writer.curr_data_size += len(data)
    return writer.stream.write(data)


def fix_rsh(reader: ChunkReader, writer: ChunkWriter):
    reader.skip_relic_chunky()
    writer.write_struct('<12s3l', b'Relic Chunky', 1706509, 1, 1)
    current_chunk = reader.read_header('FOLDSHRF')
    with writer.start_chunk('FOLDSHRF', name=current_chunk.name):
        for current_chunk in reader.iter_chunks():
            with writer.start_chunk(current_chunk.typeid, name=current_chunk.name):
                match current_chunk.typeid:
                    case 'FOLDTXTR': CH_FOLDTXTR(reader, writer)
                    case 'FOLDSHDR':
                        force_write(writer, reader.stream.read(current_chunk.size))
                    case _: raise Exception('WTF')


def CH_FOLDTXTR(reader: ChunkReader, writer: ChunkWriter):
    current_chunk = reader.read_header('DATAHEAD')
    image_type, num_images = reader.read_struct('<2l')
    # with writer.start_chunk('DATAINFO', name=current_chunk.name):
    #     writer.write_struct('<l', num_images)
    with writer.start_chunk('DATAHEAD', name=current_chunk.name):
        writer.write_struct('<2l', image_type, num_images)
    # with writer.start_chunk('DATAINFO', name=current_chunk.name):
    #     writer.write_struct('<l', num_images)
    foldimag_chunk = reader.read_header('FOLDIMAG')
    foldimag_attr = reader.read_header('DATAATTR')
    image_format, width, height, num_mips = reader.read_struct('<4l')

    with writer.start_chunk('DATAINFO', name=current_chunk.name):
        writer.write_struct('<4l', image_type, width, height, num_images)
    with writer.start_chunk(foldimag_chunk.typeid, name=foldimag_chunk.name):
        with writer.start_chunk(foldimag_attr.typeid, name=foldimag_attr.name):
            writer.write_struct('<4l', image_format, width, height, num_mips)
        foldimag_data = reader.read_header('DATADATA')
        with writer.start_chunk(foldimag_data.typeid, name=foldimag_data.name):
            force_write(writer, reader.stream.read(foldimag_data.size))
    # with writer.start_chunk(current_chunk.typeid, name=current_chunk.name):
    #     force_write(writer, reader.stream.read(current_chunk.size))
    # with writer.start_chunk('DATAINFO', name=current_chunk.name):
    #     writer.write_struct('<l', num_images)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Original .rsh file', type=pathlib.Path)
    parser.add_argument('output', help='Result .rsh file', type=pathlib.Path)
    args = parser.parse_args()
    with open(args.input, 'rb') as f_in, open(args.output, 'wb') as f_out:
        reader = ChunkReader(f_in)
        writer = ChunkWriter(f_out, {
            'FOLDSHRF': {
                'version': 1,
                'FOLDTXTR': {
                    'version': 1,
                    'DATAHEAD': {'version': 1},
                    'DATAINFO': {'version': 3},
                    'FOLDIMAG': {
                        'version': 1,
                        'DATAATTR': {'version': 2},
                        'DATADATA': {'version': 2},
                    }
                },
                'FOLDSHDR': {
                    'version': 1,
                    'DATAINFO': {'version': 1},
                    'DATACHAN': {'version': 3},
                }
            }
        })
        fix_rsh(reader, writer)
