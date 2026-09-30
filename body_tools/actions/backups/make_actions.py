#!/usr/bin/env python3
"""Body action clips for the Shadowveil rig (Base Body): jump, run, anger.
Writes body_tools/actions/{jump,run,anger}.json (same schema as body_tools/idle/idle_clips.json clips:
{fps 30, duration, loop, interp linear, keys, viewKeys}), plus checks.json. NOTES.md is hand-written from checks.json.
- Rig units: limbs +-1 = +-25 deg, BodyLean +-1 = 8 deg, Toe per part (v<0 = toes bend up, -1 = 30 deg).
- keys = apose values; viewKeys give full per-view overrides for tpose, left, right, back (profiles face opposite
  ways, back is mirrored, leg lengths differ, so legs and root are solved per view).
- RootY (px, +down) exists only in rig/index.v18-wip.html (clamped there to +-40 px, whole px). It is keyed here
  within +-40; the unclamped wanted curve is in "pendingRoot". The live v1.7.1 renderer ignores RootY.
- Hair's BodyLean head offsets (hair/actions/hair_actions.json) are folded in additively and clamped to +-1.
Only reads views/, rig/, hair/; only writes body_tools/actions/."""
import json, math, os
import numpy as np
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
VIEWS = ('apose', 'tpose', 'left', 'right', 'back')
LIMB, LEAN, ROOTLIM = 25.0, 8.0, 40.0
BODY_PARAMS = ['BodyLean'] + [f'{j}{s}' for j in ('Shoulder', 'Elbow', 'Hip', 'Knee', 'Ankle', 'Toe') for s in 'LR']
rig = {v: json.load(open(f'{ROOT}/views/{v}/body/rig.json')) for v in VIEWS}
skin = {v: json.load(open(f'{ROOT}/views/{v}/body/skin.json')) for v in VIEWS}
foot_line = {v: json.load(open(f'{ROOT}/views/body.json'))['views'][v]['footLineY'] for v in VIEWS}
hair = json.load(open(f'{ROOT}/hair/actions/hair_actions.json'))['clips']
FACING = {'left': -1, 'right': +1}          # screen x direction she faces (toes pivot vs ankle pivot)
PROFILE = ('left', 'right')

def rnd(x, n=4): return round(float(x), n)
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def ease_in(x): x = min(1.0, max(0.0, x)); return x * x
def ease_out(x): x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 2
EASE = {'ss': ss, 'in': ease_in, 'out': ease_out, 'lin': lambda x: min(1.0, max(0.0, x))}
def track(keys):
    """keys: [(t, value, ease_into_this_key)], eased piecewise; value(t)"""
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(keys, keys[1:]):
            if t <= t1: return v0 + (v1 - v0) * EASE[e]((t - t0) / (t1 - t0))
        return keys[-1][1]
    return f
def cyc(keys, period):
    """periodic Catmull-Rom through (phase 0..1, value) keys"""
    ps = [k[0] for k in keys]; vs = [k[1] for k in keys]; n = len(keys)
    def f(t):
        p = (t / period) % 1.0
        i = max(j for j in range(n) if ps[j] <= p + 1e-12)
        p0, p1 = ps[i], (ps[i + 1] if i + 1 < n else 1.0)
        u = (p - p0) / (p1 - p0)
        v0, v1, v2, v3 = vs[(i - 1) % n], vs[i], vs[(i + 1) % n], vs[(i + 2) % n]
        return 0.5 * ((2 * v1) + (-v0 + v2) * u + (2 * v0 - 5 * v1 + 4 * v2 - v3) * u * u + (-v0 + 3 * v1 - 3 * v2 + v3) * u ** 3)
    return f

# ---------------------------------------------------------------- kinematics (canvas rotate: + = clockwise, y down)
def R(deg):
    t = math.radians(deg); c, s = math.cos(t), math.sin(t); return np.array([[c, -s], [s, c]])
def bones(v): return {b['name']: b for b in skin[v]['bones']}
def bone_deg(b, val):
    if b.get('maxRotDeg', 0) == 0: return 0.0
    if 'minRotDeg' in b or 'rotDir' in b:
        d = b.get('rotDir', 1); mn = b.get('minRotDeg', -b['maxRotDeg'])
        return d * (-val * mn if val < 0 else val * b['maxRotDeg'])
    return val * b['maxRotDeg']
def world(v, pv):
    """bone -> (2x2, t) world affine for param values pv (dict)"""
    B = bones(v); M = {}
    def m(n):
        if n in M: return M[n]
        b = B[n]; A0, t0 = (np.eye(2), np.zeros(2)) if not b['parent'] else m(b['parent'])
        p = np.array(b['pivot'], float); Rr = R(bone_deg(b, pv.get(b['param'], 0.0)) if b['param'] else 0.0)
        A = A0 @ Rr; t = A0 @ (p - Rr @ p) + t0; M[n] = (A, t); return M[n]
    for n in B: m(n)
    return M
