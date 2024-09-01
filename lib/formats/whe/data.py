import dataclasses
import enum
import struct


@dataclasses.dataclass
class BurnInfo:
    tool: str = ''
    username: str = ''
    date: str = ''


@dataclasses.dataclass
class Event:
    @dataclasses.dataclass
    class Property:
        param: str
        value: str

    name: str
    properties: list[Property]


@dataclasses.dataclass
class Clause:
    @enum.unique
    class Type(enum.IntEnum):
        FLOAT = 0
        BOOLEAN = 1
        STRING = 2

    @enum.unique
    class Comparison(enum.IntEnum):
        EQUAL = 0
        NOT_EQUAL = 1
        LESS = 2
        LESS_OR_EQUAL = 3
        GREATER = 4
        GREATER_OR_EQUAL = 5
    
    name: str
    type: Type
    variable: str
    comparison: Comparison
    value: float | bool | str
    default: float | bool | str


@dataclasses.dataclass
class Condition:
    name: str
    clauses: list[str | Clause] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class Modifier:
    @enum.unique
    class Type(enum.IntEnum):
        ABSOLUTE_TIME = 0
        SPEED_SCALE = 1

    name: str
    variable: str
    type: Type
    ref_value: float
    default: float


@dataclasses.dataclass
class AnimationXref:
    name: str
    source_path: str
    source_name: str


@dataclasses.dataclass
class Motion:
    @enum.unique
    class Type(enum.IntEnum):
        NON_LOOPING = 0
        LOOPING = 1
        HOLD_END = 2

    @dataclasses.dataclass
    class RandomMotion:
        motion: 'str | Motion'
        weight: float

    @dataclasses.dataclass
    class MotionEvent:
        @enum.unique
        class Time(float, enum.Enum):
            ENTER = -1.
            EXIT = struct.unpack('<f', b'\xff\xff\x7f\x7f')

        event: str | Event
        time: float

    name: str
    animations: list[str]
    random_motions: list[RandomMotion]
    randomize_each_loop: bool
    events: list[MotionEvent]
    type: Type
    start_delay: tuple[float, float]
    loop_delay: tuple[float, float]
    exit_delay: tuple[float, float]
    inset: tuple[float, float]
    transition_out: float
    ignore_exit_delay: bool
    ignore_transitions: bool
    modifier: Modifier


@dataclasses.dataclass
class Action:
    @enum.unique
    class CompareType(enum.IntEnum):
        IF = 0
        ELSE_IF = 1
        ELSE = 2
        NONE = 3
        
    @dataclasses.dataclass
    class ActionMotion:
        motion: str | Motion
        compare_type: 'Action.CompareType'
        condition: str | Condition

    @dataclasses.dataclass
    class Subaction:
        action: 'str | Action'
        compare_type: 'Action.CompareType'
        condition: str | Condition

    name: str
    motions: list[ActionMotion]
    subactions: list[Subaction]


@dataclasses.dataclass
class VecftorXZ:
    x: float
    z: float

    def __iter__(self):
        yield self.x
        yield self.z


@dataclasses.dataclass
class VecftorXYZ:
    x: float
    y: float
    z: float

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


@dataclasses.dataclass
class SelectedUi:
    @enum.unique
    class DisplayType(enum.IntEnum):
        CIRCLE = 0
        RECTANGLE = 1

    display_type: DisplayType
    scale: VecftorXZ
    offset: VecftorXZ
    volume_scale: VecftorXYZ
    volume_offset: VecftorXYZ
    matrix: list[list[float]]


@dataclasses.dataclass
class ObjectData:
    burn_info: BurnInfo = None
    events: dict[str, Event] = dataclasses.field(default_factory=dict)
    clauses: dict[str, Clause] = dataclasses.field(default_factory=dict)
    conditions: dict[str, Condition] = dataclasses.field(default_factory=dict)
    xrefed_animations: dict[str, AnimationXref] = dataclasses.field(default_factory=dict)
    modifiers: dict[str, Modifier] = dataclasses.field(default_factory=dict)
    motions: dict[str, Motion] = dataclasses.field(default_factory=dict)
    actions: dict[str, Action] = dataclasses.field(default_factory=dict)
    selected_ui: SelectedUi = None

    def resolve_links(self):
        for c in self.conditions.values():
            c.clauses = [self.clauses[i] for i in c.clauses]
        for m in self.motions.values():
            for e in m.events:
                e.event = self.events[e.event]
            for r in m.random_motions:
                r.motion = self.motions[r.motion]
            if m.modifier is not None:
                m.modifier = self.modifiers[m.modifier]
        for a in self.actions.values():
            for m in a.motions:
                m.motion = self.motions[m.motion]
                if m.condition is not None:
                    m.condition = self.conditions[m.condition]
            for s in a.subactions:
                s.action = self.actions[s.action]
                if s.condition is not None:
                    s.condition = self.conditions[s.condition]
