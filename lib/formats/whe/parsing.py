import contextlib
import datetime
import enum
import io
import json
import pathlib
import typing

from ...chunky import ChunkReader, ChunkHeader, ChunkWriter
from ...slpp import slpp, SLPP
from . import data as d


T = typing.TypeVar('T')


class Parser:
    def parse(self, reader: ChunkReader) -> d.ObjectData:
        result = d.ObjectData()
        reader.skip_relic_chunky()   # Skip 'Relic Chunky' Header
        header = reader.read_header('DATAFBIF')  # Read 'File Burn Info' Header
        tool_name = reader.read_str()
        unk = reader.read_one('<L')  # zero
        result.burn_info = d.BurnInfo(
            tool=tool_name,
            username=reader.read_str(errors='ignore'),
            date=reader.read_str(),
        )
        header = reader.read_header('FOLDREBP')  # Skip 'Folder EBP' Header
        for current_chunk in reader.iter_chunks():  # Read Chunks Until End Of File
            match current_chunk.typeid:
                case 'FOLDEVCT': result.events = self.parse_list(reader, current_chunk, self.parse_event)
                case 'FOLDCLST': result.clauses = self.parse_list(reader, current_chunk, self.parse_clause)
                case 'FOLDCONL': result.conditions = self.parse_list(reader, current_chunk, self.parse_condition)
                case 'FOLDMODL': result.modifiers = self.parse_list(reader, current_chunk, self.parse_modifier)
                case 'FOLDMTRE': result.motions = self.parse_list(reader, current_chunk, self.parse_motion)
                case 'DATAACTS': result.actions = self.parse_actions(reader)
                case 'DATASEUI': result.selected_ui = self.parse_selected_ui(reader)
                case 'FOLDANIM': 
                    anim = self.parse_xrefed_animation(reader, current_chunk)
                    result.xrefed_animations[anim.name] = anim
                case _: 
                    raise Exception(f'UNK CHUNK {current_chunk.typeid}')
                    reader.skip(current_chunk.size)  # Skipping Chunks By Default
        result.resolve_links()
        return result

    def parse_bytes(self, data: bytes) -> dict:
        with io.BytesIO(data) as f:
            reader = ChunkReader(f)
            return self.parse(reader)

    def parse_list(self,
                   reader: ChunkReader,
                   header: ChunkHeader,
                   parse_fn: typing.Callable[[ChunkReader, ChunkHeader], T]) -> dict[str, T]:
        folder_reader = reader.read_folder(header)
        result = {}
        for current_chunk in folder_reader.iter_chunks():
            result[current_chunk.name] = parse_fn(folder_reader, current_chunk)
        return result
    
    def parse_event(self, reader: ChunkReader, header: ChunkHeader) -> d.Event:
        assert header.typeid == 'DATAEVNT', header.typeid
        num_props = reader.read_one('<L')
        return d.Event(
            name=header.name,
            properties=[d.Event.Property(param=reader.read_str(), value=reader.read_str()) for _ in range(num_props)]
        )
    
    def parse_clause(self, reader: ChunkReader, header: ChunkHeader) -> d.Clause:
        assert header.typeid == 'DATACLAS', header.typeid
        type = d.Clause.Type(reader.read_one('<L'))
        variable = reader.read_str()
        comparison = d.Clause.Comparison(reader.read_one('<L'))
        match type:
            case d.Clause.Type.FLOAT: 
                value, default = reader.read_struct('<2f')
                value, default = value * 100, default * 100
            case d.Clause.Type.BOOLEAN: value, default = map(bool, reader.read_struct('2B'))
            case d.Clause.Type.STRING: value, default = reader.read_str(), reader.read_str()
        return d.Clause(name=header.name, type=type, variable=variable, comparison=comparison, value=value, default=default)
    
    def parse_condition(self, reader: ChunkReader, header: ChunkHeader) -> d.Condition:
        assert header.typeid == 'DATACOND', header.typeid
        num_clauses = reader.read_one('<L')
        return d.Condition(
            name=header.name,
            clauses=[reader.read_str() for _ in range(num_clauses)]
        )

    def parse_modifier(self, reader: ChunkReader, header: ChunkHeader) -> d.Modifier:
        assert header.typeid == 'DATAMODF', header.typeid
        return d.Modifier(
            name=header.name, 
            variable=reader.read_str(),
            type=d.Modifier.Type(reader.read_one('<L')),
            ref_value=reader.read_one('<f') * 100,
            default=reader.read_one('<f') * 100,
        )

    def parse_motion(self, reader: ChunkReader, header: ChunkHeader) -> d.Motion:
        assert header.typeid == 'DATAMTON', header.typeid
        num_animations = reader.read_one('<L')
        animations = [reader.read_str() for _ in range(num_animations)]
        num_random_motions = reader.read_one('<L')
        random_motions = []
        for _ in range(num_random_motions):
             name, weight = reader.read_str(), reader.read_one('<f')
             random_motions.append(d.Motion.RandomMotion(name, weight))
        randomize_each_loop = bool(reader.read_one('<B'))
        num_events = reader.read_one('<L')
        events = []
        for _ in range(num_events):
             name, time = reader.read_str(), reader.read_one('<f')
             if time in set(d.Motion.MotionEvent.Time):
                 time = d.Motion.MotionEvent.Time(time)
             events.append(d.Motion.MotionEvent(name, time))
        
        type = d.Motion.Type(reader.read_one('<L'))
        start_delay = reader.read_struct('<2f')
        loop_delay  = reader.read_struct('<2f')
        transition_out = reader.read_one('<f')
        inset = reader.read_struct('<2f')
        exit_delay = reader.read_struct('<2f')
        ignore_exit_delay = bool(reader.read_one('<B'))
        ignore_transitions = bool(reader.read_one('<B'))
        has_modifier = bool(reader.read_one('<B'))
        modifier = reader.read_str() if has_modifier else None

        return d.Motion(
            name=header.name,
            animations=animations,
            random_motions=random_motions,
            randomize_each_loop=randomize_each_loop,
            events=events,
            type=type,
            start_delay=start_delay,
            loop_delay=loop_delay,
            exit_delay=exit_delay,
            inset=inset,
            transition_out=transition_out,
            ignore_exit_delay=ignore_exit_delay,
            ignore_transitions=ignore_transitions,
            modifier=modifier,
        )
    
    def parse_actions(self, reader: ChunkReader) -> dict[str, d.Action]:
        result = {}
        num_actions = reader.read_one('<L')
        for _ in range(num_actions):
            action_name = reader.read_str()
            num_motions = reader.read_one('<L')
            motions = []
            for __ in range(num_motions):
                motion_name = reader.read_str()
                compare_type = d.Action.CompareType(reader.read_one('<L'))
                condition_name = reader.read_str() if compare_type not in (d.Action.CompareType.NONE, d.Action.CompareType.ELSE) else None
                motions.append(d.Action.ActionMotion(motion=motion_name, compare_type=compare_type, condition=condition_name))
            num_subactions = reader.read_one('<L')
            subactions = []
            for __ in range(num_subactions):
                subaction_name = reader.read_str()
                compare_type = d.Action.CompareType(reader.read_one('<L'))
                condition_name = reader.read_str() if compare_type not in (d.Action.CompareType.NONE, d.Action.CompareType.ELSE) else None
                subactions.append(d.Action.Subaction(action=subaction_name, compare_type=compare_type, condition=condition_name))
            result[action_name] = d.Action(name=action_name, motions=motions, subactions=subactions)
        return result
    
    def parse_selected_ui(self, reader: ChunkReader) -> d.SelectedUi:
        return d.SelectedUi(
            display_type=d.SelectedUi.DisplayType(reader.read_one('<L')),
            scale=d.VecftorXZ(*reader.read_struct('<2f')),
            offset=d.VecftorXZ(*reader.read_struct('<2f')),
            volume_offset=d.VecftorXYZ(*reader.read_struct('<3f')),
            volume_scale=d.VecftorXYZ(*reader.read_struct('<3f')),
            matrix=[reader.read_struct('<3f') for _ in range(3)],
    )

    def parse_xrefed_animation(self, reader: ChunkReader, header: ChunkHeader) -> d.AnimationXref:
        reader.read_header('DATAXREF')
        src_path, src_name = reader.read_str(), reader.read_str()
        dataanbv = reader.read_header('DATAANBV')
        reader.skip(dataanbv.size)
        return d.AnimationXref(
            name=header.name,
            source_path=src_path,
            source_name=src_name,
        )


