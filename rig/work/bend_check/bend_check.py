#!/usr/bin/env python3
"""--bend-check (STAGED, scope-cut 03:53 PT): measures ONLY the 4 defects in Base Body's 045/315 before/after tiles, on the same pieces and setup
(body_tools/work/diag_body = OLD, body_tools/work/diag_body_fix = NEW; posed with Body's own posekit.pose: child subtree rotated about the joint pivot,
nearest, teammates as green cover). Read-only on Body's files; writes rig/work/bend_check/ only. Rig untouched.
  pieces: waist = torso+pelvis only; hips = torso+pelvis+legs (arms/hands hang over the hips in these views); shoulders/elbows and the neck =
         all pieces + teammates as cover (hair covers the nape legitimately).
  1 waist_side_step_px : waist joint. Per side (left/right silhouette edge), over rows within 35 px of the waist pivot: the largest jump in the
                         edge x between consecutive rows (a step in the side outline). Reported per side, posed minus her rest value.
  2 hip_crease_dent_px : hip_L/hip_R. Deepest notch of the posed silhouette vs its closing with an 8 px disk, inside the joint band; also notch area px.
  3 jagged_spikes      : shoulder_L/R, elbow_L/R. Outline points in the band whose direction turns > 50 deg over a 4 px chord either side
                         (corner spikes), plus the largest outline deviation from its sigma-3 smoothed path (px). Posed minus rest.
  4 head_neck_gap_px   : head_neck + neck_base. Background px the head/neck rotation opens INSIDE her figure near the neck seam: px in the
                         closing (6 px disk) of the posed silhouette that are not covered, minus the same at rest; plus the widest gap (px).
usage: python3 rig/qa_gates.py --bend-check [--bend-port 8793]   or   python3 rig/work/bend_check/bend_check.py [--angles 045,315] [--live apose]
Live front baseline: rig/work/bend_check/render_live.js renders views/apose at each joint 0/+-1 (needs a local http server on the repo root)."""
import sys, os, json
T = '/workspace/shadowveil/body_tools/work/diag_body_fix/tools'; sys.path.insert(0, T)
_cwd = os.getcwd(); os.chdir(T)
from posekit import *          # H, W, ORIG, FIX, load_set, pose, band_of, disk, ctx, np, ndi, cv2, Image  (Body's, read-only)
os.chdir(_cwd)
from PIL import ImageDraw
OUT = '/workspace/shadowveil/rig/work/bend_check'; ROOTD = '/workspace/shadowveil'
def sil(comp): return comp[..., 3] > 0
def waist_step(S, c):
    out = {}
    ys = range(int(c[1]) - 35, int(c[1]) + 36)
    for side in ('left', 'right'):
        xs = []
        for y in ys:
            row = np.nonzero(S[y, max(0, int(c[0]) - 140):min(S.shape[1], int(c[0]) + 140)])[0]
            xs.append(np.nan if not len(row) else (row.min() if side == 'left' else row.max()))
        d = np.abs(np.diff(np.array(xs, float))); out[side] = float(np.nanmax(d)) if np.isfinite(d).any() else 0.0
        out[side + '_y'] = int(list(ys)[int(np.nanargmax(d))]) if np.isfinite(d).any() else None
    return out
def dent(S, band, r=8):
    cl = cv2.morphologyEx(S.astype(np.uint8), cv2.MORPH_CLOSE, disk(r)) > 0; n = cl & ~S & band
    return float(ndi.distance_transform_edt(cl & ~S)[band].max()) if n.any() else 0.0, int(n.sum()), n
def jag(S, band):
    cs, _ = cv2.findContours(S.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); spikes = 0; dev = 0.0; pts = []
    for cc in cs:
        p = cc[:, 0, :].astype(float); n = len(p)
        if n < 40: continue
        a = p - np.roll(p, 4, 0); b = np.roll(p, -4, 0) - p
        ang = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))))
        sm = np.stack([ndi.gaussian_filter1d(p[:, 0], 3, mode='wrap'), ndi.gaussian_filter1d(p[:, 1], 3, mode='wrap')], 1); dv = np.hypot(*(p - sm).T)
        xi, yi = p[:, 0].astype(int).clip(0, S.shape[1] - 1), p[:, 1].astype(int).clip(0, S.shape[0] - 1); inb = band[yi, xi]
        sp = inb & (ang > 50) & (ang >= np.roll(ang, 1)) & (ang >= np.roll(ang, -1))
        spikes += int(sp.sum()); pts += [tuple(map(int, q)) for q in p[sp]]
        if inb.any(): dev = max(dev, float(dv[inb].max()))
    return spikes, round(dev, 2), pts
