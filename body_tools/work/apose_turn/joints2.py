# Joint proxies v2. A turn about the vertical axis keeps y, so joint y's are fixed in rig scale
# (front-half: from f001, calibrated to our apose rig ratios; back-half: from f109 with our back ratios);
# per-frame only x is measured: limb centreline x of the separated limb run at that y (null if merged).
import json, os, numpy as np, sys
sys.path.insert(0, '.')
from measure import mask_of, measure, runs
FR = '/workspace/shadowveil/reference/apose_turn/frames/f{:03d}.png'
J1 = json.load(open('joints_all.json')); T = json.load(open('turn_measure.json'))
Y = {}
for key, f in (('front', 1), ('back', 109)):
    j = [x for x in J1['frames'] if x['f'] == f][0]['joints']
    Y[key] = {n: round((j[n+'_R'][1] + j[n+'_L'][1]) / 2, 1) for n in ('shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle')}
Y['front']['thigh'] = Y['back']['thigh'] = None
def row_runs(m, y): return [r for r in runs(m[int(round(y))]) if r[1] - r[0] >= 3]
out = []
for r in T['frames']:
    f = int(r['f']); th = r['angle_best']; m = mask_of(FR.format(f)); o = measure(m)
    prof = abs(((th + 90) % 180) - 90) > 60; foot_t = 1681 if prof else 1682
    s = (foot_t - 40) / o['H']; ny = lambda yr: o['top'] + (yr - 40) / s; rx = lambda x: round(681.5 + (x - o['cx']) * s, 1)
    yy = Y['back' if 90 < th < 270 else 'front']; J = {}
    tor = [row_runs(m, ny(yy['elbow']))]  # not used; torso run per row found below
    def torso_run(y):
        rr = row_runs(m, y); c = o['cx']
        inside = [q for q in rr if q[0] <= c <= q[1]]
        return inside[0] if inside else None, rr
    for n in ('shoulder', 'elbow', 'wrist'):
        t, rr = torso_run(ny(yy[n]))
        if n == 'shoulder':
            # shoulder: outer edge of the torso/shoulder run at shoulder height, inset like our rig (front inset = 22 rig px)
            J['shoulder_R'] = [rx(t[0]) + 22 if t else None, yy[n]]; J['shoulder_L'] = [rx(t[1]) - 22 if t else None, yy[n]]
            continue
        left = [q for q in rr if t and q[1] < t[0]]; right = [q for q in rr if t and q[0] > t[1]]
        J[n+'_R'] = [rx((left[-1][0] + left[-1][1]) / 2), yy[n]] if left else None
        J[n+'_L'] = [rx((right[0][0] + right[0][1]) / 2), yy[n]] if right else None
    lo = o['cx'] - 0.2 * o['H']; hi = o['cx'] + 0.2 * o['H']
    for n, yr in (('hip', 40 + 0.53 * 1642), ('knee', yy['knee']), ('ankle', yy['ankle'])):
        rr = [q for q in row_runs(m, ny(yr)) if lo < (q[0] + q[1]) / 2 < hi]
        yv = yy['hip'] if n == 'hip' else yy[n]
        if len(rr) >= 2: J[n+'_R'] = [rx((rr[0][0] + rr[0][1]) / 2), yv]; J[n+'_L'] = [rx((rr[-1][0] + rr[-1][1]) / 2), yv]
        else: J[n+'_R'] = J[n+'_L'] = None; J[n+'_merged_x'] = rx((rr[0][0] + rr[0][1]) / 2) if rr else None
    for k in list(J):
        if isinstance(J[k], list) and J[k][0] is None: J[k] = None
    out.append({'f': f, 'angle_best': th, 'joints': J})
res = {'method': 'y fixed per half (orthographic turn keeps y); x measured; hip x = thigh centre at u=0.53; shoulder x = torso-run edge +/-22 px inset', 'joint_y': Y, 'frames': out}
json.dump(res, open('j2.tmp', 'w'), indent=0); os.replace('j2.tmp', 'joints_rig.json')
print(Y)
