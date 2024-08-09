import pathlib
import io
import html

import flask
from PIL import Image, ImageOps
from ..lib.slpp import slpp as lua
from ..lib.dow_layout import DowLayout, LayoutPath
from ..lib.translation import Translator


app = flask.Flask(__name__)


def find_files(root: LayoutPath, extention: str) -> list[LayoutPath]:
    if root is None:
        return []

    def walk(path: LayoutPath):
        if path.is_dir():
            for child in path.iterdir():
                yield from walk(child)
        elif path.suffix == extention:
            yield path

    return sorted(walk(root))


def load_styles(path: LayoutPath) -> dict:
    content = path.read_text()
    parsed = lua.decode(f'{{{content}}}')
    result = {}
    for style in parsed['StyleSheet']['Styles']:
        result[style['name']] = style
    return result


def load_colours(paths: list[LayoutPath]) -> dict:
    result = {}
    for path in paths:
        content = path.read_text()
        parsed = lua.decode(f'{{{content}}}')
        for c in parsed['ColourTable']:
            result[c['key']] = c['value']
    return result


@app.route('/')
def app_list_screens():
    files = find_files(app.config['screen_dir'], '.screen')
    return flask.render_template('screen_list.html', files=[f.relative_to(app.config['screen_dir']) for f in files])


@app.route('/open')
def app_open():
    filepath = flask.request.args.get('filepath')
    return flask.redirect(flask.url_for('app_screen', filepath=filepath))


@app.route('/screen/<path:filepath>')
def app_screen(filepath):
    test = flask.request.args.get('test', default = False, type = bool)
    filepath = app.config['screen_dir'] / filepath
    layout: DowLayout = app.config['dow_layout']
    with filepath.open('r') as f:
        content = f.read()
        screen = lua.decode(f'{{{content}}}')

    widget_info = {
        i['name']: i
        for i in screen.get('ToolInfo', {}).get('WidgetInfo', [])
        if 'name' in i
    }
    
    def iter_html(node: dict, scale: tuple[float, float] = (1, 1)):
        if style_id := node.get('style'):
            style = app.config['loaded_styles'][style_id[0].lower()][style_id[1]]
        else:
            style = {
                'position': [0, 0],
                'size': [1, 1]
            }
        size = node.get('size', style.get('size', [1, 1]))
        elem_size = size[0] / scale[0], size[1] / scale[1]
        position = node.get('position', style.get('position', [0, 0]))
        elem_position = position[0] / scale[0], position[1] / scale[1]
        child_scale = size[0], size[1]
        elem_class = f'screen_block screen_{node["type"].lower()}'
        name = node.get('name')
        if widget_info.get(name, {}).get('hidden', False):\
            elem_class = f'{elem_class} screen_block_hidden'
        yield (
            f'''<div class="{elem_class}"'''
            f''' style="left: {elem_position[0]*100:.0f}%; top: {elem_position[1]*100:.0f}%;'''
            f''' width: {elem_size[0]*100:.0f}%; height: {elem_size[1]*100:.0f}%"'''
            f''' original_width="{size[0]:.5f}" original_height="{size[1]:.5f}"'''
            f''' original_left="{position[0]:.5f}" original_top="{position[1]:.5f}"'''
            f''' calc_scale_horiz="{scale[0]:.5f}" calc_scale_vert="{scale[1]:.5f}"'''
            f''' {f'id="{name}"' if name else ''}>'''
        )
        tooltip_text = node.get('tooltip_text')
        text = app.config['translator'][node.get('text')]
        node_presentation = node.get('Presentation')
        style_presentation = style.get('Presentation', {})
        yield from iter_presentation(
            (node_presentation if node_presentation is not None else style_presentation).get('Art', []),
            text,
        )
        for c in node.get('Children', []):
            yield from iter_html(c, child_scale)
        yield '</div>'

    def iter_presentation(presentation: list[dict], text: str = None):
        for block in presentation:
            size = block.get('size', [1, 1])
            # elem_size = size[0] / scale[0], size[1] / scale[1]
            elem_size = size
            position = block.get('position', [0, 0])
            # elem_position = position[0] / scale[0], position[1] / scale[1]
            elem_position = position
            elem_style = (
                f'''left: {elem_position[0]*100:.0f}%; top: {elem_position[1]*100:.0f}%;'''
                f''' width: {elem_size[0]*100:.0f}%; height: {elem_size[1]*100:.0f}%;'''
            )
            elem_class = 'screen_repr'
            if 'type' in block:
                elem_class = f'{elem_class} screen_repr_{block["type"].lower()}'
            elem_class = f'{elem_class} {" ".join(f"screen_repr_state_{i.lower()}" for i in block.get("states", []))}'
            if block.get('multiline', False):
                elem_class = f'{elem_class} text_multiline'
            if 'horzAlign' in block:
                elem_class = f'{elem_class} text_align_{block["horzAlign"].lower()}'
            if 'fontname' in block:
                elem_class = f'{elem_class} textstyle_{block["fontname"].replace(" ", "_")}'
            if block.get('dropShadow', False):
                elem_class = f'{elem_class} text_dropshadow'
            if block.get('flipVertical', False):
                elem_class = f'{elem_class} flip_vertical'
            if block.get('flipHorizontal', False):
                elem_class = f'{elem_class} flip_horizontal'
            elem_class = f'class="{elem_class}"'
            match block.get('type'):
                case  'Swf':
                    yield f'''<div {elem_class} style="{elem_style}">{block['swf']}</div>'''
                case 'Rectangle':
                    if 'colour' in block:
                        if block.get('rectangleType') == 'Border':
                            new_style = f'border: 3px solid {get_html_colour(block["colour"])};'
                        else:
                            new_style = f'background: {get_html_colour(block["colour"])};'
                        elem_style = f'{elem_style} {new_style}'
                    yield f'''<div {elem_class} style="{elem_style}"></div>'''
                case 'Graphic':
                    img_path = block.get('texture')
                    if img_path is None:
                        continue
                    if img_path.startswith('generic:'):
                        img_path = img_path.split(':', 1)[1]
                    yield f'''<img {elem_class} style="{elem_style}" src="{flask.url_for('app_image', filepath=img_path)}">'''
                case 'Text':
                    if 'textColourTop' in block:
                        text_style = f'background-image: linear-gradient({get_html_colour(block["textColourTop"])}, {get_html_colour(block.get("textColourBottom", block["textColourTop"]))});'
                    else:
                        text_style = ''                   
                    yield f'''<p {elem_class} style="{elem_style}"><span style="{text_style}">{html.escape(text) if text else text}</span></p>'''
                case 'Line':
                    yield f'''<svg {elem_class} style="{elem_style}"><line x1="{block["p1"][0]*100:.0f}%" y1="{block["p1"][1]*100:.0f}%" x2="{block["p2"][0]*100:.0f}%" y2="{block["p2"][1]*100:.0f}%" style="stroke: {get_html_colour(block["colour"])};stroke-width: 1;"></line></svg>'''
                    '''colour =  
                    {
                        0,
                        0,
                        0,
                        33,
                    },
                    ID = 69004,
                    p2 =  
                    {
                        0.83470,
                        0.77131,
                    },
                    p1 =  
                    {
                        0.16530,
                        0.77131,
                    },'''
                case default:
                    print(f'Unknown {default}')

    def get_html_colour(data: list | str) -> str:
        if isinstance(data, str):
            if not test and data.startswith('Test'):
                data = [0,0,0,0]
            else:
                data = app.config['loaded_colours'][data]
        if len(data) == 4:
            data = list(data)
            data[3] = round(data[3] / 255., 5)
        return f'rgb({",".join(map(str, data))})'

    return flask.render_template('editor.html', filepath=filepath, preview_html='\n'.join(iter_html(screen['Screen']['Widgets'])))


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