def sole_points(v):
    """rest sole points per side (x, y, bone): skin vertices dominated by foot_/toes_ within 30 px of the lowest,
    same rule as the v1.8 foot plant. A profile's far foot has no skin, so it borrows the near foot's sole shifted by
    the ankle-pivot offset (the far leg is hidden but still physically carries weight)."""
    S = skin[v]; names = [b['name'] for b in S['bones']]; out = {}
    for s in 'LR':
        pts = []
        for (x, y), w in zip(S['vertices'], S['weights']):
            bi, _ = max(w, key=lambda q: q[1]); n = names[bi]
            if n in (f'foot_{s}', f'toes_{s}'): pts.append((x, y, n))
        if pts:
            ym = max(p[1] for p in pts); out[s] = [p for p in pts if p[1] >= ym - 30]
    for s in 'LR':
        if s not in out:
            o = 'R' if s == 'L' else 'L'; B = bones(v)
            d = np.array(B[f'foot_{s}']['pivot']) - np.array(B[f'foot_{o}']['pivot'])
            out[s] = [(x + d[0], y + d[1], n.replace('_' + o, '_' + s)) for x, y, n in out[o]]
    return out
SOLE = {v: sole_points(v) for v in VIEWS}
def feet_pts(v, pv):
    M = world(v, pv)
    return {s: np.array([M[n][0] @ np.array([x, y]) + M[n][1] for x, y, n in pts]) for s, pts in SOLE[v].items()}
def feet(v, pv):
    """per side: (lowest posed y, x of the lowest sole points = contact point)"""
    M = world(v, pv); r = {}
    for s, pts in SOLE[v].items():
        P = np.array([M[n][0] @ np.array([x, y]) + M[n][1] for x, y, n in pts])
        ym = float(P[:, 1].max()); r[s] = (ym, float(P[P[:, 1] >= ym - 1.0, 0].mean()))   # (lowest y, x of the contact point)
    return r
REST_FEET = {v: feet(v, {}) for v in VIEWS}
SOLE_LINE = {v: max(y for y, _ in REST_FEET[v].values()) for v in VIEWS}   # rest lowest sole point (the v1.8 plant line); body.json footLineY differs by a few px
def plant_rooty(v, pv):
    """RootY (px, +down) that puts the lower foot's lowest sole point on the rest foot line (v1.8 foot-plant rule)"""
    f = feet(v, pv); low = max(y for y, _ in f.values()); d = SOLE_LINE[v] - low; return d if abs(d) > 1e-9 else 0.0
def ankle_x(v, s, hip_deg, knee_deg):
    B = bones(v); h, k, a = (np.array(B[n]['pivot'], float) for n in (f'thigh_{s}', f'shin_{s}', f'foot_{s}'))
    return (h + R(hip_deg) @ (k - h) + R(hip_deg + knee_deg) @ (a - k))[0]
def planted_hip(v, s, knee_deg, sign):
    """hip param-deg (sign of 'sign') so the ankle keeps its rest x for this knee param-deg (bisection)"""
    x0 = bones(v)[f'foot_{s}']['pivot'][0]; lo, hi = 0.0, 40.0 * sign
    flo = ankle_x(v, s, lo, knee_deg) - x0
    if abs(knee_deg) < 1e-12 or abs(flo) < 1e-9: return 0.0
    for _ in range(60):
        mid = (lo + hi) / 2; fm = ankle_x(v, s, mid, knee_deg) - x0
        if (fm > 0) == (flo > 0): lo, flo = mid, fm
        else: hi = mid
    return (lo + hi) / 2
def ball_x(v, s, hip_deg, knee_deg, foot_world_deg):
    B = bones(v); h, k, a, b = (np.array(B[n]['pivot'], float) for n in (f'thigh_{s}', f'shin_{s}', f'foot_{s}', f'toes_{s}'))
    return (h + R(hip_deg) @ (k - h) + R(hip_deg + knee_deg) @ (a - k) + R(foot_world_deg) @ (b - a))[0]
def planted_hip_ball(v, s, knee_deg, foot_world_deg, sign):
    """hip param-deg so the ball of the foot (toes pivot) keeps its rest x: flat foot = ankle planted; on the toes the
    ankle is free to move so the ball does not sweep across the floor at toe-off"""
    x0 = bones(v)[f'toes_{s}']['pivot'][0]
    if abs(knee_deg) < 1e-12 and abs(foot_world_deg) < 1e-12: return 0.0
    f = lambda h: ball_x(v, s, h, knee_deg, foot_world_deg) - x0
    hs = np.linspace(-40, 40, 161); fs = [f(h) for h in hs]
    best = None
    for h0, h1, f0, f1 in zip(hs, hs[1:], fs, fs[1:]):
        if f0 == 0 or (f0 > 0) != (f1 > 0):
            lo, hi, flo = h0, h1, f0
            for _ in range(50):
                mid = (lo + hi) / 2; fm = f(mid)
                if (fm > 0) == (flo > 0): lo, flo = mid, fm
                else: hi = mid
            r = (lo + hi) / 2
            if best is None or abs(r) < abs(best): best = r
    return best if best is not None else 0.0
