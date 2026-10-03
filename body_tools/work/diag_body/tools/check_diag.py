"""Rest recomposite, palette/chroma/soft, teammate overlap and +-25 deg joint hole test for diag_body/<ang>. Usage: python3 check_diag.py 045 [315]"""
import sys; sys.path.insert(0, '.'); from common import *
from PIL import ImageDraw
H, W = 1168, 768
def over(dst, src):
    sa = src[..., 3:] / 255.; da = dst[..., 3:] / 255.; oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-9), 0); return np.concatenate([rgb, oa * 255], -1)
def run(ang):
    od = f'{OUT}/{ang}'; pj = json.load(open(f'{od}/parts.json')); F = frame(ang); fg, _ = fg_mask(F); T = team_masks(ang)
    TM = np.zeros((H, W), bool)
    for k, v in T.items():
        if not k.endswith('all_states'): TM |= v
    A = fg & ~TM
    order = pj['layerOrder_backToFront']; pc = {p['id']: p for p in pj['pieces']}
    img = {k: np.array(Image.open(f"{od}/pieces/{k}.png")).astype(float) for k in order}
    res = dict(angle=ang, frame=ANG[ang]['frame'])
    # ---- rest
    comp = np.zeros((H, W, 4))
    for k in order: comp = over(comp, img[k])
    ca = comp[..., 3]; diff_in = A & ((np.abs(comp[..., :3] - F).max(2) > 0) | (ca < 255)); extra = (ca > 0) & ~A
    res['rest'] = dict(diff_px_vs_frame_on_body_px=int(diff_in.sum()), body_px_outside_body_area=int(extra.sum()), body_px=int(A.sum()),
                       note='composite of the 14 pieces (layer order, flaps hidden) vs her frame px; body area = her keyed figure minus teammates rest px')
    cov = fg & ~(ca > 0) & ~TM; res['rest']['figure_px_covered_by_nobody'] = int(cov.sum())
    res['rest']['teammate_px_outside_her_keyed_figure'] = {k: int((v & ~fg).sum()) for k, v in T.items() if not k.endswith('all_states')}
    # diff image
    dimg = (F * 0.3 + 60).astype(np.uint8); dimg[A & ~diff_in] = (F[A & ~diff_in] * 0.5 + 100).clip(0, 255).astype(np.uint8)
    dimg[diff_in] = (255, 0, 0); dimg[extra] = (255, 0, 255); Image.fromarray(dimg).save(f'{od}/rest_recomposite_diff.png')
    # ---- palette / chroma / soft / overlap per piece
    pal = np.unique((F[fg][:, 0] << 16) | (F[fg][:, 1] << 8) | F[fg][:, 2])
    tot = dict(off_palette=0, chroma=0, soft=0, overlap_teammates_rest=0)
    allst = TM | T.get('eyes_all_states', False) | T.get('mouth_all_states', False)
    per = {}
    for k in order:
        a = img[k].astype(int); op = a[..., 3] == 255
        cc = a[..., :3][op]; code = (cc[:, 0] << 16) | (cc[:, 1] << 8) | cc[:, 2]
        off = int((~np.isin(code, pal)).sum()); ch = int(((a[..., 3] > 0) & (a[..., 2] > np.maximum(a[..., 0], a[..., 1]) + 60) & (a[..., 2] > 120)).sum())
        soft = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()); ov = int(((a[..., 3] > 0) & TM).sum()); ova = int(((a[..., 3] > 0) & allst).sum())
        per[k] = dict(opaque=int(op.sum()), off_palette=off, chroma=ch, soft=soft, overlap_teammates_rest=ov, overlap_teammates_incl_lid_and_mouth_states=ova)
        tot['off_palette'] += off; tot['chroma'] += ch; tot['soft'] += soft; tot['overlap_teammates_rest'] += ov
    # her exact frame colours that trip the F8 key test B-max(R,G)>25 (her dark purple ink): allowlist, kept as drawn
    alw = {}; alw_n = 0
    for k in order:
        a = img[k].astype(int); op = a[..., 3] == 255
        hit = op & ((a[..., 2] - np.maximum(a[..., 0], a[..., 1])) > 25) & (np.abs(a[..., :3] - F).max(2) == 0)
        per[k]['her_exact_px_tripping_key25'] = int(hit.sum()); alw_n += int(hit.sum())
        for c_ in map(tuple, a[..., :3][hit].tolist()): alw[c_] = alw.get(c_, 0) + 1
    res['hers_allowlist_key25'] = dict(px=alw_n, colours=[dict(rgb=list(k), px=v, b_minus_maxrg=k[2] - max(k[0], k[1])) for k, v in sorted(alw.items(), key=lambda kv: -kv[1])],
        note='body px whose exact RGB is her frame px but B-max(R,G)>25 (enclosed ink islands < 6 px kept as figure); NOT snapped or removed; qa_gates chroma (b>max+60 & b>120) = 0')
    res['pieces'] = per; res['totals'] = tot
    res['palette_rule'] = 'off-palette = opaque px whose exact RGB (tol 0) does not occur in her keyed figure px of this frame; chroma = qa_gates rule b>max(r,g)+60 & b>120'
    # overlap with each teammate
    union = np.zeros((H, W), bool)
    for k in order: union |= img[k][..., 3] > 0
    res['overlap_by_teammate'] = {k: int((union & v).sum()) for k, v in T.items()}
    # ---- joint test
    kids = {}
    for p in pj['pieces']: kids.setdefault(p['parent'], []).append(p['id'])
    def subtree(k): s = [k]; [s.extend(subtree(c)) for c in kids.get(k, [])]; return s
    teamimg = {}
    for k, v in T.items():
        if k.endswith('all_states') and 'wristflap' not in k: continue
        t = np.zeros((H, W, 4)); t[v] = (0, 255, 0, 255); teamimg[k] = t
    team_owner = dict(hand_R='forearm_R', hand_L='forearm_L', hand_R_wristflap_all_states='forearm_R', hand_L_wristflap_all_states='forearm_L', hair='head', eyes='head', mouth='head')
    JT = {}; tiles = []
    ONLY = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
    wc = json.load(open(f'{od}/wrist_cuts.json'))['wrists']
    jl = list(pj['joints'].items()) + [(f'wrist_{s}', dict(flap_on=None, under=f'forearm_{s}', pivot=wc[s]['f8_palm_pivot_frame'], joint_radius_px=22.0, hand=f'hand_{s}')) for s in 'RL']
    for jn, j in jl:
        if 'joint_radius_px' not in j or (ONLY and jn not in ONLY): continue
        ch = j['flap_on'] if jn != 'head_neck' else 'head'
        c = j['pivot']; r = j['joint_radius_px'] + 15; R = int(r + 30)
        x0, y0 = int(c[0]) - R, int(c[1]) - R; x1, y1 = int(c[0]) + R, int(c[1]) + R
        yy, xx = np.mgrid[y0:y1, x0:x1]; sub = subtree(ch) if ch else []
        layers = [(k, img[k]) for k in order]
        movers = set(sub) | {t for t, o in team_owner.items() if o in sub and t in teamimg}
        if j.get('hand'): movers = {j['hand'], j['hand'] + '_wristflap_all_states'}
        stack = [('team_' + t, teamimg[t]) for t in teamimg if 'wristflap' in t] + [('team_' + t, teamimg[t]) for t in teamimg if 'wristflap' not in t]
        layers = [(k, im) for k, im in layers]; stack_under = [s_ for s_ in stack if 'wristflap' in s_[0] or s_[0].startswith('team_hand')]
        _un = {s_[0] for s_ in stack_under}; stack = [s_ for s_ in stack if s_[0] not in _un]   # teammates count as cover (drawn on top here; only coverage matters)
        def sample(full, th, mode):
            t = np.radians(-th); dx, dy = xx + 0.5 - c[0], yy + 0.5 - c[1]
            fx = c[0] + np.cos(t) * dx - np.sin(t) * dy - 0.5; fy = c[1] + np.sin(t) * dx + np.cos(t) * dy - 0.5
            if mode == 'nearest':
                sx = np.round(fx).astype(int); sy = np.round(fy).astype(int); ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
                o = np.zeros((y1 - y0, x1 - x0, 4)); o[ok] = full[sy[ok], sx[ok]]; return o
            pm = full.copy(); pm[..., :3] *= pm[..., 3:] / 255.
            xf = np.floor(fx).astype(int); yf = np.floor(fy).astype(int); ax = fx - xf; ay = fy - yf
            def g(yi, xi):
                ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H); o = np.zeros((y1 - y0, x1 - x0, 4)); o[ok] = pm[yi[ok], xi[ok]]; return o
            o = g(yf, xf) * ((1 - ax) * (1 - ay))[..., None] + g(yf, xf + 1) * (ax * (1 - ay))[..., None] + g(yf + 1, xf) * ((1 - ax) * ay)[..., None] + g(yf + 1, xf + 1) * (ax * ay)[..., None]
            a = o[..., 3:]; o[..., :3] = np.where(a > 0, o[..., :3] * 255. / np.maximum(a, 1e-9), 0); return o
        band = np.hypot(xx + 0.5 - c[0], yy + 0.5 - c[1]) <= r
        JT[jn] = {}
        for mode in ('nearest', 'bilinear'):
            JT[jn][mode] = {}
            for th in (0, -25, 25):
                cp = np.zeros((y1 - y0, x1 - x0, 4)); pair = np.zeros((y1 - y0, x1 - x0), bool)
                for k, im in stack_under + layers + stack:
                    kk = k[5:] if k.startswith('team_') else k
                    s = sample(im, th if kk in movers else 0, mode); cp = over(cp, s)
                    if kk in sub or kk == j['under'] or (k.startswith('team_') and kk in movers): pair |= s[..., 3] >= 254.5
                if j.get('hand'): pass  # wrist: F8 hand (rotated, drawn under the forearm here only as cover) + forearm
                op = cp[..., 3] >= 254.5
                enc = ndi.binary_fill_holes(pair) & ~op & band
                crack = ndi.binary_fill_holes(ndi.binary_closing(pair, iterations=1)) & ~op & band
                JT[jn][mode][f'{th:+d}'] = dict(holes_enclosed=int(enc.sum()), holes_seethrough_lt128=int((enc & (cp[..., 3] < 128)).sum()), holes_alpha0=int((enc & (cp[..., 3] < 1)).sum()), crack1=int(crack.sum()))
                if th == 0: rest_enc = enc.copy()
                elif enc.any():
                    new = enc & ~ndi.binary_dilation(rest_enc, iterations=3)
                    JT[jn][mode][f'{th:+d}']['holes_not_at_rest'] = int(new.sum())
                    JT[jn][mode][f'{th:+d}']['holes_not_at_rest_xy'] = [[int(a + x0), int(b + y0), int(round(cp[b, a, 3]))] for b, a in zip(*np.nonzero(new))][:40]
                if th and mode == 'nearest':
                    a = cp[..., 3:] / 255; v = cp[..., :3] * a + np.array([150, 230, 150]) * (1 - a); v[crack] = [255, 160, 0]; v[enc] = [255, 0, 0]
                    tiles.append((f'{jn} {th:+d}: holes {int(enc.sum())} crack {int(crack.sum())}', v.clip(0, 255).astype(np.uint8)))
    res['joint_test_25'] = JT
    res['joint_test_note'] = ('child subtree (incl. F8 hands under forearms; hair/eyes/mouth with head) rotated +-25 deg about the pivot, nearest and premultiplied bilinear; '
                              'holes_enclosed = px with alpha<255 fully enclosed by the joint pieces within joint radius+15 px; crack1 = same after a 1 px closing (outline notches). '
                              'Teammate rest px count as cover (green in the sheet).')
    json.dump(res, open(f'{od}/checks.json', 'w'), indent=1)
    tw = 260; cols = 6; sh = Image.new('RGB', (cols * tw, ((len(tiles) + cols - 1) // cols) * (tw + 18)), (255, 255, 255)); d = ImageDraw.Draw(sh)
    for i, (lbl, t) in enumerate(tiles):
        im = Image.fromarray(t).resize((tw - 8, tw - 8), Image.NEAREST); X = (i % cols) * tw; Y = (i // cols) * (tw + 18); sh.paste(im, (X + 4, Y + 16)); d.text((X + 4, Y + 2), lbl, fill=(0, 0, 0))
    sh.save(f'{od}/joint_test_25.png')
    print(ang, 'rest', res['rest'], 'totals', tot, 'overlap', res['overlap_by_teammate'], 'allowlist', res['hers_allowlist_key25'])
    for jn in JT: print(' ', jn, {m: {t: (v['holes_enclosed'], v['holes_seethrough_lt128'], v.get('holes_not_at_rest', 0)) for t, v in JT[jn][m].items()} for m in JT[jn]})
if __name__ == '__main__':
    for a in sys.argv[1:] or ['045', '315']: run(a)
