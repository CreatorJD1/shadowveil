"""Measure lash and crease stroke width per lid frame vs rest (base.png), per column, for a views tree.
Usage: python3 measure.py <view> <tree_root> <tag>   -> tmp/measure_<tag>_<view>.json (+ summary on stdout)
lash width (col c): longest run of lid/lash-layer pixels (alpha>=128) with lum<85 in rows [Lt-2, bot+1] of the render;
  rest = lum<85 pixels of her band rows [Lt, Lb) in base.png (Lt/Lb from lashfix2.lash_geom).
crease width (col c in c0-8..c1+8): lum<85 pixels above her lash band (rows Lt-14 .. Lt-1) in the render vs base.
breaks: opening columns with no lash run, or lash runs of neighbouring columns that do not touch (8-connected).
kinks: jog of the lash top/bottom edge between neighbouring columns compared with the rest jog (|change| >= 2)."""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0, '/workspace/shadowveil/eyes/tools')
import render_eyes, lfcommon as L, lashfix2 as F
v, root, tag = sys.argv[1:4]
render_eyes.VIEWS = root; render_eyes._cache.clear()
base = np.array(Image.open(f'{L.ROOT}/views/{v}/base.png').convert('RGB')).astype(int); blum = base.mean(2)
res = {}
for e in L.EYES[v]:
    g = L.geo(v, e); c0, c1, top, bot = g['c0'], g['c1'], g['top'], g['bot']
    lg = json.load(open(f'{L.HERE}/lashfix2_log.json'))[f'{v}/{e}']     # final per-column geometry used by lashfix2
    Lt = {int(c): x for c, x in lg['Lt'].items() if x is not None}; Lb_raw = {int(c): x for c, x in lg['Lb_raw'].items() if x is not None}
    prof = v in ('left', 'right'); side = g['side']
    ccols = [c for c in range(c0 - 8, c1 + 9) if not (prof and ((c < c0) if side > 0 else (c > c1)))]
    lt = lambda c: Lt[min(max(c, c0), c1)]
    rest_l = {c: int((blum[Lt[c]:Lb_raw[c], c] < 85).sum()) for c in range(c0, c1 + 1)}
    rest_iv = {}
    for c in range(c0, c1 + 1):
        rr = np.nonzero(blum[Lt[c]:Lb_raw[c], c] < 85)[0] + Lt[c]
        rest_iv[c] = (int(rr.min()), int(rr.max())) if len(rr) else None
    rest_c = {c: int((blum[lt(c) - 14:lt(c), c] < 85).sum()) for c in ccols}
    lash = g['lash']
    out = {}
    for k in range(8):
        o = 1 - k / 7
        I = render_eyes.render(v, dict(EyeLOpen=o, EyeROpen=o), base=f'{L.ROOT}/views/{v}/base.png')[..., :3].astype(int); lum = I.mean(2)
        if k == 0:
            A = np.ones(lum.shape, bool)
        else:
            A = np.array(Image.open(f'{root}/{v}/eyes/{e}_lid_{k}.png'))[..., 3] >= 128
            A |= np.array(Image.open(f'{root}/{v}/eyes/{e}_lash.png'))[..., 3] >= 128
        wl = {}; iv = {}
        for c in range(c0, c1 + 1):
            if k == 0: wl[c] = rest_l[c]; iv[c] = rest_iv[c]; continue
            m = (lum[:, c] < 85) & A[:, c]; best = (0, None)
            r = Lt[c] - 2; rend = max(bot[c] + 1, Lb_raw[c] + 16)    # lid-layer pixels only, so iris/lower lid never count
            while r <= rend:
                if m[r]:
                    s_ = r
                    while r <= rend and m[r]: r += 1
                    if r - s_ > best[0]: best = (r - s_, (s_, r - 1))
                else: r += 1
            wl[c] = best[0]; iv[c] = best[1]
        wc = {c: int((lum[lt(c) - 14:lt(c), c] < 85).sum()) for c in ccols}
        cchg = int(sum(((I[lt(c) - 14:lt(c), c] != base[lt(c) - 14:lt(c), c]).any(-1)).sum() for c in ccols))
        dl = {c: wl[c] - rest_l[c] for c in wl}; dc = {c: wc[c] - rest_c[c] for c in wc}
        brk = [c for c in range(c0 + 1, c1) if iv[c] is None]
        for c in range(c0, c1):
            a, b = iv[c], iv[c + 1]
            if a and b and (b[0] > a[1] + 1 or a[0] > b[1] + 1): brk.append(f'{c}|{c + 1}')
        kink = []
        if k:
            for c in range(c0, c1):
                if iv[c] and iv[c + 1] and rest_iv[c] and rest_iv[c + 1]:
                    for j in (0, 1):
                        jog = iv[c + 1][j] - iv[c][j]; rj = rest_iv[c + 1][j] - rest_iv[c][j]
                        if abs(jog - rj) >= 2: kink.append((c, j, jog - rj))
        # the 2 corner columns of each end carry <= 1-2 px of lash; report interior and corner separately
        inner = [c for c in range(c0 + 2, c1 - 1)]
        tick = None
        if not prof and k:   # outer-corner tick: rows her static wing tail hangs below the band's corner-column bottom
            ce, co = (c1, c1 + 1) if side > 0 else (c0, c0 - 1)
            la = np.array(Image.open(f'{root}/{v}/eyes/{e}_lash.png'))[..., 3] > 0; rr = np.nonzero(la[:, co])[0]
            if len(rr) and iv[ce]: tick = int(max(0, rr.max() - iv[ce][1]))
        out[k] = dict(tick=tick, lash_maxdev=int(max(abs(dl[c]) for c in inner)), lash_maxdev_all=int(max(abs(x) for x in dl.values())),
                      lash_mean=round(float(np.mean([wl[c] for c in inner])), 2), lash_rest_mean=round(float(np.mean([rest_l[c] for c in inner])), 2),
                      crease_maxdev=int(max(abs(x) for x in dc.values())), crease_px_changed=cchg,
                      breaks=brk, kinks=kink, wl=wl, dl=dl)
    res[e] = out
    print(v, e, tag, ' '.join(f"k{k}:t{out[k]['tick']} L{out[k]['lash_maxdev']}/{out[k]['lash_maxdev_all']} m{out[k]['lash_mean']} C{out[k]['crease_maxdev']} b{len(out[k]['breaks'])} x{len(out[k]['kinks'])}" for k in range(1, 8)), 'rest lash mean', out[1]['lash_rest_mean'])
json.dump(res, open(f'{L.HERE}/tmp/measure_{tag}_{v}.json', 'w'), indent=1, default=str)
