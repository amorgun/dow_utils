import html
import io
import pathlib
import platform
import subprocess
import tempfile

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
    test = flask.request.args.get('test', default = True, type = bool)
    filepath = app.config['screen_dir'] / filepath
    layout: DowLayout = app.config['dow_layout']

    loaded_styles = {path.stem.lower(): load_styles(path) for group in [
        find_files(layout.find('art/ui/styles'), '.styles'),
        find_files(app.config['screen_dir'] / '../styles', '.styles'),
    ] for path in group}
    loaded_colours = load_colours(
        path
        for group in [
            find_files(layout.find('art/ui/styles'), '.colours'),
            find_files(app.config['screen_dir'] / '../styles', '.colours'),
        ]
        for path in group)
    fonts_paths, text_styles = {}, {}
    for file in layout.iterdir('font'):
        if file.suffix == '.ttf':
            fonts_paths.setdefault(file.name, file.layout_path())
    font_styles = {}
    for file in layout.iterdir('font'):
        if file.suffix == '.fnt':
            style = lua.decode(f'{{{file.read_text()}}}')['font']
            font_styles[style['name']] = {
                **style,
                'path': fonts_paths[style['file'].lower()]
            }
            text_styles[file.stem] = style

    with filepath.open('r') as f:
        content = f.read()
        screen = lua.decode(f'{{{content}}}')

    widget_info = {
        i['name']: i
        for i in screen.get('ToolInfo', {}).get('WidgetInfo', [])
        if 'name' in i
    }

    seen_sounds = set()
    
    def iter_html(node: dict, scale: tuple[float, float] = (1, 1), role: str = None, parent_name: str = None):
        if style_id := node.get('style'):
            style = loaded_styles[style_id[0].lower()][style_id[1]]
        else:
            style = {
                'position': [0, 0],
                'size': [1, 1]
            }
        node_with_style = {**style, **node}
        size = node_with_style.get('size', [1, 1])
        if scale[0] == 0 or scale[1] == 0:
            scale = scale[0] or 1e-6, scale[1] or 1e-6
        elem_size = size[0] / scale[0], size[1] / scale[1]
        position = node_with_style.get('position', [0, 0])
        elem_position = position[0] / scale[0], position[1] / scale[1]
        child_scale = size[0], size[1]
        elem_class = f'screen_block screen_{node["type"].lower()}'
        if role is not None:
            elem_class = f'{elem_class} screen_role_{role.lower()}'
        name = node.get('name')
        if widget_info.get(name, {}).get('hidden', False):\
            elem_class = f'{elem_class} screen_block_hidden'
        tooltip_text = app.config['translator'][node.get('tooltip_text')]
        sound_attrs = []
        for sound in node_with_style.get('Presentation', {}).get('Sound', []):
            seen_sounds.add(sound['sample'])
            sound_attrs.append(f'sound_{sound["event"].lower()}="{sound["sample"]}"')
        yield (
            f'''<div class="{elem_class}"'''
            f''' style="left: {elem_position[0]*100:.2f}%; top: {elem_position[1]*100:.2f}%;'''
            f''' width: {elem_size[0]*100:.2f}%; height: {elem_size[1]*100:.2f}%"'''
            f''' original_width="{size[0]:.5f}" original_height="{size[1]:.5f}"'''
            f''' original_left="{position[0]:.5f}" original_top="{position[1]:.5f}"'''
            f''' {f'tooltip_text="{html.escape(tooltip_text)}"' if tooltip_text else ''}'''
            f''' {" ".join(sound_attrs) if sound_attrs else ""}'''
            f''' {f'id="{name}"' if name else ''}>'''
        )
        text = app.config['translator'][node.get('text')]
        if node["type"] == 'CheckButton':
            yield f'''<input type="checkbox" class="screen_repr screen_repr_checkbox screen_repr_checkable">'''
        if node["type"] == 'RadioButton':
            yield f'''<input type="radio" class="screen_repr screen_repr_radiobutton screen_repr_checkable"{f' name="{parent_name}"' if parent_name else ''} checked>'''
        yield from iter_presentation(node_with_style.get('Presentation', {}).get('Art', []), text)
        for c in node_with_style.get('Children', []):
            yield from iter_html(c, child_scale, parent_name=name)
        for child_key in [
            'Label', 'ArrowButton', 'ListBox', 'ItemsGroup', 'ItemTemplate',
            'ScrollBar', 'ButtonIncrement', 'ButtonDecrement', 'ButtonTrack',
        ]:
            if child_key in node_with_style:
                yield from iter_html(node_with_style[child_key], child_scale, role=child_key, parent_name=name)
        yield '</div>'

    def iter_presentation(presentation: list[dict], text: str = None):
        for block in presentation:
            size = block.get('size', [1, 1])
            elem_size = size
            position = block.get('position', [0, 0])
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
                    colour = block.get('colour', [0, 0, 0])
                    if block.get('rectangleType') == 'Border':
                        new_style = f'border: 1px solid {get_html_colour(colour)};'
                    else:
                        new_style = f'background: {get_html_colour(colour)};'
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
                    if 'textColourTop' in block and 'textColourBottom' in block:
                        text_style = f'background-image: linear-gradient({get_html_colour(block["textColourTop"])}, {get_html_colour(block["textColourBottom"])});'
                    else:
                        text_style = 'color: black;'
                    yield f'''<p {elem_class} style="{elem_style}"><span style="{text_style}">{html.escape(text) if text else text}</span></p>'''
                case 'Line':
                    colour = block.get("colour", (0, 0, 0))
                    yield f'''<svg {elem_class} style="{elem_style}"><line x1="{block["p1"][0]*100:.0f}%" y1="{block["p1"][1]*100:.0f}%" x2="{block["p2"][0]*100:.0f}%" y2="{block["p2"][1]*100:.0f}%" style="stroke: {get_html_colour(colour)};stroke-width: 1;"></line></svg>'''
                case default:
                    print(f'Unknown {default}')

    def get_html_colour(data: list | str) -> str:
        if isinstance(data, str):
            if not test and data.startswith('Test'):
                data = [0,0,0,0]
            else:
                data = loaded_colours[data]
        if len(data) == 4:
            data = list(data)
            data[3] = round(data[3] / 255., 5)
        return f'rgb({",".join(map(str, data))})'

    parts_main = iter_html(screen['Screen']['Widgets'])
    parts_tooltip = iter_html(screen['Screen']['TooltipWidgets'], role='Tooltip')
    preview_html = '\n'.join(p for g in [parts_main, parts_tooltip] for p in g)
    sound_data = [{'name': i, 'volume': 1, 'path': pathlib.Path('sound') / i} for i in seen_sounds]
    for sound in sound_data:
        rat_path = layout.find(sound['path'].with_suffix('.rat'))
        if rat_path and rat_path.is_file():
            sound_conf = lua.decode(f'{{{rat_path.read_text()}}}')
            sound['volume'] = sound_conf.get('volume', 1.)
    return flask.render_template('editor.html', filepath=filepath, fonts=font_styles, text_styles=text_styles, sounds=sound_data, preview_html=preview_html)


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


