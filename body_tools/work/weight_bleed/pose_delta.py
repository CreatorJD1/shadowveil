# Base Body weight_bleed: per pose, LBS position delta (px) of every vertex, live skin.json vs staged candidate (read-only)
import sys, json, numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('qg', '/workspace/shadowveil/rig/qa_gates.py'); Q = importlib.util.module_from_spec(spec); spec.loader.exec_module(Q)
view, cand = sys.argv[1], sys.argv[2]
a = json.load(open(Q.P('views', view, 'body', 'skin.json'))); b = json.load(open(cand)); bones = a['bones']
V = np.asarray(a['vertices'], float); Wa = Q.dense_w(a['weights'], len(bones)); Wb = Q.dense_w(b['weights'], len(bones))
ch = np.nonzero(np.abs(Wa - Wb).max(1) > 1e-9)[0]
out = {'changed_vertices': ch.tolist(), 'xy': V[ch].tolist(), 'deg': {x['name']: [Q.body_angle(x, 1), Q.body_angle(x, -1)] for x in bones if x.get('param')}, 'poses': {}}
for nm, ang in Q.poses_for(bones).items():
    M = Q.bone_mats(bones, ang); d = np.linalg.norm(Q.lbs_fast(V, Wa, M) - Q.lbs_fast(V, Wb, M), axis=1)
    out['poses'][nm] = {'max_px': round(float(d.max()), 3), 'n_gt_0.5': int((d > 0.5).sum()), 'n_gt_1': int((d > 1).sum())}
print(json.dumps({k: v for k, v in out.items() if k != 'xy'}, indent=0)[:3000])
json.dump(out, open(cand.replace('.json', '_posedelta.json'), 'w'), indent=1)
