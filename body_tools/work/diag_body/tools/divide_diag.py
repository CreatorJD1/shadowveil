"""Divide her diagonal turn frame (her px only) into the 14 Base Body pieces (STAGED). Usage: python3 divide_diag.py 045 [315 ...]
Pieces are full-canvas 768x1168 RGBA in FRAME px, binary alpha, RGB = her exact frame px; hidden joint flaps = her frame's flat skin tone (+ her line tone on
flap px that touch the background). Teammates' rest px (F8 hands, Eyes lid_0/white/iris/lash, Hair diagonals_v3, Mouth rest lips) are never written."""
import sys; sys.path.insert(0, '.'); from common import *
from PIL import ImageDraw
from wrist_cuts import wrist_info
CFG = json.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/diag_config.json'))
H, W = 1168, 768
YY, XX = np.mgrid[0:H, 0:W]; PX = XX + 0.5; PY = YY + 0.5
LAYER = dict(foot_L=201, foot_R=201, shin_L=203, shin_R=203, thigh_L=205, thigh_R=205, forearm_L=220, forearm_R=220, upper_arm_L=222, upper_arm_R=222,
             neck=239, torso=240, head=242, pelvis=250)
PARENT = dict(foot_L='shin_L', foot_R='shin_R', shin_L='thigh_L', shin_R='thigh_R', thigh_L='pelvis', thigh_R='pelvis', forearm_L='upper_arm_L',
              forearm_R='upper_arm_R', upper_arm_L='torso', upper_arm_R='torso', neck='torso', torso='pelvis', head='neck', pelvis=None)
def poly_mask(pts):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1); return np.array(im) > 0
def curve_y(pts):  # y(x) of a polyline, flat beyond its ends
    p = np.array(pts, float); return np.interp(PX[0], p[:, 0], p[:, 1])
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def centre_on(mask, p, axis):
    """re-centre p on the limb: midpoint of mask px within 1 px of the line through p perpendicular to axis"""
    n = unit(axis); t = np.array([-n[1], n[0]])
    for _ in range(2):
        d = (PX - p[0]) * n[0] + (PY - p[1]) * n[1]; s = (PX - p[0]) * t[0] + (PY - p[1]) * t[1]
        sel = mask & (np.abs(d) <= 0.75) & (np.abs(s) < 45)
        if sel.sum() < 3: break
        sv = s[sel]; p = np.array(p) + t * (sv.min() + sv.max()) / 2
    return [round(float(p[0]), 1), round(float(p[1]), 1)]
def side(p, n): return (PX - p[0]) * n[0] + (PY - p[1]) * n[1]

