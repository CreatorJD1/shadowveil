# diag_body_fix: joint fixes for the 45° and 315° diagonal body pieces (STAGED; nothing live touched)
Sat Oct 3 2026, ~3:52–4:30 AM PT. Base: `body_tools/work/diag_body/{045,315}` (left untouched). Nothing committed, rig/ and views/ not edited,
no ports or browser used (file-based, offline Python). rig/index.html md5 still starts 562c32a7.

## What changed (and what didn't)
- **Same 14 pieces, same partition, layers, parents, file names and rigid-piece rig.** Every visible px at rest is her frame px, exactly as before.
- Only **hidden px** changed (045: 31,498 px; 315: 30,945 px, all under a higher piece at rest), and **joint pivots** were moved to the joint centres.
- Head piece: 0 px changed (face and skull stay fully on the head). Forearms: 0 px changed within 30 px of the wrist (the wrist end stays fully on the forearm).

Method, per joint (`tools/build_fix.py`):
1. **Pivot at the true joint centre.** For hinges (elbow, knee, ankle, waist, neck base), the pivot is the midpoint of the seam chord between the two points where the seam meets her outline. Shoulders: the deltoid centre, hand-placed from 6x crops. Hips: femoral head (045 hip_L moved 414,540 → 421,545). Head: top of the neck (387.5/374.5, 228), 9–10 px above the old chin-level pivot.
2. **Round joint cap.** This is a disk around the pivot on the turning piece. It is drawn only on px that the covering piece hides at rest. Its radius is half the seam chord for limbs, her inscribed radius for shoulders, and the distance to the outer hip seam end for hips (so the cap carries the hip mass round). As the piece turns, the disk spins in place, so the outer side of each bend becomes a round arc between the two outlines.
3. **Envelope-limited flaps.** The old flaps are kept only where every rotated position from −25° to +25° (in 5° steps) stays inside the closed envelope of her own posed shape: rest figure plus turned piece, closed with 8 px (shoulders 16, hips 20, waist 20), minus 1 px. Flaps may fill armpit, crotch and waist wedges but can no longer stick out as lumps. This removes the old flap lumps over the shoulders and hips.
4. **Neck underlap.** Her neck column is continued about 40 px up under the jaw (side lines extrapolated from her neck sides), with a round cap at the top-of-neck pivot. It sits on the neck piece under the head and never on Hair, Eyes or Mouth px.
5. **Colours and feathered rim.** Every hidden px copies one of her own frame px. Cap px within 2 px of the cap edge copy her nearest rim px of the same depth, which feathers her AA rim pattern round the arc. All other fill copies her nearest plain-skin px. Flaps carry no line px, so no stray dark marks or folds show when they swing.

## Checks (Body's own `diag_body/tools/check_diag.py`, unchanged, run on these pieces via `tools/check_fix.py`)
| | 045 | 315 |
|---|---|---|
| rest diff vs her frame (Body px) | **0** | **0** |
| Body px outside her body area / figure px covered by nobody | 0 / 0 | 0 / 0 |
| off-palette / chroma / soft alpha | 0 / 0 / 0 | 0 / 0 / 0 |
| overlap with teammates' rest px (hands, eyes incl. lids, mouth rest, hair) | 0 | 0 |
| see-through holes at ±25, nearest and bilinear, every joint | 0, except neck (see below) | 0 |
By design, as before: F12 wrist flaps lie under the forearm, and the open-mouth states cover face skin (the mouth draws on top).

**045 neck key gap:** there are 56 px of her key blue (all B−max(R,G) > 25) at x 408–411, y 210–227, between Hair's strand and her neck/jaw. They are **alpha 0 in all 14 Body pieces** (they were already 0, and the new neck underlap is kept off them). They are not in her keyed figure, and Body draws no px there.
The mask and list are in `045/neck_keygap_alpha0_mask.png` and `045/neck_keygap_alpha0.json`. This is the only "hole" in the neck tiles (50–56 px). It moves with the hair and head, so it is not a Body seam. If Coder still sees blue there, it comes from another layer or from the raw frame, not from Body.

