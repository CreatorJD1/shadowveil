"""wrist_cuts.json per angle: forearm ends exactly where Hands' F8 frame_scale parts begin (forearm = her fg px not in the F8 hand)."""
import sys; sys.path.insert(0, '.'); from common import *
DC = json.load(open(f'{ROOT}/hands/work/turn_check/diag_check.json'))
def wrist_info(ang, F, fg, T):
    k = ANG[ang]['hands']; res = {}
    yy, xx = np.mgrid[0:1168, 0:768]
    for side in 'LR':
        d = DC[f'{k}_{side}']; (x1, y1), (x2, y2) = d['wrist_cut']; wx, wy = d['wrist']; th = np.deg2rad(d['axis_deg'])
        u = np.array([np.cos(th), np.sin(th)]); H = T['hand_' + side]
        sd = (xx + 0.5 - wx) * u[0] + (yy + 0.5 - wy) * u[1]
        if sd[H].mean() < 0: sd = -sd; u = -u
        near = np.hypot(xx + 0.5 - wx, yy + 0.5 - wy) < 30
        arm = fg & ~H & near & (sd < 6)
        # boundary: arm px 4-adjacent to hand px, and hand px 4-adjacent to arm
        st = ndi.generate_binary_structure(2, 1)
        bA = arm & ndi.binary_dilation(H, st); bH = H & ndi.binary_dilation(arm, st)
        v = np.array([-u[1], u[0]])  # along the cut
        ys, xs = np.nonzero(bA | bH); t = (xs + 0.5 - wx) * v[0] + (ys + 0.5 - wy) * v[1]
        sb = (xs + 0.5 - wx) * u[0] + (ys + 0.5 - wy) * u[1]
        i0, i1 = np.argmin(t), np.argmax(t)
        # line through the boundary (between arm & hand px): fit s = a + b t on the shared edges
        cs = []
        for (dyy, dxx) in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            sh = np.roll(np.roll(H, dyy, 0), dxx, 1)
            ay, ax = np.nonzero(arm & sh)
            for y, x in zip(ay, ax): cs.append((x + 0.5 - dxx / 2, y + 0.5 - dyy / 2))
        cs = np.array(cs); ct = (cs[:, 0] - wx) * v[0] + (cs[:, 1] - wy) * v[1]; cS = (cs[:, 0] - wx) * u[0] + (cs[:, 1] - wy) * u[1]
        b, a = np.polyfit(ct, cS, 1); t0, t1 = ct.min(), ct.max()
        P = lambda tt: [round(float(wx + u[0] * (a + b * tt) + v[0] * tt), 2), round(float(wy + u[1] * (a + b * tt) + v[1] * tt), 2)]
        hand_beyond = int((fg & ~H & (sd >= 0) & ndi.binary_dilation(H, iterations=3)).sum())
        res[side] = dict(
            hands_part_files=f"hands/staged/f8_diagonals/{k}/frame_scale/{side}_*.png",
            f8_palm_pivot_frame=None,
            diag_check_red_line=[[x1, y1], [x2, y2]],
            boundary_line_fit=[P(t0), P(t1)],
            boundary_line_note='least-squares line through the shared edges between forearm px and F8 hand px (frame px, edge coords)',
            boundary_edge_count=int(len(cs)), boundary_offset_from_red_line_px=dict(min=round(float(cS.min()), 2), max=round(float(cS.max()), 2), mean=round(float(cS.mean()), 2)),
            forearm_px_on_boundary=int(bA.sum()), hand_px_on_boundary=int(bH.sum()),
            rest_overlap_px=0, rest_gap_px_wrist_zone=int((fg & near & ~H & ~arm).sum()),
            nonhand_fg_px_on_hand_side=hand_beyond)
        res[side]['_arm_mask'] = arm
    return res
if __name__ == '__main__':
    for ang in sys.argv[1:] or ['045', '315']:
        F = frame(ang); fg, _ = fg_mask(F); T = team_masks(ang); r = wrist_info(ang, F, fg, T)
        rig = json.load(open(f"{ROOT}/hands/staged/f8_diagonals/{ANG[ang]['hands']}/rig.json")); f = fit(ang)
        for side in 'LR':
            p = [q for q in rig['parts'] if q['id'] == side + '_palm'][0]
            r[side]['f8_palm_pivot_frame'] = [round((p['pivotX'] - f['dx']) / f['scale'], 2), round((p['pivotY'] - f['dy']) / f['scale'], 2)]
            arm = r[side].pop('_arm_mask'); H = T['hand_' + side]
            r[side]['rest_overlap_px'] = int((arm & H).sum())
        os.makedirs(f'{OUT}/{ang}', exist_ok=True)
        out = dict(angle=int(ang), frame=ANG[ang]['frame'], units='FRAME px of reference/apose_turn/frames/%s.png (768x1168), origin top-left; matches hands/staged/f8_diagonals/%s/frame_scale/' % (ANG[ang]['frame'], ANG[ang]['hands']),
                   side_labels='R/L as in Hands F8 / diag_check (R = viewer-left arm, L = viewer-right arm)',
                   rule='forearm_<side> = her figure px (not key: B-max(R,G)<=25, border-connected) minus the union of F8 frame_scale <side>_* parts; hands draw UNDER the forearm; no forearm flap past the cut (it would cover F8 px at rest)',
                   view_fit=fit(ang), wrists=r)
        json.dump(out, open(f'{OUT}/{ang}/wrist_cuts.json', 'w'), indent=1)
        print(ang, json.dumps({s: {k: v for k, v in r[s].items() if k in ('diag_check_red_line', 'boundary_line_fit', 'rest_overlap_px', 'rest_gap_px_wrist_zone', 'boundary_offset_from_red_line_px', 'nonhand_fg_px_on_hand_side')} for s in 'LR'}))