def gap(S, band):
    cl = cv2.morphologyEx(S.astype(np.uint8), cv2.MORPH_CLOSE, disk(6)) > 0; g = cl & ~S & band
    return int(g.sum()), (float(ndi.distance_transform_edt(cl & ~S)[band].max()) * 2 if g.any() else 0.0), g
def tile(comp, c, R, marks=None, pts=()):
    a = comp[..., 3:] / 255.; t = (comp[..., :3] * a + np.array([255, 255, 255]) * (1 - a)).clip(0, 255).astype(np.uint8)
    if marks is not None: t[marks] = (255, 0, 255)
    x0, y0 = int(c[0]) - R, int(c[1]) - R; o = np.full((2 * R, 2 * R, 3), 255, np.uint8)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + 2 * R, t.shape[1]), min(y0 + 2 * R, t.shape[0]); o[ya - y0:yb - y0, xa - x0:xb - x0] = t[ya:yb, xa:xb]
    for x, y in pts:
        if 0 <= x - x0 < 2 * R and 0 <= y - y0 < 2 * R: o[max(0, y - y0 - 1):y - y0 + 2, max(0, x - x0 - 1):x - x0 + 2] = (255, 0, 0)
    return o
def run_diag(ANG):
  REP = {'doc': __doc__, 'angles': {}}; tiles = []
  for ang in ANG:
      sets = {'old': load_set(f'{ORIG}/{ang}'), 'new': load_set(f'{FIX}/{ang}')}; R = {}
      def run(jn, fn, keep=None, team=True):
          R[jn] = {'pieces': keep or 'all', 'teammates_as_cover': team}
          for w, (pj0, img) in sets.items():
              pj = dict(pj0, layerOrder_backToFront=[k for k in pj0['layerOrder_backToFront'] if keep is None or k in keep])
              c = pj['joints'][jn]['pivot']; band, _, r = band_of(pj, jn); R[jn][w] = {}
              base = None
              for th in (0, -25, 25):
                  comp = pose(ang, pj, img, jn, th, team=team); m, mk, pts = fn(sil(comp), band, c)
                  if th == 0: base = m
                  R[jn][w][f'{th:+d}'] = m
                  if th: R[jn][w][f'{th:+d}_vs_rest'] = {k: (round(v - base[k], 2) if isinstance(v, (int, float)) and isinstance(base.get(k), (int, float)) else None) for k, v in m.items()}
                  if th:
                      full = pose(ang, pj0, img, jn, th)   # tile shows her full posed figure; marks come from the measured subset
                      tiles.append((ang, jn, w, th, m, tile(full, sets['old'][0]['joints'][jn]['pivot'], int(r + 20), mk, pts)))
      run('waist', lambda S, b, c: (waist_step(S, c), None, ()), keep=['torso', 'pelvis'], team=False)
      for jn in ('hip_L', 'hip_R'):
          def f(S, b, c):
              d, a, n = dent(S, b); return {'dent_px': round(d, 2), 'notch_px': a}, n, ()
          run(jn, f, keep=['torso', 'pelvis', 'thigh_L', 'thigh_R', 'shin_L', 'shin_R', 'foot_L', 'foot_R'], team=False)
      for jn in ('shoulder_L', 'shoulder_R', 'elbow_L', 'elbow_R'):
          def f(S, b, c):
              s, dv, pts = jag(S, b); return {'spikes': s, 'max_dev_px': dv}, None, pts
          run(jn, f)
      for jn in ('head_neck', 'neck_base'):
          def f(S, b, c):
              n, wd, g = gap(S, b); return {'gap_px': n, 'gap_width_px': round(wd, 1)}, g, ()
          run(jn, f)
      REP['angles'][ang] = R
  # cross-check vs Body's own metrics_before_after.json (step_px / dent_px / lump_px on the same tiles)
  for ang in ANG:
      try: BM = json.load(open(f'{FIX}/{ang}/metrics_before_after.json'))['joints']
      except Exception: BM = {}
      REP['angles'][ang]['_body_metrics'] = {jn: {t: {w: BM[jn][t][w] for w in ('old', 'new')} for t in ('-25', '+25')} for jn in REP['angles'][ang] if jn in BM}
  json.dump(REP, open(f'{OUT}/bend_check_diag.json', 'w'), indent=1)
  # sheet: one row per (angle, joint, angle), OLD | NEW
  TW = 200; rows = {}
  for ang, jn, w, th, m, t in tiles: rows.setdefault((ang, jn, th), {})[w] = (m, t)
  keys = list(rows); sheet = Image.new('RGB', (2 * TW + 330, 24 + len(keys) * (TW + 6)), 'white'); D = ImageDraw.Draw(sheet)
  D.text((6, 6), 'bend-check (staged): OLD diag_body | NEW diag_body_fix, +-25 deg, Body posekit. magenta = notch/gap px, red = outline spikes', fill=(0, 0, 0))
  for i, k in enumerate(keys):
      y = 24 + i * (TW + 6)
      for j, w in enumerate(('old', 'new')):
          if w in rows[k]: sheet.paste(Image.fromarray(rows[k][w][1]).resize((TW, TW), Image.NEAREST), (j * (TW + 4), y))
      txt = f'{k[0]} {k[1]} {k[2]:+d}\n' + '\n'.join(f"{w}: " + ', '.join(f'{a}={b}' for a, b in rows[k][w][0].items() if not a.endswith('_y')) for w in ('old', 'new') if w in rows[k])
      D.text((2 * TW + 12, y + 4), txt, fill=(0, 0, 0))
  sheet.save(f'{OUT}/bend_check_diag_sheet.png')
  for ang in ANG:
      for jn, d in REP['angles'][ang].items():
          if jn.startswith('_'): continue
          print(ang, jn, {w: {t: d[w][t] for t in ('+0', '-25', '+25')} for w in ('old', 'new')})
  return REP