@enum.unique
class ExportFormat(enum.Enum):
    WHE = enum.auto()
    EBP = enum.auto()


class Exporter:
    def __init__(self, format: ExportFormat = ExportFormat.WHE) -> None:
        self.format = format

    def export(self, data: d.ObjectData, writer: ChunkWriter):
        self.write_relic_chunky(writer)
        if self.format is ExportFormat.WHE:
            self.write_meta(writer, data.burn_info.username)
        with writer.start_chunk('FOLDREBP'):
            for anim in data.xrefed_animations.values():
                with writer.start_chunk('FOLDANIM', name=anim.name):
                    with writer.start_chunk('DATAXREF'):
                        writer.write_str(anim.source_path)
                        writer.write_str(anim.source_name)
                    with writer.start_chunk('DATAANBV', name=anim.name):
                        writer.write_struct('<24x')
            with writer.start_chunk('FOLDEVCT'):
                for e in data.events.values():
                    with writer.start_chunk('DATAEVNT', name=e.name):
                        writer.write_struct('<L', len(e.properties))
                        for p in e.properties:
                            writer.write_str(p.param)
                            writer.write_str(p.value)
            with writer.start_chunk('FOLDCLST'):
                for c in data.clauses.values():
                    with writer.start_chunk('DATACLAS', name=c.name):
                        writer.write_struct('<L', c.type)
                        writer.write_str(c.variable)
                        writer.write_struct('<L', c.comparison)
                        match c.type:
                            case d.Clause.Type.FLOAT: writer.write_struct('<2f', c.value / 100., c.default / 100.)
                            case d.Clause.Type.BOOLEAN: writer.write_struct('<2B', c.value, c.default)
                            case d.Clause.Type.STRING:
                                writer.write_str(c.value)
                                writer.write_str(c.default)
            with writer.start_chunk('FOLDCONL'):
                for c in data.conditions.values():
                    with writer.start_chunk('DATACOND', name=c.name):
                        writer.write_struct('<L', len(c.clauses))
                        for cl in c.clauses:
                                writer.write_str(cl.name)
            with writer.start_chunk('FOLDMODL'):
                for m in data.modifiers.values():
                    with writer.start_chunk('DATAMODF', name=m.name):
                        writer.write_str(m.variable)
                        writer.write_struct('<Lff', m.type, m.ref_value / 100., m.default / 100.)
            with writer.start_chunk('FOLDMTRE'):
                for m in data.motions.values():
                    with writer.start_chunk('DATAMTON', name=m.name):
                        writer.write_struct('<L', len(m.animations))
                        for a in m.animations:
                            writer.write_str(a)
                        writer.write_struct('<L', len(m.random_motions))
                        for rm in m.random_motions:
                            writer.write_str(rm.motion.name)
                            writer.write_struct('<f', rm.weight)
                        writer.write_struct('<B', m.randomize_each_loop)
                        writer.write_struct('<L', len(m.events))
                        for e in m.events:
                            writer.write_str(e.event.name)
                            writer.write_struct('<f', e.time)
                        writer.write_struct(
                            '<L 2f 2f f 2f 2f 3B', m.type, *m.start_delay, *m.loop_delay, m.transition_out,
                            *m.inset, *m.exit_delay, m.ignore_exit_delay, m.ignore_transitions, m.modifier is not None
                        )
                        if m.modifier is not None:
                            writer.write_str(m.modifier.name)
            with self.start_chunk(writer, ExportFormat.WHE, 'DATAACTS'), \
                self.start_chunk(writer, ExportFormat.EBP, 'FOLDACTR'):
                if self.format is ExportFormat.WHE:
                    writer.write_struct('<L', len(data.actions))
                for a in data.actions.values():
                    with self.start_chunk(writer, ExportFormat.EBP, 'DATAACTN', name=a.name):
                        if self.format is ExportFormat.WHE:
                            writer.write_str(a.name)
                        writer.write_struct('<L', len(a.motions))
                        for m in a.motions:
                            writer.write_str(m.motion.name)
                            writer.write_struct('<L', m.compare_type)
                            if m.compare_type not in (d.Action.CompareType.NONE, d.Action.CompareType.ELSE):
                                writer.write_str(m.condition.name)
                        writer.write_struct('<L', len(a.subactions))
                        for s in a.subactions:
                            writer.write_str(s.action.name)
                            writer.write_struct('<L', s.compare_type)
                            if s.compare_type not in (d.Action.CompareType.NONE, d.Action.CompareType.ELSE):
                                writer.write_str(s.condition.name)
            with writer.start_chunk('DATASEUI'):
                writer.write_struct(
                    '<L 2f 2f 3f 3f 9f', data.selected_ui.display_type, *data.selected_ui.scale,
                    *data.selected_ui.offset, *data.selected_ui.volume_offset, *data.selected_ui.volume_scale,
                    *(i for r in data.selected_ui.matrix for i in r),
                )

    def start_chunk(self, writer: ChunkWriter, format: ExportFormat, *args, **kwargs):
        if format == self.format:
            return writer.start_chunk(*args, **kwargs)
        return contextlib.nullcontext()

    def write_relic_chunky(self, writer: ChunkWriter):
        writer.write_struct('<12s3l', b'Relic Chunky', 1706509, 1, 1)

    def write_meta(self, writer: ChunkWriter, meta: str):
        with writer.start_chunk('DATAFBIF', name='FileBurnInfo'):
            writer.write_str('https://github.com/amorgun/dow_object_tool')
            writer.write_struct('<l', 0)
            writer.write_str(meta)
            writer.write_str(datetime.datetime.utcnow().strftime('%B %d, %I:%M:%S %p'))


