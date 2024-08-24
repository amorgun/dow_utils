import dataclasses
import enum
import io
import re
import typing

import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers.scripting import LuaLexer
from pygments.token import Token as LangToken
from whoosh.analysis import entoken, Filter
from whoosh.analysis.acore import Token

from ..lib.dow_layout import LayoutPath
from ..lib.formats.rgd import RgdParser
from ..lib.slpp import slpp as lua, SLPP


@enum.unique
class QueryMode(str, enum.Enum):
    INDEX = 'index'
    QUERY = 'query'
    NOT_SET = ''


def normalize(tok: str) -> str:
    return tok.lower().replace('_', '')


def iter_token_forms(tok: str) -> typing.Generator[str, None, None]:
    yield tok.lower()
    if '_' in tok:
        yield re.sub(r'_', '', tok.lower())


def iter_words(text: str) -> typing.Generator[str, None, None]:
    for s in re.finditer('\w{3,}', text):
        yield normalize(s.group(0))


class TokenFormFilter(Filter):
    def __call__(self, tokens) -> typing.Generator[Token, None, None]:
        for t in tokens:
            for form in iter_token_forms(t.text):
                t.text = form
                yield t


class LineHtmlFormatter(HtmlFormatter):

    def wrap(self, source):
        for i, t in source:
            if i == 1:
                yield i, t

    def _wrap_div(self, source):
        return source

    
def get_doc_html_formatter():
    return HtmlFormatter(linenos='table', cssclass='source', wrapcode=True, classprefix='hl_', anchorlinenos=True, lineanchors='lineno')


def get_line_html_formatter():
    return LineHtmlFormatter(cssclass='line_preview', wrapcode=True, classprefix='hl_')


@dataclasses.dataclass
class Line:
    content_html: str = None
    content_tokens: list[Token] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Document:
    path: LayoutPath
    path_tokens: list[Token]
    extention: str
    size: int
    content_html: str = None
    content_tokens: list[Token] = dataclasses.field(default_factory=list)
    lines: list[Line] = dataclasses.field(default_factory=list)


class SimpleFileIndexer:
    def index(self, path: LayoutPath) -> Document:
        return Document(
            path, 
            path_tokens=[normalize(path.stem)],
            extention=path.suffix.lstrip('.'),
            size=path.data_size,
        )


@dataclasses.dataclass
class ContentIndexer(SimpleFileIndexer):
    doc_html_formatter: HtmlFormatter
    line_html_formatter: LineHtmlFormatter


@dataclasses.dataclass
class LuaIndexer(ContentIndexer):
    lexer: typing.Any = dataclasses.field(default_factory=LuaLexer)

    def index(self, path: LayoutPath) -> Document:
        result = super().index(path)
        content = path.read_text(errors='ignore')
        content_tokens = list(pygments.lex(content, self.lexer))
        return self._index_tokens(content_tokens, result)
    
    def _index_tokens(self, tokens: list[Token], doc: Document) -> Document:
        html_lines = pygments.format(tokens, self.line_html_formatter).split('\n')
        doc.content_html = pygments.format(tokens, self.doc_html_formatter)
        doc.content_tokens = list(self.iter_index_tokens(tokens))
        doc.lines = [
            Line(
                content_html=line_html,
                content_tokens=list(self.iter_index_tokens(line_tokens)),
            )
            for line_tokens, line_html in zip(self.iter_line_tokens(tokens), html_lines)
        ]
        assert len(doc.lines) == len(html_lines), f'{len(doc.lines)} != {len(html_lines)} ({doc.path})'
        return doc
    
    def split_tokens(self, tokens: typing.Iterable['LangToken']) -> typing.Generator['LangToken', None, None]:
        for tok, s in tokens:
            if '\n' not in s:
                yield tok, s
                continue
            parts = s.split('\n')
            for p in parts[:-1]:
                yield tok, p + '\n'
            yield tok, parts[-1]

    def iter_line_tokens(self, tokens: typing.Iterable['LangToken']) -> typing.Generator[list[Token], None, None]:
        curr_toks = []
        for tok, s in self.split_tokens(tokens):
            curr_toks.append((tok, s))
            if s.endswith('\n'):
                yield curr_toks
                curr_toks = []
        yield curr_toks

    def iter_index_tokens(self, tokens: typing.Iterable['LangToken']) -> typing.Generator[Token, None, None]:
        for tok, s in tokens:
            if tok in LangToken.Literal or tok in LangToken.Name or tok in LangToken.Comment:
                for tok in iter_words(s):
                    yield normalize(tok)


@dataclasses.dataclass
class Rgdndexer(LuaIndexer):
    parser: RgdParser = None

    def index(self, path: LayoutPath) -> Document:
        result = super().index(path)
        try:
            content_data = self.parser.parse_bytes(path.read_bytes())
        except Exception as e:
            print(f'error {e} on {path}')
            return result
        
        lua = SLPP()
        lua.tab = ' ' * 4
        
        content = lua.encode(content_data)
        content_tokens = list(pygments.lex(content, self.lexer))
        return self._index_tokens(content_tokens, result)


class DocumentIndexer:
    def __init__(self):
        defaults = {'doc_html_formatter': get_doc_html_formatter(), 'line_html_formatter': get_line_html_formatter()}
        self.indexers = {
            '.scar': LuaIndexer(**defaults),
            '.nis': LuaIndexer(**defaults),
            '.lua': LuaIndexer(**defaults),
            '.rgd': Rgdndexer(parser=RgdParser(), **defaults),
        }
        self.default_indexer = SimpleFileIndexer()

    def index(self, path: LayoutPath) -> Document:
        indexer = self.indexers.get(path.suffix, self.default_indexer)
        return indexer.index(path)


def normalize_query(text: str, mode: str = '', **kwargs) -> typing.Generator[Token, None, None]:
    return entoken([normalize(text)], positions=True)
