"""diag_body_fix: same 14 pieces, same partition, layers, parents and rigid-piece rig as diag_body; only HIDDEN px (joint caps,
underlaps, flaps) and joint pivots change. STAGED. Usage: python3 build_fix.py 045 315
Per joint (the turning piece is drawn UNDER the piece it meets, except head over neck):
  pivot : true joint centre. Limb hinges (elbow, knee, ankle, waist, neck base) = midpoint of the seam chord between the two points
          where the seam meets her outline; shoulders/hips/head = hand-placed in CFG (deltoid centre, femoral head, top of neck).
  cap   : disk(pivot, r) on the turning piece, only on px covered at rest by a higher piece (hidden). r = half the seam chord
          (limbs), her inscribed radius (shoulders), distance to the outer hip seam end (hips: carries the hip mass round).
          Turning, the disk spins in place, so the outer side of every bend becomes a round arc that meets both outlines.
          Cap px are kept only where they also pass the envelope test below (so the arc never bulges past her shape).
  flap  : the old flap px kept only where, at every angle -25..+25 (step 5), the px stays inside the closed envelope of the posed
          figure (her rest figure + the turned pieces, closed with ENV_R_J px (8 default; shoulders 16, hips 20, waist 20) minus 1 px):
          it may fill armpit/crotch/waist wedges but never makes a lump past her outline.
  neck  : (head_neck) her neck column continued up under the jaw, plus a round cap at the top-of-neck pivot.
  colour: every px is one of her frame px: cap px within 2 px of the cap edge (or of her silhouette) copy her nearest rim px of the
          same depth (feathered rim, her AA pattern); all other fill px (flaps, cap interior) copy her nearest plain-skin px of the two
          joint pieces. Flaps carry no rim/line px, so nothing dark can surface inside the body when they swing (no new lines/folds).
Every hidden px is under a higher Body piece at rest and never on Hands/Eyes/Mouth/Hair px (all states)."""
import sys; sys.path.insert(0, '.'); from posekit import *
import shutil
from seams import seam_ends
ENV_R = 8
ENV_R_J = dict(shoulder_R=16, shoulder_L=16, hip_R=20, hip_L=20, waist=20)
CFG = {
 '045': dict(pivots=dict(shoulder_R=[319.0, 289.0], shoulder_L=[456.0, 292.0], hip_R=[338.0, 545.0], hip_L=[421.0, 545.0], head_neck=[387.5, 228.0]), neck_seam_y=236),
 '315': dict(pivots=dict(shoulder_R=[302.0, 295.0], shoulder_L=[441.0, 288.0], hip_R=[344.0, 535.0], hip_L=[424.0, 546.0], head_neck=[374.5, 228.0]), neck_seam_y=236),
}
PIECE_OF_JOINT = dict(shoulder_R='upper_arm_R', shoulder_L='upper_arm_L', elbow_R='forearm_R', elbow_L='forearm_L', hip_R='thigh_R', hip_L='thigh_L',
                      knee_R='shin_R', knee_L='shin_L', ankle_R='foot_R', ankle_L='foot_L', waist='torso', neck_base='neck', head_neck='head')
YY, XX = np.mgrid[0:H, 0:W]; PX = XX + 0.5; PY = YY + 0.5
def rotpts(xs, ys, p, th):
    t = np.radians(th); dx = xs + 0.5 - p[0]; dy = ys + 0.5 - p[1]
    return p[0] + np.cos(t) * dx - np.sin(t) * dy, p[1] + np.sin(t) * dx + np.cos(t) * dy
def nearest_from(src, F):
    """colour map: every px gets her colour of the nearest src px"""
    _, (iy, ix) = ndi.distance_transform_edt(~src, return_indices=True); return F[iy, ix], np.hypot(iy - YY, ix - XX)
