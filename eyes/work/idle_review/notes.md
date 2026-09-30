# Eye review: Coder's idle battle-test renders (read-only)

**Source:** the lossless PNG frames the renders were made from, `rig/previews/idle/frames/<run>/frames/f0000–f0239.png`, plus each run's `meta.json`, which holds the per-frame params. I used these instead of decoding the mp4s.
- 30 fps, 8 s.
- Frame N plays at t = (N+1)/30 s, the same convention as Coder's QA names.
- **16 runs:** the auto idle plus the idle_breathe, idle_weight_shift and idle_arm_settle keys, each in apose, tpose, left and right. back has no eyes.
- Nothing under `views/` or `rig/` was changed.

**Method** (`analyze.py`, one run at a time, crops only):
1. Align each frame to rest on the face around the eyes (ECC, Euclidean, eyes masked out).
2. Re-composite the expected eye from the view's own parts, using the lid frame and iris offset the params imply. I checked that this composite for lid 0 equals rest exactly in all 4 views.
3. Fit the best lid frame and iris offset, the eye-vs-face slide, alpha holes and new white pixels.

## Rest
- Frame 0 of each auto run is identical to rest.png.
- rest.png equals base.png exactly inside every eye part (0 px differ).
- The only rest vs base differences near the eyes are at the edge of the workRegion (hair and silhouette, max 3–22, no eye pixels).

## 1) Blinks
The schedule is the same in every view. The keys runs are shifted +1 frame.

| blink | lid frame per video frame (0 = open, 7 = shut) | close | shut hold | reopen | total |
|---|---|---|---|---|---|
| #1: f0047–f0051 (t 1.600–1.733 s) | 3, 7, 6, 3, 1 | 33 ms | 33 ms fully shut (67 ms ≥ lid 6) | 67 ms | 167 ms |
| #2: f0060–f0065 (t 2.033–2.200 s) | 1, 6, 7, 4, 2, 1 | 67 ms | 33 ms (67 ms) | 100 ms | 233 ms |
| #3: f0231–f0235 (t 7.733–7.867 s) | same as #1 | 33 ms | 33 ms | 67 ms | 167 ms |

