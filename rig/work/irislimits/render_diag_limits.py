"""Render a staged diagonal eye rig on its turn frame (drawImage semantics as tools/render_eyes.py, per-iris drive).
Also: rest check (all eyes open, gaze 0, must equal the frame exactly) and the blink/gaze sheet.
Usage: python3 render_diag.py check | sheet"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/workspace/shadowveil/eyes/tools')
from render_eyes import over, atop, shift
import math
ROOT = '/workspace/shadowveil'; D = f'{ROOT}/eyes/staged/diagonals'
# copy (rig/work/irislimits): --irislimits diag uses diag_irislimits.json dx limits (dy unchanged); outputs stay in this dir
import os; OUT = os.path.dirname(os.path.abspath(__file__)); DIAG = '--irislimits' in sys.argv and sys.argv[sys.argv.index('--irislimits') + 1] == 'diag'
LIM = json.load(open(f'{OUT}/diag_irislimits.json')) if DIAG else None
jr = lambda z: int(math.floor(z + 0.5))
def ld(p): return np.array(Image.open(p).convert('RGBA')).astype(float) / 255
def render(tag, p):
    rig = json.load(open(f'{D}/{tag}/rig.json')); fr = np.array(Image.open(f'{ROOT}/{rig["frameSource"]}').convert('RGBA')).astype(float) / 255
    parts = {q['id']: q for q in rig['parts']}; cv = fr.copy(); touched = np.zeros(fr.shape[:2], bool)
    for e in rig['eyes']:
        dr = dict(parts[f'{e}_iris']['drive'])
        if LIM: l = LIM[tag]['eyes'][e]['irislimits_diag']; dr['EyeBallX'] = [l['dxAtXminus1'], l['dxAtXplus1']]
        X, Y = p.get('EyeBallX', 0), p.get('EyeBallY', 0)
        dx = jr(X * (dr['EyeBallX'][1] if X > 0 else -dr['EyeBallX'][0])); dy = jr(Y * (dr['EyeBallY'][1] if Y > 0 else -dr['EyeBallY'][0]))
        layer = over(np.zeros_like(cv), ld(f'{D}/{tag}/{e}_white.png'))
        layer = atop(layer, shift(ld(f'{D}/{tag}/{e}_iris.png'), dx, dy)); cv = over(cv, layer); touched |= layer[..., 3] > 0
        k = int(math.floor((1 - min(1, max(0, p.get(e + 'Open', 1)))) * 7 + 0.5))
        for f in (f'{e}_lid_{k}.png', f'{e}_lash.png'):
            s = ld(f'{D}/{tag}/{f}'); cv = over(cv, s); touched |= s[..., 3] > 0
    out = (fr * 255 + 0.5).astype(np.uint8); out[touched] = (cv[touched] * 255 + 0.5).astype(np.uint8)
    return out[..., :3], rig
if __name__ == '__main__':
    if sys.argv[1] == 'check':
        res = {}
        for tag in ('045', '315'):
            im, rig = render(tag, {}); fr = np.array(Image.open(f'{ROOT}/{rig["frameSource"]}').convert('RGB'))
            res[tag] = int((im != fr).any(-1).sum())
        print(json.dumps(res)); json.dump(res, open(f'{OUT}/rest_check_{"diag" if DIAG else "current"}.json', 'w'))
    else:
        z = 10; cols = []
        for tag in ('045', '315'):
            rig = json.load(open(f'{D}/{tag}/rig.json')); x0, y0, x1, y1 = rig['workRegion']; x0 -= 3; y0 -= 3; x1 += 3; y1 += 3
            tiles = [(f'k{k}', dict(EyeLOpen=1 - k / 7, EyeROpen=1 - k / 7)) for k in range(8)]
            tiles += [(f'X{X:+d} k{k}', dict(EyeBallX=X, EyeLOpen=1 - k / 7, EyeROpen=1 - k / 7)) for X in (1, -1) for k in (0, 3, 5)]
            tiles += [(n, dict(EyeBallX=X, EyeBallY=Y)) for n, X, Y in (('gaze X-1 (her right)', -1, 0), ('gaze X+1', 1, 0),  ('gaze Y-1 up', 0, -1), ('gaze Y+1 down', 0, 1))]
            col = []
            for n, p in tiles:
                im, _ = render(tag, p); I = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
                C = Image.new('RGB', (I.width, I.height + 16), 'white'); C.paste(I, (0, 16)); ImageDraw.Draw(C).text((3, 2), f'{tag} deg  {n}', fill=(0, 0, 0))
                col.append(np.array(C)); col.append(np.full((4, C.width, 3), 255, np.uint8))
            cols.append(np.concatenate(col, 0))
        Hm = max(c.shape[0] for c in cols); cols = [np.pad(c, ((0, Hm - c.shape[0]), (0, 10), (0, 0)), constant_values=255) for c in cols]
        fn = f'{OUT}/sheet_{"diag" if DIAG else "current"}.png'; Image.fromarray(np.concatenate(cols, 1)).save(fn); print('wrote', fn)
