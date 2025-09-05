import io
import logging
import pathlib
import struct
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import webbrowser

from PIL import Image
import quicktex.dds
import quicktex.s3tc.bc1
import quicktex.s3tc.bc3
import sv_ttk

from ..lib.chunky import ChunkReader, ChunkWriter


def converter_window(files_root: pathlib.Path):
    logging.getLogger().handlers.append(logging.FileHandler(files_root / 'rtx_converter.log', 'w'))
    root = tk.Tk(className='RTX Converter')
    root.title('Dawn of War DE RTX Converter')
    mainframe = ttk.Frame(root)
    mainframe.grid(column=0, row=0)

    pbar = ttk.Progressbar(mainframe, orient='horizontal', mode='determinate', length=200)
    pbar.grid(column=0, row=8, columnspan=2)
    
    ttk.Label(mainframe, text='Pack Format:').grid(column=0, row=1, padx=(15, 0), sticky=tk.E, pady=(5, 15))
    dds_format = ttk.Combobox(mainframe, state='readonly', values=['Auto', 'DXT1', 'DXT5'], width=8)
    dds_format.set('Auto')
    dds_format.grid(column=1, row=1, padx=(10, 15), pady=(5, 15))
    pack_button = ttk.Button(mainframe, text='Convert to RTX', style='Accent.TButton', command=lambda: pack_files(dds_format.get(), pbar))
    pack_button.grid(column=0, row=0, columnspan=2)
    ttk.Separator(mainframe).grid(column=0, row=2, columnspan=2)
    ttk.Label(mainframe, text='Unpack Format:').grid(column=0, row=6, padx=(15, 0), sticky=tk.E, pady=(5, 15))
    unpack_format = ttk.Combobox(mainframe, state='readonly', values=['Original', 'PNG'], width=8)
    unpack_format.set('Original')
    unpack_format.grid(column=1, row=6, padx=(10, 15), pady=(5, 15))
    ttk.Button(mainframe, text='Unpack RTX', style='Accent.TButton', command=lambda: unpack_files(unpack_format.get(), pbar)).grid(
        column=0, row=5, ipadx=10, columnspan=2)
    
    def show_about():
        def dismiss():
            dlg.grab_release()
            dlg.destroy()

        dlg = tk.Toplevel(root)
        ttk.Label(dlg, text='RTX Converter v0.2').grid(pady=(10, 0))
        ttk.Label(dlg, text='The source code is available on Github:').grid()
        link = ttk.Label(dlg, text='https://github.com/amorgun/dow_utils', foreground='blue', cursor='hand2')
        link.grid(padx=6)
        link.bind('<ButtonRelease-1>', lambda e: webbrowser.open('https://github.com/amorgun/dow_utils'))
        ttk.Label(dlg, text='Go leave a star there!').grid(pady=(0, 10))
        ttk.Button(dlg, text='Ok', command=dismiss).grid()
        dlg.protocol('WM_DELETE_WINDOW', dismiss)
        dlg.transient(root)
        dlg.resizable(False, False)
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.wait_window()

    menubar = tk.Menu(root, tearoff=False)
    root['menu'] = menubar
    menubar.add_command(label='About',command=show_about)
    
    pack_button.focus()
    mainframe.columnconfigure(1, weight=1, minsize=80)
    mainframe.rowconfigure(0, weight=1)
    root.minsize(200, 80)
    root.resizable(False, False)

    sv_ttk.set_theme("light")
    root.mainloop()


RTX_CHUNK_VERSIONS = {
    'FOLDTXTR': {
        'version': 1,
        'DATAHEAD': {'version': 1},
        'DATAINFO': {'version': 3},
        'FOLDIMAG': {
            'version': 1,
            'DATAATTR': {'version': 2},
            'DATADATA': {'version': 2},
        }
    }
}