def build(ang, opts=None):
    opts = opts or {}
    C = ctx(ang); F = C['F'].astype(np.uint8); fg = C['fg']; T = C['T']
    TMall = C['TM'].copy()
    for k, v in T.items():
        if k.endswith('all_states') and 'wristflap' not in k: TMall |= v
    fig = fg | C['TM']
    pj0, img = load_set(f'{ORIG}/{ang}'); pj = json.loads(json.dumps(pj0)); L = {p['id']: p['layer'] for p in pj['pieces']}
    owner = np.full((H, W), '', object)
    for k in pj['layerOrder_backToFront']: owner[img[k][..., 3] > 0] = k
    own = {k: owner == k for k in img}
    new = {k: np.zeros((H, W, 4), np.uint8) for k in img}
    for k in img: new[k][own[k]] = img[k][own[k]]
    dtfg = ndi.distance_transform_edt(fig)
    lum = C['F'].sum(2); bm = C['F'][..., 2] - np.maximum(C['F'][..., 0], C['F'][..., 1])
    darkish = ndi.binary_dilation(fg & (lum < 330), iterations=2)
    plain = fg & ~C['TM'] & (lum >= 340) & (bm < 0) & ~darkish & (dtfg > 3)
    piv = {}; info = {}
    def paint(ch, par, m, ringdepth=None, rim_ok=None):
        """colour hidden px m of piece ch: her rim copies near outlines, her plain skin elsewhere (from ch/par own px)."""
        src_own = own[ch] | own[par]
        im = new[ch]
        fillc, _ = nearest_from(plain & src_own, F)
        col = fillc.copy()
        rimrest = m & (dtfg <= 2.0) & (rim_ok if rim_ok is not None else True)            # px on her rest outline: her px there (the covering piece's rim)
        col[rimrest] = F[rimrest]
        if ringdepth is not None:
            for dpt in (1, 2):
                src = src_own & fg & ~C['TM'] & (np.abs(dtfg - dpt) < 0.5) & ~(np.abs(F.astype(int) - F.astype(int)).sum(2) > 0)
                if not src.any(): continue
                cc, _ = nearest_from(src, F); sel = m & (ringdepth == dpt) & ~rimrest; col[sel] = cc[sel]
        im[m, :3] = col[m]; im[m, 3] = 255
    for jn, j in pj['joints'].items():
        if 'joint_radius_px' not in j: continue
        ch, par = j['flap_on'], j['under']
        ends = seam_ends(ang, pj0, img, jn)
        p = list(map(float, CFG[ang]['pivots'].get(jn, j['pivot'])))
        if jn == 'head_neck':
            sy = CFG[ang]['neck_seam_y']; rows = range(sy, sy + 14)
            lx = np.array([np.nonzero(own['neck'][y])[0].min() for y in rows], float); rx = np.array([np.nonzero(own['neck'][y])[0].max() for y in rows], float)
            yr = np.array(list(rows), float); al = np.polyfit(yr, lx, 1); ar = np.polyfit(yr, rx, 1)
            xl = np.polyval(al, YY); xr = np.polyval(ar, YY)
            col_ = (XX >= np.round(xl)) & (XX <= np.round(xr)) & (YY >= sy - opts.get('neck_up', 40)) & (YY < sy + 14)
            under = own['head'] & ~TMall
            colm = col_ & under
            rc = float(dtfg[int(p[1]), int(p[0])]) - 0.5; d = np.hypot(PX - p[0], PY - p[1])
            cd = (d <= rc) & under & ~colm
            rd = np.zeros((H, W), int)
            sd = np.minimum(XX - np.round(xl), np.round(xr) - XX) + 1; rd[colm & (sd <= 2)] = sd[colm & (sd <= 2)].astype(int)
            cdd = np.ceil(rc - d + 1e-6).astype(int); rd[cd & (cdd <= 2)] = cdd[cd & (cdd <= 2)]
            paint('neck', 'neck', colm | cd, rd)
            piv[jn] = p
            info[jn] = dict(flap_on='neck', under='head', mover='head', pivot=p, old_pivot=j['pivot'], joint_radius_px=j['joint_radius_px'], cap_radius_px=round(rc, 1),
                            neck_underlap_px=int(colm.sum()), cap_px=int(cd.sum()), method='neck column continued under the jaw + round cap at the top-of-neck pivot (on the neck piece, hidden under the head)')
            continue
        if jn in CFG[ang]['pivots']: mode = 'outer' if jn.startswith('hip') else 'dt'
        else:
            mode = 'chord'; (x1, y1, _), (x2, y2, _) = ends; p = [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)]
        if mode == 'chord': rc = float(np.hypot(x2 - x1, y2 - y1)) / 2
        elif mode == 'outer': rc = float(min(np.hypot(e[0] - p[0], e[1] - p[1]) for e in ends))
        else: rc = float(dtfg[int(p[1]), int(p[0])]) - 0.5
        rc += opts.get('cap_extra', {}).get(jn, 0.0)
        piv[jn] = p
        d = np.hypot(PX - p[0], PY - p[1])
        hide = np.zeros((H, W), bool)
        for k in img:
            if L[k] > L[ch]: hide |= own[k]
        hide &= ~TMall
        cap = (d <= rc) & hide & own[par]
        ringdepth = np.ceil(rc - d + 1e-6).astype(int); ringdepth[~cap | (ringdepth > 2)] = 0
        # envelope-limited flap from the old flap px of this joint
        sub = subtree(pj, ch); subown = np.zeros((H, W), bool)
        for k in sub: subown |= own[k]
        static = fig & ~subown
        old = (img[ch][..., 3] > 0) & ~own[ch] & hide & own[par] & (d <= j['joint_radius_px'] + 0.5) & ~cap
        cand = old | cap
        ys, xs = np.nonzero(cand); ok = np.ones(len(xs), bool)
        tf = np.zeros((H, W), bool)
        for t_, o_ in TEAM_OWNER.items():
            if o_ in sub and t_ in T and 'wristflap' not in t_: tf |= T[t_]
        static = static & ~tf
        base = (subown | tf).astype(np.uint8) * 255
        for th in range(-25, 26, 5):
            if th == 0: continue
            moved = rot(base, p, th) > 0
            env = cv2.morphologyEx((static | moved).astype(np.uint8), cv2.MORPH_CLOSE, disk(opts.get('env', {}).get(jn, ENV_R_J.get(jn, ENV_R)))) > 0
            env = ndi.binary_erosion(env, iterations=1) | (static & fig)
            rx, ry = rotpts(xs, ys, p, th); ix = np.floor(rx).astype(int); iy = np.floor(ry).astype(int)
            inside = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H); ok &= inside; ok[inside] &= env[iy[inside], ix[inside]]
        keep = np.zeros((H, W), bool); keep[ys[ok], xs[ok]] = True
        capk = cap & keep; flap = old & keep
        paint(ch, par, capk | flap, ringdepth, rim_ok=capk)
        info[jn] = dict(flap_on=ch, under=par, pivot=p, old_pivot=j['pivot'], joint_radius_px=j['joint_radius_px'], cap_mode=mode, cap_radius_px=round(rc, 1),
                        envelope_close_px=opts.get('env', {}).get(jn, ENV_R_J.get(jn, ENV_R)), cap_px=int(capk.sum()), cap_px_before_envelope=int(cap.sum()), flap_px=int(flap.sum()), old_flap_px=int(j.get('flap_px', 0)), seam_ends=ends)
    for p_ in pj['pieces']:
        for jn, pc in PIECE_OF_JOINT.items():
            if pc == p_['id'] and jn in piv: p_['pivot'] = piv[jn]
    od = f'{FIX}/{ang}'; os.makedirs(f'{od}/pieces', exist_ok=True)
    for k in img:
        a = new[k]; assert ((a[..., 3] == 0) | (a[..., 3] == 255)).all()
        Image.fromarray(a, 'RGBA').save(f'{od}/pieces/{k}.png')
    for p_ in pj['pieces']:
        a = new[p_['id']][..., 3] > 0; p_['flapPx'] = int((a & ~own[p_['id']]).sum()); p_.pop('flapLinePx', None)
    for jn in info: pj['joints'][jn] = info[jn]
    pj['colours'] = dict(rule='every hidden px copies one of her frame px: rim px = her nearest rim px of the same depth (1 or 2 px in); fill = her nearest plain-skin px of the two joint pieces',
                         old=pj0['colours'])
    pj['fix'] = dict(tool='body_tools/work/diag_body_fix/tools/build_fix.py', base='body_tools/work/diag_body/' + ang, envelopeClosePx=ENV_R, opts=opts,
                     note='same pieces/partition/layers/parents as diag_body; only hidden px and joint pivots changed')
    json.dump(pj, open(f'{od}/parts.json', 'w'), indent=1)
    shutil.copy(f'{ORIG}/{ang}/wrist_cuts.json', f'{od}/wrist_cuts.json')
    return pj
if __name__ == '__main__':
    for a in sys.argv[1:] or ['045', '315']: build(a); print('built', a)
