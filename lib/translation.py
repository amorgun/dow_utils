import dataclasses


@dataclasses.dataclass
class Translator:
    index: dict[int, str] = dataclasses.field(repr=False)

    @classmethod
    def from_files(cls, *paths: list, encoding='utf-16') -> 'Translator':
        index = {}
        for path in paths:
            with open(path, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line:
                        key, *s = line.split(None, 1)
                        s = s[0] if s else ''
                        index.setdefault(int(key), s)
        return cls(index)
    
    def __getitem__(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        if text.startswith('$'):
            try:
                return self.index[int(text[1:])]
            except (ValueError, KeyError):
                return text
        return text
