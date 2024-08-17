import tempfile
import pathlib

import bpy

from PIL import Image
import PIL.ImageOps


for mat in bpy.data.materials:
    images = {}
    if mat.node_tree is None:
        continue
    for node in mat.node_tree.nodes:
        with tempfile.TemporaryDirectory() as t:
            temp_dir = pathlib.Path(t)
            if node.label == 'sic':
                image_path = str(temp_dir/'sic.dds')
                with open(image_path, 'wb') as f:
                    f.write(node.image.packed_file.data)
                img = Image.open(image_path)
                metallic, self_illumination, teamcolor, *_ = img.split()
                for label, layer in [
                    ('specularity', metallic),
                    ('self_illumination', self_illumination),
                    ('teamcolor', teamcolor),
                    ('dirt', PIL.ImageOps.invert(teamcolor)),
                ]:
                    layer_filename = temp_dir/f'{label}.png'
                    layer.save(str(layer_filename))
                    bpy_image = bpy.data.images.load(str(layer_filename))
                    bpy_image.pack()
                    bpy_image.use_fake_user = True
                    images[label] = bpy_image
                continue
            if node.label == 'diffuse':
                images[node.label] = node.image
                image_path = str(temp_dir/'default.dds')
                with open(image_path, 'wb') as f:
                    f.write(node.image.packed_file.data)
                img = Image.open(image_path)
                converted_path = str(temp_dir/'default.png')
                img.save(converted_path)
                bpy_image = bpy.data.images.load(converted_path)
                bpy_image.pack()
                bpy_image.use_fake_user = True
                images['default'] = bpy_image
                continue
    if not images:
        continue
    for key, node_label in [
        ('default', 'color_layer_default'),
        ('dirt', 'color_layer_dirt'),
        ('teamcolor', 'color_layer_primary'),
        ('specularity', 'specularity'),
        ('self_illumination', 'self_illumination'),
    ]:
        node_tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node_tex.image = images[key]
        node_tex.label = node_label
