import html
import io
import pathlib
import platform
import subprocess
import tempfile
import zlib

import flask
from PIL import Image, ImageOps
import whoosh.index
from whoosh.qparser import MultifieldParser

from ..lib.dow_layout import DowLayout
from .indexer import get_doc_html_formatter, get_line_html_formatter

app = flask.Flask(__name__)


@app.route('/')
def app_search():
    query = flask.request.args.get('query', default=None, type=str)
    if query is None:
        return flask.render_template('search.html', query=query, styles=get_line_html_formatter().get_style_defs())
    ndocs = flask.request.args.get('ndocs', default=12, type=int)
    page = flask.request.args.get('page', default=1, type=int)
    query_parser = MultifieldParser(['path', 'content'], app.config['index_schema'])
    with app.config['index'].searcher() as searcher:
        query_parsed = query_parser.parse(query)
        results = searcher.search_page(query_parsed, page, pagelen=ndocs, terms=True)
        template_data = []
        for r in results:
            data = {'path': r['path_full'], 'lines': None}
            template_data.append(data)
            matched_tokens = {str(m, 'utf8') for s, m in r.matched_terms() if s == 'content'}
            if not matched_tokens:
                continue
            data['lines'] = []
            content = str(zlib.decompress(r['content']), 'utf8')
            line_tokens = content[:r['line_tokens_data_size']].split('\n')
            line_html = content[r['line_tokens_data_size']:r['line_tokens_data_size']+r['line_html_data_size']].split('\n')
            for lineno, (toks, html) in enumerate(zip(line_tokens, line_html)):
                for t in toks.split():
                    if t in matched_tokens:
                        data['lines'].append({'lineno': lineno, 'html': html})
                        break
    num_results = len(results)
    pagination = [
        {
            'current': i + 1 == page,
            'page': i + 1,
        }
        for i in range(0, (num_results + ndocs - 1) // ndocs)
    ]
    return flask.render_template('search.html', query=query, results=template_data, num_results=num_results, styles=get_line_html_formatter().get_style_defs(), pagination=pagination)


@app.route('/doc/<path:filepath>')
def app_doc(filepath):
    with app.config['index'].searcher() as searcher:
        doc = searcher.document(path_full=filepath)
        if doc is None:
            flask.abort(404)
    formatter = get_doc_html_formatter()
    html_content = ''
    if doc['content'] is not None and doc['content'] != []:
        content = str(zlib.decompress(doc['content']), 'utf8')
        html_content = content[doc['line_tokens_data_size'] + doc['line_html_data_size']:]
    return flask.render_template('doc.html', doc=doc, code=html_content, styles=formatter.get_style_defs() , path=pathlib.PurePosixPath(filepath))


@app.route('/image/<path:filepath>')
def app_image(filepath):
    layout: DowLayout = app.config['dow_layout']
    filepaths = [filepath]
    if filepath.lower().endswith('.tga'):
        filepaths.append(filepath[:-4] + '.dds')
    for filepath in reversed(filepaths):
        full_path = layout.find(filepath)
        if full_path is None or not full_path.is_file():
            continue
        img = Image.open(io.BytesIO(full_path.read_bytes()))
        if full_path.suffix == '.dds':
            img = ImageOps.flip(img)
        buff = io.BytesIO()
        img.save(buff, 'png')
        buff.seek(0)
        return flask.send_file(
            buff,
            mimetype='image/png',
            download_name=f'{full_path.stem}.png',
        )
    flask.abort(404)


@app.route('/ping')
def app_ping():
    return 'Ok'


def start_server(mod_dir: pathlib.Path, index_path: pathlib.Path, files_root: pathlib.Path = None, **kwargs):
    app.root_path = files_root
    app.config['mod_dir'] = mod_dir
    layout = DowLayout.from_mod_folder(mod_dir)
    app.config['dow_layout'] = layout
    with layout.open():
        ix = whoosh.index.open_dir(str(index_path), indexname='docs')
        app.config['index'] = ix
        app.config['index_schema'] = ix.schema
        app.run(debug=True, **kwargs)
