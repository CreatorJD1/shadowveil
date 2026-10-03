"""Lash/crease fix v2 for lid frames 1..7 -> STAGED output (never writes views/ live files).

Defect (live frames 1..7 from export.py): the lid is flat skin from the top of the cover (crease included) down to a
thin flat lash curve (1.4-3 px), so her crease vanishes and the 4-7 px lash band thins as soon as the lid moves.

Fix, per opening column c in [c0, c1]:
 * her crease (everything above her lash band) is never covered: base.png shows, pixel for pixel, on every frame;
 * her lash band = the dark run (lum < 85) directly above the opening top plus her near-black core rows inside the
   opening (<= 2) is moved down rigidly (integer shift per column, her own pixels, width preserved exactly) by
   d_k(c) = round(w(c) * D_k(c)); D_k = travel of export.py's lid-edge curve (T + k/7 (B - T); closed: C4), w = a
   smoothstep ramp to 0 over the last R columns at each corner (front-side corner of profiles excluded: the old
   forward-lash tuft/bridge, seated on the full travel, is kept);
 * rows vacated above the moved band get export.py's flat lid skin; below it the eye shows (k<7) or flat skin (k=7);
 * k=7 also keeps the old closed frame outside the opening columns but uncovers her crease above the lash level.
Hair-swept pixels are only written where the old frame had a lid pixel; the tpose wisp is never written.
Usage: python3 lashfix2.py [views...]   (src: eyes/work/backups_lashfix/views, out: eyes/work/lashfix/staged/<view>/)
"""
import sys, os, json, numpy as np
from PIL import Image
import lfcommon as L
from lfcommon import H, W, KC, NF, ROOT
SRC = f'{ROOT}/eyes/work/backups_lashfix/views'
ALT = os.environ.get('LF_ALT') == '1'
OUT = f'{L.HERE}/staged_alt_crease_hidden' if ALT else f'{L.HERE}/staged'
KEY = np.array([0, 0, 255]); LINE = 85; BAND = 50; CORE_MAX = 40; R0 = int(os.environ.get('LF_R0', 1)); MAXRUN = 10

def edge_D(g):
    cols, top, bot, c0, c1 = g['cols'], g['top'], g['bot'], g['c0'], g['c1']
    xc = cols + 0.5; mu = xc.mean(); sd = max(1.0, xc.std())
    def pfit(vals, deg=3):
        p = np.polyfit((xc - mu) / sd, np.asarray(vals, float), deg); return lambda x: np.polyval(p, (x - mu) / sd)
    Tc = pfit(top[cols]); Bc = pfit(bot[cols] + 1); span = max(1.0, c1 + 1 - c0)
    m0 = (top[c0] + bot[c0] + 1) / 2; m1 = (top[c1] + bot[c1] + 1) / 2
    def C4(x):
        ch = m0 + (np.clip(x, c0, c1 + 1) - c0) / span * (m1 - m0); return ch + 0.85 * (np.maximum(Bc(x), ch) - ch)
    def D(c, k):
        X = c + (np.arange(8) + 0.5) / 8; T_ = Tc(X)
        e = C4(X) if k == KC else np.clip(T_ + k / KC * (Bc(X) - T_), T_, Bc(X))
        return float(np.maximum(0, e - T_).mean())
    return D