@app.route('/sound/<path:filepath>')
def app_sound(filepath):
    layout: DowLayout = app.config['dow_layout']
    full_path = layout.find(f'sound/{filepath}.fda')
    if full_path is None or not full_path.is_file():
        flask.abort(404)
    with tempfile.TemporaryDirectory(dir=str(app.root_path), prefix='sounds') as tmp_dir:
        tmp_dir = pathlib.Path(tmp_dir)
        src_path = tmp_dir / full_path.name
        src_path.write_bytes(full_path.read_bytes())
        dst_path = src_path.with_suffix('.wav')
        for vgmstream_cli in [
            'vgmstream/vgmstream-cli',
            'vgmstream-linux-cli/vgmstream-cli',
            'vgmstream-win64/vgmstream-cli.exe',
        ]:
            if not (app.root_path / vgmstream_cli).is_file():
                continue
            subprocess.run(
                [app.root_path / vgmstream_cli, '-o', dst_path, src_path],
                check=True,
                capture_output=True,
            )
            return flask.send_file(
                io.BytesIO(dst_path.read_bytes()),
                download_name=dst_path.name,
            )
        flask.abort(500)


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


@app.route('/open_explorer')
def app_show_file():
    path = pathlib.Path(flask.request.args.get('filepath', type = str))
    match platform.system():
        case 'Windows':
            subprocess.run(['explorer', '/select,', str(path)], check=True, capture_output=True)
        case 'Linux':
            subprocess.run(['xdg-open', str(path.parent)], check=True, capture_output=True)
        case _:
            flask.abort(501)
    return 'Ok'


@app.route('/ping')
def app_ping():
    return 'Ok'


def start_editor(mod_dir: pathlib.Path, screen_dir: pathlib.Path, files_root: pathlib.Path = None, **kwargs):
    app.root_path = files_root
    app.config['mod_dir'] = mod_dir
    app.config['screen_dir'] = screen_dir
    layout = DowLayout.from_mod_folder(mod_dir)
    app.config['dow_layout'] = layout
    app.config['translator'] = Translator.from_files(*layout.translation_files)
    with layout.open():
        app.run(debug=True, **kwargs)
