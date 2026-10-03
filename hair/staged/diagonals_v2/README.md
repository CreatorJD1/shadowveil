# diagonals_v2 (Base Hair, 2026-10-03, about 03:15 PT)
- Built from hair/staged/diagonals. Alpha is thresholded at 128 to 0/255. Each px is snapped to the view palette (live hair art plus source-frame colours with blue excess ≤ 20). Shape matches the soft 50% iso-line (xor 0). Scripts: work/snap.py, work/stats2.py, result.json.
- Eye cut (work/eyecut.py, eyecut.json): hair px over Eyes' staged diagonal eye parts were set to alpha 0, not snapped. The parts are white, lash, lid_0..7 and iris ±4 frame px, mapped with viewFit and dilated 1 px. Masks: <ang>/eye_region_view.png. The pre-cut copies are in pre_eyecut/.
  Files changed: 045 hair_front 53→0, 045 strand_03_tip 117→0, 315 strand_06 217→0 (green iris px), 315 hair_front 0. All 11 px listed by Eyes now have alpha 0.
- qa_gates (leak, part hair), run on a copy of the script at hair/qa/qa_gates_runs/qa_gates_diagv2.py with the path changed to v2:
  v1 = 144 off-palette, 1 chroma, 41207 soft px; v2 = 0, 0, 0 over 34 files. See hair/qa/qa_gates_runs/.
- 225/extra_2 is empty because every px had α < 128. 135/225 hair_front were already empty in the source.
