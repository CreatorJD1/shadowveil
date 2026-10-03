"""Shared helpers for the diagonal body cut (STAGED). All coords = FRAME px of the turn frame (768x1168)."""
import json, glob, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = '/workspace/shadowveil'
OUT = f'{ROOT}/body_tools/work/diag_body'
DIAG = json.load(open(f'{ROOT}/body_tools/work/apose_turn/diagonals/diagonals.json'))['diagonals']
ANG = {'045': dict(frame='f033', hands='45', hairmouth='045', eyes='045', key='45'),
       '315': dict(frame='f191', hands='315', hairmouth='315', eyes='315', key='315'),
       '135': dict(frame='f087', hands='135', hairmouth='135', eyes=None, key='135'),
       '225': dict(frame='f131', hands='225', hairmouth='225', eyes=None, key='225')}
KEYT = 25  # Hands' F8 key rule: B - max(R,G) > 25 is key
def frame(ang): return np.array(Image.open(f"{ROOT}/reference/apose_turn/frames/{ANG[ang]['frame']}.png").convert('RGB')).astype(np.int32)
def fit(ang): return DIAG[ANG[ang]['key']]['view_fit']
def fg_mask(F):
    """her figure: everything not connected-to-border key; enclosed key islands >= 6 px are background (gaps), smaller ones = her dark ink"""
    key = (F[..., 2] - np.maximum(F[..., 0], F[..., 1])) > KEYT
    lab, n = ndi.label(key)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndi.sum(key, lab, range(1, n + 1))
    bg = np.zeros_like(key)
    for i in range(1, n + 1):
        if i in border or sizes[i - 1] >= 6: bg |= lab == i
    fg = ~bg
    # drop specks not attached to the figure
    lab, n = ndi.label(fg, structure=np.ones((3, 3)))
    sizes = ndi.sum(fg, lab, range(1, n + 1)); big = np.argmax(sizes) + 1
    return lab == big, key
def alpha(path): return np.array(Image.open(path).convert('RGBA'))[..., 3]
def view_to_frame_mask(A, ang, H=1168, W=768):
    """frame px claimed if any view px whose CENTRE maps into it (Hair's convention fx=floor((X+0.5-dx)/s)) has alpha>0"""
    f = fit(ang); s, dx, dy = f['scale'], f['dx'], f['dy']
    ys, xs = np.nonzero(A > 0); M = np.zeros((H, W), bool)
    fx = np.floor((xs + 0.5 - dx) / s).astype(int); fy = np.floor((ys + 0.5 - dy) / s).astype(int)
    ok = (fx >= 0) & (fx < W) & (fy >= 0) & (fy < H); M[fy[ok], fx[ok]] = True
    return M
def team_masks(ang):
    c = ANG[ang]; T = {}
    # Hands: F12 rig (F8 parts + F12 wrist flaps), frame_scale copies; flaps are hidden under the forearm by design (kept separate)
    a8 = c['hands']; base = f"{ROOT}/hands/staged/f8_diagonals/{a8}"; rj = f"{ROOT}/hands/staged/f12_wrist_diag/{a8}/rig.json"
    rig = json.load(open(rj if os.path.exists(rj) else f"{base}/rig.json"))
    for side in 'LR':
        m = np.zeros((1168, 768), bool); fl = np.zeros((1168, 768), bool)
        for p in rig['parts']:
            if not p['id'].startswith(side + '_'): continue
            if 'wristflap' in p['id']: fl |= alpha(os.path.normpath(f"{base}/{p['frame_file']}")) > 0
            else: m |= alpha(f"{base}/frame_scale/{p['file']}") > 0
        T['hand_' + side] = m; T['hand_' + side + '_wristflap_all_states'] = fl
    if c['eyes']:
        m = np.zeros((1168, 768), bool)
        for f in glob.glob(f"{ROOT}/eyes/staged/diagonals/{c['eyes']}/*.png"):
            b = os.path.basename(f)
            if b.endswith('_chroma.png'): continue
            if '_lid_' in b and not b.endswith('_lid_0.png'): continue   # rest = lid_0
            m |= alpha(f) > 0
        T['eyes'] = m
        T['eyes_all_states'] = np.zeros((1168, 768), bool)
        for f in glob.glob(f"{ROOT}/eyes/staged/diagonals/{c['eyes']}/*.png"):
            if not f.endswith('_chroma.png'): T['eyes_all_states'] |= alpha(f) > 0
    hd = f"{ROOT}/hair/staged/diagonals_v3/{c['hairmouth']}/hair"
    if os.path.isdir(hd):
        A = np.zeros((1739, 1365), np.uint8)
        for f in glob.glob(hd + '/*.png'): A |= (alpha(f) > 0).astype(np.uint8)
        T['hair'] = view_to_frame_mask(A, ang)
    md = f"{ROOT}/mouth/staged/diag_posable/{c['hairmouth']}/frame_scale"
    if os.path.exists(f"{md}/rest.png"):
        T['mouth'] = alpha(f"{md}/rest.png") > 0
        T['mouth_all_states'] = np.zeros((1168, 768), bool)
        for f in glob.glob(md + '/*.png'): T['mouth_all_states'] |= alpha(f) > 0
    return T
def save_rgba(F, M, path):
    o = np.zeros(M.shape + (4,), np.uint8); o[M, :3] = F[M]; o[M, 3] = 255
    Image.fromarray(o, 'RGBA').save(path)
