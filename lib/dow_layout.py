import abc
import configparser
import contextlib
import dataclasses
import enum
import pathlib
import typing

from .formats.sga import SgaArchive, SgaPath


@enum.unique
class TextureLevel(str, enum.Enum):
    HIGH = 'Full'


@enum.unique
class SoundLevel(str, enum.Enum):
    HIGH = 'Full'
    MEDIUM = 'Med'
    LOW = 'Low'


@enum.unique
class Modelevel(str, enum.Enum):
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'


T = typing.TypeVar('T')


class AbstractSource(abc.ABC):
    @abc.abstractmethod
    def make_path(self, path: str | pathlib.PurePath) -> 'LayoutPath':
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError
    

@dataclasses.dataclass
class DirectoryPath:
    full_path: pathlib.Path
    root: pathlib.PurePosixPath

    def __getattr__(self, key):
        return getattr(self.full_path, key)

    def layout_path(self) -> pathlib.PurePosixPath:
        return self.full_path.relative_to(self.root)


LayoutPath = SgaPath | DirectoryPath

class DirectorySource(AbstractSource):
    def __init__(self, root: str | pathlib.Path):
        self.root = pathlib.Path(root)

    def make_path(self, path: str | pathlib.PurePath) -> DirectoryPath:
        path = pathlib.PurePath(path)
        if path.is_absolute():
            path = path.relative_to('/')
        return DirectoryPath(self.root / path, self.root)

    def exists(self) -> bool:
        return self.root.exists()

    @contextlib.contextmanager
    def open(self):
        yield self

    def __repr__(self) -> str:
        return f'DirectorySource({self.root})'


class SgaSource(AbstractSource):
    def __init__(self, path: str | pathlib.Path):
        self.path = path
        self._archive = None

    @property
    def archive(self):
        if self._archive is None and self.path.exists():
            self._archive = SgaArchive.parse(self.path)
        return self._archive

    def make_path(self, path: str | pathlib.PurePath) -> SgaPath:
        return self.archive.make_path(path)

    def exists(self) -> bool:
        return self.path.exists()

    @contextlib.contextmanager
    def open(self):
        archive = self.archive
        if archive is not None:
            with archive.open():
                yield self
                return
        yield self

    def __repr__(self) -> str:
        return f'SgaSource({self.path})'


