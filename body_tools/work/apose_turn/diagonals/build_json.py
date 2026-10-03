import json
A=json.load(open('_analysis.json')); M=json.load(open('_mirror_sharp.json')); O=json.load(open('_mirror_open.json')); S=json.load(open('_spill.json'))
P={int(k):v for k,v in json.load(open('picks.json')).items()}
NOTES={
45:{"facing":"3/4 toward viewer-left, near side = her LEFT (green eye near, amber far); same side as views/left (90). Not mirrored: amber at viewer-left, green at viewer-right; 2 marks under the green (left) eye = canonical left-cheek pair; amber-side single mark hidden by the turn (expected).",
    "eyes":"Both eyes sharp, no blur; far (amber) eye whole: iris, white and lashes present, outer corner just inside the cheek contour (stays whole f029-f034, begins to narrow f035+).",
    "hands":"Both clear of hips (min gap viewer-L 86 px, viewer-R 132 px raw), all fingers visible and spread.",
    "choice":"Agreed f033 kept. Mirror test vs f191: IoU 0.915 (peak f034 0.925, i.e. within 1 frame/~1.3 deg). Sharpness equal to neighbours; f034 is slightly softer (aa 1.255)."},
135:{"facing":"Back 3/4: back + her LEFT side; head turned viewer-left, her left ear visible, toes toward viewer-left/away. Correct side (between views/left 90 and views/back 180). Face not visible.",
    "hands":"Both clear (min gap 124 / 102 px raw), fingers visible.",
    "choice":"Mutual best mirror pair with f131 (IoU 0.904, the best of f081-f093). Legs open (no enclosed key gap), unlike f083-f084."},
225:{"facing":"Back 3/4: back + her RIGHT side; head turned viewer-right, her right ear visible. Correct side (between views/back 180 and views/right 270). Face not visible.",
    "hands":"Both clear (min gap 102 / 122 px raw), fingers visible.",
    "choice":"f131 over the map's hold f132: f131 is the best mirror of f087 (IoU 0.903 vs f132 0.883); sharpness f131 >= f132 (aa 1.389 vs 1.440, edge grad 216.6 vs 213.2), so the map note 'f132 sharper' is not supported. Arms are slightly closer to A-pose. f129 (~220 deg) is the sharpest neighbour (aa 1.116) with open legs and is the fallback, but it is under-turned (IoU vs mirror f087 is 0.891).",
    "concern":"f130-f135: the inner thighs/calves touch, so the gap between the legs is an enclosed blue island (~15.5k px at f131). seg.py binary_fill_holes counts that as body, so any cutout made with seg.py masks will keep a blue slab between the legs. Key it with the unfilled key test (blue-max(r,g)>120) instead. All f130-f135 frames are softer than f127-f129 (aa 1.32-1.44)."},
315:{"facing":"3/4 toward viewer-right, near side = her RIGHT (amber near, green far); same side as views/right (270). Not mirrored: amber at viewer-left, green at viewer-right; the single mark under the amber (right) eye = canonical; green-side pair hidden by the turn (expected).",
    "eyes":"Both eyes sharp; far (green) eye whole: iris and white present, touching the cheek contour (whole f187-f193, starts clipping by f195).",
    "hands":"Both clear of hips (min gap 130 / 86 px raw), all fingers visible (the reference case).",
    "choice":"Agreed f191 kept. Mirror vs f033: IoU 0.915 (peak f193 0.932, so f191 may be ~1-2 deg less turned than the mirror of f033). Not worth changing."}}
common="Despill: every frame has ~5k px of blue-tinted kept edge pixels (about 1.2k in the hair zone: flyaway strands with key showing between them) plus 40-110 px of enclosed blue islands inside hair loops. The amount is the same across all candidates, so it does not decide any pick, but Hair needs to despill strands at all four. Back-half frames are ~2% smaller and higher (camera drift), so use the per-frame fit, not a single scale."
out={"_doc":"Diagonal frames for the 8-point ring. Frames are reference/apose_turn/frames/fNNN.png (768x1168), raw px. view_fit: base_x = scale*frame_x + dx, base_y = scale*frame_y + dy into the 1365x1739 view space. Head top maps to y40, and the sole maps to y1682 (45/315, like apose) or y1681 (135/225, like back and the profiles). dx centres the hip-band median x on the mean of the two neighbouring sharp views. handoff_interp is the mean of the two neighbouring angle_map handoffs, given to show its residuals; do NOT use it as-is, because it puts soles about 10 px low (front half) or 11 px high (back half). arm_angle = armpit-to-fingertip angle from vertical in the image plane (views/apose 46.0/46.2, views/back 43.8/43.8; foreshortened at diagonals, so compare within the strip). Side labels R/L = viewer-left/viewer-right arm. Scripts: analyze.py, mirror_sharp.py, mirror2.py, spill.py, sheets.py, build_json.py.",
     "ring":{"0":"views/apose","45":"f%03d"%P[45],"90":"views/left","135":"f%03d"%P[135],"180":"views/back","225":"f%03d"%P[225],"270":"views/right","315":"f%03d"%P[315]},
     "view_arm_angle_deg":A['view_arm_angle_deg'],"diagonals":{},"common_notes":common}
for ang in (45,135,225,315):
    rows={r['frame']:r for r in A['rows'][str(ang)]}; r=rows[P[ang]]; f=P[ang]
    nb=[]
    for g,x in rows.items():
        nb.append({"frame":g,"angle_est":x['angle_est'],"raw_H":x['raw_H'],"raw_sole_y":x['raw_sole'],"arm_angle_deg":x['arm_angle_deg'],
                   "hands_clear":{k:v['clear'] for k,v in x['hands'].items()},"hand_gap_px":{k:v['gap_min_px'] for k,v in x['hands'].items()},
                   "aa_band":x['aa_band'],"edge_grad":M[str(ang)][str(g)]['edge_grad_mean'],"motion":M[str(ang)][str(g)]['motion_meanabs'],
                   "enclosed_key_px":S[str(g)]['enclosed_key_px'],"hair_spill_px":S[str(g)]['hair_spill_px']})
    out["diagonals"][str(ang)]={"frame":f,"file":"reference/apose_turn/frames/f%03d.png"%f,"angle_est":r['angle_est'],"angle_range":r['angle_range'],
        "height_px_raw":r['raw_H'],"head_top_y_raw":r['raw_top'],"sole_y_raw":r['raw_sole'],"view_fit":r['fit'],
        "handoff_interp":r['handoff_interp'],"iou_vs_neighbour_views":r['iou_neighbour_views'],"arm_angle_deg":r['arm_angle_deg'],
        "hands":{k:{"clear_of_hip":v['clear'],"min_gap_px":v['gap_min_px'],"fingers_visible":True} for k,v in r['hands'].items()},
        "sharpness":{"aa_band":r['aa_band'],"edge_grad":M[str(ang)][str(f)]['edge_grad_mean'],"motion_meanabs":M[str(ang)][str(f)]['motion_meanabs']},
        "notes":NOTES[ang],"neighbours":nb,"strip":"strip_%03d.png"%ang}
json.dump(out,open('diagonals.json','w'),indent=1)
for a,d in out['diagonals'].items(): print(a,d['frame'],d['angle_est'],d['height_px_raw'],d['sole_y_raw'],d['view_fit'],d['handoff_interp']['H_err'],d['handoff_interp']['sole_err'],d['arm_angle_deg'],d['iou_vs_neighbour_views'])