def planted_knee(v, s, hip_deg):
    """knee param-deg so the ankle keeps its rest x for this hip param-deg (front splay: knee comes back in)"""
    x0 = bones(v)[f'foot_{s}']['pivot'][0]; B = bones(v)
    h, k, a = (np.array(B[n]['pivot'], float) for n in (f'thigh_{s}', f'shin_{s}', f'foot_{s}'))
    kw = h + R(hip_deg) @ (k - h); b = a - k; tgt = x0 - kw[0]
    rr = math.hypot(*b); beta = math.atan2(b[1], b[0])      # b.x cos(phi) - b.y sin(phi) = rr cos(phi + beta)
    phi = -beta + math.acos(max(-1, min(1, tgt / rr)))
    phi2 = -beta - math.acos(max(-1, min(1, tgt / rr)))
    phi = min((phi, phi2), key=lambda q: abs(math.remainder(q, 2 * math.pi)))
    return math.degrees(math.remainder(phi, 2 * math.pi)) - hip_deg

# ---------------------------------------------------------------- sign maps
# profile: canonical = left-view param degrees; right view = mirror (x -1) of everything except Toe.
# canonical (left, facing -x): hip +flex, knee -flexion, ankle +toes-up, shoulder +forward, elbow +flexion, lean -forward
# front (apose/tpose): her L is on screen right. abduct (limb away from midline): L -, R +. back view: mirrored (L +, R -).
def front_out(v, s): return (-1 if s == 'L' else 1) * (-1 if v == 'back' else 1)

class Rec:
    """records wanted vs got for the notes (per clip, per joint)"""
    def __init__(s): s.rows = {}
    def add(s, clip, joint, wanted, got, where): s.rows.setdefault(clip, []).append({'joint': joint, 'wanted': wanted, 'got': got, 'where': where})
REC = Rec()

T_ = lambda dur: [rnd(i / FPS) for i in range(int(round(dur * FPS)) + 1)]
def lim(x, m=1.0): return max(-m, min(m, x))

def fold_hair(clip, view, t):
    c = hair[clip]; ks = (c.get('viewKeys', {}).get(view) or {}).get('BodyLean') or c['keys'].get('BodyLean')
    if not ks: return 0.0
    if c.get('loop'): t = t % c['duration']
    if t <= ks[0][0]: return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1: return v0 + (v1 - v0) * (t - t0) / (t1 - t0) if t1 > t0 else v1
    return ks[-1][1]

# =========================================================================== JUMP (1.6 s, once)
JUMP_BEATS = {'rest': 0.0, 'crouch_start': 0.0, 'crouch_low': 0.40, 'takeoff': 0.50, 'apex': 0.80, 'landing_contact': 1.10,
              'landing_absorb_low': 1.20, 'recovered_rest': 1.60}
JUMP_H_WANT = 150.0
def jump_profile_pose(t):
    """canonical (left view) param-deg + ground flag + ground knee"""
    # knee flexion (positive) through ground phases; hips solved planted; heel lift via foot world pitch
    if t <= 0.50:
        kf = track([(0, 0, 'ss'), (0.40, 25, 'ss'), (0.50, 0, 'in')])(t)        # wanted 80 deg at 0.40
        td = track([(0, 0, 'ss'), (0.40, 0, 'ss'), (0.44, 4, 'in'), (0.50, JUMP_TD, 'in')])(t)   # toe-down foot pitch (heel rises)
        toe = track([(0, 0, 'ss'), (0.42, 0, 'ss'), (0.50, -0.8, 'in')])(t)                 # toes bend up: ball stays down
        sh = track([(0, 0, 'ss'), (0.40, -25, 'ss'), (0.50, 25, 'in')])(t)       # arms back (wanted -50), then up/forward (wanted +150)
        el = track([(0, 0, 'ss'), (0.40, 6, 'ss'), (0.50, 3, 'in')])(t)
        lean = track([(0, 0, 'ss'), (0.40, 0.85, 'ss'), (0.50, 0.25, 'in')])(t)  # forward, rig units
        return dict(ground=True, kf=kf, td=td, toe=toe, sh=sh, el=el, lean=lean)
    if t < 1.10:
        u = t
        hip = track([(0.50, JUMP_TO_HIP, 'lin'), (0.62, 14, 'out'), (0.80, 25, 'ss'), (0.95, 18, 'ss'), (1.10, JUMP_LAND_HIP, 'ss')])(u)   # tuck, wanted 60
        kf = track([(0.50, 0, 'lin'), (0.62, 16, 'out'), (0.80, 25, 'ss'), (0.95, 20, 'ss'), (1.10, 8, 'ss')])(u)                # wanted 90
        td = track([(0.50, JUMP_TD, 'lin'), (0.65, 18, 'out'), (0.80, 12, 'ss'), (1.10, 0, 'ss')])(u)
        toe = track([(0.50, -0.8, 'lin'), (0.60, 0, 'out'), (1.10, 0, 'lin')])(u)
        sh = track([(0.50, 25, 'lin'), (0.80, 25, 'ss'), (1.10, 8, 'ss')])(u)
        el = track([(0.50, 3, 'lin'), (0.80, 8, 'ss'), (1.10, 5, 'ss')])(u)
        lean = track([(0.50, 0.25, 'lin'), (0.80, 0.10, 'ss'), (1.10, 0.35, 'ss')])(u)
        return dict(ground=False, hip=hip, kf=kf, td=td, toe=toe, sh=sh, el=el, lean=lean)
    kf = track([(1.10, 8, 'lin'), (1.20, 25, 'out'), (1.60, 0, 'ss')])(t)           # wanted 70 at 1.20
    sh = track([(1.10, 8, 'lin'), (1.20, 6, 'out'), (1.35, -4, 'ss'), (1.60, 0, 'ss')])(t)   # arms down, small overshoot back
    el = track([(1.10, 5, 'lin'), (1.20, 10, 'out'), (1.60, 0, 'ss')])(t)
    lean = track([(1.10, 0.35, 'lin'), (1.20, 0.75, 'out'), (1.60, 0, 'ss')])(t)
    return dict(ground=True, kf=kf, td=0.0, toe=0.0, sh=sh, el=el, lean=lean)
