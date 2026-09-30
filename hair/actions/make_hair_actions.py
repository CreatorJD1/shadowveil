#!/usr/bin/env python3
"""Hair action head keys (Base Hair): jump, anger, run. Same schema as body_tools/idle/idle_clips.json.
The rig has no head/neck param: the head part is undriven and rides the torso, so the only head motion is BodyLean (+-8 deg).
Front/back views: BodyLean is a side ROLL. Profiles: it is a forward/back PITCH (left view faces -x so forward = -1, right view
faces +x so forward = +1; measured from eye x vs torso pivot). A forward dip/drop is therefore only expressible in left/right
(viewKeys); keys (front/back) carry 0 for jump/anger and a small stride roll for run.
BodyLean is also Body's param: these are HEAD OFFSETS meant to be ADDED to Body's BodyLean (clamp [-1,1]), not a replacement."""
import json, math, os
FPS = 30; HERE = os.path.dirname(os.path.abspath(__file__))
FWD = {'left': -1.0, 'right': 1.0}
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def seg(pts):  # piecewise smoothstep through (t, v) points
    def f(t):
        if t <= pts[0][0]: return pts[0][1]
        for (a, va), (b, vb) in zip(pts, pts[1:]):
            if t <= b: return va + (vb - va) * ss((t - a) / (b - a))
        return pts[-1][1]
    return f
def pulse(t, c, w): return math.sin(math.pi * (t - c) / w) ** 2 if c <= t <= c + w else 0.0
def track(f, dur, extra=(), rest_end=True):
    T = sorted(set([round(i / FPS, 4) for i in range(int(round(dur * FPS)) + 1)] + list(extra)))
    ks = [[t, round(f(t), 4)] for t in T]; out = [ks[0]]
    for i in range(1, len(ks) - 1):
        if not (ks[i - 1][1] == ks[i][1] == ks[i + 1][1]): out.append(ks[i])
    out.append(ks[-1]); out[0][1] = 0.0
    if rest_end: out[-1][1] = 0.0
    return out
Z = lambda d: [[0.0, 0.0], [d, 0.0]]
clips = {}
# ---- jump 1.6 s: crouch 0-0.40, takeoff 0.50, apex 0.80, landing 1.10, rest by 1.60 (pitch, + = forward)
JP = [(0.0, 0.0), (0.40, 0.15), (0.50, -0.12), (0.80, -0.04), (1.10, 0.0), (1.20, 0.20), (1.60, 0.0)]
jf = seg(JP); ex = [p[0] for p in JP]
clips['jump'] = {'fps': FPS, 'duration': 1.6, 'loop': False, 'interp': 'linear', 'keys': {'BodyLean': Z(1.6)},
  'viewKeys': {v: {'BodyLean': track(lambda t, s=s: s * jf(t), 1.6, ex)} for v, s in FWD.items()},
  'beats': {'crouch': [0.0, 0.40], 'takeoff': 0.50, 'apex': 0.80, 'landing': 1.10, 'rest': 1.60},
  'notes': 'profiles only (pitch): dip forward 0.15 (1.2 deg) at 0.40, head up/back -0.12 (-1.0 deg) at takeoff 0.50, easing to -0.04 at apex, 0 at landing 1.10, drop forward 0.20 (1.6 deg) at 1.20, rest by 1.60. Front/back: 0 (a dip is not a roll). The hair gets no lift/drop from the jump itself: stepHair has no root/vertical input (see report).'}
# ---- anger 3.0 s: set 0-0.40 (head drops forward), then HOLD 0.40 with a small breath to the end (matches Body's anger; no release)
def af(t):
    base = seg([(0.0, 0.0), (0.40, 0.40)])(t)
    br = 0.02 * math.sin(2 * math.pi * (t - 0.40) / 2.2) if t >= 0.40 else 0.0   # breath period 2.2 s, starts at 0 at 0.40
    return base + br * ss((t - 0.40) / 0.3)
clips['anger'] = {'fps': FPS, 'duration': 3.0, 'loop': False, 'interp': 'linear', 'endsAtRest': False, 'keys': {'BodyLean': Z(3.0)},
  'viewKeys': {v: {'BodyLean': track(lambda t, s=s: s * af(t), 3.0, [0.4], rest_end=False)} for v, s in FWD.items()},
  'beats': {'set': [0.0, 0.40], 'hold': [0.40, 3.0]},
  'notes': 'profiles: forward 0.40 (3.2 deg) by 0.40, then held with a +-0.02 (0.16 deg) breath through 3.0 s (no release; ends held, not at rest, matching Body). Front/back: 0 (forward/down is not expressible as a roll).'}
# ---- run 2.0 s loop: contacts every 0.333 s (k/3); stride = 0.667 s
C = [k / 3 for k in range(6)]; W = 0.25
def rp(t): return 0.08 * sum(pulse(t, c, W) for c in C)                       # pitch dip after each contact, peak +0.125 s
def rr(t): return 0.05 * sum((-1) ** k * pulse(t, c, W) for k, c in enumerate(C))  # roll toward alternating stance side
exr = [round(c + W * q, 4) for c in C for q in (0, 0.5, 1)]
clips['run'] = {'fps': FPS, 'duration': 2.0, 'loop': True, 'interp': 'linear', 'keys': {'BodyLean': track(rr, 2.0, exr)},
  'viewKeys': dict({v: {'BodyLean': track(lambda t, s=s: s * rp(t), 2.0, exr)} for v, s in FWD.items()},
                   back={'BodyLean': track(lambda t: -rr(t), 2.0, exr)}),   # seen from behind: mirrored roll
  'beats': {'contacts': [round(c, 4) for c in C], 'stride': 0.667},
  'notes': 'profiles: forward dip 0.08 (0.64 deg) peaking 0.125 s after each contact, 0 at every contact. front: roll 0.05 (0.4 deg) alternating sides per contact (+ at 0, 0.667, 1.333; - at 0.333, 1.0, 1.667); back: the same roll with the sign flipped (mirrors the front, seen from behind). Starts/ends at 0, seamless loop. Sign of the front roll vs stance foot is a guess; flip if Body\'s run loads the other foot first.'}
for c in clips.values():
    pk = 0.0
    for ks in [c['keys']['BodyLean']] + [vv['BodyLean'] for vv in c['viewKeys'].values()]:
        pk = max(pk, max(abs(x[1]) for x in ks)); assert ks[0][1] == 0 and ks[-1][0] == c['duration'] and (ks[-1][1] == 0 or c is clips['anger'])
    c['peakAbs'] = {'BodyLean': round(pk, 4)}; assert pk <= 1.0
out = {'format': 'shadowveil idle clips v1 (same schema as body_tools/idle/idle_clips.json)',
       'spec': 'value(t) = linear interpolation of keys[param] (viewKeys[view][param] overrides for that view); params not listed stay at their default',
       'units': 'rig param units (BodyLean x 8 deg; front/back = roll, profiles = pitch, left forward = -1, right forward = +1)',
       'combine': 'head offsets: ADD to Body\'s BodyLean from body_tools/actions/<clip>.json and clamp to [-1,1]; the renderer has no separate head param',
       'generator': 'python3 hair/actions/make_hair_actions.py', 'clips': clips}
dst = f'{HERE}/hair_actions.json'; json.dump(out, open(dst + '.tmp', 'w'), separators=(',', ':')); os.replace(dst + '.tmp', dst)
print(dst, os.path.getsize(dst), {n: c['peakAbs'] for n, c in clips.items()})
