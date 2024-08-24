import argparse
import pathlib

from whoosh.filedb.filestore import FileStorage
from whoosh.qparser import MultifieldParser


def query_index(index: pathlib.Path, query: str, limit: int = 50):
    storage = FileStorage(str(index))
    ix = storage.open_index()
    with ix.searcher() as searcher:
        query = MultifieldParser(['path_tokens', 'content_tokens'], ix.schema).parse(query)
        results = searcher.search(query, limit=limit)
        ret = []
        for res in results:
            ret.append(dict(res))
        return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('index', help='Original folder', type=pathlib.Path)
    parser.add_argument('query', help='Query string', type=str)
    parser.add_argument('-l', '--limit', help='Max number of search results', type=int, default=50)
    args = parser.parse_args()
    for res in query_index(args.index, args.query, args.limit):
        print(res['path'])
