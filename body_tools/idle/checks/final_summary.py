import json, math, os, numpy as np
from PIL import Image
ID = os.environ.get('FRAMES_ROOT', '/workspace/shadowveil/rig/previews/idle/frames')
P = json.load(open('/workspace/shadowveil/body_tools/work/apose_turn/ours_pivots.json'))
def posed(view, fb, side):
    el = P[view]['forearm_' + side]; wr = P[view]['wrist_' + side]; x, y, a = fb['forearm_' + side]; r = math.radians(a)
    dx, dy = wr[0] - el[0], wr[1] - el[1]; return (x, y), (x + dx * math.cos(r) - dy * math.sin(r), y + dx * math.sin(r) + dy * math.cos(r))
def feet_rest(name):
    A = np.array(Image.open(f'{ID}/{name}/rest.png'))[..., 3] >= 128; meta = json.load(open(f'{ID}/{name}/meta.json'))
    pelx = [b for b in meta['info']['bones'] if b['id'] == 'pelvis'][0]['pivot'][0]; o = {}
    for s, sl in (('xlo', slice(0, int(pelx))), ('xhi', slice(int(pelx), A.shape[1]))):
        r = np.nonzero(A[:, sl].any(1))[0]; o[s] = int(r.max())
    return o, int(np.nonzero(A.any(1))[0].max())
res = {}
for c in ('idle_arm_settle', 'idle_weight_shift', 'idle_arm_sway'):
    for v in ('apose', 'tpose', 'left', 'right', 'back'):
        n = f'keys_{c}_{v}'
        if not os.path.exists(n + '.check.json'): continue
        d = json.load(open(n + '.check.json')); R = d['rows']; meta = json.load(open(f'{ID}/{n}/meta.json'))
        fr, restline = feet_rest(n); per = []
        for r in R:
            fb = meta['frames'][r['f']]['bones']; hz = []
            for s in 'LR':
                e, w = posed(v, fb, s); hz.append((e, w))
            def handzone(cm):
                cx, cy = (cm[1] + cm[3]) / 2, (cm[2] + cm[4]) / 2
                return any(math.hypot(cx - w[0], cy - w[1]) < 110 and math.hypot(cx - e[0], cy - e[1]) > math.hypot(w[0] - e[0], w[1] - e[1]) for e, w in hz)
            bh = [cm for cm in r['holes_body_comps'] if not handzone(cm)]; bt = [cm for cm in r['tears_body_comps'] if not handzone(cm)]
            lift = {s: (fr[s] - r['foot'][s]['y']) if r['foot'][s] else None for s in r['foot']}
            line = max(r['foot'][s]['y'] for s in r['foot'] if r['foot'][s])
            per.append({'f': r['f'], 'hole': sum(x[0] for x in bh), 'holec': bh[:1], 'tear': sum(x[0] for x in bt), 'tearc': bt[:1], 'navy': r['navy_interior_new'],
                        'lift': max(v2 for v2 in lift.values() if v2 is not None), 'lineoff': line + 1 - d['foot_target'], 'dx': max(abs(r['foot'][s]['dx']) for s in r['foot'] if r['foot'][s]),
                        'axis': r['headAxis']})
        worst = lambda k: sorted(per, key=lambda x: -x[k])[:3]
        res[n] = {'rest_line': restline + 1, 'target': d['foot_target'],
                  'holes': [(x['f'], x['hole'], x['holec']) for x in worst('hole') if x['hole'] > 0], 'hole_frames': sum(x['hole'] > 0 for x in per),
                  'tears': [(x['f'], x['tear'], x['tearc']) for x in worst('tear') if x['tear'] > 0], 'tear_frames': sum(x['tear'] > 0 for x in per),
                  'navy_new': [(x['f'], x['navy']) for x in worst('navy')],
                  'foot_lift_max': [(x['f'], x['lift']) for x in worst('lift')][:1], 'foot_dx_max': [(x['f'], x['dx']) for x in worst('dx')][:1],
                  'line_vs_target_at_rest': restline + 1 - d['foot_target'], 'axis_frames': [x['f'] for x in per if x['axis']]}
        print(n, json.dumps(res[n]))
json.dump(res, open('final_summary.json.tmp', 'w'), indent=1); os.replace('final_summary.json.tmp', 'final_summary.json')
