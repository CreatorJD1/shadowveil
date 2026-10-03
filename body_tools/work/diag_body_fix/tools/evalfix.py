"""Before/after numbers per +-25 tile. Junction zone = 14 px disks round each seam end where the joint's outline meets her silhouette,
both the static end and the end carried by the turning piece. step = max deviation of the outline from its own sigma-6 px smoothed path
inside the zone; dent = deepest notch (vs a 10 px-radius closing) inside the zone; holes = enclosed non-opaque px within joint radius+15."""
import sys; sys.path.insert(0, '.'); from posekit import *
from seams import seam_ends
ZR = 14
JOINTS = ['shoulder_R', 'shoulder_L', 'elbow_R', 'elbow_L', 'hip_R', 'hip_L', 'knee_R', 'knee_L', 'ankle_R', 'ankle_L', 'waist', 'neck_base', 'head_neck']
def zone(ends, c, th):
    Z = np.zeros((H, W), bool); YY, XX = np.mgrid[0:H, 0:W]
    t = np.radians(th)
    for x, y, _ in ends:
        for (ex, ey) in ((x, y), (c[0] + np.cos(t) * (x - c[0]) - np.sin(t) * (y - c[1]), c[1] + np.sin(t) * (x - c[0]) + np.cos(t) * (y - c[1]))):
            Z |= np.hypot(XX + 0.5 - ex, YY + 0.5 - ey) <= ZR
    return Z
def run(ang, which, joints=JOINTS, ths=(-25, 0, 25)):
    d = f'{ORIG}/{ang}' if which == 'old' else f'{FIX}/{ang}'
    pj, img = load_set(d); pjo, imgo = load_set(f'{ORIG}/{ang}')
    out = {}
    for jn in joints:
        ends = seam_ends(ang, pjo, imgo, jn); c = pj['joints'][jn]['pivot']
        hb, _, _ = band_of(pj, jn, 15); out[jn] = {}
        for th in ths:
            comp = pose(ang, pj, img, jn, th); Z = zone(ends, c, th)
            m, v = metrics(comp, Z); m['holes'] = int((ndi.binary_fill_holes(comp[..., 3] > 0) & ~(comp[..., 3] > 0) & hb).sum())
            out[jn][f'{th:+d}'] = m
    return out
if __name__ == '__main__':
    ang = sys.argv[1]; js = sys.argv[2].split(',') if len(sys.argv) > 2 else JOINTS
    for w in ('old', 'new'):
        r = run(ang, w, js)
        for jn in r: print(ang, w, jn, {t: (v['step_px'], v['dent_px'], v['holes'], v['line_break_px']) for t, v in r[jn].items()})
