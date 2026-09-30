"""Lash / crease fix for lid frames 1..7 (post-step of eyes/work/export.py; see lashfix/notes.md).

Defect: lid_1..7 painted the whole upper lid (from the top of the cover) with flat skin and redrew the lid edge as a
thin flat 'lash' curve, so her drawn crease vanished and the upper lash thinned as soon as the lid left frame 0.

Fix, per eye column c of the opening [c0, c1] (plus a 4-column fade on the inner/nose side of front-view eyes):
 * her lid line structure = base.png rows s(c) .. b(c)-1: the upper lash band, its AA, the crease line(s) above it
   (skin gaps of <= 3 rows between them) and their soft edge, plus the near-black lash core she drew in the first
   rows of the opening;
 * on frame k it is moved down, pixel for pixel, by an integer d_k(c) = round(E_k - T): the travel of export.py's own
   lid-edge curve (E_k = T + k/7 (B - T), closed frame E_7 = C4), faded to 0 over 4 columns past the inner corner;
 * rows s .. s+d-1 left behind get export.py's flat lid skin; rows above s are left to her drawing (transparent lid);
 * k < 7: the opening below the moved line is transparent (eye shows); k = 7: the old flat skin below it is kept.
Everything else of the old frame is kept byte-for-byte (outer lash wing = lash part, profile forward-lash tuft and
bridge, feather ring, lower lid, closed-frame corner cover-up). Pixels any hair part can sweep over are only rewritten
where the old frame already had a lid pixel (footprint never grows into the hair-clearance zone); the tpose wisp is
never written. Only base.png pixels and export.py's flat skin are used: nothing is painted or invented.

Usage: python3 lashfix.py [--src ROOT_WITH_OLD_FRAMES] [--out ROOT] [views...]
  default --src eyes/work/backups_lashfix/views (pristine pre-fix frames), --out views
"""
import sys, os, json, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lashgeo
from lashgeo import EYES, H, W, KC, NF
ROOT = '/workspace/shadowveil'
KEY = np.array([0, 0, 255])
LINE_LUM = 85    # her line pixels (lash band, crease core); eyeshadow (~95-115) and skin (~125-140) are not lines
GAP = 3          # skin rows allowed between lash band and crease inside one column
SEARCH = 14      # max rows above the opening top that can belong to the lid line structure
CORE_MAX = 40    # near-black, neutral lash core just inside the opening top (iris hues excluded)
TAPER = 4        # columns past the inner corner over which the travel fades to 0 (no break in her lines there)

def edge_curves(g):
    cols, top, bot, c0, c1 = g['cols'], g['top'], g['bot'], g['c0'], g['c1']
    xc = cols + 0.5; mu = xc.mean(); sd = max(1.0, xc.std())
    def pfit(vals, deg=3):
        p = np.polyfit((xc - mu) / sd, np.asarray(vals, float), deg); return lambda x: np.polyval(p, (x - mu) / sd)
    Tc = pfit(top[cols]); Bc = pfit(bot[cols] + 1)          # same fits as export.py
    span = max(1.0, c1 + 1 - c0)
    m0 = (top[c0] + bot[c0] + 1) / 2; m1 = (top[c1] + bot[c1] + 1) / 2
    def C4(x):
        ch = m0 + (np.clip(x, c0, c1 + 1) - c0) / span * (m1 - m0)
        return ch + 0.85 * (np.maximum(Bc(x), ch) - ch)
    def D(c, k):
        """smooth downward travel of export.py's lid edge in column c on frame k (mean over 8 sub-columns)."""
        X = c + (np.arange(8) + 0.5) / 8; Xq = np.clip(X, c0, c1 + 1)
        T_ = Tc(Xq)
        if k == KC: e = C4(X)
        else:
            B_ = Bc(Xq); e = np.clip(T_ + k / KC * (B_ - T_), T_, B_)
        return float(np.maximum(0, e - T_).mean())
    return D

def plain_mask(g):
    return (g['skin_d'] < 22) & ~g['band'] & ~g['aa'] & ~g['crease'] & (g['lum'] >= LINE_LUM)

def line_top(g, c, plain, stop):
    """s(c): top row of her lid line structure in column c."""
    top = g['top'][c]; lum = g['lum']
    lineish = (lum < LINE_LUM) | g['band'] | g['aa'] | g['crease']
    s_ = top; gap = 0
    for r in range(top - 1, top - 1 - SEARCH, -1):
        if stop[r, c]: break
        if lineish[r, c]: s_ = r; gap = 0
        else:
            gap += 1
            if gap > GAP: break
    for _ in range(2):          # the lines' soft edge / light rim (not plain skin) travels with them
        r = s_ - 1
        if stop[r, c] or plain[r, c] or stop[r - 1, c]: break
        s_ = r
    return s_

def smooth_cols(vals, w=5):
    v = np.asarray(vals, float); out = v.copy(); h = w // 2
    for i in range(len(v)): out[i] = np.median(v[max(0, i - h):i + h + 1])
    return out

def save(rgba, path):
    Image.fromarray(rgba, 'RGBA').save(path)
    a = rgba[..., 3:4].astype(float) / 255.0
    ch = (rgba[..., :3].astype(float) * a + KEY * (1 - a)).round().astype(np.uint8)
    Image.fromarray(ch, 'RGB').save(path.replace('.png', '_chroma.png'))

