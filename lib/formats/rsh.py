from ..chunky import ChunkReader, ChunkHeader
from .rtx import CH_FOLDTXTR


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


def load_rsh(reader: ChunkReader | None = None, path: str | None = None) -> dict:
    if reader is None:
        assert path is not None
        reader = ChunkReader(open(path, 'rb'))
    reader.skip_relic_chunky()
    current_chunk = reader.read_header('FOLDSHRF')
    result = header_to_dict(current_chunk)
    for current_chunk in reader.iter_chunks():
        data = None
        match current_chunk.typeid:
            case 'FOLDTXTR': data = CH_FOLDTXTR(reader, current_chunk)
            case 'FOLDSHDR': data = CH_FOLDSHDR(reader, current_chunk)
            case _: reader.skip(current_chunk.size)
        if data is not None:
            result['children'].append({
                **header_to_dict(current_chunk),
                **data,
            })
    return result


def CH_FOLDSHDR(reader: ChunkReader, parent_chunk: ChunkHeader) -> dict:
    result = header_to_dict(parent_chunk)
    current_chunk = reader.read_header('DATAINFO')
    curr_data = header_to_dict(current_chunk, result)['data']
    curr_data['num_images'], *curr_data['info_bytes'] = reader.read_struct('<2L 4B L B')

    for img_idx in range(curr_data['num_images']):
        current_chunk = reader.read_header('DATACHAN')
        curr_data = header_to_dict(current_chunk, result)['data']
        curr_data['channel_idx'], curr_data['method'], *curr_data['colour_mask'] = reader.read_struct('<2l4B')
        curr_data['channel_name'] = reader.read_str()
        curr_data['unk1'], curr_data['num_coords'], curr_data['unk2'] = reader.read_struct('<l l l')
        curr_data['floats'] = []
        for _ in range(4):
            for ref_idx in range(4):
                x, y = reader.read_struct('<2f')
                curr_data['floats'].extend((x, y))
    return result