@app.route('/file/<path:filepath>')
def app_file(filepath):
    layout: DowLayout = app.config['dow_layout']
    full_path = layout.find(filepath)
    if full_path is None or not full_path.is_file():
        flask.abort(404)
    buff = io.BytesIO(full_path.read_bytes())
    return flask.send_file(
        buff,
        download_name=full_path.name,
    )


@app.route('/ping')
def app_ping():
    return f'Ok'


def start_editor(mod_dir: pathlib.Path, screen_dir: pathlib.Path, files_root: pathlib.Path = None, **kwargs):
    app.root_path = files_root
    print(app.root_path)
    app.config['mod_dir'] = mod_dir
    app.config['screen_dir'] = screen_dir
    layout = DowLayout.from_mod_folder(mod_dir)
    style_files = find_files(layout.find('art/ui/styles'), '.styles')
    app.config['loaded_styles'] = {path.stem.lower(): load_styles(path) for path in style_files}
    app.config['loaded_colours'] = load_colours(find_files(layout.find('art/ui/styles'), '.colours'))
    fonts_paths, text_styles = {}, {}
    for file in layout.iterdir('font'):
        if file.suffix == '.ttf':
            fonts_paths.setdefault(file.name, file.layout_path())
    font_names = {}
    for file in layout.iterdir('font'):
        if file.suffix == '.fnt':
            style = lua.decode(f'{{{file.read_text()}}}')['font']
            font_names[style['name']] = {
                **style,
                'path': fonts_paths[style['file'].lower()] 
            }
            text_styles[file.stem] = style
    app.config['fonts'] = font_names
    app.config['text_styles'] = text_styles
    app.config['dow_layout'] = layout
    app.config['translator'] = Translator.from_files(*layout.translation_files)
    with layout.open():
        app.run(debug=True, **kwargs)
