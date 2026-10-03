#!/usr/bin/env python3
"""rig/qa_gates.py: read-only QA gates for the Shadowveil rig. Usage notes: rig/work/qa_gates/README.md

  G1 weights : weight bleed in body skin.json (+underlay), and bone-isolation motion test
  G2 leak    : chroma / off-palette / soft-edge / colour-outside-mask sweep (live + staged + diagonals)
  G3 scale   : hand / foot proportions vs head & forearm, per view, against the apose master

Never writes outside --out (default rig/work/qa_gates/out). Exit code 1 if any gate fails.
"""
import argparse, json, os, re, sys, glob
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['apose', 'tpose', 'left', 'right', 'back']
SYSTEMS = ['body', 'eyes', 'mouth', 'hands', 'hair']
BODY_LIMIT_DEFAULT = {'toes_L': [20, -30], 'toes_R': [20, -30]}  # mirrors rig/index.html line 52
DIAG_FRAME = {'045': 'f033', '135': 'f087', '225': 'f131', '315': 'f191'}
STAGED_TONE = ['eyes/work/lashfix/staged', 'hair/staged/tone_fix', 'mouth/staged/tone_fix']

def P(*a): return os.path.join(ROOT, *a)

# per-part dir overrides (--hair-dir/--mouth-dir/--eyes-dir/--hands-dir/--body-dir): a system's folder for a view is looked up
# in the override first: DIR with {view} substituted, DIR/<view>/<sys>, DIR/views/<view>/<sys>, DIR/<view>, DIR (if it has
# rig.json); falls back to views/<view>/<sys>. Diagonal angles (045/135/225/315) can be passed to --view with an override.
SYS_DIR = {}
def sysdir(view, system):
    o = SYS_DIR.get(system)
    if o:
        o = o if os.path.isabs(o) else P(o)
        for c in (o.replace('{view}', view), os.path.join(o, view, system), os.path.join(o, 'views', view, system), os.path.join(o, view), o):
            if '{view}' not in c and os.path.isdir(c) and (os.path.exists(os.path.join(c, 'rig.json')) or glob.glob(os.path.join(c, '*.png'))): return c
    return P('views', view, system)
def jload(p):
    with open(p) as f: return json.load(f)
def parts_of(rig): return rig if isinstance(rig, list) else rig.get('parts', [])
def rgba(p): return np.asarray(Image.open(p).convert('RGBA'))

# ---------------------------------------------------------------- pose maths (index.html bodyAngle / rotAt / chain)
def rot_at(px, py, deg):
    t = np.deg2rad(deg); c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, px - c*px + s*py], [s, c, py - s*px - c*py], [0, 0, 1.0]])

def body_angle(b, x):
    lim = BODY_LIMIT_DEFAULT.get(b['name']) if (b.get('maxDeg', b.get('maxRotDeg')) is None and b.get('degAtPlus1') is None and b.get('degAtMinus1') is None) else None
    mx = b.get('maxDeg', b.get('maxRotDeg')) or 0
    rd = b.get('rotDir', 1) if isinstance(b.get('rotDir'), (int, float)) else 1
    up = b['degAtPlus1'] if b.get('degAtPlus1') is not None else (lim[0] if lim else rd*mx)
    if b.get('degAtMinus1') is not None: dn = b['degAtMinus1']
    elif isinstance(b.get('minRotDeg'), (int, float)): dn = rd*b['minRotDeg']
    else: dn = lim[1] if lim else -rd*mx
    return x*up if x >= 0 else abs(x)*dn

def bone_mats(bones, angles):
    """angles: {boneName: deg}. Returns list of 3x3 world matrices (M = M_parent . rotAt)."""
    idx = {b['name']: i for i, b in enumerate(bones)}; out = [None]*len(bones)
    def get(i):
        if out[i] is not None: return out[i]
        b = bones[i]; par = b.get('parent'); pi = idx.get(par) if isinstance(par, str) else par
        Mp = get(pi) if pi is not None else np.eye(3)
        out[i] = Mp @ rot_at(b['pivot'][0], b['pivot'][1], angles.get(b['name'], 0.0)); return out[i]
    for i in range(len(bones)): get(i)
    return out

def lbs(verts, wts, mats):
    V = np.c_[verts, np.ones(len(verts))]; out = np.zeros((len(verts), 2))
    for i, ws in enumerate(wts):
        for bi, w in ws: out[i] += w * (mats[bi] @ V[i])[:2]
    return out

