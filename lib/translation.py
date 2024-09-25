import dataclasses
import re

from .dow_layout import DowLayout


@dataclasses.dataclass
class Translator:
    index: dict[int, str] = dataclasses.field(repr=False)

    @classmethod
    def from_files(cls, *paths: list, encoding='utf-16') -> 'Translator':
        index = {}
        line_re = re.compile(r'(\d+)\s*(.*)')
        for path in paths:
            for line in path.read_text(encoding=encoding, errors='ignore').splitlines():
                line = line.rstrip('\n')
                if line:
                    match = line_re.match(line)
                    try:
                        index.setdefault(int(match.group(1)), match.group(2))
                    except Exception:
                        print(f'Cannot parse line "{line}" ({path})')
                        raise
        return cls(index)
    
    @classmethod
    def from_layout(cls, layout: DowLayout) -> 'Translator':
        return cls.from_files(*[p for p in layout.iterdir('.') if p.suffix == '.ucs'])

    def __getitem__(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        if text.startswith('$'):
            try:
                return self.index[int(text[1:])]
            except (ValueError, KeyError):
                return text
        return text
