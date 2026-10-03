# 2-bone fit (upperArm about the shoulder + forearm about the elbow) for the measured handoff wrist offsets; also forearm-only.
import json, numpy as np
ROOT = '/workspace/shadowveil'; M = json.load(open('handoff_arm_offsets.json')); out = {'table': {}, 'fit': {}}
def R(t): c, s = np.cos(t), np.sin(t); return c, s
for v, r in M.items():
    sk = {b['name']: b for b in json.load(open(f'{ROOT}/views/{v}/body/skin.json'))['bones']}
    for sd in ('L', 'R'):
        k = f'forearm_{sd}'
        if k not in r: continue
        S = np.array(sk[f'upperArm_{sd}']['pivot'], float); E = np.array(sk[k]['pivot'], float); wp = sk[k]['wristPivot']; Wr = np.array([wp['x'], wp['y']])
        d = r[k]['rel_torso']; T = Wr + [d['dx'], d['dy']]
        a = np.radians(np.arange(-30, 30.01, 0.1)); A1, A2 = np.meshgrid(a, a, indexing='ij')
        c1, s1 = np.cos(A1), np.sin(A1); e = E - S; Ex = S[0] + c1*e[0] - s1*e[1]; Ey = S[1] + s1*e[0] + c1*e[1]
        w = Wr - E; c12, s12 = np.cos(A1 + A2), np.sin(A1 + A2); Wx = Ex + c12*w[0] - s12*w[1]; Wy = Ey + s12*w[0] + c12*w[1]
        res = np.hypot(Wx - T[0], Wy - T[1]); cost = res + 0.05*(np.abs(np.degrees(A1)) + np.abs(np.degrees(A2)))
        i, j = np.unravel_index(np.argmin(cost), cost.shape)
        fo = np.argmin(res[a.size//2 if False else np.argmin(np.abs(a)), :])
        out['table'].setdefault(f'upperArm_{sd}', {})[v] = round(float(np.degrees(a[i])), 1)
        out['table'].setdefault(k, {})[v] = round(float(np.degrees(a[j])), 1)
        z = np.argmin(np.abs(a))
        out['fit'][f'{v}/{sd}'] = {'want_wrist_move': d, 'ncc': r[k]['ncc'], 'two_bone_residual_px': round(float(res[i, j]), 1),
                                   'two_bone_deg': [round(float(np.degrees(a[i])), 1), round(float(np.degrees(a[j])), 1)],
                                   'forearm_only_deg': round(float(np.degrees(a[fo])), 1), 'forearm_only_residual_px': round(float(res[z, fo]), 1)}
print(json.dumps(out, indent=1)); json.dump(out, open('armsub_fit.json', 'w'), indent=1)
