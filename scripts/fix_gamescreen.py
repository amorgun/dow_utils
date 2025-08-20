import argparse
import pathlib
import textwrap

from ..lib.slpp import SLPP, Preformat



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='Original gamescreen', type=pathlib.Path)
    parser.add_argument('dst', help='Result path', type=pathlib.Path)
    args = parser.parse_args()

    my_lua = SLPP()
    my_lua.table_newlines = True
    my_lua.shorten_tables = False
    parsed = my_lua.decode('{' + args.src.read_text() + "}")
    
    # def fix_position(pos, scale):
    #     x, y = pos[0] / scale[0], pos[1] / scale[1]
    #     x -= 0.2
    #     return x * scale[0], y * scale[1]
    
    def fix_position(pos, scale, dir=''):
        x, y = pos
        orig_w, orig_h = 4, 3
        new_w, new_h = 16, 9
        orig_w_in_new = orig_w * new_h / orig_h
        pad_size = (new_w - orig_w_in_new) / 2 / orig_w_in_new
        # x -= pad_size
        # print(f'{pad_size=}')
        if dir == 'left':
            x -= pad_size
        elif dir == 'right':
            x += pad_size
        else:
            if x <= 0.179:
                x -= pad_size
            else:
                x += pad_size
        return x, y
    
    # print(fix_position([0, 0], 0, 'left'))
    # print(fix_position([1, 1], 0, 'right'))

    def fn(root, scale: tuple[float, float] = (1, 1)):
        size = root.get('size', [1, 1])
        if scale[0] == 0 or scale[1] == 0:
            scale = scale[0] or 1e-6, scale[1] or 1e-6

        name = root.get('name')
        direction = ''
        if name in {
            'grpHero',
            'btnNextBuilder',
            'btnNextMilitary',
            'ctmMinimap',
            'grpReq',
            'grpPower',
            'grpSouls',
            'grpFaith',
            'txtBonus',
            'iconBonus',
        }:
            direction = 'left'
        elif name in {
            'grpCommandIcons',
            'grpExtramenu',
            'grpUpgrades',
            'grpMenuButtons',
            'btnChatHistory',
            'grpAllHelpText',
            'grpStrategicUI',
        }:
            direction = 'right'
        elif name in {
            # 'grpMenubar',
            'grpIntelEvent',
            'grpSoulAbilities1',
            'grpSoulAbilities2',
            'grpSoulAbilities3',
            'grpSoulAbilities4',
            'txtChatInput',
            'txtSystemMessage',
            'txtCriticalWarning',
            'txtChatTeam',
            'txtChatAll',
            'grpBuildQueue',

        }:
            return
        if direction != '' or root.get('Presentation'):
            if 'position' in root:
                root['position'] = fix_position(root['position'], scale, dir=direction)
            if 'HitArea' in root and 'position' in root['HitArea']:
                root['HitArea']['position'] = fix_position(root['HitArea']['position'], scale, dir=direction)
        else:
            for c in root.get('Children', []):
                fn(c, size)
        
    def fix_format(root):
        def fix_val(v):
            if v == 0 or v == 1:
                return Preformat(f'{v:.0f}')
            return Preformat(f'{v:#.5f}')
        
        if isinstance(root, dict):
            # if root.get('name') == 'txtReq':
            #     print(root)
            if (
                'name' in root
                and 'ArtGuides' not in root
                and root.get('type') not in {'Text', 'Graphic', }
            ):
                root['Clip'] = False
            for k in list(root):
                v = root[k]
                if isinstance(v, (list, tuple)):
                    root[k] = [fix_format(i) for i in v]
                elif isinstance(v,dict):
                    root[k] = {a: fix_format(b) for a, b in v.items()}
                else:
                    root[k] = fix_format(v)
        elif isinstance(root, list):
            for idx, v in enumerate(root):
                root[idx] = fix_format(v)
        elif isinstance(root, float):
            root = fix_val(root)
        return root

    fn(parsed['Screen']['Widgets'])
    fn(parsed['Screen']['TooltipWidgets'])
    fix_format(parsed)
    parsed['Screen']['AspectRatio'] = Preformat('1.33333')

    newline = '\r\n'
    def to_str(data):
        result = my_lua.encode(data)
        lines = result.split('\n')[2:-1]
        lines = [l + ' ' if l.endswith('= ') or l.endswith('\t') else l for l in lines]
        return textwrap.dedent(newline.join(lines))
    args.dst.write_text(
        to_str({'Screen': parsed['Screen']})[:-1] + newline + to_str({'ToolInfo': parsed['ToolInfo']})[:-1] + newline
    )
