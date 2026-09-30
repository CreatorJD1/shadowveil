#!/usr/bin/env python3
"""Hair showcase clip (Base Hair). Same format as body_tools/idle/idle_clips.json ({fps, duration, loop, interp, keys, viewKeys}).
The rig has NO head/neck params (no tilt/nod/turn): the head part is undriven (maxRotDeg 0) and rides the torso, so the only head
motion is BodyLean (torso, +-8 deg at +-1, pivot at the pelvis). stepHair reads the head (torso) angle a and its velocity:
root target tx = clamp(-a/6,-1,1)*0.8 (+wind), plus a kick -va*0.02 from angular velocity. HairSwayX/Y are NOT keyed (they are
the springs' output). No nod exists, so that segment is omitted. Writes only hair/showcase/hair_showcase.json."""
import json, os, re
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
# (t0, t1, v0, v1): eased move; holds are implied between segments
MOVES = [(0.5, 1.0, 0.0, -1.0),   # tilt to viewer's left, max (-8 deg)
         (1.8, 2.6, -1.0, 1.0),   # tilt to viewer's right, max (+8 deg)
         (3.4, 3.9, 1.0, 0.0),    # back to 0
         (4.9, 5.05, 0.0, 1.0),   # snap: 8 deg in 0.15 s
         (6.55, 6.70, 1.0, 0.0)]  # snap back
DUR = 8.2
def lean(t):
    v = 0.0
    for a, b, v0, v1 in MOVES:
        if t >= b: v = v1
        elif t > a: return v0 + (v1 - v0) * ss((t - a) / (b - a))
    return v
T = set([round(i / FPS, 4) for i in range(int(round(DUR * FPS)) + 1)])
for a, b, *_ in MOVES:
    T |= {a, b}; n = max(4, int(round((b - a) * FPS)))
    T |= {round(a + (b - a) * i / n, 4) for i in range(n + 1)}       # >=4 sub-steps even inside the 0.15 s snaps
T = sorted(T)
def thin(ks):
    out = [ks[0]]
    for i in range(1, len(ks) - 1):
        if not (ks[i - 1][1] == ks[i][1] == ks[i + 1][1]): out.append(ks[i])
    out.append(ks[-1]); return out
keys = {'BodyLean': thin([[t, round(lean(t), 4)] for t in T])}
Z = [[0.0, 0.0], [DUR, 0.0]]
for p in ('ShoulderL', 'ShoulderR', 'ElbowL', 'ElbowR', 'HipL', 'HipR', 'KneeL', 'KneeR', 'AnkleL', 'AnkleR', 'ToeL', 'ToeR'): keys[p] = Z
for s in 'LR':
    for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Spread', 'ThumbSpread'): keys[f'Hand{s}{f}'] = Z
    keys[f'Wrist{s}'] = Z
keys['MouthOpen'] = Z; keys['MouthForm'] = Z
timeline = [{'t0': 0.0, 't1': 0.5, 'what': 'rest (all 0)'},
            {'t0': 0.5, 't1': 1.0, 'what': 'tilt to viewer\'s left, BodyLean 0 -> -1 (-8 deg), smoothstep'},
            {'t0': 1.0, 't1': 1.8, 'what': 'hold -1'},
            {'t0': 1.8, 't1': 2.6, 'what': 'tilt to viewer\'s right, -1 -> +1 (+8 deg)'},
            {'t0': 2.6, 't1': 3.4, 'what': 'hold +1'},
            {'t0': 3.4, 't1': 3.9, 'what': '+1 -> 0'},
            {'t0': 3.9, 't1': 4.9, 'what': 'hold 0 (settle)'},
            {'t0': 4.9, 't1': 4.9, 'what': 'nod: SKIPPED, the rig has no head pitch/nod param'},
            {'t0': 4.9, 't1': 5.05, 'what': 'snap 0 -> +1 (8 deg in 0.15 s, ~53 deg/s avg, ~80 deg/s peak)'},
            {'t0': 5.05, 't1': 6.55, 'what': 'hold +1 (swing and settle)'},
            {'t0': 6.55, 't1': 6.70, 'what': 'snap back +1 -> 0'},
            {'t0': 6.70, 't1': 8.2, 'what': 'hold 0 (settle), ends at exact rest'}]
clip = {'fps': FPS, 'duration': DUR, 'loop': False, 'interp': 'linear', 'keys': keys, 'viewKeys': {}, 'timeline': timeline,
        'peakAbs': {'BodyLean': 1.0},
        'notes': 'Head motion = BodyLean only (torso +-8 deg; the head part is undriven and rides the torso; no tilt/nod/turn/neck params exist in rig/index.html or runtime-contract v1.7.1). Sign: +1 = clockwise on screen (head toward viewer\'s right). Body/hands/mouth keyed at 0 (rest), eyes and HairSwayX/Y left to the rig auto (keying HairSwayX/Y would override the springs). One-shot (loop false); first and last frames are exact rest.'}
out = {'format': 'shadowveil idle clips v1 (same schema as body_tools/idle/idle_clips.json)',
       'spec': 'value(t) = linear interpolation of keys[param] (viewKeys[view][param] overrides for that view); params not listed stay at their default',
       'units': 'rig param units (-1..1; BodyLean x 8 deg)', 'generator': 'python3 hair/showcase/make_hair_showcase.py',
       'clips': {'hair_showcase': clip}}
dst = f'{HERE}/hair_showcase.json'; json.dump(out, open(dst + '.tmp', 'w'), indent=None, separators=(',', ':')); os.replace(dst + '.tmp', dst)
print(dst, os.path.getsize(dst), len(keys['BodyLean']), 'BodyLean keys')