def read_whe(filename: str | pathlib.Path) -> d.ObjectData:
    with open(filename, 'rb') as f:
        reader = ChunkReader(f)
        parser = Parser()
        return parser.parse(reader)
    

def write_format(data: d.ObjectData, filename: pathlib.Path, format: ExportFormat):
    with filename.open('wb') as f:
        writer = ChunkWriter(f, {
            'DATAFBIF': {
                'version': 1,
            },
            'FOLDREBP': {
                'version': 4,
                'FOLDANIM': {
                    'version': 3 if format is ExportFormat.WHE else 1,
                    'DATAXREF': {'version': 1},
                    'DATAANBV': {'version': 1},
                },
                'FOLDEVCT': {
                    'version': 1,
                    'DATAEVNT': {'version': 3},
                },
                'FOLDCLST': {
                    'version': 1,
                    'DATACLAS': {'version': 2},
                },
                'FOLDCONL': {
                    'version': 1,
                    'DATACOND': {'version': 1},
                },
                'FOLDMODL': {
                    'version': 1,
                    'DATAMODF': {'version': 1},
                },
                'FOLDMTRE': {
                    'version': 3,
                    'DATAMTON': {'version': 4},
                },
                'FOLDACTR': {  # EBP only
                    'version': 1,
                    'DATAACTN': {'version': 1},
                },
                'DATAACTS': {'version': 1},  # WHE only
                'DATASEUI': {'version': 3},
            }
        })
        exporter = Exporter(format)
        return exporter.export(data, writer)