## Before/after numbers per ±25° tile
Definitions are in `tools/report_fix.py` and the full table is in `<ang>/metrics_before_after.json`. All values are frame px, and the zone is 18 px round each seam end where the joint's outline meets her silhouette.
- **step** = max deviation of the posed outline from its own σ = 6 px smoothed path (corners and stair-steps).
- **dent** = deepest notch against a closing with a 10 px disk (hinge dents, bites).
- **lump** = deepest posed px outside her own two outlines (closed with 10 px): flaps or caps bulging past her shape.

Her own drawing already scores at rest (0°): shoulders 2.4–3.5 step / 3.6–4.1 dent (her armpit corner), head/neck ≈ 3 / 2, everything else ≈ 1 / 1.

### 045

| joint | old pivot -> new pivot | cap r | -25 step old->new | -25 dent old->new | +25 step old->new | +25 dent old->new | lump (-25/+25) old->new | see-through holes old->new |
|---|---|---|---|---|---|---|---|---|
| shoulder_R | [312.0, 300.0] -> [319.0, 289.0] | 8.4 | 1.88->2.63 | 1.0->1.0 | 2.7->2.58 | 1.41->1.0 | 9.85/13.0 -> 0.0/2.24 | 0/0 -> 0/0 |
| shoulder_L | [444.0, 300.0] -> [456.0, 292.0] | 18.9 | 3.68->2.99 | 3.0->2.0 | 2.16->2.95 | 1.0->1.0 | 5.0/3.0 -> 1.41/1.0 | 0/0 -> 0/0 |
| elbow_R | [274.6, 397.3] -> [274.9, 397.7] | 13.9 | 2.03->1.66 | 1.0->1.0 | 2.15->2.11 | 1.0->1.0 | 2.0/1.41 -> 0.0/0.0 | 0/0 -> 0/0 |
| elbow_L | [521.2, 394.1] -> [521.0, 394.0] | 15.3 | 2.2->1.78 | 1.0->1.0 | 1.79->1.57 | 1.0->1.0 | 1.0/1.0 -> 0.0/0.0 | 0/0 -> 0/0 |
| hip_R | [338.0, 545.0] -> [338.0, 545.0] | 48.2 | 1.61->3.26 | 1.0->1.0 | 3.2->3.2 | 1.41->1.41 | 10.2/0.0 -> 3.61/0.0 | 0/0 -> 0/0 |
| hip_L | [414.0, 540.0] -> [421.0, 545.0] | 48.2 | 4.59->4.92 | 1.41->3.16 | 1.3->2.03 | 1.0->1.0 | 0.0/8.06 -> 0.0/1.0 | 0/0 -> 0/0 |
| knee_R | [348.0, 780.5] -> [348.0, 780.5] | 19.0 | 1.92->1.89 | 1.0->1.0 | 1.92->1.6 | 1.0->1.0 | 1.41/1.41 -> 0.0/0.0 | 0/0 -> 0/0 |
| knee_L | [429.0, 780.5] -> [428.8, 780.6] | 21.5 | 1.82->2.45 | 1.0->1.0 | 1.45->2.36 | 1.0->1.0 | 2.24/2.0 -> 1.0/0.0 | 0/0 -> 0/0 |
| ankle_R | [345.8, 1015.9] -> [348.5, 1013.5] | 15.9 | 2.68->1.99 | 1.0->1.0 | 1.95->2.63 | 1.0->1.41 | 2.83/2.0 -> 0.0/0.0 | 0/0 -> 0/0 |
| ankle_L | [437.3, 1032.9] -> [440.0, 1030.5] | 15.4 | 2.14->2.18 | 1.0->1.0 | 1.9->1.86 | 1.0->1.0 | 2.83/2.0 -> 0.0/0.0 | 0/0 -> 0/0 |
| waist | [373.0, 470.0] -> [374.0, 469.8] | 56.3 | 3.74->3.31 | 2.0->1.41 | 3.88->3.2 | 2.0->2.0 | 0.0/1.41 -> 7.0/7.0 | 0/0 -> 0/0 |
| neck_base | [395.0, 264.0] -> [392.4, 263.8] | 32.0 | 4.07->3.88 | 5.39->5.0 | 2.54->3.63 | 2.0->2.24 | 5.83/3.16 -> 0.0/0.0 | 52/53 -> 51/50 |
| head_neck | [387.0, 237.0] -> [387.5, 228.0] | 20.5 | 3.66->3.51 | 3.0->2.24 | 3.36->2.76 | 2.24->2.24 | 1.0/4.0 -> 0.0/1.0 | 33/55 -> 56/52 |

