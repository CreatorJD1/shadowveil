#!/usr/bin/env python3
"""Body showcase clip (Base Body): every body joint one at a time to its current limit, then a 4 s combined natural move.
Same format as idle_clips.json ({fps, duration, loop, interp, keys, viewKeys}); rig param units (-1..1: limbs x25 deg, BodyLean x8 deg).
Each solo segment is 1.5 s: v = sin(2*pi*u) -> 0 -> +1 (0.375 s) -> -1 (1.125 s) -> 0 (1.5 s), 0.1 s gap between segments.
Pelvis is the fixed rig root: in the solo leg segments the OTHER (standing) leg stays at 0 (no lift); the swinging foot itself leaves the floor
by design. Combined part: the free (right) leg bends at a planted-ankle solve (hip 5 deg), standing (left) leg stays 0."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FPS = 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VIEWS = ('apose', 'tpose', 'left', 'right', 'back')
rig = {v: json.load(open(f'{ROOT}/views/{v}/body/rig.json')) for v in VIEWS}
parts = {v: {p['id']: p for p in rig[v]['parts']} for v in VIEWS}
LIMB = 25.0
def leg(v, s):
    h, k, a = parts[v]['thigh_' + s], parts[v]['shin_' + s], parts[v]['foot_' + s]
    return math.dist((h['pivotX'], h['pivotY']), (k['pivotX'], k['pivotY'])), math.dist((k['pivotX'], k['pivotY']), (a['pivotX'], a['pivotY']))
def planted(v, s, hip_deg):
    L1, L2 = leg(v, s); th = math.radians(hip_deg); psi = -math.asin(max(-1, min(1, L1 * math.sin(th) / L2)))
    lift = L1 * (1 - math.cos(th)) + L2 * (1 - math.cos(psi))
    return hip_deg / LIMB, (math.degrees(psi) - hip_deg) / LIMB, -math.degrees(psi) / LIMB, lift
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
SOLO = ['BodyLean', 'ShoulderL', 'ShoulderR', 'ElbowL', 'ElbowR', 'HipL', 'HipR', 'KneeL', 'KneeR', 'AnkleL', 'AnkleR']
LEAD, SEG, GAP, COMB, TAIL = 0.5, 1.5, 0.1, 4.0, 0.4
seg = {}; t = LEAD
for p in SOLO: seg[p] = (round(t, 4), round(t + SEG, 4)); t += SEG + GAP
C0 = round(t, 4); C1 = round(C0 + COMB, 4); DUR = round(C1 + TAIL, 4)
N = int(round(DUR * FPS)); T = sorted(set([round(i / FPS, 4) for i in range(N + 1)] + [round(seg[p][0] + q * SEG, 4) for p in SOLO for q in (0.25, 0.75)]))   # exact +-1 peaks keyed
def solo(p, tt):
    a, b = seg[p]
    return math.sin(2 * math.pi * (tt - a) / SEG) if a <= tt <= b else 0.0
# combined: left arm swing (1 cycle, 0.5 = 12.5 deg) with elbow follow-through; right leg knee bend (opposite arm) peaking at C0+2 s;
# right arm small counter-swing; slight lean toward the standing (left) leg.
def env(tt): u = (tt - C0) / COMB; return 0.0 if u <= 0 or u >= 1 else ss(u / 0.25) * ss((1 - u) / 0.25)
def comb(p, tt, v=None):
    if not (C0 <= tt <= C1): return 0.0
    u = (tt - C0) / COMB; e = env(tt)
    if p == 'ShoulderL': return 0.5 * math.sin(2 * math.pi * u) * e
    if p == 'ElbowL': return 0.3 * math.sin(2 * math.pi * (u - 0.08)) * e
    if p == 'ShoulderR': return -0.15 * math.sin(2 * math.pi * u) * e
    if p == 'ElbowR': return -0.1 * math.sin(2 * math.pi * (u - 0.08)) * e
    if p == 'BodyLean': return 0.2 * math.sin(math.pi * u) ** 2
    if p in ('HipR', 'KneeR', 'AnkleR'):
        sg = {'left': 1.0, 'right': -1.0}.get(v, 1.0)          # profile flex direction per facing (as idle_weight_shift)
        h = sg * 5.0 * math.sin(math.pi * u) ** 2              # 0 -> 6 deg at C0+2 s -> 0
        r = planted(v or 'apose', 'R', h); return r[{'HipR': 0, 'KneeR': 1, 'AnkleR': 2}[p]]
    return 0.0
def thin(ks):   # drop keys that are exactly collinear (flat runs)
    out = [ks[0]]
    for i in range(1, len(ks) - 1):
        if not (ks[i - 1][1] == ks[i][1] == ks[i + 1][1]): out.append(ks[i])
    out.append(ks[-1]); return out
def track(p, v=None): return thin([[tt, round(solo(p, tt) + comb(p, tt, v), 4)] for tt in T])
keys = {p: track(p) for p in SOLO}
for p in ('ToeL', 'ToeR'): keys[p] = [[0.0, 0.0], [DUR, 0.0]]
FING = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Spread', 'ThumbSpread']
for s in 'LR':
    for f in FING: keys[f'Hand{s}{f}'] = [[0.0, 0.0], [DUR, 0.0]]     # Hands' rest = drawn f0 (curl 0)
    keys[f'Wrist{s}'] = [[0.0, 0.0], [DUR, 0.0]]
keys['MouthOpen'] = [[0.0, 0.0], [DUR, 0.0]]; keys['MouthForm'] = [[0.0, 0.0], [DUR, 0.0]]
viewKeys = {v: {p: track(p, v) for p in ('HipR', 'KneeR', 'AnkleR')} for v in VIEWS}
# ---- validation
html = open(f'{ROOT}/rig/index.html').read()
for v in VIEWS:
    bp = set(rig[v]['params'])
    for p in SOLO + ['ToeL', 'ToeR']: assert p in bp, (v, p)
# renderer param table (rig/index.html const P + loop over L/R x fingers/Spread/ThumbSpread + WristL/R); all default 0 = rest
assert "P['Hand'+h+f]" in html and "P['Hand'+h+'Spread']" in html and "P['Hand'+h+'ThumbSpread']" in html and 'P.WristL=' in html and 'MouthOpen:[0,1,0]' in html and 'MouthForm:[-1,1,0]' in html
RP = {'MouthOpen', 'MouthForm', 'WristL', 'WristR'} | {f'Hand{h}{f}' for h in 'LR' for f in FING}
for p in keys:
    if p.startswith(('Hand', 'Wrist', 'Mouth')): assert p in RP, p
allk = list(keys.items()) + [(p, k) for vv in viewKeys.values() for p, k in vv.items()]
peak = {}
for p, ks in allk:
    m = max(abs(x[1]) for x in ks); peak[p] = max(peak.get(p, 0), m); assert m <= 1.0 + 1e-9, (p, m)
lift = {v: round(planted(v, 'R', 5.0)[3], 2) for v in VIEWS}
timeline = [{'t0': seg[p][0], 't1': seg[p][1], 'joint': p, 'shape': '0 -> +1 @%.3f -> -1 @%.3f -> 0' % (seg[p][0] + SEG / 4, seg[p][0] + 3 * SEG / 4),
             'deg': '+-%d' % (8 if p == 'BodyLean' else 25)} for p in SOLO]
timeline.append({'t0': C0, 't1': C1, 'joint': 'combined', 'shape': 'ShoulderL 0.5 swing (1 cycle) + ElbowL 0.3 lag 0.32 s; ShoulderR -0.15 / ElbowR -0.1 counter; BodyLean 0->0.2 @+2 s->0; right leg planted bend hip 5 deg @+2 s (knee/ankle solved per view); left (standing) leg 0'})
clip = {'fps': FPS, 'duration': DUR, 'loop': True, 'interp': 'linear', 'keys': keys, 'viewKeys': viewKeys, 'timeline': timeline, 'peakAbs': {p: round(m, 4) for p, m in sorted(peak.items()) if m > 0},
        'notes': ('Solo sweeps go to the full current limit (+-1.0). Pelvis is the fixed root: during HipL/HipR/KneeL/KneeR/AnkleL/AnkleR solos only that leg moves '
                  '(the other, standing leg stays 0 -> no lift); the swinging foot itself leaves the floor by design (about 73 px at hip 25 deg, 39 px at knee 25 deg in apose). '
                  f'Combined: free right foot lifts {lift} px at the 5 deg bend peak (standing foot 0). Fingers/wrists at Hands rest (0 = drawn f0), mouth rest, eyes/hair rig auto.')}
out = {'format': 'shadowveil idle clips v1 (same as idle_clips.json)', 'spec': 'value(t) = linear interpolation of keys[param] (viewKeys[view][param] overrides for that view); t wraps at duration',
       'units': 'rig param units (-1..1; body deg = value x 25, BodyLean x 8)', 'generator': 'python3 body_tools/idle/make_body_showcase.py', 'clips': {'body_showcase': clip}}
dst = f'{ROOT}/body_tools/idle/body_showcase.json'; json.dump(out, open(dst + '.tmp', 'w'), separators=(',', ':')); os.replace(dst + '.tmp', dst)
print(dst, os.path.getsize(dst), 'duration', DUR)
for x in timeline: print('%6.3f-%6.3f  %-9s %s %s' % (x['t0'], x['t1'], x['joint'], x.get('deg', ''), x['shape']))
print('peak', clip['peakAbs']); print('combined free-foot lift px', lift)