def lbs_fast(verts, W, mats):
    V = np.c_[verts, np.ones(len(verts))]; out = np.zeros((len(verts), 2))
    for k, M in enumerate(mats):
        if W[:, k].any(): out += W[:, k:k+1] * (V @ M.T)[:, :2]
    return out

def dense_w(wts, nb):
    W = np.zeros((len(wts), nb))
    for i, ws in enumerate(wts):
        for bi, w in ws: W[i, bi] += w
    return W

def relations(bones):
    idx = {b['name']: i for i, b in enumerate(bones)}
    par = [idx.get(b['parent']) if isinstance(b.get('parent'), str) else b.get('parent') for b in bones]
    kids = [[j for j in range(len(bones)) if par[j] == i] for i in range(len(bones))]
    rel = []
    for i in range(len(bones)):
        s = {i}
        if par[i] is not None: s |= {par[i]} | set(kids[par[i]])
        s |= set(kids[i]); rel.append(s)
    def desc(i):
        s = set(); st = list(kids[i])
        while st: j = st.pop(); s.add(j); st += kids[j]
        return s
    return par, kids, rel, desc

def poses_for(bones):
    """rest, each param ±1 alone, all +1, all -1"""
    ps = {'rest': {}}
    params = [b for b in bones if b.get('param')]
    for b in params:
        for x in (1, -1): ps[f"{b['param']}{'+' if x > 0 else '-'}1"] = {b['name']: body_angle(b, x)}
    ps['all+1'] = {b['name']: body_angle(b, 1) for b in params}
    ps['all-1'] = {b['name']: body_angle(b, -1) for b in params}
    return ps

# ---------------------------------------------------------------- owner map (top-layer body part masks, like build_skin)
def owner_map(view, bones):
    rig = jload(os.path.join(sysdir(view, 'body'), 'rig.json')); idx = {b['name']: i for i, b in enumerate(bones)}
    om = None
    for p in sorted(parts_of(rig), key=lambda p: p.get('layer', 0)):
        if not p.get('file'): continue
        f = os.path.join(sysdir(view, 'body'), p['file'])
        if p['id'] not in idx or not os.path.exists(f): continue
        a = rgba(f)[..., 3]
        if om is None: om = np.full(a.shape, -1, np.int16)
        x, y = int(p.get('x', 0)), int(p.get('y', 0)); h, w = a.shape
        sub = om[y:y+h, x:x+w]; m = a[:sub.shape[0], :sub.shape[1]] > 0; sub[m] = idx[p['id']]
    return om

