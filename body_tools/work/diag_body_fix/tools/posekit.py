"""Shared posing + metrics for diag_body_fix (STAGED). FRAME px. Same joint test convention as diag_body/tools/check_diag.py:
child subtree (teammates with their owner) rotated about the joint pivot, nearest sampling, teammates' rest px count as cover."""
import sys, os, json
sys.path.insert(0, '/workspace/shadowveil/body_tools/work/diag_body/tools')
from common import *            # frame, fg_mask, team_masks, ROOT
import cv2
H, W = 1168, 768
ORIG = f'{ROOT}/body_tools/work/diag_body'
FIX = f'{ROOT}/body_tools/work/diag_body_fix'
TEAM_OWNER = dict(hand_R='forearm_R', hand_L='forearm_L', hand_R_wristflap_all_states='forearm_R', hand_L_wristflap_all_states='forearm_L',
                  hair='head', eyes='head', mouth='head')
JOINT_CHILD = {'head_neck': 'head'}
_cache = {}
def ctx(ang):
    if ang in _cache: return _cache[ang]
    F = frame(ang); fg, key = fg_mask(F); T = team_masks(ang)
    TM = np.zeros((H, W), bool)
    for k, v in T.items():
        if not k.endswith('all_states'): TM |= v
    _cache[ang] = dict(F=F, fg=fg, key=key, T=T, TM=TM); return _cache[ang]
def load_set(d):
    pj = json.load(open(f'{d}/parts.json'))
    img = {p['id']: np.array(Image.open(f"{d}/{p['file']}").convert('RGBA')) for p in pj['pieces']}
    return pj, img
def subtree(pj, k):
    kids = {}
    for p in pj['pieces']: kids.setdefault(p['parent'], []).append(p['id'])
    out = [k]; [out.extend(subtree(pj, c)) for c in kids.get(k, [])]; return out
def rot(im, c, th):
    """rotate full-canvas image by th deg (canvas convention + = clockwise on screen) about c, nearest"""
    if th == 0: return im
    M = cv2.getRotationMatrix2D((c[0] - 0.5, c[1] - 0.5), -th, 1.0)
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def pose(ang, pj, img, joint, th, team=True):
    """composite RGBA (binary alpha) with the joint's child subtree rotated th deg. teammates drawn as green cover (hands/flaps under, others on top)."""
    C = ctx(ang); j = pj['joints'][joint]; ch = JOINT_CHILD.get(joint, j['flap_on']); c = j['pivot']
    sub = set(subtree(pj, ch))
    comp = np.zeros((H, W, 4), np.uint8)
    def put(a):
        m = a[..., 3] > 0; comp[m] = a[m]
    tl = {}
    if team:
        for k, v in C['T'].items():
            if k.endswith('all_states') and 'wristflap' not in k: continue
            t = np.zeros((H, W, 4), np.uint8); t[v] = (0, 255, 0, 255); tl[k] = t
        for k in tl:
            if k.startswith('hand'): put(rot(tl[k], c, th) if TEAM_OWNER[k] in sub else tl[k])
    for k in pj['layerOrder_backToFront']:
        put(rot(img[k], c, th) if k in sub else img[k])
    for k in tl:
        if not k.startswith('hand'): put(rot(tl[k], c, th) if TEAM_OWNER[k] in sub else tl[k])
    return comp
def band_of(pj, joint, extra=15):
    j = pj['joints'][joint]; c = j['pivot']; r = j.get('test_radius_px', j['joint_radius_px']) + extra
    YY, XX = np.mgrid[0:H, 0:W]; return np.hypot(XX + 0.5 - c[0], YY + 0.5 - c[1]) <= r, c, r
def disk(r):
    r = int(np.ceil(r)); y, x = np.mgrid[-r:r + 1, -r:r + 1]; return (x * x + y * y <= r * r).astype(np.uint8)
def metrics(comp, band, rest_comp=None):
    """outline step / dent / holes / line breaks of the posed silhouette inside band."""
    S = comp[..., 3] > 0
    # holes: enclosed non-opaque px in band
    holes = ndi.binary_fill_holes(S) & ~S & band
    # dent: deepest notch the silhouette has vs its closing with a 10 px disk
    cl = cv2.morphologyEx(S.astype(np.uint8), cv2.MORPH_CLOSE, disk(10)) > 0
    notch = cl & ~S
    dt = ndi.distance_transform_edt(notch)
    dent = float(dt[band].max()) if band.any() else 0.0
    # step: outline deviation from its own 6 px (sigma) smoothed path
    cs, _ = cv2.findContours(S.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    step = 0.0
    for cc in cs:
        p = cc[:, 0, :].astype(float)
        if len(p) < 40: continue
        sm = np.stack([ndi.gaussian_filter1d(p[:, 0], 6, mode='wrap'), ndi.gaussian_filter1d(p[:, 1], 6, mode='wrap')], 1)
        dv = np.hypot(*(p - sm).T); xi = p[:, 0].astype(int).clip(0, W - 1); yi = p[:, 1].astype(int).clip(0, H - 1)
        inb = band[yi, xi]
        if inb.any(): step = max(step, float(dv[inb].max()))
    # line breaks: silhouette-edge px (8-adj to background) whose 5x5 neighbourhood inside S holds no line-dark px
    rgb = comp[..., :3].astype(int); dark = S & (rgb.sum(2) < 260) & ~((rgb[..., 1] == 255) & (rgb[..., 0] == 0))
    team = S & (rgb[..., 1] == 255) & (rgb[..., 0] == 0) & (rgb[..., 2] == 0)
    edge = S & ndi.binary_dilation(~S, np.ones((3, 3))) & ~team
    near_dark = ndi.binary_dilation(dark, np.ones((5, 5)))
    brk = edge & ~near_dark & band & ~ndi.binary_dilation(team, np.ones((7, 7)))
    return dict(step_px=round(step, 2), dent_px=round(dent, 2), holes=int(holes.sum()), line_break_px=int(brk.sum())), dict(holes=holes, notch=notch & band, brk=brk)