# ---------------------------------------------------------------- live front rig baseline (browser renders from render_live.js, nearest)
def run_live(view='apose'):
    D = f'{OUT}/live'; sk = json.load(open(f'{ROOTD}/views/{view}/body/skin.json')); piv = {b['name']: b['pivot'] for b in sk['bones'] if b.get('pivot')}
    meta = json.load(open(f'{D}/{view}_meta.json')); neck = (meta['headPivot']['x'], meta['headPivot']['y'])
    J = {'waist': ('BodyLean', piv['torso'], 45, 'body'), 'hip_L': ('HipL', piv['thigh_L'], 45, 'body'), 'hip_R': ('HipR', piv['thigh_R'], 45, 'body'),
         'shoulder_L': ('ShoulderL', piv['upperArm_L'], 50, 'body'), 'shoulder_R': ('ShoulderR', piv['upperArm_R'], 50, 'body'),
         'elbow_L': ('ElbowL', piv['forearm_L'], 35, 'body'), 'elbow_R': ('ElbowR', piv['forearm_R'], 35, 'body'),
         'head_neck': ('HeadTilt', neck, 45, 'full'), 'head_nod': ('HeadNod', neck, 45, 'full')}
    LH, LW = 1739, 1365; YY, XX = np.mgrid[0:LH, 0:LW]; R = {'view': view, 'note': 'live rig, nearest; BodyLean is +-8 deg (live limit), other joints +-25 deg; body-only renders for waist/hips/shoulders/elbows, full (with hair) for the neck', 'joints': {}}; tiles = []
    for jn, (par, c, rad, solo) in J.items():
        S0 = np.asarray(Image.open(f'{D}/{view}__rest__{solo}.png'))[..., 3] > 0; edge = S0 & ndi.binary_dilation(~S0)
        ey, ex = np.nonzero(edge); dmin = float(np.hypot(ex - c[0], ey - c[1]).min()) if len(ex) else 0.0
        rad = max(rad, int(dmin + 25))   # the band always reaches her outline (pivots sit inside the limb)
        band = np.hypot(XX - c[0], YY - c[1]) <= rad; R['joints'][jn] = {'param': par, 'pivot': c, 'band_radius_px': rad}; base = None
        for tag in ('rest', par + '-1', par + '+1'):
            f = f'{D}/{view}__{tag}__{solo}.png'
            if not os.path.exists(f): continue
            comp = np.asarray(Image.open(f).convert('RGBA')); S = comp[..., 3] > 0
            if jn == 'waist': m, mk, pts = waist_step(S, c), None, ()
            elif jn.startswith('hip'): d, a, mk = dent(S, band); m, pts = {'dent_px': round(d, 2), 'notch_px': a}, ()
            elif jn.startswith(('shoulder', 'elbow')): sp, dv, pts = jag(S, band); m, mk = {'spikes': sp, 'max_dev_px': dv}, None
            else: n, wd, mk = gap(S, band); m, pts = {'gap_px': n, 'gap_width_px': round(wd, 1)}, ()
            if tag == 'rest': base = m
            R['joints'][jn][tag] = m
            if tag != 'rest' and base: R['joints'][jn][tag + '_vs_rest'] = {k: round(v - base[k], 2) for k, v in m.items() if isinstance(v, (int, float)) and isinstance(base.get(k), (int, float))}
            if tag != 'rest':
                full = np.asarray(Image.open(f'{D}/{view}__{tag}__full.png').convert('RGBA'))
                a = full[..., 3:] / 255.; t = (full[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
                if mk is not None: t[mk] = (255, 0, 0) if False else (255, 0, 255)
                for x, y in pts: t[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (255, 0, 0)
                x0, y0 = int(c[0]) - rad - 20, int(c[1]) - rad - 20; tiles.append((jn, tag, m, t[max(0, y0):y0 + 2 * (rad + 20), max(0, x0):x0 + 2 * (rad + 20)]))
    json.dump(R, open(f'{OUT}/bend_check_live_{view}.json', 'w'), indent=1)
    TW = 200; sheet = Image.new('RGB', (2 * (TW + 4) + 360, 24 + ((len(tiles) + 1) // 2) * (TW + 6)), 'white'); Dr = ImageDraw.Draw(sheet)
    Dr.text((6, 6), f'bend-check live {view} baseline (nearest). magenta = notch/gap px, red = outline spikes', fill=(0, 0, 0))
    for i, (jn, tag, m, t) in enumerate(tiles):
        y = 24 + (i // 2) * (TW + 6); x = (i % 2) * (TW + 4)
        sheet.paste(Image.fromarray(t).resize((TW, TW), Image.NEAREST), (x, y))
        Dr.text((2 * (TW + 4) + 6 + (i % 2) * 180, y + 4), f'{jn} {tag}\n' + '\n'.join(f'{a}={b}' for a, b in m.items() if not a.endswith('_y')), fill=(0, 0, 0))
    sheet.save(f'{OUT}/bend_check_live_{view}_sheet.png')
    for jn, d in R['joints'].items(): print('live', view, jn, {k: v for k, v in d.items() if k not in ('param', 'pivot', 'band_radius_px')})
    return R

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--angles', default='045,315'); ap.add_argument('--live', default='apose'); a = ap.parse_args(argv)
    out = {'diag': run_diag([x for x in a.angles.split(',') if x]) if a.angles else None,
           'live': {v: run_live(v) for v in a.live.split(',') if v and os.path.exists(f'{OUT}/live/{v}_meta.json')}}
    json.dump({'doc': __doc__, 'files': ['bend_check_diag.json', 'bend_check_diag_sheet.png'] + [f'bend_check_live_{v}.json' for v in out['live']] + [f'bend_check_live_{v}_sheet.png' for v in out['live']]},
              open(f'{OUT}/bend_check_report.json', 'w'), indent=1)
    return out

if __name__ == '__main__': main()