@dataclasses.dataclass
class DowLayout:
    default_lang: str = 'english'
    default_texture_level: TextureLevel = TextureLevel.HIGH
    default_sound_level: SoundLevel = SoundLevel.HIGH
    default_model_level: Modelevel = Modelevel.HIGH
    sources: list[AbstractSource] = dataclasses.field(default_factory=list)
    translation_files: list[pathlib.Path] = dataclasses.field(default_factory=list)

    @classmethod
    def from_mod_folder(cls, path: str | pathlib.Path) -> 'DowLayout':
        path = pathlib.Path(path)
        dow_folder = path.parent
        res = cls._initilize_defaults(dow_folder)
        mod_configs = cls.load_mod_configs_options(dow_folder)
        required_mods = [mod_configs.get(path.name.lower(), cls._make_default_mod_config(path.name))]
        for required_mod_name in required_mods[0].get('requiredmods', ['dxp2', 'w40k']) + ['engine']:
            required_mods.append(mod_configs.get(required_mod_name.lower(), cls._make_default_mod_config(required_mod_name)))
        for mod in required_mods:
            res.sources.append(DirectorySource(dow_folder / mod['modfolder'] / 'Data'))
            for folder in mod.get('datafolders', []):
                folder = res.interpolate_path(folder)
                res.sources.append(SgaSource(dow_folder / mod['modfolder'] / f'{folder}.sga'))
            for file in mod.get('archivefiles', []):
                file = res.interpolate_path(file)
                res.sources.append(SgaSource(dow_folder / mod['modfolder']/f'{file}.sga'))
            locale_dir = dow_folder / mod['modfolder'] / res.interpolate_path('%LOCALE%')
            if locale_dir.is_dir():
                for filepath in locale_dir.iterdir():
                    if filepath.suffix == '.ucs' and filepath.stem.lower() == mod['modfolder'].lower():
                        res.translation_files.append(filepath)
        return res

    @classmethod
    def _initilize_defaults(cls, root: pathlib.Path) -> 'DowLayout':
        lang_config = cls.load_lang(root)
        game_config = cls.load_game_options(root)
        res = cls()
        res.default_lang = lang_config.get('default', res.default_lang)
        res.default_texture_level = game_config.get('texture_level', res.default_texture_level)
        res.default_sound_level = game_config.get('texture_level', res.default_sound_level)
        res.default_model_level = game_config.get('model_level', res.default_model_level)
        return res

    @classmethod
    def _make_default_mod_config(cls, folder_name: str) -> dict:
        return {
            'modfolder': folder_name,
            'datafolders': ['Data']
        }

    @classmethod
    def load_lang(cls, path: pathlib.Path) -> dict:
        conf_path = path / 'regions.ini'
        if not conf_path.is_file():
            return {}
        config = configparser.ConfigParser()
        config.read(conf_path)
        return {
            **{k.lower(): v for k, v in config['mods'].items()},
            'default': config['global']['lang'],
        }

    @classmethod
    def load_game_options(cls, path: pathlib.Path) -> dict:
        return {}  # TODO

    @classmethod
    def load_mod_configs_options(cls, path: pathlib.Path) -> dict:
        result = {}
        for file in path.iterdir():
            if file.suffix.lower() != '.module' or not file.is_file():
                continue
            config = configparser.ConfigParser(interpolation=None)
            config.read(file)
            config = config['global']
            result[file.stem.lower()] = {
                **{k: config[k] for k in ('uiname', 'description', 'modfolder')},
                **{
                    f'{key}s': [
                        i for _, i in sorted([(k, v)
                            for k, v in config.items()
                            if k.startswith(f'{key}.')
                        ], key=lambda x: int(x[0].rsplit('.')[1]))
                    ]
                    for key in ('datafolder', 'archivefile', 'requiredmod')
                },
            }
            if 'engine' not in result:
                result['engine'] = {
                    'modfolder': 'engine',
                    'archivefiles': ['%LOCALE%\EnginLoc', 'Engine', 'Engine-New'],
                }
        return result

    def interpolate_path(
            self,
            path: str,
            lang: str = None,
            texture_level: TextureLevel = None,
            sound_level: SoundLevel = None,
            model_level: Modelevel = None,
        ) -> str:
        path = path.replace('%LOCALE%', 'Locale/' + (lang or self.default_lang).title())
        path = path.replace('%TEXTURE-LEVEL%', texture_level or self.default_texture_level)
        path = path.replace('%SOUND-LEVEL%', sound_level or self.default_sound_level)
        path = path.replace('%MODEL-LEVEL%', model_level or self.default_model_level)
        return pathlib.PureWindowsPath(path).as_posix()

    def iter_paths(self, path: str | pathlib.PurePath) -> typing.Iterator[LayoutPath]:
        for source in self.sources:
            if not source.exists():
                continue
            source_path = source.make_path(path)
            if source_path.exists():
                yield source_path

    def find(self, path: str | pathlib.PurePath, default: T = None) -> LayoutPath | T:
        for p in self.iter_paths(path):
            return p
        return default

    def iterdir(self, path: str | pathlib.PurePath) -> typing.Iterator[LayoutPath]:
        seen_files = set()
        for source in self.sources:
            if not source.exists():
                continue
            source_path = source.make_path(path)
            if source_path.exists():
                for i in source_path.iterdir():
                    if i.name not in seen_files:
                        seen_files.add(i.name)
                        yield i

    @contextlib.contextmanager
    def open(self):
        with contextlib.ExitStack() as stack:
            for source in self.sources:
                if source.exists():
                    stack.enter_context(source.open())
            yield self