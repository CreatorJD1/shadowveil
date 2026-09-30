#!/usr/bin/env python3
"""Idle body clips for the Shadowveil rig (Base Body). No native clip format exists in rig/index.html or runtime-contract
(v1.6.1): this writes the simple JSON {fps, duration, loop, interp, keys:{param:[[t,v],..]}, viewKeys:{view:{param:..}}}.
Keys are sampled every frame (30 fps) from smooth periodic curves, so linear interpolation between keys is exact enough.
viewKeys override keys for that view only (legs: the profiles face opposite ways, and knee compensation uses each view's
own leg lengths). Eyes and hair are left to the rig's own auto."""
import json, math, os
FPS, DUR = 30, 8.0
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
T = [round(i / FPS, 4) for i in range(int(DUR * FPS) + 1)]
LIMB, LEAN, WRIST = 25.0, 8.0, 25.0          # deg at +-1 (rig maxRotDeg; hands rigs set no wristMaxDeg -> 25)
def wrap(t): return t % DUR
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def bump(t, c, w):                             # smooth periodic bump on the 8 s loop, peak 1 at c
    d = (wrap(t - c) + DUR / 2) % DUR - DUR / 2; return math.exp(-(d / w) ** 2)
def S(t, per, ph=0.0): return math.sin(2 * math.pi * (t / per + ph))
def pulse(t, a, b, c, d):                      # 0 before a, ease up to 1 at b, hold to c, ease down to 0 at d (loop-aware)
    t = wrap(t)
    if t < a or t >= d: return 0.0
    if t < b: return ss((t - a) / (b - a))
    if t < c: return 1.0
    return 1 - ss((t - c) / (d - c))
def rnd(x): return round(x, 4)
def keys(f): return [[t, rnd(f(t))] for t in T]
def const(v): return [[0.0, v], [DUR, v]]
rig = {v: {p['id']: p for p in json.load(open(f'{ROOT}/views/{v}/body/rig.json'))['parts']} for v in ('apose', 'tpose', 'left', 'right', 'back')}
def leg(v, s):
    h, k, a = rig[v]['thigh_' + s], rig[v]['shin_' + s], rig[v]['foot_' + s]
    return math.dist((h['pivotX'], h['pivotY']), (k['pivotX'], k['pivotY'])), math.dist((k['pivotX'], k['pivotY']), (a['pivotX'], a['pivotY']))
def planted(v, s, hip_deg):
    """hip rotation -> (hip, knee, ankle) param values keeping the ankle's x (L1 sin th + L2 sin psi = 0) and the foot level."""
    L1, L2 = leg(v, s); th = math.radians(hip_deg)
    psi = -math.asin(max(-1, min(1, L1 * math.sin(th) / L2)))
    return hip_deg / LIMB, (math.degrees(psi) - hip_deg) / LIMB, -math.degrees(psi) / LIMB
HAND_HOLD = {'Thumb': 0.2, 'Index': 0.3, 'Middle': 0.5, 'Ring': 0.5, 'Pinky': 0.55}
def hands_and_mouth(elbow_deg):
    k = {}
    for side, lag in (('R', 0.0), ('L', 0.6)):
        for f, v0 in HAND_HOLD.items():
            fn = (lambda v0, lag: (lambda t: v0 + 0.15 * pulse(t - lag, 3.0, 3.4, 3.6, 4.2)))(v0, lag) if f in ('Middle', 'Ring', 'Pinky') else None
            k[f'Hand{side}{f}'] = keys(fn) if fn else const(v0)   # one curl per finger drives all 3 joints (contract 4, Hands)
        k[f'Hand{side}Spread'] = const(0.1)
        ph = 0.0 if side == 'R' else 0.6 / DUR
        k[f'Wrist{side}'] = keys((lambda side, ph: (lambda t: max(-8, min(8, 0.3 * elbow_deg[side](t - 0.3) + 3 * S(t, 8, ph))) / WRIST))(side, ph))
    k['MouthOpen'] = const(0.0)
    k['MouthForm'] = [[0.0, 0.0], [2.5, 0.0]] + [[rnd(2.5 + i * 0.05), rnd(ss(i / 6))] for i in range(1, 7)] + [[4.6, 1.0]] + [[rnd(4.6 + i * 0.05), rnd(1 - ss(i / 6))] for i in range(1, 7)] + [[8.0, 0.0]]
    return k
