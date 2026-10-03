# forearm sub-rotation (deg about the elbow) that best moves each wrist by the measured handoff arm offset (rel. torso)
import json, math
ROOT = '/workspace/shadowveil'; M = json.load(open('handoff_arm_offsets.json')); out = {'_note': '', 'forearm': {}, 'fit': {}}
for v, r in M.items():
    sk = {b['name']: b for b in json.load(open(f'{ROOT}/views/{v}/body/skin.json'))['bones']}
    for s in ('L', 'R'):
        k = f'forearm_{s}'
        if k not in r: continue
        b = sk[k]; ex, ey = b['pivot']; wp = b['wristPivot']; wx, wy = wp['x'] - ex, wp['y'] - ey
        d = r[k]['rel_torso']; tx, ty = wx + d['dx'], wy + d['dy']
        th = math.degrees(math.atan2(wx*ty - wy*tx, wx*tx + wy*ty))
        c, sn = math.cos(math.radians(th)), math.sin(math.radians(th)); nx, ny = c*wx - sn*wy, sn*wx + c*wy
        out['forearm'].setdefault(k, {})[v] = round(th, 2)
        out['fit'][f'{v}/{k}'] = {'elbow': [ex, ey], 'wristPivot': [wp['x'], wp['y']], 'want_wrist_move': d, 'got_wrist_move': [round(nx - wx, 1), round(ny - wy, 1)],
                                  'residual_px': round(math.hypot(tx - nx, ty - ny), 1), 'ncc': r[k]['ncc']}
print(json.dumps(out, indent=1)); json.dump(out, open('armsub_fit.json', 'w'), indent=1)