def fix_eye(v, e, src_root, out_root, log):
    g = lashgeo.geom(v, e)
    rgb = g['rgb'].astype(np.uint8); cols = g['cols']; top, bot = g['top'], g['bot']
    c0, c1, side = int(g['c0']), int(g['c1']), g['side']; lum = g['lum']; mask = g['mask']
    protect = g['hair_sw'].copy(); wisp = np.zeros((H, W), bool)
    if v == 'tpose' and e == 'EyeR':
        wisp = np.array(Image.open(f'{ROOT}/hair/tpose_eye_crossing_wisp_mask.png')) > 0
        protect |= wisp
    stop = protect | g['dark_unconn']            # never moved / copied: hair, brows, moles
    plain = plain_mask(g)
    D = edge_curves(g)
    s_raw = np.array([line_top(g, c, plain, stop) for c in cols]); s_sm = np.round(smooth_cols(s_raw)).astype(int)
    s_c = np.maximum(np.minimum(s_raw, s_sm), s_sm - 2)   # her whole line, but no spikes up crossing strands
    nn = []
    for c in cols:
        t = top[c]; n = 0
        while n < 2 and mask[t + n, c] and rgb[t + n, c].max() < CORE_MAX and np.ptp(rgb[t + n, c]) < 12: n += 1
        nn.append(n)
    nn = np.array(nn); nn2 = nn.copy()
    for i in range(len(nn)):   # no single-column spikes on the lash bottom
        nb = [nn[j] for j in (i - 1, i + 1) if 0 <= j < len(nn)]
        nn2[i] = min(nn[i], max(nb))
    S = {int(c): int(s_c[i]) for i, c in enumerate(cols)}
    Bv = {int(c): int(top[c] + nn2[i]) for i, c in enumerate(cols)}
    # the travel fades out past the opening only on the inner (nose) side of a front-view eye: the outer side ends in
    # her static lash wing (lash part, drawn on top) and the profiles' front side keeps the old forward-lash handling
    lo, hi = c0, c1
    if not g['fwd'].any():
        if side < 0: hi = c1 + TAPER
        else: lo = c0 - TAPER
    wcols = list(range(lo, hi + 1))
    def col_params(c, k):
        cc = min(max(c, c0), c1); dd = D(cc, k)
        if c < c0: dd *= max(0.0, 1 - (c0 - c) / (TAPER + 1))
        if c > c1: dd *= max(0.0, 1 - (c - c1) / (TAPER + 1))
        return int(round(dd)), S[cc], Bv[cc]
    info = dict(c0=c0, c1=c1, cols=[lo, hi], s=S, b=Bv, d={})
    skin = np.array(g['skin'], np.uint8)          # export.py's flat lid skin (median of her skin around the lid)
    for k in range(1, NF):
        old = np.array(Image.open(f'{src_root}/{v}/eyes/{e}_lid_{k}.png').convert('RGBA'))
        new = old.copy(); dk = {}
        wr = ~protect | ((old[..., 3] > 0) & ~wisp)
        for c in wcols:
            d, s_, b_ = col_params(c, k); dk[c] = d
            incol = c0 <= c <= c1
            # 1) the old frame's flat lid above her line structure -> transparent (base.png shows her drawing)
            for r in range(s_ - SEARCH - 12, s_):
                if wr[r, c] and g['cover'][r, c]: new[r, c] = 0
            if k < KC or not incol:   # rebuild this column below s (old flat skin + thin flat lash removed)
                for r in range(s_, (bot[c] + 1) if incol else (b_ + d + 3)):
                    if wr[r, c] and not g['fwd_cover'][r, c]: new[r, c] = 0
            # 2) rows s .. s+d-1 left behind by the line: flat lid skin (as the old lid frames)
            for y in range(s_, s_ + d):
                if wr[y, c]: new[y, c, :3] = skin; new[y, c, 3] = 255
            # 3) her line structure rows [s, b) moved down by d, pixel for pixel (hair / brow pixels not copied)
            if d == 0 and not incol: continue            # unchanged outside the opening: base shows
            for y in range(s_ + d, b_ + d):
                if not wr[y, c]: continue
                sy = y - d
                new[y, c, :3] = rgb[sy, c] if not stop[sy, c] else skin; new[y, c, 3] = 255
            # 4) below the lid edge inside the opening: the eye shows (k<7); the closed frame keeps its flat skin
            if k < KC and incol:
                for r in range(b_ + d, bot[c] + 1):
                    if wr[r, c]: new[r, c] = 0
        new[new[..., 3] == 0, :3] = 0
        if k == KC:   # the closed frame must still hide the whole opening
            m = mask & ~protect; assert (new[..., 3][m] == 255).all(), (v, e, int((new[..., 3][m] < 255).sum()))
        info['d'][k] = dk
        os.makedirs(f'{out_root}/{v}/eyes', exist_ok=True)
        save(new, f'{out_root}/{v}/eyes/{e}_lid_{k}.png')
    log[f'{v}/{e}'] = info

if __name__ == '__main__':
    args = sys.argv[1:]
    src = f'{ROOT}/eyes/work/backups_lashfix/views'; out = f'{ROOT}/views'
    if '--src' in args: i = args.index('--src'); src = args[i + 1]; del args[i:i + 2]
    if '--out' in args: i = args.index('--out'); out = args[i + 1]; del args[i:i + 2]
    views = args or list(EYES)
    lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lashfix_log.json')
    log = json.load(open(lp)) if os.path.exists(lp) else {}
    for v in views:
        for e in EYES[v]:
            fix_eye(v, e, src, out, log); json.dump(log, open(lp, 'w'), indent=1); print('fixed', v, e, flush=True)