# ---------------------------------------------------------------- G1 weights
def gate_weights(view, skin_path=None, tol_px=0.5, wmin=1e-3):
    sk = jload(skin_path or os.path.join(sysdir(view, 'body'), 'skin.json')); bones = sk['bones']; nb = len(bones)
    par, kids, rel, desc = relations(bones); names = [b['name'] for b in bones]
    om = owner_map(view, bones); res = {'skin': os.path.relpath(skin_path or os.path.join(sysdir(view, 'body'), 'skin.json'), ROOT), 'meshes': {}}
    meshes = [('skin', sk)] + ([('underlay', sk['underlay'])] if isinstance(sk.get('underlay'), dict) and sk['underlay'].get('weights') else [])
    fail = False
    for mname, m in meshes:
        V = np.asarray(m['vertices'], float); W = dense_w(m['weights'], nb)
        dom = W.argmax(1)
        # texel owner at the vertex (falls back to dominant weight bone off-mask)
        xi = np.clip(np.round(V[:, 0]).astype(int), 0, om.shape[1]-1); yi = np.clip(np.round(V[:, 1]).astype(int), 0, om.shape[0]-1)
        own = om[yi, xi].astype(int); own = np.where(own >= 0, own, dom)
        bleed = {}; bleed_v = set()
        for i in range(len(V)):
            for k in np.nonzero(W[i] > wmin)[0]:
                if k not in rel[dom[i]]:
                    key = f"{names[dom[i]]}<-{names[k]}"; bleed[key] = bleed.get(key, 0) + 1; bleed_v.add(i)
        mask_bleed = {}
        for i in range(len(V)):
            for k in np.nonzero(W[i] > wmin)[0]:
                if k not in rel[own[i]]:
                    key = f"{names[own[i]]}<-{names[k]}"; mask_bleed[key] = mask_bleed.get(key, 0) + 1
        # isolation: rotate each bone alone at ±1
        iso = {}
        for bi, b in enumerate(bones):
            if not b.get('param'): continue
            allowed = {bi} | desc(bi) | rel[bi]   # self, descendants, parent, siblings = related (seam blending is allowed)
            worst = 0.0; n = 0; who = {}; seam = 0
            for x in (1, -1):
                mats = bone_mats(bones, {b['name']: body_angle(b, x)})
                d = np.linalg.norm(lbs_fast(V, W, mats) - V, axis=1)
                bad = (d > tol_px) & ~np.isin(own, list(allowed))
                seam = max(seam, int(((d > tol_px) & np.isin(own, list(rel[bi] - {bi} - desc(bi)))).sum()))
                n = max(n, int(bad.sum())); worst = max(worst, float(d[bad].max()) if bad.any() else 0.0)
                for o in np.unique(own[bad]): who[names[o]] = max(who.get(names[o], 0), int((own[bad] == o).sum()))
            iso[b['name']] = {'verts_of_other_parts_moving_gt_%.1fpx' % tol_px: n, 'max_px': round(worst, 2), 'by_part': who, 'info_related_parent_or_sibling_verts_moving': seam}
        r = {'vertices': len(V), 'bleed_vs_dominant_bone': {'vertices': len(bleed_v), 'pairs': bleed},
             'bleed_vs_texel_owner': {'pairs': mask_bleed, 'vertices_total': int(sum(mask_bleed.values()))},
             'isolation': iso}
        r['pass'] = (len(bleed_v) == 0) and all(v[list(v)[0]] == 0 for v in iso.values())
        fail |= not r['pass']; res['meshes'][mname] = r
    res['pass'] = not fail
    return res

# ---------------------------------------------------------------- palette
_pal_cache = {}
def colours(path, alpha_min=255):
    a = rgba(path); m = a[..., 3] >= alpha_min
    c = a[..., :3][m].astype(np.int32); return np.unique((c[:, 0] << 16) | (c[:, 1] << 8) | c[:, 2])

def palette(keys):
    k = tuple(sorted(set(keys)))
    if k not in _pal_cache:
        s = np.unique(np.concatenate([colours(P(x), 255 if x.endswith('.png') else 0) for x in k]))
        _pal_cache[k] = s
    return _pal_cache[k]

def palette_sources(view, system, fname):
    """per part: base.png tones + her own authored art that the part comes from"""
    src = []
    if view in VIEWS: src.append(f'views/{view}/base.png')
    else:  # diagonal angle: all view bases + her turn frame
        src += [f'views/{v}/base.png' for v in VIEWS]
        fr = DIAG_FRAME.get(view)
        if fr and os.path.exists(P('reference/apose_turn/frames', fr + '.png')): src.append(f'reference/apose_turn/frames/{fr}.png')
    # her own live part files for this system and view (parent rule 01:58: a tone is hers if it is in ANY of her art for the
    # part+view, e.g. the live apose hand parts' (13,11,29)); diagonals: her live files of that system in all 5 views
    for v in ([view] if view in VIEWS else VIEWS):
        src += [os.path.relpath(f, ROOT) for f in live_files(v, system)]
    if system == 'mouth':
        src.append('reference/test_sheet_expressions.jpg')   # mouth interior, teeth, tongue
        if 'anger' in fname: src.append('reference/grok_build/public/puppet/emotions/anger.png')
    return src

def unpack(c): return np.stack([(c >> 16) & 255, (c >> 8) & 255, c & 255], 1)

def offpal_count(img, pal_codes, tol):
    a = img; op = a[..., 3] == 255
    c = a[..., :3][op].astype(np.int32); codes = (c[:, 0] << 16) | (c[:, 1] << 8) | c[:, 2]
    miss = ~np.isin(codes, pal_codes)
    if tol > 0 and miss.any():
        from scipy.spatial import cKDTree
        key = id(pal_codes)
        if key not in _tree_cache: _tree_cache[key] = cKDTree(unpack(pal_codes))
        u, inv = np.unique(codes[miss], return_inverse=True)
        d, _ = _tree_cache[key].query(unpack(u), k=1)
        miss_idx = np.nonzero(miss)[0]; still = d[inv] > tol
        miss = np.zeros_like(miss); miss[miss_idx[still]] = True
    return int(miss.sum()), int(op.sum())