JUMP_LAND_HIP = planted_hip_ball('left', 'L', -8.0, 0.0, +1)      # air keys end exactly on the planted landing pose
JUMP_TD = 20.0                                           # toe-off foot pitch (deg, toes down)
JUMP_TO_HIP = planted_hip_ball('left', 'L', 0.0, -JUMP_TD, +1)   # ball-planted hip at takeoff; air keys start there

def profile_pv(v, P, sides_phase=None):
    """canonical pose P (per side dict or shared) -> param values for view v"""
    mir = -1 if v == 'right' else 1; pv = {}
    for s in 'LR':
        q = P[s] if 'L' in P else P
        if q.get('ground'):
            hipc = planted_hip_ball(v, s, -q['kf'] * mir, -q['td'] * mir, mir) * mir     # solved in this view's own geometry, back to canonical
        else:
            hipc = q['hip']
        kneec = -q['kf']
        anklec = -q['td'] - hipc - kneec
        pv[f'Hip{s}'] = hipc * mir / LIMB; pv[f'Knee{s}'] = kneec * mir / LIMB; pv[f'Ankle{s}'] = anklec * mir / LIMB
        pv[f'Toe{s}'] = q['toe']
        pv[f'Shoulder{s}'] = q['sh'] * mir / LIMB; pv[f'Elbow{s}'] = q['el'] * mir / LIMB
    q = P['L'] if 'L' in P else P
    pv['BodyLean'] = -q['lean'] * mir
    return pv

def jump_front_pv(v, t):
    # front/back: knees-out crouch (hip splay, knee comes back in so the ankle keeps its x), arms in-plane
    splay = track([(0, 0, 'ss'), (0.40, 10, 'ss'), (0.50, 0, 'in'), (0.80, 5, 'ss'), (1.10, 2, 'ss'), (1.20, 10, 'out'), (1.60, 0, 'ss')])(t)
    raise_ = track([(0, 0, 'ss'), (0.40, -12, 'ss'), (0.50, 25, 'in'), (0.80, 25, 'ss'), (1.10, 5, 'ss'), (1.20, -8, 'out'), (1.60, 0, 'ss')])(t)
    elb = track([(0, 0, 'ss'), (0.40, 4, 'ss'), (0.50, 2, 'in'), (0.80, 4, 'ss'), (1.20, 6, 'out'), (1.60, 0, 'ss')])(t)
    pv = {}
    for s in 'LR':
        o = front_out(v, s); h = splay * o; k = planted_knee(v, s, h) if splay else 0.0
        pv[f'Hip{s}'] = h / LIMB; pv[f'Knee{s}'] = k / LIMB; pv[f'Ankle{s}'] = -(h + k) / LIMB; pv[f'Toe{s}'] = 0.0
        pv[f'Shoulder{s}'] = raise_ * o / LIMB; pv[f'Elbow{s}'] = -elb * o / LIMB   # elbow bends toward the body
    pv['BodyLean'] = 0.0
    return pv

def jump_root(v, t, pv, H):
    if t <= 0.50 or t >= 1.10: return plant_rooty(v, pv)
    s = (t - 0.50) / 0.60
    a = JR_CACHE[v]
    return a[0] + (a[1] - a[0]) * s - H * 4 * s * (1 - s)
def jump_pv(v, t): return profile_pv(v, jump_profile_pose(t)) if v in PROFILE else jump_front_pv(v, t)
JR_CACHE = {v: (plant_rooty(v, jump_pv(v, 0.50)), plant_rooty(v, jump_pv(v, 1.10))) for v in VIEWS}

# =========================================================================== RUN (2.0 s loop, 3 strides x 0.667 s)
STRIDE = 2.0 / 3.0
RUN_BEATS = {'contact_L': [0.0, 0.6667, 1.3333], 'contact_R': [0.3333, 1.0, 1.6667],
             'passing': [0.1667, 0.5, 0.8333, 1.1667, 1.5, 1.8333], 'toe_off_L': [0.2667, 0.9333, 1.6], 'toe_off_R': [0.6, 1.2667, 1.9333]}