clips = {}
# breath(): kept only because idle_arm_settle's BodyLean uses it (the idle_breathe clip was dropped by the user)
def breath(t): x = wrap(t) % 4.0; return math.sin(math.pi * min(x / 1.7, 1.0)) ** 2 if x < 1.7 else math.cos(math.pi / 2 * (x - 1.7) / 2.3) ** 2   # 0..1, inhale 1.7 s, exhale 2.3 s
# ---- idle_arm_sway: slow natural standing arm sway, pushed to the rig limits once per loop (replaces idle_breathe)
# sway(t) in [-1, 1]: one slow 8 s swing plus a lighter 8/3 s ripple and two eased peaks (+1 at ~2.03 s, -1 at ~6.03 s).
# The positive and negative halves are normalised separately so the peaks are exactly +1.0 / -1.0 (the rig limit).
# Meaning of +: front views (apose/tpose) = arm out from the body (tpose: up), back = same (mirrored signs),
# profiles = arm forward. Left lags the right by 0.6 s; elbows follow the shoulder 0.35 s behind, bend only (never
# hyperextend), peak exactly 0.6 once per loop, deepest on the forward/out swing. Legs stay 0 (feet planted).
SWAY_LAG_L, ELBOW_LAG = 0.6, 0.35
def sway_raw(t): return 0.30 * S(t, 8) + 0.08 * S(t, 8 / 3, 0.1) + 0.6 * (bump(t, 2.0, 0.45) - bump(t, 6.0, 0.45))
_sw = [sway_raw(t) for t in T]; SW_POS, SW_NEG = max(_sw), -min(_sw)
def sway(t): r = sway_raw(t); return r / SW_POS if r >= 0 else r / SW_NEG
def elbow_raw(t): return 0.10 + 0.08 * (1 + sway(t - ELBOW_LAG)) + 0.26 * bump(t, 2.0 + ELBOW_LAG, 0.5)
EL_PEAK = max(max(elbow_raw(t) for t in T), max(elbow_raw(t - SWAY_LAG_L) for t in T))
def elbow_sw(t): return 0.6 * elbow_raw(t) / EL_PEAK                         # ~0.12..0.6, flexion only
shw = {'R': lambda t: sway(t), 'L': lambda t: sway(t - SWAY_LAG_L)}
elw = {'R': lambda t: elbow_sw(t), 'L': lambda t: elbow_sw(t - SWAY_LAG_L)}
lean_sw = lambda t: 0.04 * sway(t - 0.3)                                      # tiny (0.32 deg), trails the arms
# per-view signs: out/forward for the shoulder, bend direction for the elbow (canvas rotate, + = clockwise)
ARM_SIGN = {'apose': {'L': -1, 'R': 1}, 'tpose': {'L': -1, 'R': 1}, 'back': {'L': 1, 'R': -1},
            'left': {'L': 1, 'R': 1}, 'right': {'L': -1, 'R': -1}}
ELB_SIGN = {'apose': {'L': 1, 'R': -1}, 'tpose': {'L': 1, 'R': -1}, 'back': {'L': -1, 'R': 1},   # front/back: in toward the body
            'left': {'L': 1, 'R': 1}, 'right': {'L': -1, 'R': -1}}                               # profiles: forearm forward
LEAN_SIGN = {'apose': 1, 'tpose': 1, 'back': -1, 'left': -1, 'right': 1}      # profiles: - left / + right = slight forward
LEGS = [f'{j}{s}' for j in ('Hip', 'Knee', 'Ankle', 'Toe') for s in 'LR']
def arm_keys(v):
    k = {}
    for s in 'LR':
        k[f'Shoulder{s}'] = keys(lambda t, s=s: ARM_SIGN[v][s] * shw[s](t))
        k[f'Elbow{s}'] = keys(lambda t, s=s: ELB_SIGN[v][s] * elw[s](t))
    k['BodyLean'] = keys(lambda t: LEAN_SIGN[v] * lean_sw(t))
    return k
