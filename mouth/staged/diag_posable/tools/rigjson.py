from common import *
OUT = f'{ROOT}/mouth/staged/diag_posable'
live = json.load(open(f'{ROOT}/views/apose/mouth/rig.json'))
rl = json.load(open(f'{ROOT}/mouth/staged/diagonals/rest_lips.json'))
SH = ['M', 'smile', 'OH_half', 'AA_half', 'EE_half', 'OH', 'AA', 'EE']
FLAG = 'diagmouth'
for tag in ('045', '315'):
    s, dx, dy = fit(tag); fs = rl[tag]['frame_space']
    ax = (fs['corners'][0][0] + fs['corners'][1][0]) / 2; ay = fs['seam_center_row']
    anc_f = [round(ax, 2), round(ay, 2)]; anc_v = [round(s * ax + dx, 2), round(s * ay + dy, 2)]
    grid = {k: v for k, v in live['grid'].items() if k != 'anger'}
    parts = []
    for n in ['rest'] + SH:
        p = dict(id=f'mouth_{n}', file=f'frame_scale/{n}.png', viewFile=f'{n}.png', chromaFile=f'frame_scale/chroma/{n}_chroma.png',
                 viewChromaFile=f'chroma/{n}_chroma.png', x=0, y=0, pivotX=anc_f[0], pivotY=anc_f[1], viewPivotX=anc_v[0], viewPivotY=anc_v[1],
                 parent='head', parentGroup='headGroup', layer=500, MouthOpen=grid[n]['MouthOpen'], MouthForm=grid[n]['MouthForm'])
        if n == 'rest':
            p.update(requiresFlag=None, note=f"HER closed lips cut from {DIAG[tag]['frame']:03d} (RGB = her frame px, hard alpha). Over her frame: 0 px diff.")
        else:
            p.update(requiresFlag=FLAG, defaultOn=False, okLine=f'diag {tag} {n}',
                     note='STAGED: FRONT apose mouth art bent onto her diagonal lips (not her diagonal drawing). Needs its own OK line. Off by default.')
        parts.append(p)
    rj = {'contract': 'v1.3-diag (staged)', 'owner': 'Base Mouth', 'view': f'diag{int(tag)}', 'staged': True,
          'source': f"reference/apose_turn/frames/f{DIAG[tag]['frame']:03d}.png",
          'coordinateSpace': 'PRIMARY = her turn-frame px (768x1168, full-canvas PNGs in frame_scale/). viewFile = same part in view px (1365x1739, base = scale*frame + (dx,dy)), secondary.',
          'canvas': {'width': 768, 'height': 1168}, 'viewCanvas': {'width': W, 'height': H},
          'viewFit': dict(scale=s, dx=dx, dy=dy, source='body_tools/work/apose_turn/diagonals/diagonals.json'),
          'anchor': dict(x=anc_f[0], y=anc_f[1], viewX=anc_v[0], viewY=anc_v[1], desc='lip-seam centre (midpoint of her seam corners, median seam row) in her frame lips'),
          'params': live['params'], 'grid': grid,
          'selection': dict(live['selection'], flagOff=f'with ?{FLAG}=1 absent the diagonal mouth ALWAYS shows rest (every non-rest part has requiresFlag)'),
          'requiresFlag': {'flag': FLAG, 'default': False, 'parts': [f'mouth_{n}' for n in SH], 'note': 'flag name is a proposal; Coder picks the real one'},
          'headGroup': {'parent': 'head', 'note': 'mouth is a head-group member like the live mouth; no sub-offset at diagonals (none measured)'},
          'chroma': {'key': '#0000FF', 'convention': 'as live mouth/<view>/<shape>_chroma.png: the part composited over pure #0000FF, RGB, same canvas'},
          'colors': dict(teeth='#EFE4DA', tongue='#9C5A4A', inner='#3F2319', lip='her f%03d lip tones' % DIAG[tag]['frame']),
          'noAnger': 'no anger shape at diagonals (none drawn)', 'parts': parts}
    json.dump(rj, open(f'{OUT}/{tag}/rig.json', 'w'), indent=1)
    print(tag, anc_f, anc_v)
open(f'{OUT}/135_225_NONE.md', 'w').write("""# 135 (f087) and 225 (f131): no mouth parts, by design

At 135° and 225° the figure is turned away. Her frames show the back of the head, the bun and the far jaw/cheek profile only.
I checked both frames for lip / lip-corner px (`135_225_check/check.py`, crops in `135_225_check/`):
- In the cheek-profile edge at mouth height (y 190-240), the contour is plain skin with her outline. There is no lip corner and 0 lip px.
- The lip-tone matches the scan finds (f087 1311 px, f131 1381 px) are neck and jaw shading and hair edges. None of them are lips.

So no part is made, and the rig draws no mouth at these angles.
""")
