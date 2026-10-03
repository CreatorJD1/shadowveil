"""Before/after numbers + sheet per angle (STAGED). Usage: python3 report_fix.py 045 315
Per +-25 tile (same joints, same angles and same crop as diag_body's joint_test_25 tiles; old and new cropped round the OLD pivot so they line up):
  step_px : max deviation of the posed outline from its own sigma-6 px smoothed path, inside the junction zone (18 px round each seam end where
            the joint's outline meets her silhouette, static end + the end carried by the turning piece). Measures corners/stair-steps.
  dent_px : deepest notch of the posed silhouette vs its closing with a 10 px disk, inside the junction zone (hinge dents, armpit/crotch bites).
  lump_px : deepest posed px outside her own two outlines (her rest figure without the turning pieces + her turning pieces' rest figure rotated)
            after closing them with a 10 px disk (so filling the wedge between them is allowed), inside the junction zone: flaps/caps bulging past her shape.
  rest values (0 deg) are the baseline from her own drawing (her armpit corner, her hair/jaw gap etc.)."""
import sys; sys.path.insert(0, '.'); from posekit import *
from seams import seam_ends
from PIL import ImageDraw
ZR = 18
JOINTS = ['shoulder_R', 'shoulder_L', 'elbow_R', 'elbow_L', 'hip_R', 'hip_L', 'knee_R', 'knee_L', 'ankle_R', 'ankle_L', 'waist', 'neck_base', 'head_neck']
YY, XX = np.mgrid[0:H, 0:W]
def zone(ends, c, th):
    Z = np.zeros((H, W), bool); t = np.radians(th)
    for x, y, _ in ends:
        for ex, ey in ((x, y), (c[0] + np.cos(t) * (x - c[0]) - np.sin(t) * (y - c[1]), c[1] + np.sin(t) * (x - c[0]) + np.cos(t) * (y - c[1]))):
            Z |= np.hypot(XX + 0.5 - ex, YY + 0.5 - ey) <= ZR
    return Z
def her_shape(ang, pj, own, jn, th):
    C = ctx(ang); j = pj['joints'][jn]; ch = JOINT_CHILD.get(jn, j['flap_on']); c = j['pivot']; sub = set(subtree(pj, ch))
    mov = np.zeros((H, W), bool)
    for k in sub: mov |= own[k]
    for t, o in TEAM_OWNER.items():
        if o in sub and t in C['T'] and 'wristflap' not in t: mov |= C['T'][t]
    fig = C['fg'] | C['TM']
    return (fig & ~mov) | (rot(mov.astype(np.uint8) * 255, c, th) > 0)
def tile(comp, c, R):
    a = comp[..., 3:] / 255.; t = (comp[..., :3] * a + np.array([150, 230, 150]) * (1 - a)).clip(0, 255).astype(np.uint8)
    x0, y0 = int(c[0]) - R, int(c[1]) - R; o = np.full((2 * R, 2 * R, 3), 255, np.uint8)
    xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x0 + 2 * R, W), min(y0 + 2 * R, H)
    o[ya - y0:yb - y0, xa - x0:xb - x0] = t[ya:yb, xa:xb]; return o