_tree_cache = {}

def chroma_count(img, alpha_min=1):
    r, g, b, a = [img[..., i].astype(int) for i in range(4)]
    return int(((a >= alpha_min) & (b > np.maximum(r, g) + 60) & (b > 120)).sum())

def soft_count(img): a = img[..., 3]; return int(((a > 0) & (a < 255)).sum())

# ---------------------------------------------------------------- file sets
def live_files(view, system):
    d = sysdir(view, system)
    if not os.path.isdir(d): return []
    # only the files the rig references (rig.json, recursively): skips *_chroma.png key previews, sheets and notes
    refs = set()
    def walk(o):
        if isinstance(o, dict): [walk(x) for x in o.values()]
        elif isinstance(o, list): [walk(x) for x in o]
        elif isinstance(o, str) and o.lower().endswith('.png') and '/' not in o: refs.add(o)
    rj = os.path.join(d, 'rig.json')
    if os.path.exists(rj): walk(jload(rj))
    fs = sorted(os.path.join(d, f) for f in refs if os.path.exists(os.path.join(d, f)))
    if system == 'body':  # renderer draws the skin texture (+ underlay) for the body
        sk = os.path.join(sysdir(view, 'body'), 'skin.json')
        if os.path.exists(sk):
            j = jload(sk); ims = [j.get('image')] + [(j.get('underlay') or {}).get('image')]
            fs += [P('views', view, x) for x in ims if x and os.path.exists(P('views', view, x))]
    return fs

def staged_lookup(sdirs, view, system, fname):
    for s in sdirs:
        s = s if os.path.isabs(s) else P(s)
        for c in (os.path.join(s, view, system, fname), os.path.join(s, 'views', view, system, fname), os.path.join(s, view, fname)):
            if os.path.exists(c) and (system != 'eyes' or c.startswith(os.path.join(s, view))):
                if system == 'eyes' and not s.startswith(P('eyes')) and c == os.path.join(s, view, fname): continue
                if system != 'eyes' and c == os.path.join(s, view, fname) and not s.startswith(P(system)): continue
                return c
    return None

def diag_sets(part_filter):
    out = []
    for ang in sorted(DIAG_FRAME):
        for f in sorted(glob.glob(os.path.join(sysdir(ang, 'hair') if 'hair' in SYS_DIR else P('hair/staged/diagonals', ang, 'hair'), '*.png'))): out.append((ang, 'hair', f))
        for f in sorted(glob.glob(os.path.join(sysdir(ang, 'mouth') if 'mouth' in SYS_DIR else P('mouth/staged/diagonals', ang, 'renders'), '*.png'))): out.append((ang, 'mouth', f))
        for f in sorted(glob.glob(P('rig/hand_angles', ang + '_*.png'))): out.append((ang, 'hands', f))
    return [o for o in out if part_filter(o[1], os.path.basename(o[2]))]

def file_report(view, system, f, tol, pal_view=None):
    img = rgba(f); fn = os.path.basename(f)
    pal = palette(palette_sources(pal_view or view, system, fn))
    off, opq = offpal_count(img, pal, tol)
    return {'file': os.path.relpath(f, ROOT), 'opaque': opq, 'off_palette': off, 'chroma': chroma_count(img), 'soft_edge': soft_count(img)}