def from_json(data: dict) -> d.ObjectData:
    def name2enum(name: str, enum_cls: type):
        return getattr(enum_cls, name.upper())
    
    def keys2enum(data: dict, *keys: list[tuple[str, type]]) -> dict:
        return {**data, **{k: name2enum(data[k], cls) for k, cls in keys}}

    result = d.ObjectData()
    result.burn_info = d.BurnInfo(**data.get('burn_info', {}))
    result.selected_ui = d.SelectedUi(
        **keys2enum(data['selected_ui'], ('display_type' , d.SelectedUi.DisplayType)))  # FIXME
    result.selected_ui.scale = d.VecftorXZ(**result.selected_ui.scale)
    result.selected_ui.offset = d.VecftorXZ(**result.selected_ui.offset)
    result.selected_ui.volume_scale = d.VecftorXYZ(**result.selected_ui.volume_scale)
    result.selected_ui.volume_offset = d.VecftorXYZ(**result.selected_ui.volume_offset)
    for e in data['events']:
        e['properties'] = [d.Event.Property(**i) for i in e['properties']]
    result.events = {e['name']: d.Event(**e) for e in data['events']}
    result.clauses = {
        c['name']: d.Clause(
            **keys2enum(c, ('type', d.Clause.Type), ('comparison', d.Clause.Comparison))
        ) for c in data['clauses']
    }
    result.conditions = {c['name']: d.Condition(**c) for c in data['conditions']}
    result.modifiers = {
        m['name']: d.Modifier(**keys2enum(m, ('type', d.Modifier.Type)))
        for m in data['modifiers']
    }
    result.xrefed_animations = {a['name']: d.AnimationXref(**a) for a in data.get('xrefed_animations', [])}
    for motion in data['motions']:
        motion.setdefault('animations', [])
        motion.setdefault('modifier', None)
        motion['random_motions'] = [
            d.Motion.RandomMotion(**m) for m in motion.get('random_motions', [])
        ]
        motion['events'] = [
            d.Motion.MotionEvent(event=e['event'],
                                time=name2enum(e['time'], d.Motion.MotionEvent.Time) 
                                        if isinstance(e['time'], str) else e['time']) 
            for e in motion.get('events', [])
        ]
    result.motions = {
        m['name']: d.Motion(**keys2enum(m, ('type', d.Motion.Type)))
        for m in data['motions']
    }
    for action in data['actions']:
        for z in [action.setdefault('motions', []), action.setdefault('subactions', [])]:
            for i in z:
                i.setdefault('condition', None)
        action['motions'] = [
            d.Action.ActionMotion(**keys2enum(m, ('compare_type', d.Action.CompareType)))
            for m in action['motions']
        ]
        action['subactions'] = [
            d.Action.Subaction(**keys2enum(s, ('compare_type', d.Action.CompareType)))
            for s in action['subactions']
        ]
    result.actions = {a['name']: d.Action(**a) for a in data['actions']}
    result.resolve_links()
    return result