k = arm_keys('apose')
k.update({p: const(0.0) for p in LEGS})
k.update(hands_and_mouth({s: (lambda t, s=s: ELB_SIGN['apose'][s] * elw[s](t) * LIMB) for s in 'LR'}))
vk = {v: arm_keys(v) for v in ('tpose', 'back', 'left', 'right')}
clips['idle_arm_sway'] = {'keys': k, 'viewKeys': vk, 'notes': 'limit test: shoulders reach exactly +1.0 (out/forward, R at 2.03 s, L at 2.63 s) and -1.0 (in/back, R at 6.03 s, L at 6.63 s) once per loop; elbows (flex only) peak 0.6 at 2.37 s (R) / 2.97 s (L), min 0.12; left lags right 0.6 s, elbows lag shoulders 0.35 s; BodyLean +-0.04 trailing 0.3 s; legs 0 (feet planted, no lift or slide). Front/back: + = out from the body (tpose: up); profiles: + = forward.'}
# ---- idle_weight_shift: hip-to-hip; one bigger excursion (12 deg hip, knee ~0.9) near 6 s to test the extremes
def shift(t): return math.tanh(1.6 * S(t, 8)) / math.tanh(1.6)          # holds on each hip, eases through the middle
def hipdeg(t): return 6.0 * shift(t) - 6.0 * bump(t, 6.0, 0.55)         # -12 deg peak at 6.0 s
k = {'BodyLean': keys(lambda t: 0.22 * shift(t - 0.25) - 0.25 * bump(t, 6.1, 0.6)),
     'ShoulderL': keys(lambda t: -0.05 * shift(t - 0.4)), 'ShoulderR': keys(lambda t: -0.05 * shift(t - 0.4)),
     'ElbowL': keys(lambda t: 0.03 * shift(t - 0.6)), 'ElbowR': keys(lambda t: 0.03 * shift(t - 0.6))}
el = {'L': lambda t: 0.03 * shift(t - 0.6) * LIMB, 'R': lambda t: 0.03 * shift(t - 0.6) * LIMB}
k.update(hands_and_mouth(el)); vk = {}
for v in ('apose', 'tpose', 'back'):     # front/back: both legs swing the same way; knee counter-bends so each ankle keeps its x, ankle levels the foot
    vk[v] = {}
    for s in 'LR':
        vk[v][f'Hip{s}'] = keys(lambda t, v=v, s=s: planted(v, s, hipdeg(t))[0])
        vk[v][f'Knee{s}'] = keys(lambda t, v=v, s=s: planted(v, s, hipdeg(t))[1])
        vk[v][f'Ankle{s}'] = keys(lambda t, v=v, s=s: planted(v, s, hipdeg(t))[2])
for v, sg in (('left', 1.0), ('right', -1.0)):   # profiles: the unloaded leg softens its knee (natural flex direction per facing)
    vk[v] = {}
    for s, w in (('L', lambda t: max(0.0, -shift(t))), ('R', lambda t: max(0.0, shift(t)))):
        d = (lambda w: (lambda t: sg * (5.0 * w(t) + 7.0 * bump(t, 6.0, 0.55) * (1 if s == 'R' else 0))))(w)
        vk[v][f'Hip{s}'] = keys(lambda t, v=v, s=s, d=d: planted(v, s, d(t))[0])
        vk[v][f'Knee{s}'] = keys(lambda t, v=v, s=s, d=d: planted(v, s, d(t))[1])
        vk[v][f'Ankle{s}'] = keys(lambda t, v=v, s=s, d=d: planted(v, s, d(t))[2])
        vk[v][f'Toe{s}'] = const(0.0)
    vk[v]['BodyLean'] = keys(lambda t: sg * (0.08 + 0.06 * S(t, 4)))
