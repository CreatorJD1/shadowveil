# shared loader for diag_posable: reuses ../../diagonals (lipcut/diag) + ../../mesh_bend (Job A) read-only
import sys, os, json
sys.dont_write_bytecode = True
ROOT = '/workspace/shadowveil'
sys.path.insert(0, f'{ROOT}/mouth/staged/diagonals'); sys.path.insert(0, f'{ROOT}/mouth/staged/mesh_bend'); sys.path.insert(0, f'{ROOT}/rig')
import numpy as np
import diag as D
from lipcut import fit, frame_rgb, cut_frame, to_view, DIAG, W, H
from run import ITERATIONS, FINAL, view_for, get_calib
from bend import render_cell, stack, ORDER
from mb import Mesh
cfg = ITERATIONS[FINAL][1]
_V = {}
def VC():
    if 'V' not in _V: _V['V'] = view_for('apose', cfg); _V['C'] = get_calib('apose')
    return _V['V'], _V['C']
def gmesh(tag):
    """the exact G (H + residual knots) diag.py used, view space; rebuilt from results.json H"""
    V, C = VC(); fx0, fy0 = V.off
    res = json.load(open(f'{ROOT}/mouth/staged/diagonals/results.json'))[tag]
    Hc = np.array(res['H']); box = tuple(res['box']); x0, y0, x1, y1 = box
    rm = json.load(open(f'{ROOT}/mouth/staged/diagonals/rest_lips.json'))
    from PIL import Image
    dsoft = np.asarray(Image.open(f'{ROOT}/mouth/staged/diagonals/diag_{tag}_rest_mask.png')).astype(float)[y0:y1, x0:x1] / 255
    frame_v = to_view(frame_rgb(tag), tag)[y0:y1, x0:x1].astype(float)
    frgb, fskin, fsoft_full, frest = D.front_reference('apose')
    silP = np.zeros(V.base.shape[:2] + (4,)); silP[..., 3] = 255 * fsoft_full[fy0:fy0 + V.base.shape[0], fx0:fx0 + V.base.shape[1]]
    m0 = D.g_mesh(V, D.GMap(Hc, box))
    rest_h = D.render_to(stack(render_cell(V, C, cfg, 0, 0)['L']), (fx0, fy0), m0, box)
    sil_h = D.render_to(silP, (fx0, fy0), m0, box)[..., 3] / 255
    feat_h = D.col_features(sil_h, D.over_bg(frame_v, rest_h)); feat_d = D.col_features(dsoft, frame_v)
    r = D.residuals(feat_h, feat_d, x1 - x0)
    return D.g_mesh(V, D.GMap(Hc, box, r)), box
def to_frame_mesh(mG, tag):
    s, dx, dy = fit(tag)
    return Mesh(mG.src, (mG.dst - [dx, dy]) / s, mG.tris_)