def read_json(filename: pathlib.Path):
    with filename.open('r') as f:
        data = json.load(f)
    return from_json(data)


def to_json(data: d.ObjectData) -> typing.Any:
    import dataclasses

    def dataclass_to_dict(data):
        res = dataclasses.asdict(data)
        for k, v in res.items():
            if isinstance(v, enum.Enum):
                res[k] = v.name.lower()
        return res

    result = {
        'burn_info': dataclass_to_dict(data.burn_info),
        'selected_ui': dataclass_to_dict(data.selected_ui),
        'events': [dataclass_to_dict(e) for e in data.events.values()],
        'clauses': [dataclass_to_dict(c) for c in data.clauses.values()],
        'conditions': [{**dataclass_to_dict(c), 'clauses': [cl.name for cl in c.clauses]} for c in data.conditions.values()],
        'modifiers': [dataclass_to_dict(m) for m in data.modifiers.values()],
        'xrefed_animations': [dataclass_to_dict(a) for a in data.xrefed_animations.values()],
        'motions': [{
            **dataclass_to_dict(m),
            'events': [{**dataclass_to_dict(e), 'event': e.event.name} for e in m.events],
            'random_motions': [{**dataclass_to_dict(i), 'motion': i.motion.name} for i in m.random_motions],
            'modifier': m.modifier.name if m.modifier is not None else None,
        } for m in data.motions.values()],
        'actions': [{
            **dataclass_to_dict(a),
            'motions': [{
                **dataclass_to_dict(m),
                'motion': m.motion.name,
                'condition': m.condition.name if m.condition is not None else None
            } for m in a.motions],
            'subactions': [{
                **dataclass_to_dict(s),
                'action': s.action.name,
                'condition': s.condition.name if s.condition is not None else None
            } for s in a.subactions],
        } for a in data.actions.values()],
    }
    if not result['xrefed_animations']:
        result.pop('xrefed_animations')
    for m in result['motions']:
        if m['modifier'] is None:
            m.pop('modifier')
        if not m['animations']:
            m.pop('animations')
        if not m['random_motions']:
            m.pop('random_motions')
        if not m['events']:
            m.pop('events')
    for a in result['actions']:
        for z in [a['motions'], a['subactions']]:
            for i in z:
                if i['compare_type'] in ('none', 'else'):
                    i.pop('condition')
        if not a['motions']:
            a.pop('motions')
        if not a['subactions']:
            a.pop('subactions')

    return result


