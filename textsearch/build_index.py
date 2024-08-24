import argparse
import concurrent.futures
import pathlib
import zlib

from tqdm.auto import tqdm
import whoosh.index
import whoosh.fields as F

from ..lib.dow_layout import DowLayout, LayoutPath

from .indexer import normalize_query, DocumentIndexer


def make_index(mod_folder: pathlib.Path, index_path: pathlib.Path, indexer: DocumentIndexer, pbar, njobs: int = 8):
    index_path.mkdir(parents=True, exist_ok=True)
    doc_schema = F.Schema(
        path_full=F.ID(stored=True, unique=True, sortable=True),
        path_type=F.STORED(),
        path=F.KEYWORD(analyzer=normalize_query, field_boost=4.),
        content=F.KEYWORD(analyzer=normalize_query, field_boost=2., stored=True),
        ext=F.ID(),
        size=F.NUMERIC(stored=True, sortable=True),
        # docid=F.NUMERIC(stored=True, unique=True),
        line_tokens_data_size=F.NUMERIC(stored=True),
        line_html_data_size=F.NUMERIC(stored=True),
    )
    # line_schema = F.Schema(
    #     path_full=F.STORED(),
    #     # path_type=F.STORED(),
    #     docid=F.NUMERIC(stored=True),
    #     path=F.KEYWORD(analyzer=normalize_query, field_boost=4.),
    #     content=F.KEYWORD(analyzer=normalize_query, field_boost=2.),
    #     content_html=F.STORED(),
    #     ext=F.ID(),
    #     lineno=F.NUMERIC(stored=True),
    # )
    ix_docs = whoosh.index.create_in(str(index_path), doc_schema, indexname='docs')
    writer_docs = ix_docs.writer(limitmb=128, procs=njobs)
    # ix_lines = whoosh.index.create_in(str(index_path), line_schema, indexname='lines')
    # writer_lines = ix_lines.writer(limitmb=256, procs=njobs, multisegment=True)

    layout = DowLayout.from_mod_folder(mod_folder)

    path_list = []
    def walk(path: LayoutPath):
        if path.is_dir():
            for child in path.iterdir():
                walk(child)
        else:
            path_list.append(path)
        pbar.update()
    walk(layout.find('.'))

    # print(f'TOTAL {len(path_list)}')
    # print(pbar.n)
    # pbar.total = pbar.n + len(path_list) + 2
    pbar.total = pbar.n + len(path_list) + 1

    with concurrent.futures.ProcessPoolExecutor(njobs) as pool:
        for docid, doc in enumerate(pool.map(indexer.index, path_list)):
            path = str(doc.path.layout_path())
            path_type = str(type(doc.path))
            content_args = {}
            if doc.content_html:
                line_tokens = '\n'.join(' '.join(l.content_tokens) for l in doc.lines)
                line_html = '\n'.join(l.content_html for l in doc.lines)
                content_args = {
                    'line_tokens_data_size': len(line_tokens),
                    'line_html_data_size': len(line_html),
                    '_stored_content': zlib.compress(bytes(f'{line_tokens}{line_html}{doc.content_html}', 'utf8')),
                }
            writer_docs.add_document(
                path_full=path,
                path_type=path_type,
                path=doc.path_tokens,
                content=doc.content_tokens,
                ext=doc.extention,
                size=doc.size,
                # docid=docid,
                **content_args,
            )
            # with writer_lines.group():
            #     for lineno, line in enumerate(doc.lines):
            #         writer_lines.add_document(
            #             path_full=path,
            #             # path_type=path_type,
            #             path=doc.path_tokens,
            #             content=line.content_tokens,
            #             content_html=line.content_html,
            #             ext=doc.extention,
            #             lineno=lineno,
            #             docid=docid,
            #         )
            pbar.update()

    writer_docs.commit()
    pbar.update()
    # writer_lines.commit(merge=False)
    # pbar.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Mod folder', type=pathlib.Path)
    parser.add_argument('output', help='Result dir with the index', type=pathlib.Path)
    args = parser.parse_args()
    pbar = tqdm(total=200000)
    indexer = DocumentIndexer()
    make_index(args.input, args.output, indexer, pbar)