# leg phase from its own contact: (phase, hipFlex, kneeFlex, footToeDown, Toe)
RUN_LEG = [(0.00, 16, 6, -10, 0.0), (0.10, 9, 14, 0, 0.0), (0.25, 0, 8, 0, 0.0), (0.40, -22, 8, 28, -0.6),
           (0.55, -18, 25, 20, 0.0), (0.72, 6, 25, -5, 0.0), (0.88, 25, 15, -10, 0.0)]
RUN_WANT = {'hip flex (reach before contact)': (40, 25), 'hip extension (toe-off)': (-25, -22), 'knee flex (swing)': (100, 25),
            'knee flex (stance)': (40, 14), 'shoulder swing fwd/back': (45, 25), 'elbow flex': (85, 25), 'forward lean (deg)': (12, 7.2)}
run_leg = {i: cyc([(k[0], k[i]) for k in RUN_LEG], STRIDE) for i in (1, 2, 3, 4)}
def run_profile_pose(t):
    P = {}
    for s, off in (('L', 0.0), ('R', STRIDE / 2)):
        tt = t - off
        hip = lim(run_leg[1](tt), 25); kf = lim(run_leg[2](tt), 25); kf = max(0.0, kf)
        td = run_leg[3](tt); toe = lim(run_leg[4](tt), 1)
        ph = 2 * math.pi * ((tt / STRIDE) % 1)
        sh = -25 * math.cos(ph - 0.25)                 # opposite to the same-side leg, slight lag
        el = 21 + 4 * math.sin(ph - 0.25 + math.pi)    # 17..25 deg, more bent on the forward swing
        P[s] = dict(ground=False, hip=hip, kf=kf, td=td, toe=toe, sh=lim(sh, 25), el=lim(el, 25), lean=0.9)
    return P
def run_front_pv(v, t):
    pv = {}
    for s, off in (('L', 0.0), ('R', STRIDE / 2)):
        p = ((t - off) / STRIDE) % 1
        lift = 8.0 * max(0.0, math.sin(2 * math.pi * (p - 0.40) / 0.60 * 0.5)) if p >= 0.40 else 0.0   # swing: knee-out lift, stance straight
        o = front_out(v, s); h = lift * o; k = planted_knee(v, s, h) if lift else 0.0
        pv[f'Hip{s}'] = h / LIMB; pv[f'Knee{s}'] = k / LIMB; pv[f'Ankle{s}'] = -(h + k) / LIMB; pv[f'Toe{s}'] = 0.0
        ph = 2 * math.pi * p
        pv[f'Shoulder{s}'] = (6 + 4 * math.cos(ph)) * o / LIMB        # arm pumps a little out/in, opposite to the leg lift
        pv[f'Elbow{s}'] = -(12 + 4 * math.cos(ph)) * o / LIMB         # elbows bent (in toward the body)
    pv['BodyLean'] = 0.0
    return pv
def run_pv(v, t): return profile_pv(v, run_profile_pose(t)) if v in PROFILE else run_front_pv(v, t)

# =========================================================================== ANGER (3.0 s, set-in 0-0.40, hold)
ANGER_BEATS = {'rest': 0.0, 'set_in': [0.0, 0.40], 'set_snap': 0.30, 'hold_start': 0.40,
               'breaths_inhale_peak': [0.62, 1.52, 2.42], 'hold_end': 3.0}
def breath_sharp(t):
    """sharp angry breath: 0.9 s period from 0.40; quick inhale 0.22 s, slower exhale"""
    if t < 0.40: return 0.0
    x = (t - 0.40) % 0.9
    return ease_out(x / 0.22) if x < 0.22 else 1 - ss((x - 0.22) / 0.68)
def anger_set(t): return track([(0, 0, 'ss'), (0.30, 1.05, 'out'), (0.40, 1.0, 'ss')])(t)   # small overshoot = sharp set
def anger_profile_pose(t):
    a = anger_set(t); b = breath_sharp(t) * (1 if t >= 0.40 else 0)
    P = {}
    for s, stance in (('L', 2.0), ('R', -2.0)):     # stance widened: one leg 2 deg forward, the other 2 deg back
        hip = stance * a
        P[s] = dict(ground=False, hip=hip, kf=0.0, td=0.0, toe=0.0, sh=(-3.0 - 1.0 * b) * a, el=(8.0 + 1.5 * b) * a,
                    lean=0.45 * a - 0.03 * b)
    return P
def anger_front_pv(v, t):
    a = anger_set(t); b = breath_sharp(t); pv = {}
    for s in 'LR':
        o = front_out(v, s)
        h = 2.0 * a * o                      # stance widened: each leg 2 deg out (feet slide out, see notes)
        pv[f'Hip{s}'] = h / LIMB; pv[f'Knee{s}'] = 0.0; pv[f'Ankle{s}'] = -h / LIMB; pv[f'Toe{s}'] = 0.0
        pv[f'Shoulder{s}'] = (8.0 + 1.0 * b) * a * o / LIMB             # arms held out from the body 8 deg (+1 on inhale)
        pv[f'Elbow{s}'] = -(10.0 + 1.0 * b) * a * o / LIMB             # elbows bent in, tense
    pv['BodyLean'] = 0.0
    return pv