# ---------------------------------------------------------------- G2b mesh colour-outside-mask (posed)
def mesh_outside(view, skin_path=None, thr=1.0):
    sk = jload(skin_path or os.path.join(sysdir(view, 'body'), 'skin.json')); bones = sk['bones']; nb = len(bones)
    par, kids, rel, desc = relations(bones); om = owner_map(view, bones)
    tex = rgba(P('views', view, sk['image'])) if os.path.exists(P('views', view, sk['image'])) else rgba(os.path.join(sysdir(view, 'body'), sk['image']))
    V = np.asarray(sk['vertices'], float); W = dense_w(sk['weights'], nb); T = np.asarray(sk['triangles'])[:, :3]
    xi = np.clip(np.round(V[:, 0]).astype(int), 0, om.shape[1]-1); yi = np.clip(np.round(V[:, 1]).astype(int), 0, om.shape[0]-1)
    own = om[yi, xi].astype(int); own = np.where(own >= 0, own, W.argmax(1))
    opaque_v = tex[yi, xi, 3] > 0
    out = {}
    for pname, ang in poses_for(bones).items():
        mats = bone_mats(bones, ang); p = lbs_fast(V, W, mats); Vh = np.c_[V, np.ones(len(V))]
        # distance from LBS position to the hull of {M_k v : k in rel(owner)} ; approximated by min distance to
        # the segment set between related-bone positions (exact for <=2 moving bones, conservative otherwise)
        Q = np.stack([(Vh @ M.T)[:, :2] for M in mats], 1)  # n x nb x 2
        dev = np.full(len(V), np.inf)
        for k in range(nb):
            for j in range(k, nb):
                sel = np.array([k in rel[o] and j in rel[o] for o in range(nb)])[own]
                if not sel.any(): continue
                a = Q[:, k]; b = Q[:, j]; ab = b - a; L = (ab**2).sum(1)
                t = np.where(L > 1e-12, ((p - a)*ab).sum(1)/np.maximum(L, 1e-12), 0).clip(0, 1)
                d = np.linalg.norm(p - (a + t[:, None]*ab), axis=1); dev = np.where(sel, np.minimum(dev, d), dev)
        bad = (dev > thr) & opaque_v
        tri_bad = bad[T].any(1)
        out[pname] = {'vertices_outside_own_mask_gt_%gpx' % thr: int(bad.sum()), 'max_px': round(float(dev[bad].max()), 2) if bad.any() else 0.0,
                      'triangles_touched': int(tri_bad.sum())}
    return out

# ---------------------------------------------------------------- G3 scale
def bbox_h(path):
    a = rgba(path)[..., 3]; ys, xs = np.nonzero(a > 0)
    return (int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1)) if len(ys) else (0, 0)

def scale_measure(view):
    out = {}
    br = {p['id']: p for p in parts_of(jload(os.path.join(sysdir(view, 'body'), 'rig.json')))}
    sk = jload(os.path.join(sysdir(view, 'body'), 'skin.json')); bones = {b['name']: b for b in sk['bones']}
    head_h, _ = bbox_h(os.path.join(sysdir(view, 'body'), br['head'].get('file') or 'head.png'))
    out['head_h'] = head_h
    hr = {p['id']: p for p in parts_of(jload(P('views', view, 'hands', 'rig.json')))}
    for side, s in (('L', 'L'), ('R', 'R')):
        fb = bones.get(f'forearm_{side}'); wp = fb.get('wristPivot') if fb else None
        if wp: out[f'forearm_{side}'] = round(float(np.hypot(wp['x'] - fb['pivot'][0], wp['y'] - fb['pivot'][1])), 2)
        palm, m1, m2, m3 = (hr.get(f'{s}_{n}') if (hr.get(f'{s}_{n}') or {}).get('pivotX') is not None and (hr.get(f'{s}_{n}') or {}).get('file') else None for n in ('palm', 'Middle1', 'Middle2', 'Middle3'))
        if palm and m1:
            out[f'palm_{side}'] = round(float(np.hypot(m1['pivotX'] - palm['pivotX'], m1['pivotY'] - palm['pivotY'])), 2)
        if m1 and m2 and m3:
            f3 = P('views', view, 'hands', m3['file']); a = rgba(f3)[..., 3]; ys, xs = np.nonzero(a > 0)
            tip = 0.0
            if len(ys): tip = float(np.max(np.hypot(xs + m3.get('x', 0) - m3['pivotX'], ys + m3.get('y', 0) - m3['pivotY'])))
            out[f'finger_{side}'] = round(float(np.hypot(m2['pivotX']-m1['pivotX'], m2['pivotY']-m1['pivotY']) + np.hypot(m3['pivotX']-m2['pivotX'], m3['pivotY']-m2['pivotY']) + tip), 2)
        ft = br.get(f'foot_{side}')
        if ft and ft.get('file'):
            h, w = bbox_h(os.path.join(sysdir(view, 'body'), ft['file'])); out[f'foot_{side}'] = max(h, w)
    return out

