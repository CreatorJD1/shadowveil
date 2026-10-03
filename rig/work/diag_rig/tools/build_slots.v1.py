#!/usr/bin/env python3
"""Diagonal rig slots (Coder, staged): rig/work/diag_rig/slots/d<ang>/ in FRAME coordinates.

Every slot PNG is 1365x1739 (the rig canvas) with her turn frame's pixels at their own frame position (offset 0,0;
no resampling, no mirroring, no drawn pixel). Only her frame pixels are ever copied; staged owner art is used as MASKS
(hands frame_scale, hair v3, mouth rest lips) or copied as-is (Eyes' frame-px parts). Reads only; writes only under
rig/work/diag_rig/. Usage: python3 build_slots.py [045,315,135,225]
"""
import json, os, sys, shutil, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = '/workspace/shadowveil'; OUT = f'{ROOT}/rig/work/diag_rig/slots'
W, H = 1365, 1739
FR = {'045': 'f033', '135': 'f087', '225': 'f131', '315': 'f191'}
FIT = {'045': (1.54468, 83.62, -55.77), '135': (1.57033, 112.9, -41.66), '225': (1.57335, 56.1, -44.96), '315': (1.54468, 104.47, -52.68)}
HANDDIR = {'045': '45', '135': '135', '225': '225', '315': '315'}
FRONT = {'045': True, '315': True, '135': False, '225': False}
def P(*a): return os.path.join(ROOT, *a)
def rgba(p): return np.asarray(Image.open(p).convert('RGBA'))
def pad(a):
    o = np.zeros((H, W, 4), np.uint8); o[:a.shape[0], :a.shape[1]] = a; return o
def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); Image.fromarray(a, 'RGBA').save(p + '.tmp.png'); os.replace(p + '.tmp.png', p)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def jdump(o, p): os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p + '.tmp', 'w'), indent=1); os.replace(p + '.tmp', p)

def key_frame(ang):
    f = np.asarray(Image.open(P('reference/apose_turn/frames', FR[ang] + '.png')).convert('RGB')).astype(int)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    key = (b > np.maximum(r, g) + 60) & (b > 120)          # = qa_gates chroma rule: what is key, is background
    fig = ~key; lab, n = ndi.label(fig); sz = ndi.sum(fig, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool); keep[1:] = sz >= 30; fig2 = keep[lab]
    a = np.zeros(f.shape[:2] + (4,), np.uint8); a[..., :3] = np.where(fig2[..., None], f, 0); a[..., 3] = fig2 * 255
    enclosed_key = int((key & ndi.binary_fill_holes(fig2) & (ndi.label(key)[0] > 0)).sum())
    return f.astype(np.uint8), a, {'key_px': int(key.sum()), 'dropped_specks_px': int((fig & ~fig2).sum()), 'dropped_specks': int((sz < 30).sum()),
                                   'fringe_px_kept(25<b-max<=60)': int((fig2 & (b - np.maximum(r, g) > 25)).sum())}

def view_mask_to_frame(vm, fit, fh=1168, fw=768):
    """vm: view-space bool/alpha (H,W). Sample at the mapped centre of each frame px (bilinear alpha >= 0.5)."""
    s, dx, dy = fit; yy, xx = np.mgrid[:fh, :fw].astype(float)
    vx = s * xx + dx; vy = s * yy + dy
    a = vm.astype(float); out = ndi.map_coordinates(a, [vy, vx], order=1, mode='constant', cval=0)
    return out >= 0.5 * a.max() if a.max() > 0 else np.zeros((fh, fw), bool)

def segs(row):
    d = np.diff(np.r_[0, row.astype(int), 0]); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]
    return [(a, b - 1) for a, b in zip(s, e)]

