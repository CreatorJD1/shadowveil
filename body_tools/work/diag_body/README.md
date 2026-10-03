# diag_body: Base Body pieces for the diagonal turn angles (STAGED; nothing live touched)
Sat Oct 3 2026, ~3:15–3:45 AM PT. Done: **45° (f033) and 315° (f191)**. Not started yet: 135° (f087) and 225° (f131).
Nothing committed, rig/index.html and live files untouched, no servers/ports used (file-based only).

## Files (per angle `045/`, `315/`)
- `pieces/*.png`: 14 pieces, full canvas **768x1168 in FRAME px** of her turn frame (x=y=0), binary alpha. Names follow the 5 base views:
  head, neck, torso, pelvis, upper_arm_R/L, forearm_R/L, thigh_R/L, shin_R/L, foot_R/L. R/L = her right/left (R = viewer-left at 45/315), same as Hands F8.
- `parts.json`: layer order (feet 201, shins 203, thighs 205, forearms 220, upper arms 222, neck 239, torso 240, head 242, pelvis 250, same as the base views),
  parent, **pivot (frame px)**, joints (flap_on/under, radius, flap px), wrist pivots/cut lines, view_fit (view = 1.54468*frame + (dx,dy)), colours.
- `wrist_cuts.json`: forearm/F8 boundary per wrist (frame px), overlap/gap at rest.
- `body_whole_rest.png` = all Body-owned px at rest (her keyed figure minus teammates' rest px); `figure_keyed_full.png` = her whole keyed figure.
- `checks.json` (all numbers), `rest_recomposite_diff.png`, `joint_test_25.png`, `sheet_<ang>.png` (frame | pieces | exploded | rest diff + ±25° tiles).
- `wrist_test/` + `../wrist_test_report.json`: wrist bend + end-notch test with F8+F12 hands (candidate wristcaps there are NOT part of the pieces).
- Tools: `tools/` (common.py, wrist_cuts.py, divide_diag.py + diag_config.json (hand-placed seams), check_diag.py, wrist_notch.py, sheets_diag.py, overview.py, crop.py).
  Run: `cd tools && python3 divide_diag.py 045 315 && python3 wrist_cuts.py && python3 check_diag.py 045 315 && python3 wrist_notch.py 3 6 10 && python3 sheets_diag.py`

## Method
- Source = her frame only (no mirroring, no generation, threequarter_apose not used). Figure = not border-connected key with Hands' F8 rule (B−max(R,G) > 25).
- Body px = figure minus teammates' REST px (frame scale): Hands F12 rig (`hands/staged/f12_wrist_diag/<a>/rig.json`, F8 parts' frame_scale copies),
  Eyes `eyes/staged/diagonals/<a>/` (white, iris, lash, lid_0), Mouth `mouth/staged/diag_posable/<a>/frame_scale/rest.png`,
  Hair `hair/staged/diagonals_v3/<a>/hair/*` mapped to frame px with Hair's own centre rule fx=floor((X+0.5−dx)/s).
- Every visible px is her exact frame px. Hidden joint flaps (disk about the pivot, only under the covering piece) = her most common skin px (189,129,88);
  flap px on her silhouette = (32,30,28), her most common dark ink px. Both are her frame colours. No folds/shading added.
- Wrists: forearm ends exactly where the F8 parts begin (F8 boundary is 2–3 px arm-side of the old diag_check red line); hands draw UNDER the forearm.
  No forearm flap past the cut (it would cover F8 px at rest).

## Checks (45 | 315)
- Rest recomposite vs her frame on Body px: **0 | 0 px**; Body px outside its area: 0 | 0; figure px covered by nobody: 0 | 0.
- Off-palette **0 | 0**, chroma (qa_gates) **0 | 0**, soft alpha 0 | 0.
- Overlap with teammates' rest px: hands 0, eyes 0 (also 0 vs all lid states), mouth rest 0, hair 0 (both angles).
  By design: F12 wrist flaps lie under the forearm (45: L 364 / R 331, 315: L 348 / R 360 px); open mouth shapes cover face skin (45: 115, 315: 97 px; mouth draws on top).
- "Hers, allowlist" (her exact colours with B−max(R,G) > 25 in Body pieces): **0 px at 45, 0 px at 315**, no colours. The only case was the 4 px at 315 L (590–591, 548–549), which now belong to Hands' L_palm and are not in Body.
- ±25° joint test, see-through holes (alpha<128 enclosed), nearest / bilinear: **0 at every joint** (shoulders, elbows, hips, knees, ankles, waist, wrists with F8+F12).
  Exceptions are her own key gap, not Body holes: at 45, neck_base and head_neck show 52/56 px at rest and ≤55 when bent. That is the blue between a hair strand (Hair's part, x408–412 y200–235) and her neck/jaw, which moves with the head.
  Bilinear "enclosed" px with alpha ≥128 are AA seams (neck/head ≤139, wrists ≤16, 315 hip_R 1).
- Wrist end notch (Hands' F12 metric, +25/−25, with F8+F12): 45 L 2/2, 45 R 6/6, 315 L 3/4, 315 R 3/4 px. I tested a forearm-owned hidden underlap ("wristcap") drawn under the hand, using flat skin plus line tone, depth 3/6/10 px, with 0 px change at rest.
  It does **not** close the notch (after: 45 L 2–3, 45 R 6–10, 315 L 4–7, 315 R 3–4). The notch lies outside her rest silhouette, so any fill there would show at rest. No change is staged into the pieces.

## Known / open
- Coder's `rig/work/diag_rig/` does not exist, so there was no skeleton, joint file or naming contract to read. Pivots are mine (seams read off 4x crops, elbow/knee re-centred on the limb from apose_turn proxies).
- Frame scale only. View-scale copies are not made; view_fit is in parts.json.
- Hair's mask has 1410 (45) / 1330 (315) px over her key (outside the keyed figure). Eyes have 10 / 26. Not Body px.
- Waist ±25 is a rigid rotation, so the side outline steps (no hole). Upper-arm flaps at the long seam side are large (45 R 6469, 315 L 6866 px), all hidden under the torso.
- The head piece is split by hair/eyes/mouth into 3–4 islands (expected). No skull fill under hair (that would overlap Hair).