def pack_files(format: str, pbar):
    files = filedialog.askopenfiles(mode='rb', filetypes=[('Image', '.png .jpg .jpeg .bmp .dds .tga')])
    if not files:
        return
    
    level = 10
    color_mode = quicktex.s3tc.bc1.BC1Encoder.ColorMode
    mode = color_mode.ThreeColor
    bc1_encoder = quicktex.s3tc.bc1.BC1Encoder(level, mode)
    bc3_encoder = quicktex.s3tc.bc3.BC3Encoder(level)

    encoder = None
    four_cc = format
    if format == 'DXT1':
        encoder = bc1_encoder
    elif format == 'DXT5':
        encoder = bc3_encoder       

    num_errors = 0
    pbar['maximum'] = len(files)
    pbar['value'] = 0
    for file in files:
        try:
            path = pathlib.Path(file.name)
            img = Image.open(file)
            if format == 'Auto':
                alpha_hist = img.getchannel('A').histogram()
                has_alpha = any([a > 0 for a in alpha_hist[:-1]])
                # TODO test for 1-bit alpha
                if has_alpha:
                    four_cc = 'DXT5'
                    encoder = bc3_encoder
                else:
                    four_cc = 'DXT1'
                    encoder = bc1_encoder
            dds = quicktex.dds.encode(img, encoder, four_cc)
            with path.with_suffix('.rtx').open('wb') as f:
                writer = ChunkWriter(f, RTX_CHUNK_VERSIONS)
                image_type = 5 if four_cc == 'DXT1' else 7
                image_format = 0x08 if four_cc == 'DXT1' else 0x0b
                width, height = dds.size
                writer.write_struct('<12s3l', b'Relic Chunky', 1706509, 1, 1)
                with writer.start_chunk('FOLDTXTR', name=path.stem):
                    with writer.start_chunk('DATAHEAD'):
                        writer.write_struct('<2l', image_type, 1)  # num_images
                    with writer.start_chunk('DATAINFO'):  # for oe compatable textures
                        writer.write_struct('<4l', image_type, width, height, 1)  # num_images
                    with writer.start_chunk('FOLDIMAG'):
                        with writer.start_chunk('DATAATTR'):
                            writer.write_struct('<4l', image_format, width, height, dds.mipmap_count)
                        with writer.start_chunk('DATADATA'):
                            for texture in dds.textures:
                                texture_data = io.BytesIO()
                                texture_data.write(texture)
                                writer.write(texture_data.getbuffer())
        except Exception:
            logging.exception('Cannot pack %s', file.name)
            num_errors += 1
        finally:
            pbar['value'] += 1
            pbar.update()
    if num_errors == 0:
        messagebox.showinfo('Files converted', f'Packed {len(files)} files')
    else:
        messagebox.showerror('Files converted with errors', f'Packed {len(files) - num_errors} out of {len(files)} files\nCheck rtx_converter.log for errors')


def write_dds(
    src: io.BufferedIOBase,
    dst: io.BufferedIOBase,
    data_size: int,
    width: int,
    height: int,
    num_mips: int,
    image_format: int,
):
    _DOW_DXT_FLAGS = 0x000A1007  # _DEFAULT_FLAGS | _dwF_MIPMAP | _dwF_LINEAR
    _ddsF_FOURCC = 0x00000004
    _DOW_DDSCAPS_FLAGS = 0x401008 # _ddscaps_F_TEXTURE | _ddscaps_F_COMPLEX | _ddscaps_F_MIPMAP_S
    fourCC = {8: b'DXT1', 10: b'DXT3', 11: b'DXT5'}[image_format]
    header = struct.Struct('<4s 7l 44x 2l 4s 20x 2l 12x').pack(
        b'DDS ', 124, _DOW_DXT_FLAGS, height, width, data_size, 0, num_mips, 
        32, _ddsF_FOURCC, fourCC,  # pixel format
        _DOW_DDSCAPS_FLAGS, 0,  # ddscaps
    )
    dst.write(header)
    dst.write(src.read(data_size))


def write_tga(
    src: io.BufferedIOBase,
    dst: io.BufferedIOBase,
    data_size: int,
    width: int,
    height: int,
    grayscale: bool = False
):
    # See http://www.paulbourke.net/dataformats/tga/
    header = struct.Struct('<3B 2HB 4H2B').pack(
        0,  # ID length
        0,  # file contains no color map
        3 if grayscale else 2,  # uncompressed grayscale image
        0, 0, 32,  # Color Map Specification
        0, 0, width, height, 8 if grayscale else 32, 0,  # Image Specification.
    )
    dst.write(header)
    dst.write(src.read(data_size))


def unpack_files(format: str, pbar):
    files = filedialog.askopenfiles(mode='rb', filetypes=[('RTX file', '.rtx')])
    if not files:
        return
    num_errors = 0
    pbar['maximum'] = len(files)
    pbar['value'] = 0
    for file in files:
        try:
            path = pathlib.Path(file.name)
            with path.open('rb') as f:
                reader = ChunkReader(f)
                reader.skip_relic_chunky()
                for current_chunk in reader.iter_chunks():
                    match current_chunk.typeid:
                        case 'DATAHEAD':
                            image_type, num_images = reader.read_struct('<2l')
                        case 'DATAINFO':
                            reader.skip(current_chunk.size)
                        case 'FOLDIMAG':
                            break
                current_chunk = reader.read_header('DATAATTR')
                image_format, width, height, num_mips = reader.read_struct('<4l')
                current_chunk = reader.read_header('DATADATA')

                img_data = io.BytesIO()
                is_tga = image_format in (0, 2)
                if is_tga:
                    write_tga(reader.stream, img_data, current_chunk.size, width, height)
                else:
                    write_dds(reader.stream, img_data, current_chunk.size, width, height, num_mips, image_format)
                if format == 'Original':
                    suffix = '.tga' if is_tga else '.dds'
                    with path.with_suffix(suffix).open('wb') as f:
                        f.write(img_data.getbuffer())
                        continue
                img = Image.open(img_data)
                with path.with_suffix('.png').open('wb') as f:
                    img.save(f)
        except Exception:
            logging.exception('Cannot unpack %s', file.name)
            num_errors += 1
        finally:
            pbar['value'] += 1
            pbar.update()
    if num_errors == 0:
        messagebox.showinfo('Files converted', f'Unpacked {len(files)} files')
    else:
        messagebox.showerror('Files converted with errors', f'Unpacked {len(files) - num_errors} out of {len(files)} files\nCheck rtx_converter.log for errors')