rest (0 deg) baseline step/dent, same zones: shoulder_R 2.54/3.61, shoulder_L 3.48/4.12, elbow_R 1.52/1.0, elbow_L 1.07/1.0, hip_R 1.04/1.0, hip_L 1.32/1.0, knee_R 0.99/1.0, knee_L 1.19/1.0, ankle_R 1.19/1.0, ankle_L 1.72/1.0, waist 1.21/1.0, neck_base 2.04/1.0, head_neck 2.96/2.0

### 315

| joint | old pivot -> new pivot | cap r | -25 step old->new | -25 dent old->new | +25 step old->new | +25 dent old->new | lump (-25/+25) old->new | see-through holes old->new |
|---|---|---|---|---|---|---|---|---|
| shoulder_R | [308.0, 292.0] -> [302.0, 295.0] | 15.9 | 3.1->2.91 | 1.0->1.0 | 2.69->2.12 | 2.0->1.41 | 5.0/4.0 -> 1.0/1.41 | 0/0 -> 0/0 |
| shoulder_L | [452.0, 305.0] -> [441.0, 288.0] | 6.6 | 3.29->3.8 | 2.24->2.0 | 2.02->3.65 | 1.0->2.24 | 12.0/11.18 -> 2.0/1.0 | 0/0 -> 0/0 |
| elbow_R | [244.1, 392.4] -> [244.2, 392.5] | 15.7 | 1.9->1.94 | 1.0->1.0 | 1.86->1.78 | 1.0->1.0 | 1.41/1.41 -> 0.0/0.0 | 0/0 -> 0/0 |
| elbow_L | [485.9, 394.8] -> [485.9, 394.8] | 12.8 | 1.86->1.86 | 1.0->1.0 | 1.48->1.76 | 1.0->1.0 | 1.0/1.0 -> 0.0/0.0 | 0/0 -> 0/0 |
| hip_R | [344.0, 535.0] -> [344.0, 535.0] | 40.0 | 1.6->1.34 | 1.0->1.0 | 1.34->1.34 | 1.0->1.0 | 5.0/0.0 -> 1.0/0.0 | 0/0 -> 0/0 |
| hip_L | [424.0, 546.0] -> [424.0, 546.0] | 49.0 | 2.81->2.81 | 1.41->1.41 | 1.43->3.25 | 1.0->1.0 | 0.0/9.49 -> 0.0/3.61 | 0/0 -> 0/0 |
| knee_R | [337.0, 778.6] -> [336.6, 779.1] | 21.7 | 2.51->1.77 | 1.0->1.0 | 1.95->2.65 | 1.0->1.0 | 1.41/2.24 -> 1.0/0.0 | 0/0 -> 0/0 |
| knee_L | [414.0, 778.5] -> [414.0, 778.5] | 19.0 | 2.45->2.45 | 1.0->1.0 | 1.98->2.22 | 1.0->1.0 | 1.41/1.41 -> 0.0/1.0 | 0/0 -> 0/0 |
| ankle_R | [320.3, 1029.9] -> [323.4, 1027.4] | 16.1 | 2.9->2.25 | 1.0->1.0 | 1.93->1.99 | 1.0->1.0 | 3.0/2.0 -> 0.0/1.0 | 0/0 -> 0/0 |
| ankle_L | [410.7, 1027.0] -> [417.0, 1024.5] | 22.1 | 2.04->1.95 | 1.0->1.0 | 2.22->2.51 | 1.0->1.41 | 4.47/2.0 -> 0.0/0.0 | 0/0 -> 0/0 |
| waist | [389.0, 470.0] -> [389.4, 469.9] | 55.7 | 3.66->2.63 | 2.0->1.41 | 4.07->3.48 | 2.0->1.0 | 1.0/1.41 -> 6.32/7.0 | 0/0 -> 0/0 |
| neck_base | [370.0, 266.0] -> [366.0, 266.8] | 35.5 | 3.51->4.19 | 2.0->2.24 | 3.88->4.35 | 9.43->8.54 | 6.71/4.12 -> 0.0/0.0 | 0/0 -> 0/0 |
| head_neck | [374.0, 238.0] -> [374.5, 228.0] | 18.5 | 3.56->2.59 | 2.0->1.41 | 3.37->3.66 | 4.0->2.83 | 4.0/0.0 -> 1.0/0.0 | 0/0 -> 0/0 |