def set_precision(data, precision=2):
    if isinstance(data, enum.Enum):
        return data
    if isinstance(data, float):
        return round(data, precision)
    if isinstance(data, dict):
        return {k: set_precision(v, precision) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return type(data)(set_precision(i, precision) for i in data)
    return data


def write_json(data: d.ObjectData, filename: pathlib.Path):
    filename.parent.mkdir(exist_ok=True, parents=True)
    result = to_json(data)
    result = set_precision(result, 2)

    def json_dump(obj, stream, indent=2, curr_indent=0, curr_path='', no_newline_paths=()):
        write_newlines = curr_path not in no_newline_paths
        if isinstance(obj, dict):
            if not obj:
                stream.write('{}')
                return
            stream.write('{')
            if write_newlines: stream.write('\n')
            for idx, (k, v) in enumerate(obj.items()):
                path = f'{curr_path}/{k}'
                new_indent = indent + curr_indent
                if write_newlines: stream.write(' ' * new_indent)
                json_dump(k, stream, curr_indent=new_indent, curr_path=path, no_newline_paths=no_newline_paths)
                stream.write(': ')
                json_dump(v, stream, curr_indent=new_indent, curr_path=path, no_newline_paths=no_newline_paths)
                if idx != len(obj) - 1:
                    stream.write(',')
                    stream.write('\n' if write_newlines else ' ')
            if write_newlines: stream.write('\n')
            if write_newlines: stream.write(' ' * curr_indent)
            stream.write('}')
            return
        if isinstance(obj, (list, tuple)):
            if not obj:
                stream.write('[]')
                return    
            stream.write('[')
            if write_newlines: stream.write('\n')
            for idx, e in enumerate(obj):
                path = f'{curr_path}/*'
                new_indent = indent + curr_indent
                if write_newlines: stream.write(' ' * new_indent)
                json_dump(e, stream, curr_indent=new_indent, curr_path=path, no_newline_paths=no_newline_paths)
                if idx != len(obj) - 1:
                    stream.write(',')
                    stream.write('\n' if write_newlines else ' ')
            if write_newlines: stream.write('\n')
            if write_newlines: stream.write(' ' * curr_indent)
            stream.write(']')
            return
        stream.write(json.dumps(obj, ensure_ascii=False))

    with filename.open('w') as f:
        json_dump(result, f, no_newline_paths={
            '/selected_ui/scale',
            '/selected_ui/offset',
            '/selected_ui/volume_scale',
            '/selected_ui/volume_offset',
            '/selected_ui/matrix/*',
            '/events/*/properties/*',
            '/conditions/*/clauses',
            '/motions/*/start_delay',
            '/motions/*/loop_delay',
            '/motions/*/exit_delay',
            '/motions/*/inset',
            '/motions/*/events/*',
            '/motions/*/random_motions/*',
            '/actions/*/motions/*',
            '/actions/*/subactions/*',
        })


def read_lua(filename: pathlib.Path):
    with filename.open('r') as f:
        data = slpp.decode(f.read())
    return from_json(data)


def write_lua(data: d.ObjectData, filename: pathlib.Path):
    lua = SLPP()
    lua.tab = ' ' * 4
    result = to_json(data)
    result = set_precision(result, 2)
    with open(filename, 'w') as f:
        f.write(lua.encode(result))