def gate_scale(views, tol=1.0):
    master = scale_measure('apose'); res = {'master_view': 'apose', 'master': master, 'views': {}}; ok = True
    for v in views:
        m = scale_measure(v); rows = {}
        for k, val in m.items():
            if k == 'head_h' or k not in master: continue
            side = k.split('_')[-1]
            for refk in ('head_h', f'forearm_{side}'):
                if refk == k or refk not in m or refk not in master or not m[refk] or not master[refk]: continue
                expect = master[k] / master[refk] * m[refk]; drift = val - expect
                rows[f'{k}/{refk}'] = {'measured': val, 'expected_from_master': round(expect, 2), 'drift_px': round(drift, 2), 'flag': abs(drift) > tol}
        # parent rule 02:24: her five base views ARE the scale truth; their drift is listed as info and never fails.
        # Only generated turn frames / generated sprites are measured against them (see --scale-gen).
        for r_ in rows.values(): r_['info_only'] = True
        res['views'][v] = {'measures': m, 'ratios': rows, 'flags': 0, 'info_drift_gt_tol': sum(r['flag'] for r in rows.values())}
    # turn-angle hand sprites (rig/hand_angles/<ang>_<side>.json, cut from turn frames): physicalLength (frame px, wrist->tip)
    # x that frame's frame->view scale (body_tools/work/apose_turn/turn_measure.json norm.scale) vs the apose palm+finger truth
    gen = {}
    try: TS = {int(f['f']): f['norm'].get('scale') for f in jload(P('body_tools/work/apose_turn/turn_measure.json'))['frames']}
    except Exception: TS = {}
    for f in sorted(glob.glob(P('rig/hand_angles', '*_*.json'))):
        try: d = jload(f)
        except Exception: continue
        if not isinstance(d, dict) or 'physicalLength' not in d: continue
        side = d.get('side'); fr = int(re.findall(r'f(\d+)', d.get('source', 'f0'))[0]); sc = TS.get(fr)
        truth = [x for x in (master.get(f'palm_{side}'), master.get(f'finger_{side}')) if x]
        if not truth or not sc: continue
        L = d['physicalLength'] * sc; T = sum(truth)
        gen[os.path.basename(f)] = {'source': d.get('source'), 'length_view_px': round(L, 1), 'apose_palm+finger_px': round(T, 1), 'drift_px': round(L - T, 1), 'flag': abs(L - T) > tol}
    res['generated'] = gen; ok &= not any(g['flag'] for g in gen.values())
    res['note'] = ('Profiles/back show hands and feet foreshortened or edge-on, so drift there is partly expected from the view itself; '
                   'turn-video angles are not measured (no per-angle hand rig). Base views are the truth (info only); generated = rig/hand_angles sprites, '
                   'physicalLength x frame scale vs apose palm+finger (wrist pivot -> Middle tip).')
    res['pass'] = bool(ok); return res

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--gate', default='all', help='weights,leak,scale or all')
    ap.add_argument('--part', default='', help='system or part filter: body|eyes|mouth|hands|hair or a file/part glob, e.g. hair/bun* or mouth/anger')
    ap.add_argument('--view', default=','.join(VIEWS), help='comma list of views (default all 5)')
    ap.add_argument('--staged-dir', action='append', default=None, help='staged tone-fix dir(s); default: the three known tone_fix dirs. Repeatable')
    ap.add_argument('--skin', default=None, help='alternate skin.json for G1/G2 mesh (e.g. a candidate build); only with one --view')
    for sy in SYSTEMS: ap.add_argument(f'--{sy}-dir', default=None, help=f'override folder for {sy} parts (see sysdir())')
    ap.add_argument('--no-diagonals', action='store_true'); ap.add_argument('--no-mesh', action='store_true')
    ap.add_argument('--tol', type=float, default=2.0, help='RGB distance tolerance for off-palette (default 2)')
    ap.add_argument('--json', default=None, help='write full JSON result here')
    a = ap.parse_args()
    for sy in SYSTEMS:
        if getattr(a, f'{sy}_dir'): SYS_DIR[sy] = getattr(a, f'{sy}_dir')
    views = [v for v in a.view.split(',') if v]; gates = VIEWS and (['weights', 'leak', 'scale'] if a.gate == 'all' else a.gate.split(','))
    sdirs = a.staged_dir if a.staged_dir is not None else STAGED_TONE
    psys, ppat = (a.part.split('/', 1) + ['*'])[:2] if a.part else ('', '*')
    if psys and psys not in SYSTEMS: psys, ppat = '', a.part
    def pf(system, fname): return (not psys or system == psys) and __import__('fnmatch').fnmatch(fname, ppat if ppat.endswith(('*', '.png')) else ppat + '*')
    R = {'views': views, 'part': a.part or 'all', 'staged_dirs': sdirs, 'tol': a.tol, 'dir_overrides': SYS_DIR}; ok = True
    body_sel = (not psys or psys == 'body')
    if 'weights' in gates and body_sel:
        R['weights'] = {v: gate_weights(v, a.skin) for v in views}; ok &= all(r['pass'] for r in R['weights'].values())
    if 'leak' in gates:
        L = {'live': {}, 'staged': {}, 'diagonals': {}, 'mesh_outside_mask': {}}
        for v in views:
            for s in SYSTEMS:
                for f in live_files(v, s):
                    fn = os.path.basename(f)
                    if not pf(s, fn): continue
                    r = file_report(v, s, f, a.tol); L['live'].setdefault(v, {}).setdefault(s, []).append(r)
                    sf = staged_lookup(sdirs, v, s, fn)
                    rs = file_report(v, s, sf, a.tol) if sf else dict(r, file=r['file'] + ' (no staged fix; live)')
                    L['staged'].setdefault(v, {}).setdefault(s, []).append(rs)
            if body_sel and not a.no_mesh: L['mesh_outside_mask'][v] = mesh_outside(v, a.skin)
        if not a.no_diagonals:
            for ang, s, f in diag_sets(pf): L['diagonals'].setdefault(ang, {}).setdefault(s, []).append(file_report(ang, s, f, a.tol))
        def tot(tree):
            t = {'off_palette': 0, 'chroma': 0, 'soft_edge': 0, 'files': 0}
            for vv in tree.values():
                for lst in vv.values():
                    for r in lst: t['files'] += 1; t['off_palette'] += r['off_palette']; t['chroma'] += r['chroma']; t['soft_edge'] += r['soft_edge']
            return t
        L['totals'] = {k: tot(L[k]) for k in ('live', 'staged', 'diagonals')}
        L['totals']['mesh_outside_mask'] = sum(x[next(iter(x))] for vv in L['mesh_outside_mask'].values() for x in vv.values())
        L['pass_live'] = L['totals']['live']['off_palette'] == 0 and L['totals']['live']['chroma'] == 0 and L['totals']['mesh_outside_mask'] == 0
        L['pass_staged'] = L['totals']['staged']['off_palette'] == 0 and L['totals']['staged']['chroma'] == 0 and L['totals']['mesh_outside_mask'] == 0
        L['note'] = 'soft_edge (0<alpha<255) is reported separately and does not fail the gate; off-palette counts opaque px only.'
        R['leak'] = L; ok &= L['pass_staged']
    if 'scale' in gates and (not psys or psys in ('hands', 'body')):
        R['scale'] = gate_scale(views); ok &= R['scale']['pass']
    R['pass'] = bool(ok)
    js = json.dumps(R, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    if a.json: os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True); open(a.json, 'w').write(js)
    # compact summary
    print(f"QA gates  views={views} part={a.part or 'all'}  PASS={R['pass']}")
    if 'weights' in R:
        for v, r in R['weights'].items():
            for m, mr in r['meshes'].items():
                iso = {b: x[next(iter(x))] for b, x in mr['isolation'].items() if x[next(iter(x))]}
                print(f"  G1 {v:6s} {m:8s} bleed_verts={mr['bleed_vs_dominant_bone']['vertices']} texel-owner_bleed={mr['bleed_vs_texel_owner']['vertices_total']} isolation_fail={iso}")
    if 'leak' in R:
        for k in ('live', 'staged', 'diagonals'): print(f"  G2 {k:9s} {R['leak']['totals'][k]}")
        print(f"  G2 mesh_outside_mask total={R['leak']['totals']['mesh_outside_mask']}")
    if 'scale' in R:
        for v, r in R['scale']['views'].items(): print(f"  G3 {v:6s} (base view = truth, info) drift>1px={r['info_drift_gt_tol']} " + ' '.join(f"{k}:{x['drift_px']:+.1f}" for k, x in r['ratios'].items()))
        for f, g in R['scale'].get('generated', {}).items(): print(f"  G3 turn-angle {f} ({g['source']}): {g['length_view_px']} vs {g['apose_palm+finger_px']} drift {g['drift_px']:+.1f} flag={g['flag']}")
    return 0 if ok else 1

if __name__ == '__main__': sys.exit(main())
