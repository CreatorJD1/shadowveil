# diagonals_v4 (Base Hair, 2026-10-03 ~03:50 PT). v3 is kept unchanged.
Scripts are in work/: build_v4.py (pixels), sway_gate.py + caps.py (sway gate and caps), before_nocap.py, sheet_v4.py, body_check.py (PROVISIONAL).
Data: build_v4.json, sway_caps.json, sway_gate_before.json, body_check_PROVISIONAL.json.

## Her hair (frame px)
- Start from v1's frame hair segmentation (key.hair_mask, with enclosed key loops keyed).
- Keep px with key-unmix alpha >= 0.5.
- Drop key-blue px (qa chroma rule): 345 / 332 / 333 / 342 px at 045 / 135 / 225 / 315.
- Drop Eyes' white + iris px.
- Drop px under the mouth lips mask.
- Drop the eye zone: dark, untinted lash/lid ink (blue excess <= 10) within 8 px of Eyes' parts. That is 56 px at 045 and 48 px at 315.
- Add Eyes' lash-trim px (her frame wins): 20 px at 045 and 18 px at 315.

## View scale
- Hair-mask px that are her hair but were uncovered in v3 are now filled. The part is the v1 part with the highest alpha there. The colour is v1's colour snapped to that part's live hair-art palette. Alpha is hard.
- v3 hair over the eye-zone ink is cleared: 73 px at 045 and 36 px at 315.
- Her hair uncovered, v3 → v4: 045 259→0, 135 181→0, 225 180→0, 315 302→0.
- Hair-mask px still uncovered: about 6.1–6.5k per angle. These are px where her frame is mostly key (alpha < 0.5), or key-blue px. They stay out on purpose.
- px added outside the hair mask: 0. px added outside her hair: 0.
- Hair over white/iris/mouth: 0.
- Lash-trim holes: 0 (45 / 42 view px are now covered).

## Frame scale (<ang>/frame_scale/hair/, 768x1168)
- Native cut: exact copies of her frame px. Each px takes the part label of the v4 view part at that px.
- Eyes' trim px that are key-blended in her frame are snapped to the hair palette.
- Rest composite vs her frame's hair: 0 px at all four angles. Trim holes: 0.
- rig.json is in frame px. Pivots are converted from the view rig. 045/315 roots parent to Body's "head" (provisional). swayYMaxPx = 3 / scale.

## Sway caps
- Sway gate: the page formula mirrored in Python, with the slider path and per-segment chain drive, X -1..1 × Y -1..1.
- Targets: Eyes' white + iris (iris swept over its gaze limits); Mouth's rest and all open shapes (alpha).
- Caps are direction-only, stored as degAtPlus1 / degAtMinus1 in both rig.json files:
  - 045 strand_03_tip: degAtMinus1 −9.5 → −1.425 (plus side unchanged at 9.5).
  - 045 strand_03: degAtMinus1 −5.7 → −1.71.
  - 315 strand_06: degAtPlus1 5.3 → 0.265 (minus side unchanged at −5.3).
- Max px over the eye opening / mouth, before → after:
  - 045 view: eye 27→0, mouth rest 15→0, shapes up to 31→0. 045 frame: eye 11→0, shapes up to 12→0.
  - 315 view: eye 66→0, mouth rest 38→0, shapes up to 29→0. 315 frame: eye 28→0, shapes up to 9→0.
- NOTE: rig/index.html hair code reads only swayWeight*maxSwayDeg, so the Coder must add degAtPlus1 / degAtMinus1 support for hair parts.

## QA
- The qa_gates copies (hair/qa/qa_gates_runs/qa_gates_diagv4*.py) give 0 off-palette / 0 chroma / 0 soft at both view and frame scale (34 files each).
- Sheet: eye_crops_v3_v4_source.png.

## Body check (PROVISIONAL)
The head piece may change. Rest only, plus hair sway; no body bends.
See body_check_PROVISIONAL.json and <ang>/for_base_body/PROVISIONAL_skull_underfill_mask_frame.png.