def fit_skeleton(ang, fig, palm):
    s, dx, dy = FIT[ang]; inv = lambda vy: (vy - dy) / s
    apose = {p['id']: p for p in json.load(open(P('views/apose/body/rig.json')))['parts']}
    ys = {k: inv(v) for k, v in dict(waist=706, shoulder=439, elbow=562.25, hip=792, knee=1150, ankle=1570, neck=363.5).items()}
    cols = np.nonzero(fig.any(0))[0]; xc0 = np.median(np.nonzero(fig)[1])
    def row(y): return segs(fig[int(round(y))])
    def seg_near(y, x):
        ss = row(y); return min(ss, key=lambda q: 0 if q[0] <= x <= q[1] else min(abs(q[0] - x), abs(q[1] - x)))
    t = seg_near(ys['waist'], xc0); xc = (t[0] + t[1]) / 2; waist_w = t[1] - t[0] + 1
    near_side = None
    # legs: first row below the hip line where the central body splits into 2 wide segments
    yc = None
    for y in range(int(ys['hip']), int(ys['knee'])):
        ss = [q for q in row(y) if q[1] - q[0] >= 15 and abs((q[0] + q[1]) / 2 - xc) < 120]
        if len(ss) >= 2: yc = y; break
    def legs_at(y):
        ss = sorted([q for q in row(y) if q[1] - q[0] >= 8 and abs((q[0] + q[1]) / 2 - xc) < 140], key=lambda q: -(q[1] - q[0]))[:2]
        ss = sorted(ss)
        if len(ss) == 2: return [((q[0] + q[1]) / 2, q[1] - q[0] + 1) for q in ss]
        if len(ss) == 1:  # merged: split at the middle
            q = ss[0]; m = (q[0] + q[1]) / 2; return [((q[0] + m) / 2, (m - q[0])), ((m + q[1]) / 2, (q[1] - m))]
        return None
    hipL = legs_at(yc + 12) if yc else None
    knee = legs_at(ys['knee']); ankle = legs_at(ys['ankle'])
    # arms: outermost segments at the elbow row; wrist = Hands' palm pivot (frame); shoulder on the wrist->elbow line
    ss = row(ys['elbow']); armVL, armVR = ss[0], ss[-1]
    elb = {'vl': ((armVL[0] + armVL[1]) / 2, armVL[1] - armVL[0] + 1), 'vr': ((armVR[0] + armVR[1]) / 2, armVR[1] - armVR[0] + 1)}
    # side map: viewer-left limbs are her RIGHT at the front diagonals, her LEFT at the back diagonals
    side = {'vl': 'R', 'vr': 'L'} if FRONT[ang] else {'vl': 'L', 'vr': 'R'}
    sideOf = {v: k for k, v in side.items()}
    piv = {}; rad = {}
    piv['pelvis'] = piv['torso'] = piv['head'] = (xc, ys['waist']); rad['torso'] = waist_w / 2
    for vside, k in (('vl', 0), ('vr', 1)):
        S = side[vside]; wx, wy = palm[S]; ex, ew = elb[vside]; ey = ys['elbow']
        # elbow: arm centre at the elbow row; shoulder: extend wrist->elbow to the shoulder row
        sy = ys['shoulder']; sx = ex + (ex - wx) * (sy - ey) / (ey - wy)
        piv['upperArm_' + S] = (sx, sy); piv['forearm_' + S] = (ex, ey); piv['wrist_' + S] = (wx, wy); rad['arm_' + S] = ew / 2
        hx = hipL[k][0] if hipL else xc + (-1 if vside == 'vl' else 1) * waist_w / 4
        piv['thigh_' + S] = (hx, ys['hip']); piv['shin_' + S] = (knee[k][0], ys['knee']); piv['foot_' + S] = (ankle[k][0], ys['ankle'])
        piv['toes_' + S] = (ankle[k][0], inv(1575)); rad['leg_' + S] = knee[k][1] / 2; rad['thighw_' + S] = (hipL[k][1] / 2) if hipL else knee[k][1] / 2
    # Body's in-progress hand-placed joints (body_tools/work/diag_body/tools/diag_config.json, FRAME px; read-only) win where present
    used = []
    try: cfg = json.load(open(P('body_tools/work/diag_body/tools/diag_config.json'))).get(ang)
    except Exception: cfg = None
    if cfg:
        for S in 'LR':
            for k, b in (('shoulder_', 'upperArm_'), ('elbow_', 'forearm_'), ('hip_', 'thigh_'), ('knee_', 'shin_')):
                if k + S in cfg: piv[b + S] = tuple(cfg[k + S]); used.append(k + S)
            if 'ankle_' + S in cfg:
                a_ = np.array(cfg['ankle_' + S], float).mean(0); piv['foot_' + S] = tuple(a_); piv['toes_' + S] = (a_[0], a_[1] + 3); used.append('ankle_' + S)
        if 'waist_pivot' in cfg: piv['pelvis'] = piv['torso'] = piv['head'] = tuple(cfg['waist_pivot']); ys['waist'] = cfg['waist_pivot'][1]; xc = cfg['waist_pivot'][0]; used.append('waist_pivot')
        if 'neck_base' in cfg: ys['neck'] = float(np.mean([q[1] for q in cfg['neck_base']])); used.append('neck_base(mean y)')
        if 'hip_R' in cfg: ys['hip'] = float(np.mean([cfg['hip_R'][1], cfg['hip_L'][1]]))
        if 'knee_R' in cfg: ys['knee'] = float(np.mean([cfg['knee_R'][1], cfg['knee_L'][1]]))
    meta = {'body_config_used': used, 'ys': {k: round(v, 2) for k, v in ys.items()}, 'xc': float(xc), 'crotch_y': yc, 'side_map(viewer->her)': side, 'radii': {k: round(v, 2) for k, v in rad.items()}}
    return piv, rad, meta, ys, side

