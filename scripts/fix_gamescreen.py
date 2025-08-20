import argparse
import pathlib

from ..lib.slpp import slpp as lua



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='Original gamescreen', type=pathlib.Path)
    parser.add_argument('dst', help='Result path', type=pathlib.Path)
    args = parser.parse_args()

    parsed = lua.decode('{' + args.src.read_text() + "}")
    
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
    fn(parsed['Screen']['Widgets'])
    fn(parsed['Screen']['TooltipWidgets'])
    result = lua.encode(parsed)
    args.dst.write_text(result[1:-1])