def lash_geom(g):
    """per opening column: Lt (top row of her lash band), Lb (exclusive bottom incl. core rows)."""
    lum, rgb, top, mask = g['lum'], g['rgb'], g['top'], g['mask']; stop = g['hair_sw'] | g['dark_unconn']
    c0, c1 = g['c0'], g['c1']; Lt = {}; Lb = {}; run = {}; GAPL = float(np.mean(g['skin'])) - 10
    for c in range(c0, c1 + 1):
        t = top[c]; r = t - 1
        if BAND <= lum[r, c] < LINE and lum[r - 1, c] < BAND: r -= 1     # her band's soft bottom row
        while lum[r, c] < BAND and not g['hair_sw'][r, c] and t - r <= MAXRUN: r -= 1
        # her band's own soft top row (mid-dark) rides along, unless it is the start of a crease run above it
        if LINE > lum[r, c] >= BAND and lum[r - 1, c] >= LINE and not g['hair_sw'][r, c]: r -= 1
        # and the darker-than-skin shading rows between her crease and the band (<= 3) ride along too, so no
        # ghost strip of them stays behind under the crease
        n = 0
        while n < 3 and LINE <= lum[r, c] < GAPL and not g['hair_sw'][r, c]: r -= 1; n += 1
        run[c] = t - 1 - r
        n = 0
        while n < 2 and mask[t + n, c] and rgb[t + n, c].max() < CORE_MAX and np.ptp(rgb[t + n, c]) < 12: n += 1
        Lb[c] = t + n
    # lash bottom: her core rows inside the opening vary 0-2 px column to column (ragged teeth when moved);
    # even it out to the 3-column median (+-1 px max) by repeating that column's own lowest lash pixel
    cs0 = sorted(Lb); lb0 = np.array([Lb[c] for c in cs0])
    for i, c in enumerate(cs0):
        m3 = int(np.median(lb0[max(0, i - 1):i + 2])); Lb[c] = int(np.clip(m3, lb0[i] - 1, lb0[i] + 1))
        Lb[c] = max(Lb[c], top[c] - 0)
    med = int(np.median(list(run.values())))
    cs = sorted(run)
    for c in cs:    # crease merged into the band (outer corner): only her lash thickness moves
        Lt[c] = top[c] - min(run[c], med + 2)
    for i, c in enumerate(cs):   # a stray stroke of hers crossing the band cut the run short: use the neighbours' top
        if run[c] < med - 2 and c0 < c < c1:
            nb = [Lt[cs[j]] for j in range(max(0, i - 2), min(len(cs), i + 3)) if j != i and run[cs[j]] >= med - 2]
            if nb: Lt[c] = int(round(np.median(nb)))
    Lb_raw = {c: int(v) for c, v in zip(cs0, lb0)}
    return Lt, Lb, run, med, Lb_raw

def save(rgba, path):
    rgba = rgba.copy(); rgba[rgba[..., 3] == 0, :3] = 0
    Image.fromarray(rgba, 'RGBA').save(path)
    a = rgba[..., 3:4].astype(float) / 255.0
    ch = (rgba[..., :3].astype(float) * a + KEY * (1 - a)).round().astype(np.uint8)
    Image.fromarray(ch, 'RGB').save(path.replace('.png', '_chroma.png'))