rest (0 deg) baseline step/dent, same zones: shoulder_R 3.41/4.0, shoulder_L 2.43/3.61, elbow_R 1.05/1.0, elbow_L 1.26/1.0, hip_R 1.35/1.0, hip_L 1.02/1.0, knee_R 1.21/1.0, knee_L 1.08/1.0, ankle_R 1.17/1.0, ankle_L 1.61/1.0, waist 1.23/1.0, neck_base 2.04/1.0, head_neck 2.91/2.24

## Still visible / honest limits
- **Waist ±25° still reads as one block turning.** The outer-side notch is now filled (step 3.7–4.1 → 2.6–3.5, dent ≤ 2 → ≤ 2). The fill shows as a smooth skin wedge, which the lump metric counts as up to 7 px past her two outlines.
  On the inner side, the pelvis's top corner still sticks out about 5 px over the torso, because the pelvis is on top and its px are her visible art. A rigid torso can't compress the inner side at 25°. It looks much better at the live BodyLean range (±8°).
- **Hips.** The old lumps are gone (045 hip_R −25: lump 10 → 3.6; 045 hip_L +25: 8 → 1; 315 hip_L +25: 9.5 → 3.6). Two things remain:
  - When the thigh swings outward, her thigh's own top corner pokes out as a small beak. The step number rises (045 hip_R −25: 1.6 → 3.3; 315 hip_L +25: 1.4 → 3.3) because the lump was replaced by a sharper corner.
  - When the thigh swings inward, her bikini-side tip (pelvis px) sticks out over a notch (045 hip_L −25 dent 1.4 → 3.2). The crotch notch at 045 hip_R +25 is unchanged: no hidden px can reach it.
- **Shoulders.** The flap lumps over the shoulder top are gone (lump 10–13 → 0–2). When the arm goes down, the deltoid now stays inside her outline.
  With the arm raised, an armpit hollow (background) shows between arm and torso. That is plausible anatomy, but it is a bit more open than the old flat flap triangle.
  Step is slightly up on 315 shoulder_L (3.3/2.0 → 3.8/3.7) and 045 shoulder_L +25 (2.2 → 3.0): her jagged AA rim at the bend is still nearest-sampled.
- **Elbows, knees and ankles** are clean: lump → 0–1, and step is mostly down or within ±0.6 px. Rim jaggies of 1–2 px from nearest-neighbour rotation of her 1 px AA rim remain at every joint, and they are her pixel art.
- **Neck.**
  - head_neck: the jaw no longer lifts off a bare edge. The neck column shows under the jaw (dent 3.0 → 2.2 at 045 −25; 4.0 → 2.8 at 315 +25).
  - 045 neck_base −25 still has a 5 px dent from her own key gap under the hair strand.
  - 315 neck_base +25 dent 9.4 → 8.5: the chin comes down near the shoulder and closes off her background under the jaw. That is the pose, not a seam.
  - neck_base step is up about 0.5–1 px, from the trapezius cap rim.
- Not done: no view-scale copies (same as diag_body). 135° and 225° are not started. Nothing is wired into rig/index.html.

## Files (per angle `045/`, `315/`)
- `pieces/*.png`: the 14 fixed pieces (768x1168 frame px, binary alpha).
- `parts.json`: new pivots, plus per-joint cap radius, cap px, flap px and old pivot. `wrist_cuts.json` is copied unchanged.
- `sheet_<ang>_before_after.png`: her frame crop, the new rest diff, then all ±25° tiles with OLD on the left and NEW on the right, with step/dent/lump labels.
- `metrics_before_after.json`: step, dent, lump and holes, old and new, at −25/0/+25.
- `checks.json`, `rest_recomposite_diff.png`, `joint_test_25.png`: Body's own check output on the fixed pieces.
- Tools are in `tools/`. Run them in this order: `build_fix.py 045 315` → `check_fix.py 045 315` → `report_fix.py 045 315`.
  Helpers: `posekit.py` (posing and metrics) and `seams.py`. `tools/scratch/` holds working zooms.