def dist_seg(xx, yy, a, b):
    a = np.array(a, float); b = np.array(b, float); d = b - a; L2 = max(d @ d, 1e-9)
    t = np.clip(((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / L2, 0, 1)
    return np.hypot(xx - (a[0] + t * d[0]), yy - (a[1] + t * d[1]))

def build(ang):
    sd = f'{OUT}/d{ang}'; fit = FIT[ang]; s, fdx, fdy = fit
    if os.path.isdir(sd): shutil.rmtree(sd)
    os.makedirs(sd)
    frame, keyed, keyrep = key_frame(ang); fig = keyed[..., 3] > 0; fh, fw = fig.shape
    rep = {'angle': int(ang), 'frame': FR[ang], 'viewFit_for_display_only': dict(scale=s, dx=fdx, dy=fdy), 'key': keyrep, 'systems': {}}
    # ---------------- hands: Hands' frame_scale alpha as the mask, pixels from her frame
    hd = P('hands/staged/f8_diagonals', HANDDIR[ang]); f12 = P('hands/staged/f12_wrist_diag', HANDDIR[ang])
    hrsrc = f'{f12}/rig.json' if os.path.exists(f'{f12}/rig.json') else f'{hd}/rig.json'; hr = json.load(open(hrsrc))
    hands_mask = np.zeros((fh, fw), bool); hparts = []; os.makedirs(f'{sd}/hands')
    inv = lambda x, y: [round((x - fdx) / s, 3), round((y - fdy) / s, 3)]
    for p in hr['parts']:
        q = dict(p); fpng = os.path.normpath(os.path.join(hd, p['frame_file'])) if p.get('frame_file') else f'{hd}/frame_scale/{p["file"]}'
        if p.get('frame_file'):  # F12 hidden wrist flap: Hands' frame-scale art copied as-is (hidden under forearm + palm at rest)
            q['file'] = os.path.basename(p['frame_file']); a = rgba(fpng).copy(); save(pad(a), f'{sd}/hands/{q["file"]}'); q.pop('frame_file', None)
        elif p.get('file') and os.path.exists(fpng):
            m = rgba(fpng)[..., 3] > 0; m &= fig; hands_mask |= m
            a = np.zeros((fh, fw, 4), np.uint8); a[m] = keyed[m]; save(pad(a), f'{sd}/hands/{p["file"]}')
        x, y = (p['pivot_frame'] if p.get('pivot_frame') else inv(p['pivotX'], p['pivotY'])); q['pivotX'], q['pivotY'] = x, y; q.pop('pivot_frame', None)
        if q.get('jointRadiusPx'): q['jointRadiusPx'] = round(q['jointRadiusPx'] / s, 3)
        hparts.append(q)
    palm = {S: next((q['pivotX'], q['pivotY']) for q in hparts if q['id'] == S + '_palm') for S in 'LR'}
    hj = {k: v for k, v in hr.items() if k != 'parts'}
    hj.update({'view': 'd' + ang, 'canvas': [W, H], 'coordinateSpace': f'FRAME px of {FR[ang]} at offset (0,0) on the {W}x{H} rig canvas',
               'source_rig': os.path.relpath(hrsrc, ROOT), 'pixels': 'her frame px under Hands\' frame_scale alpha', 'parts': hparts})
    jdump(hj, f'{sd}/hands/rig.json'); rep['systems']['hands'] = {'parts': len([q for q in hparts if q.get('file')]), 'px': int(hands_mask.sum()),
        'near': [S for S in 'LR' if any(q['id'].startswith(S + '_Index') for q in hparts)]}
    # ---------------- skeleton fit (shared bone names / params / limits from views/apose/body/rig.json)
    piv, rad, meta, ys, side = fit_skeleton(ang, fig, palm)
    body = fig & ~hands_mask
    yy, xx = np.mgrid[:fh, :fw].astype(float)
    caps = {}
    xc = meta['xc']
    caps['torso'] = dist_seg(xx, yy, (xc, ys['neck']), (xc, ys['waist'])) - rad['torso']
    ylim = max(meta['crotch_y'] or ys['hip'], ys['hip']) + 5
    caps['pelvis'] = np.where(yy <= ylim, dist_seg(xx, yy, (xc, ys['waist']), (xc, ys['hip'])) - rad['torso'] * 0.95, 1e9)
    for S in 'LR':
        caps['upperArm_' + S] = dist_seg(xx, yy, piv['upperArm_' + S], piv['forearm_' + S]) - rad['arm_' + S] * 1.1
        caps['forearm_' + S] = dist_seg(xx, yy, piv['forearm_' + S], piv['wrist_' + S]) - rad['arm_' + S]
        caps['thigh_' + S] = dist_seg(xx, yy, piv['thigh_' + S], piv['shin_' + S]) - rad['thighw_' + S]
        caps['shin_' + S] = dist_seg(xx, yy, piv['shin_' + S], piv['foot_' + S]) - rad['leg_' + S]
        caps['foot_' + S] = dist_seg(xx, yy, piv['foot_' + S], (piv['foot_' + S][0], fh)) - rad['leg_' + S] * 0.8
    # feet: below the ankle line, a watershed of her figure from each ankle (the split falls on the narrowest contact)
    from skimage.segmentation import watershed
    ay = min(piv['foot_L'][1], piv['foot_R'][1]) + 8; low = body & (yy > ay)
    mk = np.zeros((fh, fw), np.int32)
    for i, S in enumerate('LR'):
        fx, fy = piv['foot_' + S]; band = low & (np.abs(yy - (ay + 3)) <= 3) & (np.abs(xx - fx) <= 10); mk[band] = i + 1
    ws = watershed(-ndi.distance_transform_edt(low), mk, mask=low)
    for i, S in enumerate('LR'): caps['foot_' + S] = np.where(ws == i + 1, -1e6, np.where(low, 1e9, caps['foot_' + S]))
    names = list(caps); D = np.stack([caps[n] for n in names]); own = np.argmin(D, 0)
    owner = {n: body & (own == i) for i, n in enumerate(names)}
    # head: everything above the neck base that the torso capsule claims (head+neck+hair+bun), never an arm
    head = body & (yy < ys['neck']) & np.isin(own, [names.index('torso'), names.index('pelvis')])
    # hair hanging below the neck line inside the torso column stays torso (it is drawn over the shoulders in her frame)
    owner['head'] = head; owner['torso'] = owner['torso'] & ~head
    # small disconnected crumbs of a part -> nearest neighbour owner (no bone owns a speck across a gap)
    for n in list(owner):
        lab, k = ndi.label(owner[n])
        if k > 1:
            sz = ndi.sum(owner[n], lab, range(1, k + 1)); big = np.argmax(sz) + 1
            for i in range(1, k + 1):
                if i != big and sz[i - 1] < 400: owner[n][lab == i] = False
    claimed = np.zeros((fh, fw), bool)
    for n in owner: claimed |= owner[n]
    un = body & ~claimed
    if un.any():
        idmap = np.full((fh, fw), -1, int); order = list(owner)
        for i, n in enumerate(order): idmap[owner[n]] = i
        _, (iy, ix) = ndi.distance_transform_edt(idmap < 0, return_indices=True); nn = idmap[iy, ix]
        for i, n in enumerate(order): owner[n] |= un & (nn == i)
    ap = json.load(open(P('views/apose/body/rig.json')))
    bparts = []; os.makedirs(f'{sd}/body')
    for p in ap['parts']:
        q = {k: v for k, v in p.items() if k not in ('pixels', 'addedHiddenPixels', 'note')}
        pid = p['id']; pv = piv.get(pid)
        q['pivotX'], q['pivotY'] = round(float(pv[0]), 2), round(float(pv[1]), 2)
        if pid.startswith('forearm_'): S = pid[-1]; q['wristPivot'] = {'x': palm[S][0], 'y': palm[S][1]}
        if p.get('file'):
            a = np.zeros((fh, fw, 4), np.uint8); m = owner[pid]; a[m] = keyed[m]; save(pad(a), f'{sd}/body/{p["file"]}'); q['pixels'] = int(m.sum())
        q['addedHiddenPixels'] = 0
        bparts.append(q)
    bj = {k: v for k, v in ap.items() if k != 'parts'}
    bj.update({'owner': 'Coder (interim, until Body\'s body_tools/work/diag_body/<angle>/ lands)', 'view': 'd' + ang, 'skin': 'skin.json',
               'canvas': [W, H], 'coordinateSpace': f'FRAME px of {FR[ang]} at (0,0) on the rig canvas; every part PNG full-canvas',
               'skeleton': 'shared: bone names, parents, params, limits and layers = views/apose/body/rig.json; pivots fitted to this frame',
               'fit': meta, 'parts': bparts})
    jdump(bj, f'{sd}/body/rig.json')
    bimg = np.zeros((fh, fw, 4), np.uint8); bimg[body] = keyed[body]
    save(pad(bimg), f'{sd}/base_body_skin.png'); save(pad(bimg), f'{sd}/base_body.png'); save(pad(keyed), f'{sd}/base.png')
    rep['systems']['body'] = {'px': int(body.sum()), 'parts': {n: int(owner[n].sum()) for n in owner}, 'pivots': {k: [round(float(v[0]), 1), round(float(v[1]), 1)] for k, v in piv.items()}, 'fit': meta}
    # ---------------- hair: v3 alpha (view space) mapped to frame px as a MASK; pixels from her frame; sway 0 (no under-strand art)
    hv = P('hair/staged/diagonals_v3', ang, 'hair'); hrj = json.load(open(f'{hv}/rig.json')); hparts2 = []; os.makedirs(f'{sd}/hair')
    taken = np.zeros((fh, fw), bool)
    for p in sorted(hrj['parts'], key=lambda p: -p.get('layer', 0)):
        q = dict(p); m = np.zeros((fh, fw), bool)
        if p.get('file') and os.path.exists(f'{hv}/{p["file"]}'):
            m = view_mask_to_frame(rgba(f'{hv}/{p["file"]}')[..., 3], fit) & fig & ~hands_mask & ~taken; taken |= m
            a = np.zeros((fh, fw, 4), np.uint8); a[m] = keyed[m]; save(pad(a), f'{sd}/hair/{p["file"]}')
        x, y = inv(p['pivotX'], p['pivotY']); q['pivotX'], q['pivotY'] = x, y
        cap = {('315', 'strand_06'): {'max': 0}, ('045', 'strand_03_tip'): {'min': 0}}.get((ang, p['id']))
        if cap: q['swayCap'] = dict(cap, why='keeps the strand out of the eye opening until Hair v4 (per part)')
        q['swayWeightStaged'] = p.get('swayWeight', 0); q['swayWeight'] = 0; q['swayY'] = 0; q['px'] = int(m.sum())
        hparts2.append(q)
    hparts2.sort(key=lambda q: [p['id'] for p in hrj['parts']].index(q['id']))
    hj2 = {k: v for k, v in hrj.items() if k != 'parts'}
    hj2.update({'view': 'd' + ang, 'canvas': [W, H], 'source_rig': os.path.relpath(f'{hv}/rig.json', ROOT), 'swayYMaxPx': 0,
                'note': 'static: her frame has no art under the strands (the head copy is under them), so sway would double-draw. Hair must supply under-strand art to enable sway.', 'parts': hparts2})
    jdump(hj2, f'{sd}/hair/rig.json'); rep['systems']['hair'] = {p['id']: p['px'] for p in hparts2}
    # ---------------- eyes (045/315 only): Eyes' frame-px parts copied as-is (padded); per-eye v4 limits
    if ang in ('045', '315'):
        ed = P('eyes/staged/diagonals', ang); ej = json.load(open(f'{ed}/rig.json')); os.makedirs(f'{sd}/eyes'); eyerep = {}
        for p in ej['parts']:
            if p.get('file'):
                a = rgba(f'{ed}/{p["file"]}').copy()
                bad = (a[..., 3] > 0) & ~fig; eyerep[p['file']] = {'px_on_key_removed': int(bad.sum())}; a[bad] = 0
                save(pad(a), f'{sd}/eyes/{p["file"]}')
        v4 = json.load(open(P('rig/work/irislimits/diag_irislimits_v4.json')))['angles'][ang]['eyes']
        per = {e: dict(v['irislimits_diag_v2'], corners={c: [x['dx'], x['dy']] for c, x in v['corners'].items()}) for e, v in v4.items()}
        common = {'dxAtXplus1': min(per[e]['dxAtXplus1'] for e in per), 'dxAtXminus1': max(per[e]['dxAtXminus1'] for e in per), 'dyAtYplus1': 1, 'dyAtYminus1': -1}
        ej = dict(ej); ej['view'] = 'd' + ang; ej['canvas'] = [W, H]; ej['irisLimitsPx'] = common
        ej['irisLimitsPxPerEye'] = per; ej['irisLimitsSource'] = 'rig/work/irislimits/diag_irislimits_v4.json (per eye, read when ?diag=1; irisLimitsPx = the common fallback)'
        jdump(ej, f'{sd}/eyes/rig.json'); rep['systems']['eyes'] = {'parts': len([p for p in ej['parts'] if p.get('file')]), 'removed_on_key': sum(v['px_on_key_removed'] for v in eyerep.values())}
        # ---------------- mouth: Mouth's diag_posable frame_scale parts (her frame px for rest), copied as-is, never resampled
        md = P('mouth/staged/diag_posable', ang); mr = json.load(open(f'{md}/rig.json')); os.makedirs(f'{sd}/mouth'); mparts = []; mrep = {}
        for p in mr['parts']:
            q = {k: v for k, v in p.items() if k not in ('viewFile', 'viewChromaFile', 'chromaFile', 'viewPivotX', 'viewPivotY')}
            fn = os.path.basename(p['file']); a = rgba(f'{md}/{p["file"]}').copy(); bad = (a[..., 3] > 0) & ~fig if p['id'] == 'mouth_rest' else np.zeros(a.shape[:2], bool)
            a[bad] = 0; save(pad(a), f'{sd}/mouth/{fn}'); q['file'] = fn; q['parent'] = 'base'; mparts.append(q); mrep[p['id']] = int((a[..., 3] > 0).sum())
        base_mj = {k: v for k, v in mr.items() if k not in ('parts', 'canvas', 'viewCanvas')}
        base_mj.update({'view': 'd' + ang, 'canvas': {'width': W, 'height': H}, 'source_rig': os.path.relpath(f'{md}/rig.json', ROOT)})
        jdump(dict(base_mj, parts=[q for q in mparts if not q.get('requiresFlag')], note='default: her rest lips only'), f'{sd}/mouth/rig.json')
        jdump(dict(base_mj, parts=mparts, note='?diagmouth=1 only: open shapes are FRONT mouth art bent onto her diagonal lips (needs an OK line)'), f'{sd}/mouth/rig_diagmouth.json')
        rep['systems']['mouth'] = {'parts_px': mrep, 'default': ['mouth_rest'], 'diagmouth': [q['id'] for q in mparts]}
    locks = {'WristL': 0, 'WristR': 0} if ang in ('045', '315') else {}
    jdump({'contract': 'diag slot v1', 'angle': int(ang), 'frame': FR[ang], 'canvas': [W, H], 'frameSize': [fw, fh], 'crop': [0, 0, fw, fh],
           'viewFit': dict(scale=s, dx=fdx, dy=fdy), 'face': ang in ('045', '315'),
           'locks': locks, 'locksWhy': 'wrist bend locked to 0 until Hands\' hidden wrist flaps pass (045/315)' if locks else '',
           'hairSway': 'static (0) until Hair supplies under-strand art; v4 per-part caps: 315 strand_06 +X, 045 strand_03_tip -X',
           'mouth': 'rest only; open shapes need ?diagmouth=1 and mouth/rig_diagmouth.json (not delivered)'}, f'{sd}/diag.json')
    rep['files'] = {os.path.relpath(os.path.join(dp, f), sd): sha(os.path.join(dp, f)) for dp, _, fs in os.walk(sd) for f in fs if f.endswith('.png')}
    jdump(rep, f'{sd}/slot.json'); return rep

if __name__ == '__main__':
    angs = (sys.argv[1] if len(sys.argv) > 1 else '045,315,135,225').split(',')
    for a in angs:
        r = build(a); print(a, json.dumps({k: r[k] for k in ('key',)}), json.dumps(r['systems'].get('body', {}).get('pivots')))