def anger_pv(v, t): return profile_pv(v, anger_profile_pose(t)) if v in PROFILE else anger_front_pv(v, t)

# =========================================================================== build + validate
def build(name, dur, loop, pv_fn, root_fn, hair_clip, beats, notes, pending_fn=None):
    T = T_(dur); per = {}; pend = {}; hairclip = []; rootclip = []
    for v in VIEWS:
        ks = {p: [] for p in BODY_PARAMS + ['RootY']}; pk = []
        for t in T:
            pv = pv_fn(v, t)
            body_lean = pv['BodyLean']; hl = fold_hair(hair_clip, v, t); tot = body_lean + hl
            if abs(tot) > 1.0 + 1e-9: hairclip.append({'view': v, 't': t, 'body': rnd(body_lean), 'hair': rnd(hl), 'sum': rnd(tot)})
            pv['BodyLean'] = lim(tot)
            for p in BODY_PARAMS:
                x = pv.get(p, 0.0)
                assert abs(x) <= 1.0 + 1e-9 or p == 'BodyLean', (name, v, p, t, x)
                ks[p].append([t, rnd(lim(x))])
            ry = root_fn(v, t, pv)
            want = pending_fn(v, t, pv) if pending_fn else ry
            if abs(ry) > ROOTLIM + 1e-9: rootclip.append({'view': v, 't': t, 'wanted': rnd(ry, 2)})
            ks['RootY'].append([t, rnd(lim(ry, ROOTLIM), 2)]); pk.append([t, rnd(want, 2)])
        if loop:
            for p in ks: ks[p][-1][1] = ks[p][0][1]
            pk[-1][1] = pk[0][1]
        if T[0] == 0.0 and not loop:
            for p in ks: ks[p][0][1] = 0.0
            pk[0][1] = 0.0
        per[v] = ks; pend[v] = pk
    keys = per['apose']; viewKeys = {v: per[v] for v in VIEWS if v != 'apose'}
    clip = {'fps': FPS, 'duration': dur, 'loop': loop, 'interp': 'linear', 'keys': keys, 'viewKeys': viewKeys,
            'pendingRoot': {'param': 'RootY', 'units': 'px, +y down, whole px on screen', 'status':
                            'RootX/RootY exist only in rig/index.v18-wip.html (contract v1.8 draft, +-40 px). Keys above are within +-40; these are the unclamped wanted values.',
                            'viewKeys': {v: pend[v] for v in VIEWS}},
            'beats': beats, 'notes': notes,
            'hairFold': {'source': f'hair/actions/hair_actions.json clips.{hair_clip} BodyLean (keys for apose/tpose/back, viewKeys for left/right)',
                         'rule': 'BodyLean = clamp(body + hair, -1, 1), sampled at 30 fps', 'clippedFrames': hairclip}}
    return clip, rootclip

def run_root(v, t, pv): return plant_rooty(v, pv)
# fit the arc so RootY peaks exactly at -40 (scaled arc, no flat top) in each view
JUMP_H_FIT = {}
for v in VIEWS:
    lo, hi = 0.0, JUMP_H_WANT
    for _ in range(50):
        mid = (lo + hi) / 2; m = min(jump_root(v, t, jump_pv(v, t), mid) for t in T_(1.6))
        (lo, hi) = (mid, hi) if m > -ROOTLIM else (lo, mid)
    JUMP_H_FIT[v] = lo
jump, jump_rc = build('jump', 1.6, False, jump_pv, lambda v, t, pv: jump_root(v, t, pv, JUMP_H_FIT[v]), 'jump', JUMP_BEATS,
                      'Profiles read best. Knees are limited to 25 deg, so the crouch drop is only what the legs give at the limit. Front/back: knees-out crouch and arms in-plane (a forward swing is out of plane there).',
                      pending_fn=lambda v, t, pv: jump_root(v, t, pv, JUMP_H_WANT))
RUN_BOB = {'left': 7.0, 'right': 7.0, 'apose': 5.0, 'tpose': 5.0, 'back': 5.0}   # half amplitude px: down at each contact, up at each passing
RUN_BASE = {v: plant_rooty(v, run_pv(v, 0.0)) - RUN_BOB[v] for v in VIEWS}
def run_root_bob(v, t, pv):
    """designed bob, but never lower than the foot plant (min: the body may rise off the floor = flight phase, it may
    not push a foot through the floor)"""
    d = RUN_BASE[v] + RUN_BOB[v] * math.cos(2 * math.pi * t / (STRIDE / 2))
    return min(plant_rooty(v, pv), d)