clips['idle_weight_shift'] = {'keys': k, 'viewKeys': vk, 'notes': 'front/back: hips +-6 deg held on each side, -12 deg peak at 6.0 s (knee ~0.9 of limit); knee/ankle solved per view so the ankle keeps its x and the foot stays level. The pelvis is the rig root and cannot translate, so the feet rise by L1(1-cos th)+L2(1-cos psi) (~3 px at 6 deg, ~14 px at 12 deg). Profiles: the unloaded knee softens.'}
# ---- idle_arm_settle: relaxed drift with follow-through (elbow lags shoulder), one near-limit peak per arm
shL = lambda t: 0.18 * S(t, 8, 0.1) + 0.08 * S(t, 8 / 3, 0.3) + 0.62 * bump(t, 2.2, 0.45)     # peak ~0.92 at 2.2 s
shR = lambda t: -0.16 * S(t, 8, 0.55) + 0.07 * S(t, 4, 0.2) - 0.7 * bump(t, 5.6, 0.45)      # peak ~-0.9 at 5.6 s
elL = lambda t: 0.25 * shL(t - 0.35) + 0.1 * S(t, 4, 0.6) + 0.55 * bump(t, 2.5, 0.4)        # ~0.9 at 2.5 s
elR = lambda t: 0.25 * shR(t - 0.35) - 0.1 * S(t, 8, 0.2) - 0.55 * bump(t, 5.9, 0.4)
k = {'ShoulderL': keys(shL), 'ShoulderR': keys(shR), 'ElbowL': keys(elL), 'ElbowR': keys(elR),
     'BodyLean': keys(lambda t: 0.06 * S(t, 8, 0.3) + 0.04 * breath(t))}
k.update(hands_and_mouth({'L': lambda t: elL(t) * LIMB, 'R': lambda t: elR(t) * LIMB}))
clips['idle_arm_settle'] = {'keys': k, 'viewKeys': {}, 'notes': 'shoulders drift +-0.25 with peaks ShoulderL ~0.92 @2.2 s, ShoulderR ~-0.9 @5.6 s; elbows lag 0.35 s, peaks ~0.9'}
# ---- tpose-only finger override (requested by Hands, hands/work/idle_bend/REPORT.md): tpose f1 is not pre-bent and curl compounds
# down the chain, so Index/Middle/Ring/Pinky idle curls x0.32 in tpose (stay <= 0.25, below the f0->f1 frame switch). Thumb/Spread unchanged.
TPOSE_FINGER_SCALE = 0.32
for c in clips.values():
    tv = c['viewKeys'].setdefault('tpose', {})
    for side in 'LR':
        for f in ('Index', 'Middle', 'Ring', 'Pinky'):
            p = f'Hand{side}{f}'; tv[p] = [[t, rnd(v * TPOSE_FINGER_SCALE)] for t, v in c['keys'][p]]
            assert max(v for _, v in tv[p]) <= 0.25 + 1e-9, (p, max(v for _, v in tv[p]))
for c in clips.values():
    c.update({'fps': FPS, 'duration': DUR, 'loop': True, 'interp': 'linear'})
    for kk in list(c['keys']) + [p for vv in c['viewKeys'].values() for p in vv]:
        pass
    mx = {p: max(abs(x[1]) for x in ks) for p, ks in c['keys'].items()}
    for vv in c['viewKeys'].values():
        for p, ks in vv.items(): mx[p] = max(mx.get(p, 0), max(abs(x[1]) for x in ks))
    c['peakAbs'] = {p: rnd(m) for p, m in sorted(mx.items()) if m > 0 and not p.startswith('Hand')}
    fing = max(x[1] for p, ks in c['keys'].items() if p.startswith('Hand') and 'Spread' not in p for x in ks)
    assert fing <= 0.75 + 1e-9, fing
    assert all(m <= 1.0 for m in mx.values())
    assert max(abs(x[1]) for x in c['keys']['WristL'] + c['keys']['WristR']) * WRIST <= 8.0 + 1e-6
out = {'format': 'shadowveil idle clips v1 (no native clip format in rig/index.html / runtime-contract v1.6.1)',
       'spec': 'value(t) = linear interpolation of keys[param] (viewKeys[view][param] overrides for that view); t wraps at duration; params not listed stay at their default; eyes and hair: rig auto',
       'units': 'rig param units (-1..1; body deg = value x 25, BodyLean x 8, Wrist x 25; finger curl 0..1, f1 = 0.5)',
       'generator': 'python3 body_tools/idle/make_idle_clips.py', 'clips': clips}
dst = f'{ROOT}/body_tools/idle/idle_clips.json'; json.dump(out, open(dst + '.tmp', 'w'), separators=(',', ':')); os.replace(dst + '.tmp', dst)
print(dst, os.path.getsize(dst)); [print(n, c['peakAbs']) for n, c in clips.items()]
