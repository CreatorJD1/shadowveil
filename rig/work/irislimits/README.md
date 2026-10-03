# (D) Iris gaze limits for the diagonal eyes (proposal; nothing in eyes/ or views/ changed)

Coder, Sat Oct 3 2026, PT.

**Inputs (read-only):** `eyes/staged/diagonals/{045,315}`. 135 and 225 have no staged diagonal eye rig (the back diagonals have no cut eyes), so there is nothing to widen there.

**Rule** (`compute.py` → `diag_irislimits.json`):
- Draw order is white → iris (source-atop) → lid_k → lash, so the iris is always clipped to her eye white and drawn under her lid line and lash.
- A shift is allowed only if it passes on **all 8 lid frames**:
  1. The iris bbox edge stays inside the eye corner (the extreme column/row of the white ∪ rest iris lock).
  2. The visible iris keeps at least 75% of what the centred iris shows on that frame, so it never slides under her lid line or lash. Frames where less than 4 px of iris is visible are skipped (they are closed).
- Limits are in frame px. View px = × viewFit.scale (1.545).

## Limits

| angle | eye | current dx −1 / +1 | `irislimits=diag` dx −1 / +1 | view px (+1) | what stops it |
|---|---|---|---|---|---|
| 315 | EyeR (near, amber) | −2 / +2 | **−3 / +4** | 6.2 | the eye corner |
| 315 | EyeL (far, green) | 0 / +2 | **0 / +1** | 1.5 | the corner. The current +2 already pushes the iris past it, so the clamp narrows this one |
| 045 | EyeL (near) | 0 / +1 | **−4 / +3** | 4.6 | the corner |
| 045 | EyeR (far) | −2 / 0 | **0 / 0** | 0 | on lid_6 the visible iris drops below 75%, and the corner stops +1 |

- **dy:** the same rule gives 0 in every case (the iris already touches her lid lines at the top and bottom). dy is therefore left at the current ±1 and not proposed.
- **Rest:** 0 px in both angles (`rest_check_diag.json`).
- **Sheets:** `sheet_diag.png` / `sheet_current.png` (8 lid frames, X±1 at k0/k3/k5, gaze tiles) and `cmp_315_Xplus1_current_vs_diag.png`.
- **Flag:** `render_diag_limits.py check|sheet --irislimits diag`, a copy of Base Eyes' render_diag.py. It writes only here.
- **rig/index.html** has no diagonal views today, so a `?irislimits=diag` switch there would have nothing to act on. When the diagonal eye rigs go live, the switch is: replace each eye's `irisLimitsPx` with `diag_irislimits.json[angle].eyes[eye].irislimits_diag` (dx keys only) when `?irislimits=diag`. Default unchanged.
- **For Base Eyes:** verify with `python3 rig/work/irislimits/compute.py` and `render_diag_limits.py sheet --irislimits diag`.

## v2 (03:00 PT, after Base Eyes' review in eyes/qa/irislimits_diag/): `compute2.py` → `diag_irislimits_v2.json` (+ `_flat.json`)
- **Row by row:** the iris is clipped per row by her white, i.e. the opening between her lid line and lash. The single corner-column clamp is gone.
- **Limit:** a side's range is the largest dx whose clip at the X±1 extreme (shifted iris core px outside the white) is ≤ that eye's Y±1 baseline clip (cap 14).
- **Linked gaze:** one value drives both eyes, each scaled to its own range. Per side, r = min(r, other + 1), and r = 0 if the other eye has 0 on that side.

| angle | eye | v1 dx −1/+1 | v2 dx −1/+1 | iris px lost X−1 / X+1 | Y±1 baseline | of |
|---|---|---|---|---|---|---|
| 045 | EyeL (near) | −4 / +3 | **−3 / +2** | 14 / 5 | 14 | 107 |
| 045 | EyeR (far) | 0 / 0 | **−3 / +1** | 3 / 8 | 8 | 50 |
| 315 | EyeR (near) | −3 / +4 | **−2 / +4** | 5 / 12 | 13 | 85 |
| 315 | EyeL (far) | 0 / +1 | **−1 / +3** | 7 / 10 | 10 | 51 |

- dy stays at ±1.
- Verified with a copy of Base Eyes' own `verify_irislimits.py` pointed at v2 (`verify_v2/`): 72 cases per angle, outside opening 0, on lid/lash ink 0, and rest diag vs current 0 px.
- The X±1,Y±1 corners still lose more than the baseline, as they already do with the current limits: 045 EyeL X−1,Y−1 loses 27; 315 EyeR X+1,Y−1 loses 22 (current: 17).
- Requiring the corners as well forces dx = 0 for every eye, because Y±1 alone already sits at the baseline. That is left as a choice for Base Eyes: clamp the corners with a radial limit, or accept them.

## v3 (03:05 PT): oval gaze clamp + v2 limits (`diag_irislimits_v3.json`, verified by `verify_v3.py` → `verify_v3/`)
- If gx² + gy² > 1, both are scaled onto the oval, so the corners land at 0.707 each. Then dx = round(gx·range) and dy = round(gy·1).
- Because 0.707 rounds to 1 px, **dy at the corners is unchanged** and only dx shrinks.
- All 9 gaze positions × 8 lid frames × both eyes: iris outside the opening 0, lid/lash crossings 0, rest diag vs current 0 px.
- Iris px lost at the corners vs the eye's Y±1 baseline. The 5 corners (of 16) that still exceed it:

| corner | offset (dx, dy) | lost | baseline | over by |
|---|---|---|---|---|
| 045 EyeL X−1,Y−1 | (−2, −1) | 22 | 14 | +8 |
| 045 EyeR X+1,Y−1 | (+1, −1) | 14 | 8 | +6 |
| 045 EyeR X+1,Y+1 | (+1, +1) | 10 | 8 | +2 |
| 315 EyeR X+1,Y−1 | (+3, −1) | 19 | 13 | +6 |
| 315 EyeL X−1,Y−1 | (−1, −1) | 15 | 10 | +5 |

## v4 (03:10 PT): whole-px corners (`compute4.py` → `diag_irislimits_v4.json`; `verify_v4.py` → `verify_v4/`)
- dy stays at ±1, and the X-only extremes (Y = 0) are as in v2.
- At each of the 16 eye-corners, the v3 oval dx is reduced 1 px at a time (down to 0) until the iris lost is at or under that eye's Y±1 baseline.
- Then the v2 link rule is applied per corner: same direction, within 1 px, and 0 if the other eye is 0.
- Full verify, 9 gaze × 8 lid frames × both eyes at 045 and 315:
  - outside opening 0 and lid/lash crossings 0 in every case;
  - rest diag vs current 0 px;
  - all 16 corners at or under baseline.
- Every up-corner (Y−1) ends with dx = 0. Its Y−1 loss already equals the baseline, so any sideways px exceeds it.
- Two corners are 0 **only because of the link rule**:
  - 045 EyeR X−1,Y−1 alone could take −2 (loses 1), but EyeL there is 0.
  - 315 EyeL X+1,Y−1 alone could take +2 (loses 7), but EyeR there is 0.
  - A looser "within 1 px, 1 vs 0 allowed" link would let them move ±1.