def fix_eye(v, e, log):
    g = L.geo(v, e); rgb = g['rgb'].astype(np.uint8); top, bot = g['top'], g['bot']
    c0, c1, side = g['c0'], g['c1'], g['side']; prof = v in ('left', 'right')
    protect = g['hair_sw'].copy(); wisp = np.zeros((H, W), bool)
    if v == 'tpose' and e == 'EyeR':
        wisp = np.array(Image.open(f'{ROOT}/hair/tpose_eye_crossing_wisp_mask.png')) > 0; protect |= wisp
    stop = protect | g['dark_unconn']; skin = g['skin'].astype(np.uint8)
    Lt, Lb, run, med, Lb_raw = lash_geom(g); D = edge_D(g)
    def ramp(c):
        a, b = c - c0, c1 - c
        if prof: u = b if side > 0 else a          # front corner (fwd tuft side) not ramped
        else: u = b if (side < 0) else a           # front views: inner (nose) corner ramps; outer handled by tailcap
        return 0.0 if u < R0 else 1.0     # corner column(s) stay put; the slope limit below makes the 45deg-max ramp
    xx = np.arange(W)[None, :].repeat(H, 0)
    front = ((xx < c0) if side > 0 else (xx > c1)) if prof else np.zeros((H, W), bool)
    lum = g['lum']; tuft = g['fwd_cover'] & ~protect if prof else np.zeros((H, W), bool)
    fopen, fout = [], []
    if prof:
        # profile front: her forward-lash tuft moves rigidly; the first opening columns (front eye contour, long
        # vertical runs) and the 2 columns in front of the opening move only their top band rows, all by the travel
        # d_f of the first regular column (no ramp, so band, contour top and tuft stay joined)
        ocols = list(range(c0, c1 + 1)) if side > 0 else list(range(c1, c0 - 1, -1))
        P = next(i for i, c in enumerate(ocols) if run[c] <= med + 2 and bot[c] - Lb[c] >= 2)
        cP = ocols[P]; fopen = ocols[:P]; fout = [c0 - 2, c0 - 1] if side > 0 else [c1 + 1, c1 + 2]
        bm = (g['band'] | g['aa']) & ~g['mask'] & ~g['fwd_cover'] & (lum < LINE)
        for c in fopen + fout:
            rr = np.nonzero(bm[:, c])[0]; rr = rr[rr >= Lt[cP] - 2]     # below her crease (also 'band'-dark here)
            if not len(rr): Lt[c] = Lb[c] = Lb_raw[c] = None; continue
            r = rr.min(); n = 0
            while lum[r + n, c] < LINE and not g['fwd_cover'][r + n, c] and not g['mask'][r + n, c]: n += 1
            Lt[c] = int(r); Lb[c] = Lb_raw[c] = int(r + min(n, med + 2))
    # outer corner of front views: the static lash part (her wing) hangs down to tailbot in the column just outside;
    # the band's outer-corner column may travel until its bottom meets that tail (no hanging tick on the closed frame)
    capd = np.full(c1 - c0 + 1, 99); ext_lim = {}
    if not prof:
        ce, co = (c1, c1 + 1) if side > 0 else (c0, c0 - 1)
        la = np.array(Image.open(f'{ROOT}/views/{v}/eyes/{e}_lash.png'))[..., 3] > 0
        rr = np.nonzero(la[:, co])[0]
        tailcap = max(0, int(rr.max()) - (Lb[ce] - 1)) if len(rr) else 0
        capd[ce - c0] = tailcap
        for j in range(3):            # corner columns may pass the (1-2 row) opening bottom to reach the tail
            cj = ce - j if side > 0 else ce + j
            if c0 <= cj <= c1: ext_lim[cj] = max(0, tailcap - j)
    info = dict(c0=c0, c1=c1, med_run=med, Lt=Lt, Lb=Lb, Lb_raw=Lb_raw, run=run, front_open=fopen, front_out=fout,
                tailcap=int(capd.min()), d={})
    for k in range(1, NF):
        old = np.array(Image.open(f'{SRC}/{v}/eyes/{e}_lid_{k}.png').convert('RGBA'))
        wr = (~protect | (old[..., 3] > 0)) & ~wisp
        if ALT and k < KC: continue
        if k < KC:
            new = np.zeros_like(old)
        else:
            new = old.copy(); new[front] = 0     # profile front: rebuilt below (old closed tuft/bridge dropped)
            # uncover her crease near the corners (rows above the lash level) and the long crease strokes
            for c in ([] if ALT else list(range(c0 - 10, c0)) + list(range(c1 + 1, c1 + 11))):
                if prof and front[0, c]: continue
                lvl = Lt[c0] if c < c0 else Lt[c1]
                sel = np.zeros(H, bool); sel[:lvl - 1] = True
                sel &= ~g['fwd_cover'][:, c]; new[sel, c] = 0
            cr = g['crease'] & ~g['fwd_cover'] & ~front
            if not ALT: new[cr] = 0
        dd = np.array([w_ * D(c, k) for c, w_ in ((c, ramp(c)) for c in range(c0, c1 + 1))])
        lim = np.array([max(bot[c] - Lb[c], ext_lim.get(c, 0)) for c in range(c0, c1 + 1)])   # band never reaches the lower lid line
        d = np.clip(np.round(np.minimum(np.minimum(dd, lim), capd)), 0, None).astype(int)
        cc = list(range(c0, c1 + 1))
        def slope():
            for _ in range(len(d)):          # slope limit: |d(c+1) - d(c)| <= 1 (no steeper than 45 degrees)
                for i in range(len(d)):
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(d): d[i] = min(d[i], d[j] + 1)
        slope()
        if k == KC and not prof:   # closed (lower lid hidden): the band's outer end meets her wing tail exactly
            ie = (c1 if side > 0 else c0) - c0; tc = int(capd[ie])
            for j in range(len(d)):
                dist = abs(j - ie); want = tc - dist
                if want > d[j]: d[j] = min(want, max(lim[j], 0))
        for _ in range(40):   # no 2 px jogs: the moved band's bottom edge keeps her own jog +-1 between columns
            bad = False
            for i in range(len(d) - 1):
                a_, b_ = cc[i], cc[i + 1]
                e_ = (Lb[b_] + d[i + 1]) - (Lb[a_] + d[i]) - (Lb_raw[b_] - Lb_raw[a_])
                if e_ >= 2 and d[i + 1] > 0: d[i + 1] -= 1; bad = True
                elif e_ <= -2 and d[i] > 0: d[i] -= 1; bad = True
            slope()
            if not bad: break
        dk = {}
        dmap = {c: int(d[i]) for i, c in enumerate(range(c0, c1 + 1))}
        if prof:   # profile: the lid line slopes from the front down... never higher at the front than further back
            cur = 0
            for c in reversed(ocols[P:]):
                cur = max(cur, dmap[c]); dmap[c] = cur     # (rows past the opening bottom are simply not drawn)
            df = dmap[cP]
            for c in fopen + fout: dmap[c] = df
        for c in sorted(dmap):
            dc = dmap[c]; dk[c] = dc; lt, lb = Lt[c], Lb[c]
            if lt is None: continue
            colkeep = tuft[:, c]; incol = c0 <= c <= c1
            end = (bot[c] + 1) if incol else (lb + dc)
            if c in ext_lim: end = max(end, lb + dc)
            if prof and (c in fopen or abs(c - (c0 if side > 0 else c1)) <= len(fopen) + 3):
                end = max(end, lb + dc)       # profile front: her band may pass the tiny front of the opening (meets the tuft)
            for r in range(0, end):   # rebuild the column from scratch
                if colkeep[r] or not wr[r, c]: continue
                if r < lt:
                    if not (ALT and k == KC): new[r, c] = 0     # ALT closed frame: old flat lid skin + crease cover kept
                elif r < lt + dc: new[r, c, :3] = skin; new[r, c, 3] = 255
                elif r < lb + dc:
                    sy = min(r - dc, Lb_raw[c] - 1)          # rows past her own lash bottom repeat its lowest pixel
                    new[r, c, :3] = rgb[sy, c] if not protect[sy, c] else skin; new[r, c, 3] = 255
                elif k == KC and incol and r <= bot[c]: new[r, c, :3] = skin; new[r, c, 3] = 255
                else: new[r, c] = 0
        if prof:   # forward-lash tuft: her pixels moved rigidly by d_f; where it was: flat lid skin
            ty, tx = np.nonzero(tuft); ok = wr[ty, tx]
            new[ty[ok], tx[ok], :3] = skin; new[ty[ok], tx[ok], 3] = 255
            ny = ty + df; ok = wr[ny, tx] & ~(g['mask'][ny, tx] & (new[ny, tx, 3] < 255) & (k == KC))
            new[ny[ok], tx[ok], :3] = rgb[ty[ok], tx[ok]]; new[ny[ok], tx[ok], 3] = 255
        if k == KC:
            m = g['mask'] & ~protect; bad = int((new[..., 3][m] < 255).sum()); assert bad == 0, (v, e, bad)
        info['d'][k] = dk
        os.makedirs(f'{OUT}/{v}', exist_ok=True); save(new, f'{OUT}/{v}/{e}_lid_{k}.png')
    log[f'{v}/{e}'] = info

if __name__ == '__main__':
    views = sys.argv[1:] or list(L.EYES)
    lp = f'{L.HERE}/lashfix2_alt_log.json' if ALT else f'{L.HERE}/lashfix2_log.json'; log = json.load(open(lp)) if os.path.exists(lp) else {}
    for v in views:
        for e in L.EYES[v]:
            fix_eye(v, e, log); print('staged', v, e, flush=True)
    json.dump(log, open(lp, 'w'), indent=1, default=int)
