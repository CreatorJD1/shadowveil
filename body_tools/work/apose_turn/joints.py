# Silhouette joint proxies in rig scale. Elbow/wrist/knee/ankle cannot be seen in a silhouette:
# x comes from the measured limb centreline; the position along the limb uses our own rig's ratios
# (calibrated on views/apose and views/back). Shoulder/hip = armpit/crotch + our rig offset.
import sys, json, math, numpy as np
sys.path.insert(0, '.')
from measure import mask_of, measure, runs, ROOT
from PIL import Image
FR = '/workspace/shadowveil/reference/apose_turn/frames/f{:03d}.png'
PIV = json.load(open('ours_pivots.json'))

def arm_line(m, o, side):
    a = o['arms'].get(side)
    if not a: return None
    ax, ay = a['armpit']; tx, ty = a['tip']; L = math.hypot(tx-ax, ty-ay)
    ux, uy = (tx-ax)/L, (ty-ay)/L
    ys, xs = np.nonzero(m[int(ay):int(ty)+1]); ys = ys + int(ay)
    s = (xs-ax)*ux + (ys-ay)*uy; p = (xs-ax)*(-uy) + (ys-ay)*ux
    # keep pixels on the arm side of the armpit, within a band around the armpit->tip line
    keep = (s > 0) & (np.abs(p) < 40 * o['H'] / 1642) & (((xs < ax) if side == 'R' else (xs > ax)))
    xs, ys, s = xs[keep], ys[keep], s[keep]
    def at(frac):
        t = frac * L; w = np.abs(s - t) < 4
        if w.sum() < 3: return None
        return [float(xs[w].mean()), float(ys[w].mean())]
    return {'armpit': [ax, ay], 'L': L, 'at': at}

def leg_centres(m, y):
    rr = [r for r in runs(m[int(y)]) if r[1]-r[0] > 3]
    return [(r[0]+r[1])/2 for r in rr]

def raw_joints(m, o, cal):
    H = o['H']; top = o['top']; J = {}
    for side in ('R', 'L'):
        al = arm_line(m, o, side)
        if al:
            ax, ay = al['armpit']; sg = -1 if side == 'R' else 1
            J['shoulder_'+side] = [ax + sg*cal['sh_dx']*H, ay + cal['sh_dy']*H]
            J['elbow_'+side] = al['at'](cal['f_elbow']); J['wrist_'+side] = al['at'](cal['f_wrist'])
        else:
            for k in ('shoulder_', 'elbow_', 'wrist_'): J[k+side] = None
    cy = o.get('crotch_y')
    hy = (cy - cal['hip_dy']*H) if cy else top + cal['hip_u']*H
    ky = top + cal['knee_u']*H; ay = top + cal['ankle_u']*H
    for nm, y, yy in (('hip', hy, (cy + 0.01*H) if cy else hy), ('knee', ky, ky), ('ankle', ay, ay)):
        c = leg_centres(m, yy)
        if len(c) >= 2:
            J[nm+'_R'] = [c[0], y]; J[nm+'_L'] = [c[-1], y]   # R = viewer-left (as in our rig for front)
        elif len(c) == 1:
            J[nm+'_merged'] = [c[0], y]
    return J

def to_rig(J, o, top_t=40, foot_t=1682, cx_t=681.5):
    s = (foot_t-top_t)/o['H']
    return {k: (None if v is None else [round(cx_t + (v[0]-o['cx'])*s, 1), round(top_t + (v[1]-o['top'])*s, 1)]) for k, v in J.items()}, s

def calibrate(view='apose'):
    m = np.array(Image.open(f'{ROOT}/views/{view}/base.png').convert('RGBA'))[..., 3] > 0; o = measure(m); P = PIV[view]; H = o['H']
    fr = 'R' if view == 'apose' else 'L'   # our part on viewer-left
    ax, ay = o['arms']['R']['armpit']; tx, ty = o['arms']['R']['tip']; L = math.hypot(tx-ax, ty-ay)
    proj = lambda p: ((p[0]-ax)*(tx-ax) + (p[1]-ay)*(ty-ay)) / L / L
    sh = P['upperArm_'+fr]
    return {'sh_dx': abs(sh[0]-ax)/H, 'sh_dy': (sh[1]-ay)/H, 'f_elbow': proj(P['forearm_'+fr]), 'f_wrist': proj(P['wrist_'+fr]),
            'hip_dy': (o['crotch_y'] - P['thigh_'+fr][1])/H, 'hip_u': (P['thigh_'+fr][1]-o['top'])/H,
            'knee_u': (P['shin_'+fr][1]-o['top'])/H, 'ankle_u': (P['foot_'+fr][1]-o['top'])/H}, m, o

if __name__ == '__main__':
    CAL = {}; OURS = {}
    for v in ('apose', 'back'):
        c, m, o = calibrate(v); CAL[v] = c
        OURS[v] = {'proxy': to_rig(raw_joints(m, o, c), o, 40, o['foot'], o['cx'])[0], 'rig': PIV[v]}
    print(json.dumps(CAL, indent=0))
    d = json.load(open('turn_measure.json'))
    out = []
    for r in d['frames']:
        f = int(r['f']); m = mask_of(FR.format(f)); o = measure(m); th = r['angle']
        c = CAL['back'] if 90 < th < 270 else CAL['apose']
        prof = abs(((th + 90) % 180) - 90) > 60
        J, s = to_rig(raw_joints(m, o, c), o, 40, 1681 if prof else 1682)
        # second angle cue: leg-centre separation at mid-thigh vs front
        lc = leg_centres(m, o['top'] + 0.60*o['H']); sep = (lc[-1]-lc[0])*s if len(lc) >= 2 else 0.0
        out.append({'f': f, 'angle': th, 'leg_sep_rig': round(sep, 1), 'joints': J})
    sep0 = out[0]['leg_sep_rig']
    for x in out: x['angle_legcue_abs'] = round(math.degrees(math.acos(min(1, x['leg_sep_rig']/sep0))), 1) if sep0 else None
    json.dump({'calibration': CAL, 'ours': OURS, 'frames': out}, open('joints_all.json.tmp', 'w'), indent=0)
    import os; os.replace('joints_all.json.tmp', 'joints_all.json')
    for x in out[::8]: print(x['f'], x['angle'], x['leg_sep_rig'], x['angle_legcue_abs'])