def run(ang):
    c = CFG[ang]; F = frame(ang); fg, _ = fg_mask(F); T = team_masks(ang)
    TM = np.zeros((H, W), bool)
    for k, v in T.items():
        if not k.endswith('all_states'): TM |= v
    A = fg & ~TM
    lum = F.sum(2)
    # skin & line tone: her most common flat skin; her most common dark skin-ink tone (brownish, R>G>B, sum 90..240)
    def mode(m):
        cc = F[m]; code = (cc[:, 0] << 16) | (cc[:, 1] << 8) | cc[:, 2]; u, n = np.unique(code, return_counts=True); k = u[np.argmax(n)]
        return [int(k >> 16), int((k >> 8) & 255), int(k & 255)], int(n.max())
    skin, skin_n = mode(fg)
    ink = fg & (lum >= 90) & (lum <= 240) & (F[..., 0] > F[..., 1]) & (F[..., 1] > F[..., 2])
    line, line_n = mode(ink)
    # ---- regions
    head = A & (PY < curve_y(c['jaw']))
    above_base = PY < curve_y(c['neck_base'])
    armR = A & poly_mask(c['arm_R']) & ~head; armL = A & poly_mask(c['arm_L']) & ~head & ~armR
    arms = armR | armL
    neck = A & ~head & ~arms & above_base
    # bikini lower edge per column
    zone = (YY >= c['waist_y']) & (YY < 600) & ~poly_mask(c['arm_R']) & ~poly_mask(c['arm_L'])
    dark = fg & zone & (lum < 200)
    lab, n = ndi.label(dark, structure=np.ones((3, 3))); sz = ndi.sum(dark, lab, range(1, n + 1)); bik = lab == (np.argmax(sz) + 1)
    yb = np.full(W, -1); cols = np.nonzero(bik.any(0))[0]
    for x in cols: yb[x] = np.nonzero(bik[:, x])[0].max()
    side_y = int(np.median([yb[cols.min()], yb[cols.max()]]))
    ybf = np.where(yb >= 0, yb, side_y)
    legs = A & ~arms & ~head & (YY > ybf[None, :]) & (YY >= c['waist_y'] + 10)
    # left/right leg split
    sp = np.array(c['leg_split'], float); xs = np.interp(PY[:, 0], sp[:, 1], sp[:, 0])
    x = sp[-1, 0]
    for y in range(int(sp[-1, 1]) + 1, H):
        r = ~fg[y]; best = None
        dd = np.diff(np.concatenate([[0], r.astype(int), [0]])); s0 = np.nonzero(dd == 1)[0]; e0 = np.nonzero(dd == -1)[0]
        for a, b in zip(s0, e0):
            if a > 0 and b < W and abs((a + b) / 2 - x) < 25 and (best is None or abs((a + b) / 2 - x) < abs(best - x)): best = (a + b) / 2
        if best is not None: x = best
        xs[y] = x
    legR = legs & (PX < xs[:, None]); legL = legs & ~legR
    pelvis = A & ~arms & ~legs & ~head & ~neck & (YY >= c['waist_y'])
    torso = A & ~arms & ~legs & ~head & ~neck & ~pelvis
    # ---- limb splits
    wi = wrist_info(ang, F, fg, T)
    P = {}; parts = {}
    for s_, arm in (('R', armR), ('L', armL)):
        sh = np.array(c['shoulder_' + s_], float); el0 = np.array(c['elbow_' + s_], float)
        wr = np.mean(np.array(wi[s_]['boundary_line_fit']), 0)
        el = np.array(centre_on(arm, el0, el0 - sh)); el = np.array(centre_on(arm, el, unit(el - sh) + unit(wr - el)))
        nrm = unit(unit(el - sh) + unit(wr - el))
        fore = arm & (side(el, nrm) > 0)
        parts['upper_arm_' + s_] = arm & ~fore; parts['forearm_' + s_] = fore
        P['upper_arm_' + s_] = [float(sh[0]), float(sh[1])]; P['forearm_' + s_] = [float(el[0]), float(el[1])]
        P['_wrist_' + s_] = [round(float(wr[0]), 2), round(float(wr[1]), 2)]
    for s_, leg in (('R', legR), ('L', legL)):
        hp = np.array(c['hip_' + s_], float); kn0 = np.array(c['knee_' + s_], float); an = np.array(c['ankle_' + s_], float)
        am = an.mean(0); kn = np.array(centre_on(leg, kn0, kn0 - hp)); kn = np.array(centre_on(leg, kn, unit(kn - hp) + unit(am - kn)))
        nrm = unit(unit(kn - hp) + unit(am - kn))
        tdir = an[1] - an[0]; fn = unit([-tdir[1], tdir[0]])
        if fn[1] < 0: fn = -fn
        foot = leg & (side(an[0], fn) > 0); shin = leg & ~foot & (side(kn, nrm) > 0)
        parts['thigh_' + s_] = leg & ~foot & ~shin; parts['shin_' + s_] = shin; parts['foot_' + s_] = foot
        P['thigh_' + s_] = [float(hp[0]), float(hp[1])]; P['shin_' + s_] = [float(kn[0]), float(kn[1])]
        P['foot_' + s_] = [round(float(am[0] + fn[0] * 3), 1), round(float(am[1] + fn[1] * 3), 1)]
    parts.update(head=head, neck=neck, torso=torso, pelvis=pelvis)
    P['head'] = c['head_pivot']; P['neck'] = c['neck_pivot']; P['torso'] = c['waist_pivot']; P['pelvis'] = c['waist_pivot']
    # ---- stray components -> neighbour with the longest shared border
    names = list(parts)
    for _ in range(3):
        moved = 0
        for k in names:
            m = parts[k]; lab, n = ndi.label(m, structure=np.ones((3, 3)))
            if n <= 1: continue
            sz = ndi.sum(m, lab, range(1, n + 1)); big = np.argmax(sz) + 1
            for i in range(1, n + 1):
                if i == big: continue
                comp = lab == i; ring = ndi.binary_dilation(comp, np.ones((3, 3))) & ~comp
                best = max(((parts[o] & ring).sum(), o) for o in names if o != k)
                if best[0] > 0: parts[k] = parts[k] & ~comp; parts[best[1]] = parts[best[1]] | comp; moved += 1
        if not moved: break
    stray = {k: int(ndi.label(parts[k], structure=np.ones((3, 3)))[1]) for k in names}
    # ---- sanity: partition of A
    tot = sum(parts[k].astype(int) for k in names)
    assert (tot <= 1).all() and ((tot == 1) == A).all(), 'pieces must partition her body px'
    # ---- flaps (hidden under the covering piece at rest)
    JOINTS = [('shoulder_R', 'upper_arm_R', 'torso'), ('shoulder_L', 'upper_arm_L', 'torso'), ('elbow_R', 'forearm_R', 'upper_arm_R'), ('elbow_L', 'forearm_L', 'upper_arm_L'),
              ('hip_R', 'thigh_R', 'pelvis'), ('hip_L', 'thigh_L', 'pelvis'), ('knee_R', 'shin_R', 'thigh_R'), ('knee_L', 'shin_L', 'thigh_L'),
              ('ankle_R', 'foot_R', 'shin_R'), ('ankle_L', 'foot_L', 'shin_L'), ('waist', 'torso', 'pelvis'), ('neck_base', 'neck', 'torso'), ('head_neck', 'neck', 'head')]
    flap = {k: np.zeros((H, W), bool) for k in names}; jinfo = {}
    st4 = ndi.generate_binary_structure(2, 1)
    for jn, ch, par in JOINTS:
        piv = P['head'] if jn == 'head_neck' else P[ch]
        seam = parts[ch] & ndi.binary_dilation(parts[par], st4)
        if not seam.any(): jinfo[jn] = dict(flap_on=ch, under=par, pivot=piv, note='no shared seam'); continue
        r = float(np.hypot(PX[seam] - piv[0], PY[seam] - piv[1]).max()) + 3
        if jn == 'waist': r = min(r, 40.0)
        disk = np.hypot(PX - piv[0], PY - piv[1]) <= r
        fm = disk & parts[par] & ~flap[ch]
        flap[ch] |= fm
        jinfo[jn] = dict(flap_on=ch, under=par, pivot=[round(float(piv[0]), 2), round(float(piv[1]), 2)], joint_radius_px=round(r, 1), flap_px=int(fm.sum()), seam_px=int(seam.sum()))
    # ---- write pieces
    od = f'{OUT}/{ang}'; os.makedirs(f'{od}/pieces', exist_ok=True)
    bgmask = ~fg | TM
    pieces = []; layers = sorted(names, key=lambda k: (LAYER[k], k))
    for k in names:
        img = np.zeros((H, W, 4), np.uint8); m = parts[k]; fl = flap[k] & ~m
        img[m, :3] = F[m]; img[m, 3] = 255
        img[fl, :3] = skin; img[fl, 3] = 255
        edge = fl & ndi.binary_dilation(~fg, st4)   # flap px on her silhouette -> her line tone
        img[edge, :3] = line
        Image.fromarray(img, 'RGBA').save(f'{od}/pieces/{k}.png')
        pieces.append(dict(id=k, file=f'pieces/{k}.png', layer=LAYER[k], parent=PARENT[k], pivot=[round(float(v), 2) for v in P[k]],
                           pixels=int(m.sum()), flapPx=int(fl.sum()), flapLinePx=int(edge.sum())))
    # whole body (her keyed px that Body owns) and full keyed figure
    save_rgba(F, A, f'{od}/body_whole_rest.png'); save_rgba(F, fg, f'{od}/figure_keyed_full.png')
    out = dict(view=f'diagonal_{ang}', angle=int(ang), frame=ANG[ang]['frame'], source=f"reference/apose_turn/frames/{ANG[ang]['frame']}.png",
               canvas=[W, H], coordinateSpace='FRAME px of the turn frame (768x1168), origin top-left; all pieces full-canvas (x=y=0) in drawn position',
               view_fit=dict(**fit(ang), rule='view_x = scale*frame_x + dx; view_y = scale*frame_y + dy (1365x1739 view space), same as Eyes/Hair/Hands diagonals'),
               layerOrder_backToFront=layers, pieces=pieces, joints=jinfo,
               wrists={s_: dict(forearm_end_pivot=P['_wrist_' + s_], cut_line=wi[s_]['boundary_line_fit'], f8_palm_pivot_frame=None, see='wrist_cuts.json') for s_ in 'RL'},
               hands_note='F8 hands draw UNDER the forearms (parentExternal forearm_R/L); forearm ends exactly at the F8 boundary (wrist_cuts.json)',
               colours=dict(skin_fill=skin, skin_fill_count_in_frame=skin_n, flap_line=line, flap_line_count_in_frame=line_n,
                            note='both are her most common px of their class in this frame; every other px is her exact frame px'),
               key_rule='figure = not border-connected key (B - max(R,G) > 25, Hands F8 rule); enclosed key islands >= 6 px are background',
               teammates_excluded={k: int(v.sum()) for k, v in T.items() if not k.endswith('all_states')},
               side_labels='R/L = her right/left (R = viewer-left at 45 and 315), same as Hands F8')
    json.dump(out, open(f'{od}/parts.json', 'w'), indent=1)
    np.save(f'{od}/_teammask.npy', TM)
    print(ang, 'pieces', {p['id']: (p['pixels'], p['flapPx']) for p in pieces}, 'stray comps', stray, 'skin', skin, 'line', line)
if __name__ == '__main__':
    for a in sys.argv[1:] or ['045', '315']: run(a)