def run(ang):
    pjo, imgo = load_set(f'{ORIG}/{ang}'); pjn, imgn = load_set(f'{FIX}/{ang}')
    owner = np.full((H, W), '', object)
    for k in pjo['layerOrder_backToFront']: owner[imgo[k][..., 3] > 0] = k
    own = {k: owner == k for k in imgo}
    res = {}; tiles = []
    for jn in JOINTS:
        ends = seam_ends(ang, pjo, imgo, jn); co = pjo['joints'][jn]['pivot']; R = int(pjo['joints'][jn]['joint_radius_px'] + 15 + 30)
        res[jn] = {}
        for th in (0, -25, 25):
            row = {}
            for w, pj, img in (('old', pjo, imgo), ('new', pjn, imgn)):
                c = pj['joints'][jn]['pivot']; comp = pose(ang, pj, img, jn, th); Z = zone(ends, c, th)
                m, _ = metrics(comp, Z); S = comp[..., 3] > 0
                hs = cv2.morphologyEx(her_shape(ang, pj, own, jn, th).astype(np.uint8), cv2.MORPH_CLOSE, disk(10)) > 0; out = S & ~hs
                m['lump_px'] = round(float(ndi.distance_transform_edt(out)[Z].max()) if (out & Z).any() else 0.0, 2)
                m.pop('holes'); m.pop('line_break_px'); row[w] = m
                if th: row[w + '_tile'] = tile(comp, co, R)
            res[jn][f'{th:+d}'] = {k: v for k, v in row.items() if not k.endswith('_tile')}
            if th: tiles.append((jn, th, row))
    # merge in Body's own hole test (check_diag) for both sets
    for w, d in (('old', ORIG), ('new', FIX)):
        ck = json.load(open(f'{d}/{ang}/checks.json'))['joint_test_25']
        for jn in JOINTS:
            for t in ('-25', '+25', '+0'):
                x = ck[jn]['nearest'][t]; b = ck[jn]['bilinear'][t]
                res[jn][t][w].update(holes_seethrough_nearest=x['holes_seethrough_lt128'], holes_seethrough_bilinear=b['holes_seethrough_lt128'],
                                     holes_new_vs_rest_nearest=x.get('holes_not_at_rest', 0))
    json.dump(dict(angle=ang, metric_doc=__doc__, joints=res), open(f'{FIX}/{ang}/metrics_before_after.json', 'w'), indent=1)
    # ---- sheet
    TW = 230; cols = 3; F = frame(ang).astype(np.uint8); fgm = ctx(ang)['fg']
    ys, xs = np.nonzero(fgm); crop = Image.fromarray(F[max(ys.min() - 10, 0):ys.max() + 10, max(xs.min() - 10, 0):xs.max() + 10])
    ch = 2 * TW + 60; crop = crop.resize((int(crop.width * ch / crop.height), ch), Image.LANCZOS)
    nrows = (len(tiles) + cols - 1) // cols; pairw = 2 * TW + 16
    Wd = max(cols * pairw, crop.width + 10); Hd = ch + 60 + nrows * (TW + 40) + 10
    sheet = Image.new('RGB', (Wd, Hd), 'white'); D = ImageDraw.Draw(sheet)
    D.text((6, 4), f"Diagonal {ang} ({pjo['frame']}), FRAME px. Her frame (crop) | below: +-25 deg joint tiles, OLD (diag_body) left vs NEW (diag_body_fix) right. Staged, not live.", fill=(0, 0, 0))
    sheet.paste(crop, (6, 22))
    # rest proof panels next to the crop
    ckn = json.load(open(f'{FIX}/{ang}/checks.json'))
    rd = Image.open(f'{FIX}/{ang}/rest_recomposite_diff.png').convert('RGB'); rd = rd.resize((int(rd.width * ch / rd.height), ch), Image.LANCZOS)
    sheet.paste(rd, (crop.width + 16, 22))
    D.text((crop.width + 22 + rd.width, 30), '\n'.join([f"NEW rest diff vs her frame: {ckn['rest']['diff_px_vs_frame_on_body_px']} px",
        f"off-palette {ckn['totals']['off_palette']}, chroma {ckn['totals']['chroma']}, soft alpha {ckn['totals']['soft']}",
        f"overlap with teammates' rest px: {ckn['totals']['overlap_teammates_rest']}",
        "(hands/eyes/mouth/hair, incl. lid + mouth states: see checks.json)",
        "", "tile label: step old->new | dent old->new (px)", "green = teammates (hands, hair, eyes, mouth)", "red = see-through hole (none)"]), fill=(0, 0, 0))
    Y0 = ch + 50
    for i, (jn, th, row) in enumerate(tiles):
        X = (i % cols) * pairw; Y = Y0 + (i // cols) * (TW + 40)
        o, n = row['old'], row['new']
        D.text((X + 4, Y), f"{jn} {th:+d}: step {o['step_px']:.1f}->{n['step_px']:.1f} | dent {o['dent_px']:.1f}->{n['dent_px']:.1f} | lump {o['lump_px']:.0f}->{n['lump_px']:.0f}", fill=(0, 0, 0))
        D.text((X + 4, Y + 12), 'OLD', fill=(150, 0, 0)); D.text((X + TW + 10, Y + 12), 'NEW', fill=(0, 110, 0))
        sheet.paste(Image.fromarray(row['old_tile']).resize((TW, TW), Image.NEAREST), (X + 2, Y + 26))
        sheet.paste(Image.fromarray(row['new_tile']).resize((TW, TW), Image.NEAREST), (X + TW + 8, Y + 26))
    sheet.save(f'{FIX}/{ang}/sheet_{ang}_before_after.png'); print('sheet', sheet.size)
    for jn in JOINTS:
        print(ang, jn, ' '.join(f"{t}: step {res[jn][t]['old']['step_px']}->{res[jn][t]['new']['step_px']} dent {res[jn][t]['old']['dent_px']}->{res[jn][t]['new']['dent_px']} lump {res[jn][t]['old']['lump_px']}->{res[jn][t]['new']['lump_px']}" for t in ('-25', '+25')))
if __name__ == '__main__':
    for a in sys.argv[1:] or ['045', '315']: run(a)
