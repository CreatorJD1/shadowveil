import sys, json; sys.path.insert(0, '.')
import build_fix, report_fix
from report_fix import *
ang = sys.argv[1]; js = sys.argv[2].split(','); opts = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
build_fix.build(ang, opts)
pjo, imgo = load_set(f'{ORIG}/{ang}'); pjn, imgn = load_set(f'{FIX}/{ang}')
owner = np.full((H, W), '', object)
for k in pjo['layerOrder_backToFront']: owner[imgo[k][..., 3] > 0] = k
own = {k: owner == k for k in imgo}
for jn in js:
    ends = seam_ends(ang, pjo, imgo, jn); s = []
    for th in (-25, 25):
        for w, pj, img in (('old', pjo, imgo), ('new', pjn, imgn)):
            c = pj['joints'][jn]['pivot']; comp = pose(ang, pj, img, jn, th); Z = zone(ends, c, th); m, _ = metrics(comp, Z)
            out = (comp[..., 3] > 0) & ~(cv2.morphologyEx(her_shape(ang, pj, own, jn, th).astype(np.uint8), cv2.MORPH_CLOSE, disk(10)) > 0); lump = float(ndi.distance_transform_edt(out)[Z].max())
            s.append(f"{w}{th:+d} st{m['step_px']:.1f} dn{m['dent_px']:.1f} lu{lump:.1f}")
    print(jn, ' | '.join(s))
