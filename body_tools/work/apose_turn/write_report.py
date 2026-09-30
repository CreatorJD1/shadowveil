import json, os, csv
T = json.load(open('turn_measure.json')); JR = json.load(open('joints_rig.json')); O = json.load(open('ours_measure.json')); P = json.load(open('ours_pivots.json'))
F = {int(r['f']): r for r in T['frames']}; JF = {x['f']: x['joints'] for x in JR['frames']}
N = ['shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle']; PART = {'shoulder': 'upperArm', 'elbow': 'forearm', 'wrist': 'wrist', 'hip': 'thigh', 'knee': 'shin', 'ankle': 'foot'}
# rig reference by viewer side: front half vl = char R (apose *_R); back half vl = char L (back *_L)
def rigref(view, vs):
    ch = ({'vl': 'R', 'vr': 'L'} if view == 'apose' else {'vl': 'L', 'vr': 'R'})[vs]
    return {n: P[view][PART[n] + '_' + ch] for n in N}
def vid(f, vs):
    j = JF[f]; s = 'R' if vs == 'vl' else 'L'; return {n: j.get(n + '_' + s) for n in N}
OFF = {}
for half, f0, view in (('front', 1, 'apose'), ('back', 109, 'back')):
    for vs in ('vl', 'vr'):
        v = vid(f0, vs); r = rigref(view, vs)
        OFF[(half, vs)] = {n: ((r[n][0] - v[n][0]) if v[n] else 0.0) for n in N}
def cal(f):
    th = F[f]['angle_best']; half = 'back' if 90 < th < 270 else 'front'; out = {}
    for vs in ('vl', 'vr'):
        v = vid(f, vs)
        for n in N: out[f'{n}_{vs}'] = None if v[n] is None else [round(v[n][0] + OFF[(half, vs)][n], 1), v[n][1]]
    return out
# per-frame CSV
with open('turn_table.csv.tmp', 'w', newline='') as fh:
    w = csv.writer(fh); ks = ['shoulder_w', 'bust_w', 'waist_w', 'hip_w', 'knee_w', 'ankle_w', 'bust_y', 'waist_y', 'hip_y', 'leg_len']
    w.writerow(['frame', 'angle_best', 'angle_range_folded', 'raw_top', 'raw_foot', 'raw_H', 'foot_target'] + ks + ['arm_reach_vl', 'arm_reach_vr', 'components', 'aa_band', 'skin_dark_frac'])
    for f in sorted(F):
        r = F[f]; n = r['norm']; ar = n.get('arms', {})
        w.writerow([f'f{f:03d}', r['angle_best'], r['angle_range_abs'], r['raw']['top'], r['raw']['foot'], r['raw']['H'], n['foot']] + [n.get(k) for k in ks] +
                   [ar.get('R', {}).get('reach'), ar.get('L', {}).get('reach'), r['q']['components'], r['q']['aa_band_px_per_edge_px'], r['q']['skin_dark_frac']])
os.replace('turn_table.csv.tmp', 'turn_table.csv')
CAND = [(23, '30'), (33, '45'), (41, '60'), (85, '135'), (129, '225 (mirror of 135)'), (183, '300 (mirror of 60)'), (191, '315 (mirror of 45)'), (203, '330 (mirror of 30)')]
H0 = F[1]['raw']['H']; F0 = F[1]['raw']['foot']
def jt(f):
    c = cal(f); return ' | '.join(f"{n[:2]} {('%.0f,%.0f' % tuple(c[n+'_vl'])) if c[n+'_vl'] else '–'} / {('%.0f,%.0f' % tuple(c[n+'_vr'])) if c[n+'_vr'] else '–'}" for n in N)
cj = {}
lines = []
for f, tgt in CAND:
    r = F[f]; cj[f'f{f:03d}'] = {'target_deg': tgt, 'angle_best': r['angle_best'], 'angle_range_folded': r['angle_range_abs'],
        'raw_H_vs_front_pct': round(100 * (r['raw']['H'] - H0) / H0, 2), 'raw_foot_vs_front_px_video': r['raw']['foot'] - F0,
        'raw_foot_vs_front_px_rig': round((r['raw']['foot'] - F0) * 1642 / H0, 1), 'quality': r['q'],
        'joints_rig_viewerLeft_viewerRight': {g: cal(g) for g in (f - 3, f, f + 3)}}
json.dump(cj, open('c.tmp', 'w'), indent=1); os.replace('c.tmp', 'candidates/candidates.json')
json.dump({f'f{f:03d}': cal(f) for f in sorted(F)}, open('j.tmp', 'w')); os.replace('j.tmp', 'joints_rig_calibrated.json')
print(json.dumps({k: {kk: v[kk] for kk in ('angle_best', 'angle_range_folded', 'raw_H_vs_front_pct', 'raw_foot_vs_front_px_rig')} for k, v in cj.items()}))
for f, _ in CAND:
    for g in (f - 3, f, f + 3): print(f'f{g:03d}', F[g]['angle_best'], jt(g))
