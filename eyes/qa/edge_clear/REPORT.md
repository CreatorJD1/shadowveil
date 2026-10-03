# Diagonal eye silhouette-edge clear

Date: 2026-10-03 03:30 PDT

Cleared the exact `check_diag_chroma_fix.py` rest-edge pixels in both keyed and `_chroma.png` assets. Backups are in `eyes/staged/diagonals/backups_edge_clear/`.

## Changes

- `045`: `EyeR_lid_0.png` and `EyeR_lid_0_chroma.png`: 2 px cleared — `(330,179)`, `(331,179)`.
- `315`: `EyeL_lid_0.png` and `EyeL_lid_0_chroma.png`: 5 px cleared — `(432,180)`, `(432,181)`, `(432,182)`, `(432,186)`, `(433,186)`.

No other part had pixels at those target coordinates. `lid_1..7`, lash, white, and shifted iris renders had no contributing pixels there, so no non-rest part was changed.

## Verification

`check_diag_chroma_fix.py` now reports:

- `045`: `inside_face: 0`, `outside_face_edge: 0`.
- `315`: `inside_face: 0`, `outside_face_edge: 0`.
- Neutral-grey composite chroma: `0` for both angles (all 144 renders per angle).

`eyes_diag_leak_supplement.py` reports staged diagonal eye files at `off_palette: 0`, `chroma: 0` for both angles. No serve/render commands were run.