run, run_rc = build('run', 2.0, True, run_pv, run_root_bob, 'run', RUN_BEATS,
                    'In-place (treadmill) run: RootX is 0, so the stance foot slides back under her. Only the near leg/arm are drawn in profiles (far limbs hidden:true), so the alternation shows as the one visible leg going forward then back.')
anger, anger_rc = build('anger', 3.0, False, anger_pv, run_root, 'anger', ANGER_BEATS,
                        'Ends in the held pose (no return to rest). Fists: Hands; anger face: Mouth/Eyes.')

# ---------------------------------------------------------------- checks
def val(ks, p, t):
    k = ks[p]; 
    for (t0, v0), (t1, v1) in zip(k, k[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return k[-1][1]
def view_keys(c, v): return c['keys'] if v == 'apose' else {**c['keys'], **c['viewKeys'][v]}
checks = {}
for name, c in (('jump', jump), ('run', run), ('anger', anger)):
    ck = {'paramsExist': {}, 'range': True, 'kneeDirection': {}, 'elbowDirection': {}, 'footLift_noRoot_px': {}, 'footLift_withRoot_px': {}, 'stanceSlide_px': {}}
    for v in VIEWS:
        K = view_keys(c, v); rp = set(rig[v]['paramMap']) 
        ck['paramsExist'][v] = sorted(p for p in K if p != 'RootY' and p not in rp) or 'all present'
        for p, ks in K.items():
            m = ROOTLIM if p == 'RootY' else 1.0
            if any(abs(x) > m + 1e-9 for _, x in ks): ck['range'] = False
        # knee/elbow direction per frame: profile knee flexion must be backward (canonical knee <= 0), front knee joint outside hip-ankle line
        bad_k, bad_e = [], []; lifts0, lifts1, slide = [], [], 0.0; prev = None; rest_off = {}; run_x = 0.0
        for i, (t, _) in enumerate(K['KneeL']):
            pv = {p: K[p][i][1] for p in K if p != 'RootY'}
            M = world(v, pv); B = bones(v)
            for s in 'LR':
                hp = M[f'thigh_{s}'][0] @ np.array(B[f'thigh_{s}']['pivot']) + M[f'thigh_{s}'][1]
                kp = M[f'shin_{s}'][0] @ np.array(B[f'shin_{s}']['pivot']) + M[f'shin_{s}'][1]
                ap = M[f'foot_{s}'][0] @ np.array(B[f'foot_{s}']['pivot']) + M[f'foot_{s}'][1]
                d1, d2 = kp - hp, ap - kp; cross = d1[0] * d2[1] - d1[1] * d2[0]
                if v in PROFILE:
                    # facing -x (left): a real knee bend puts the knee in front (-x) of the hip-ankle line -> cross < 0 ... check via param sign
                    flex = -pv[f'Knee{s}'] * (1 if v == 'left' else -1)
                    if flex < -1e-4: bad_k.append((t, s, rnd(pv[f'Knee{s}'])))
                    ef = pv[f'Elbow{s}'] * (1 if v == 'left' else -1)
                    if ef < -1e-4: bad_e.append((t, s, rnd(pv[f'Elbow{s}'])))
                else:
                    line = ap - hp; off = (kp[0] - (hp[0] + line[0] * (kp[1] - hp[1]) / line[1])) if abs(line[1]) > 1e-6 else 0
                    outward = np.sign(B[f'thigh_{s}']['pivot'][0] - B['pelvis']['pivot'][0])
                    if s not in rest_off:
                        Mr = world(v, {}); hr, kr, ar = (Mr[n][0] @ np.array(B[n]['pivot']) + Mr[n][1] for n in (f'thigh_{s}', f'shin_{s}', f'foot_{s}'))
                        rest_off[s] = kr[0] - (hr[0] + (ar - hr)[0] * (kr[1] - hr[1]) / (ar - hr)[1])
                    if (off - rest_off[s]) * outward < -0.5: bad_k.append((t, s, rnd(off - rest_off[s], 2)))   # knee pushed inward of its rest line = knock-knee kink
            f = feet(v, pv); low = max(y for y, _ in f.values())
            ry = K['RootY'][i][1]
            lifts0.append(rnd(SOLE_LINE[v] - low, 2)); lifts1.append(rnd(SOLE_LINE[v] - (low + round(ry)), 2))
            st = max(f, key=lambda s: f[s][0]); on = abs(SOLE_LINE[v] - (low + round(ry))) <= 1.0   # planted (with root)
            FP = feet_pts(v, pv)[st]; j = int(np.argmax(FP[:, 1]))
            # slip = x motion of the material sole point that is touching the floor, summed while that foot stays planted
            if prev and prev[0] == st and prev[1] and on: run_x += abs(FP[j, 0] - prev[2][j, 0]); slide = max(slide, run_x)
            else: run_x = 0.0
            prev = (st, on, FP)
        ck['kneeDirection'][v] = bad_k[:5] or 'ok'; ck['elbowDirection'][v] = bad_e[:5] or 'ok'
        ck['footLift_noRoot_px'][v] = {'max': max(lifts0), 'min': min(lifts0)}
        ck['footLift_withRoot_px'][v] = {'max': max(lifts1), 'min': min(lifts1)}
        ck['stanceSlide_px'][v] = rnd(slide, 1)   # longest continuous x travel of a planted foot (RootX = 0)
        if not c['loop']: ck.setdefault('startsAtRest', {})[v] = all(ks[0][1] == 0 for ks in K.values())
        else: ck.setdefault('seamless', {})[v] = all(ks[0][1] == ks[-1][1] and ks[-1][0] == c['duration'] for ks in K.values())
    if name == 'jump': ck['endsAtRest'] = {v: all(ks[-1][1] == 0 for ks in view_keys(c, v).values()) for v in VIEWS}
    if name == 'run':
        alt = {}
        for v in VIEWS:
            K = view_keys(c, v)
            # which ankle is ahead (facing direction) / higher at each contact and passing
            res = []
            for t in [0.0, 0.3333, 0.6667, 1.0, 1.3333, 1.6667]:
                i = int(round(t * FPS)); pv = {p: K[p][i][1] for p in K if p != 'RootY'}; M = world(v, pv); B = bones(v)
                ax = {s: (M[f'foot_{s}'][0] @ np.array(B[f'foot_{s}']['pivot']) + M[f'foot_{s}'][1]) for s in 'LR'}
                if v in PROFILE: res.append(max('LR', key=lambda s: ax[s][0] * FACING[v]))     # leg in front at contact
                else: res.append(min('LR', key=lambda s: -ax[s][1]))                            # planted (lower) foot
            alt[v] = {'legInFrontOrPlantedAtContacts': res, 'alternates': all(a != b for a, b in zip(res, res[1:]))}
        hl, hr = [x for _, x in run['viewKeys']['left']['HipL']], [x for _, x in run['viewKeys']['left']['HipR']]
        alt['hipL_hipR_correlation_left'] = rnd(np.corrcoef(hl, hr)[0, 1], 3)
        ry = [x for _, x in run['viewKeys']['left']['RootY']]; alt['rootBob_left_px'] = [min(ry), max(ry), rnd(max(ry) - min(ry), 1)]
        ryb = [x for _, x in run['keys']['RootY']]; alt['rootBob_apose_px'] = [min(ryb), max(ryb), rnd(max(ryb) - min(ryb), 1)]
        ck['legsAlternate'] = alt
    ck['rootClamped'] = {'frames': len({(r['view'], r['t']) for r in (jump_rc if name == 'jump' else run_rc if name == 'run' else anger_rc)})}
    ck['hairFoldClippedFrames'] = len(c['hairFold']['clippedFrames'])
    ck['peakAbs'] = {v: {p: rnd(max(abs(x) for _, x in ks), 3) for p, ks in view_keys(c, v).items() if max(abs(x) for _, x in ks) > 0} for v in VIEWS}
    checks[name] = ck
checks['jumpArc'] = {'wantedApexPx': JUMP_H_WANT, 'fittedArcPx': {v: rnd(h, 1) for v, h in JUMP_H_FIT.items()},
                     'rootY_at': {v: {str(t): val(view_keys(jump, v), 'RootY', t) for t in (0.4, 0.5, 0.8, 1.1, 1.2, 1.6)} for v in VIEWS},
                     'pendingRootY_at': {v: {str(t): val({'R': jump['pendingRoot']['viewKeys'][v]}, 'R', t) for t in (0.4, 0.5, 0.8, 1.1, 1.2)} for v in VIEWS}}
checks['runWanted'] = RUN_WANT
checks['otherOwnersBodyParams'] = {}
for f in ('eyes/showcase/eye_showcase.json', 'mouth/actions/mouth_actions.json', 'hands/actions/hand_actions.json', 'hair/actions/hair_actions.json'):
    d = json.load(open(f'{ROOT}/{f}')); hits = set()
    for cn, c in d['clips'].items():
        for p in list(c.get('keys', {})) + [p for vk in c.get('viewKeys', {}).values() for p in vk]:
            if p in BODY_PARAMS or p.startswith('Root'): hits.add(f'{cn}:{p}')
    checks['otherOwnersBodyParams'][f] = sorted(hits) or 'none'

for name, c in (('jump', jump), ('run', run), ('anger', anger)):
    c.update({'format': 'shadowveil body action clip v1 (same clip schema as body_tools/idle/idle_clips.json)',
              'spec': 'value(t) = linear interpolation of keys[param]; viewKeys[view][param] overrides for that view; loop wraps at duration; params not listed stay at default; RootY is a v1.8-draft param (ignored by v1.7.1)',
              'units': 'limbs x25 deg, BodyLean x8 deg, Toe: -1 = toes bend up 30 deg; RootY px (+down, clamp +-40)',
              'generator': 'python3 body_tools/actions/make_actions.py'})
    dst = f'{HERE}/{name}.json'; json.dump(c, open(dst + '.tmp', 'w'), separators=(',', ':')); os.replace(dst + '.tmp', dst)
    print(dst, os.path.getsize(dst))
json.dump(checks, open(f'{HERE}/checks.json', 'w'), indent=1, default=str)