- **Keys runs:** f0048–52, f0061–66 and f0232–36.
- **Count:** 3 blinks per 8 s.
- **Intervals:** 13 frames = 0.43 s (#1 → #2, a double blink), then 171 frames = 5.70 s (#2 → #3).
- **Against the reference** (total 333 ms: close 42, hold 250, reopen 125; interval 2.5 to more than 5 s):
  - Close and reopen are about right.
  - The shut hold is about 4–7× too short (33–67 ms vs 250 ms), so the total is 167–233 ms.
  - The 0.43 s double blink has no counterpart in the reference clips.
  - The 5.7 s gap is fine.
- **Both eyes together:** in all 16 runs the lid frame drawn in the pixels matches the params on every frame, and EyeR and EyeL use the same lid frame on the same frame.
- **Only the upper lid moves:** yes.
- **Crease pop:** as soon as the lid leaves frame 0 (lid 1 and up), the lid crease line disappears and the upper lash gets thinner. It comes back at lid 0. This shows as a pop at the first and last frame of each blink, for example apose f0051 vs f0052 (`sheet_blink_apose.png`) and left/right f0051 vs f0052 (`sheet_blink_profiles.png`). Seen in all views.

## 2) White, background, gaps and specks
- **A (all front runs): white line above the iris when gaze is down.** When EyeBallY > 0.25, the iris moves 1 px down (dy = +1) and a flat 1-px pale/white row of the backfilled sclera shows between the upper lash and the iris top, in both eyes.
  - Auto apose/tpose: f0116–f0239 (t 3.9–8.0 s), eyes open. Brightest on the sharp frames (f0136–138, f0224–228).
  - Keys apose/tpose: f0117–f0189.
  - Profiles aren't affected (dy stays 0 there).
  - Sheet: `sheet_gaze_down_white.png` (rest / f0110 / f0136 / f0200).
- **B (right view, auto): white speck at the front edge of the iris.** A 1-px white speck at about (760, 215) whenever the iris steps −1 px toward the eye centre: f0190–f0213 (t 6.37–7.13 s; seen at 190, 200 and 212). It comes from the white part's front-edge column. Not in the keys runs, where the horizontal gaze offset stays 0. Sheet: `sheet_right_speck.png`.
- **C (all 4 tpose runs): background showing near EyeR.** Blue (transparent) pixels show along a hair-strand line above the outer corner of EyeR, at x ≈ 630–632, y ≈ 205–210 (9–13 px from the sclera, inside the lid parts' footprint). 1–19 px per frame, in 196–219 of 240 frames per run, from f0002 in auto and f0000 in the keys runs.
  - It sits where the tpose hair wisp was cut out of the EyeR parts, so it's most likely a hair/eye seam that opens as the hair sways.
  - Not seen in apose, left or right.
  - Sheet: `sheet_tpose_hole.png`.
- **D (right view): small light specks during blinks.**
  - A faint light tail at the front end of the closed lash line (f0048 and f0062, lid 7).
  - 1–4 bright px during the partial frames: auto f0047 and f0050–55; arm_settle right f0047, f0048, f0052.
  - Sheet: `sheet_blink_profiles.png`.
- **Nothing else found:** no alpha holes in the lid, lash or iris areas and no new white in apose, left or tpose outside A–C.

## 3) Iris inside the opening and gaze size
- **The iris never leaves the opening.** It is drawn source-atop on the white, and the fitted offsets always match the rule exactly in the front views.
- **Offsets actually drawn:**

| view | auto idle | as fraction of eye width |
|---|---|---|
| apose | dy +1 from f0116; dx −2 at f0190–f0213; dx +1 at f0214–f0239 | 0.06 / 0.03 of 34 px |
| tpose | same timing, dx −1 / +1 | ≤ 0.03 of 32 px |
| left | dx +1 at f0190–f0213 only | 0.056 of 18 px |
| right | dx −1 at f0190–f0213 | 0.04 of 24 px; the other ±1 fits in the right view are sub-pixel fitting noise |

- **Keys runs:** X ≤ 0.19, so there's no horizontal gaze. Only dy +1 at f0117–f0189 in the front views.
- **Against the reference (~0.1 eye width):** at most 0.06, so smaller than the reference but in the same direction.
- **Timing:** gaze changes are 0.8 s holds with no glances back.

## 4) Eyes sliding on the face
The table shows how far each eye moves relative to the aligned face, and how far the face itself moves.

| run type | eye slide vs face | face moved |
|---|---|---|
| front views | ≤ 0.17–0.32 px (p95 ≤ 0.27) | auto ±2 px / ±0.3°; weight_shift −36…+17 px, −3.9…+1.9° |
| profiles | ≤ 0.4–0.66 px (p95 ≤ 0.5) | – |

All sub-pixel and within resampling noise, so there is no visible sliding. Per-run numbers are in `summary.json`.

## 5) Sharp/soft head flicker
- On axis-aligned frames the head is drawn without resampling. There the eye region is about 2× sharper than on soft frames (Laplacian variance median 5600 vs 2800; rest is 4952).
- Lash and iris edges visibly snap crisp and then soften again.
- **Sharp frames:**

| run | sharp frames | toggles |
|---|---|---|
| auto (all views) | f0000, f0067–69, f0136–138, f0224–228 | 7, at 1, 67, 70, 136, 139, 224, 229 |
| breathe | f0000–03, f0042, f0104–106, f0119–121, f0239 | – |
| arm_settle | f0049, f0070, f0142, f0163–167 | – |
| weight_shift | none | – |

- Soft frames also vary from 1400 to 4500 with sub-pixel phase, which reads as a mild shimmer.
- The flicker makes defect A most visible (f0136). Sheet: `sheet_flicker.png` (f0066 soft / f0067 sharp / f0070 soft / f0136 sharp / f0139 soft).

## 6) Left-profile reversed gaze (export.py line 355)
It **does show in the auto idle**:
- **f0190–f0213 (t 6.37–7.13 s):** EyeBallX = −0.72 (her right, away from camera). The iris moves +1 px toward the back / eye centre, which is the wrong way. It should stay put or move toward the front.
- **f0214–f0239 (t 7.17–8.0 s):** EyeBallX = +0.66 (her left, toward camera). The iris doesn't move, where it should move +1 px toward the eye centre.
- It's 1 px (0.056 of eye width), so it's subtle but real. Sheet: `sheet_left_gaze.png` (rest, f0150, f0200, f0210, f0216, f0225).
- It does **not** show in the keys runs, where X ≤ 0.19 rounds to 0 px.
- The right profile behaves correctly.

## Files
- **Scripts:** `params.py` (per-frame params → `params.json`), `expect.py`, `analyze.py` (→ `res_<run>.json`), `summarize.py` (→ `summary.json`), `sharp.py` (→ `sharp_<run>.json`), `speck.py`, `sheet.py`
- **Sheets:** each has rest first, then frames, with labels in header strips only (nothing drawn on her):
  - `sheet_blink_apose.png`
  - `sheet_blink_profiles.png`
  - `sheet_gaze_down_white.png`
  - `sheet_right_speck.png`
  - `sheet_left_gaze.png`
  - `sheet_tpose_hole.png`
  - `sheet_flicker.png`
- **Unreliable, not used:** `iris.py`/`iris2.py` (colour-based and sub-pixel iris trackers, too noisy on these small irises).
- **Scratch:** `tmp/`
