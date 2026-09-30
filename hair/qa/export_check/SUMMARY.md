# Hair vs puppet export clips + clean-room stills + apose-turn: read-only QA (2026-09-30, ~02:20-03:00 PT)
Owner: Base Hair. Nothing outside `hair/qa/export_check/` was changed. No hair part, rig.json or spring was touched. `validate_hair.py` was not run because it writes `hair/validation.json`.
Sources: `reference/grok_build` commit 0596d8a (`public/puppet/export/clips/*.json`, 12 fps), `clean-room/layers/hierarchy/still/*`, and the shared turn frames `reference/apose_turn/frames/f001..f241.png` (24 fps).

## Files
- `sim.py`: a line-for-line Python port of `rig/index.html` `stepHair` + `headPose` (FNV phase hash, wind, gravity `clamp(-a/6)*g`, velocity kicks, 1/120 s substeps, child low-pass, clamp of x to [-1,1]). `run_sim.py` writes `sim_results.json` (every view/clip/input/setting/part) and `worst.json`.
- `frame_check.py` renders the worst frames with the real hair PNGs, the rig pivots, the per-part drives and chains, and dy. Output: `frame_check.json` and **`worst_frames_sheet.png`**, plus the zoom `zoom_side_back.png`.
- `survey_stills.py` writes `stills_survey.json`, `stills_hair_sheet.png` (20 sampled), and `stills_side_back_sheet.png` (12 side/back, hair tinted red).
- `turn_measure.py`, `turn_compare.py` and `turn_clean.py` write `turn_measure.json`, `turn_compare.json` and `turn_clean.json`. `turn_sheet.py` makes **`turn_sheet.png`**. `turn_zoom_0_90_180_270.png` is a 2x zoom of the matched pairs.

## Method (task 1)
- The clips contain joints torso, hinge, neck and head. In the puppet skeleton (mesh.ts) the chain is torso -> hinge -> neck -> head. **idle and look have all joints = 0.** look is a view-yaw change only (gaze 0/45/315), so hair gets wind only. wave moves only neck and head (max 3.8 deg total).
- I tested three head inputs:
  - **ref**: the full puppet head motion, torso+hinge+neck+head, through FK. Puppet joint positions are scaled onto our canvas, so hair_front pivot velocity is realistic. This gives peak head angles of 138.8 deg (hinge) and 140 deg (collapse).
  - **rig8**: what our rig can play today. hinge maps to BodyLean, clamped to the torso maxRotDeg of 8 deg, and the head is a rigid child of the torso. Our rig has no neck or head joint.
  - **rig12**: the same, with BodyLean raised to 12 deg.
- Settings:
  - current: roots f1.1 z0.3, children f1.0 z0.3, smoothing 0.09 s, gravity 0.8.
  - A: f4.0 z0.8, smoothing 0.03, gravity 0.4 (for roots and children).
  - B: f2.0 z0.6, smoothing 0.05, gravity 0.8.
- Timeline: 4 s of wind pre-roll, then the clip (1 s clips are played 3x back to back; idle and look are played once, 9 s), then 5 s of rest.
- Head-driven response is the run minus a wind-only baseline with the same t. Settle means the head-driven response stays inside 5% of the limit after the clip ends. Overshoot is how far the peak head-driven x goes past the static gravity target g, in %, and is only measured when the head exceeds 6 deg (the point where gravity saturates). Rebound is the opposite-sign swing after the clip, as a fraction of the limit.

## Task 1 results
**Key structural fact: the rendered angle can never exceed a part's limit.** The code computes `angle = swayWeight*maxSwayDeg*clamp(x)` and clamps x to [-1,1] every step. All swayWeight values are <= 1, so no part renders past its own maxSwayDeg in any clip or setting. "Over limit" therefore shows up in two forms:
1. **Clamp saturation**: the spring's unclamped demand exceeds +-1, so the strand pins at +-w*maxSwayDeg (a visible hard stop). The table shows the demand in degrees beyond the limit.
2. **Chain sum on tips**: root angle + tip angle vs the tip's own maxSwayDeg. The tip's local angle stays within its limit, but its world swing relative to the head does not.

Frame notation `(k, loop)` means clip frame k (12 fps) in play-through loop 0/1/2. "parts clamped" counts all 37 swaying parts across the 5 views.

| clip | head input | setting | peak head deg | parts clamped (all views) | max demand over limit deg (part/view/frame) | max chain Sum over tip maxSwayDeg (tip/view/frame) | peak/limit | overshoot % past gravity target | rebound (x of limit) | settle s (5%) |
|---|---|---|---|---|---|---|---|---|---|---|
| hinge | ref | current | 138.79 | 37/37 | +1.20 (strand_07/apose/(3, 0),(3, 1),(3, 2)) | +6.06 (strand_01_tip/right/f07/loop0) | 1.00 | 51 | 0.68 | 2.17 |
| hinge | ref | A | 138.79 | 0/37 | 0 | 0 | 0.59 | 9 | 0.00 | 0.15 |
| hinge | ref | B | 138.79 | 31/37 | +0.37 (strand_07/apose/(2, 1),(2, 2),(3, 1)) | +5.66 (strand_01_tip/right/f05/loop1) | 1.00 | 30 | 0.06 | 0.47 |
| hinge | rig8 | current | 8.0 | 37/37 | +0.30 (strand_01_tip/right/(7, 0),(8, 0),(9, 0)) | +5.38 (strand_01_tip/right/f07/loop0) | 1.00 | 45 | 0.47 | 2.28 |
| hinge | rig8 | A | 8.0 | 0/37 | 0 | 0 | 0.57 | 0 | 0.00 | 0.15 |
| hinge | rig8 | B | 8.0 | 0/37 | 0 | +4.70 (strand_01_tip/right/f05/loop1) | 0.97 | 8 | 0.08 | 0.52 |
| hinge | rig12 | current | 12.0 | 37/37 | +0.31 (strand_01_tip/right/(7, 0),(8, 0),(9, 0)) | +5.47 (strand_01_tip/right/f08/loop1) | 1.00 | 47 | 0.48 | 2.28 |
| hinge | rig12 | A | 12.0 | 0/37 | 0 | 0 | 0.57 | 0 | 0.00 | 0.15 |
| hinge | rig12 | B | 12.0 | 0/37 | 0 | +4.76 (strand_01_tip/right/f05/loop1) | 0.97 | 9 | 0.08 | 0.52 |
| wave | ref | current | 3.84 | 0/37 | 0 | 0 | 0.48 | n/a (<6 deg) | 0.11 | 1.00 |
| wave | ref | A | 3.84 | 0/37 | 0 | 0 | 0.32 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | ref | B | 3.84 | 0/37 | 0 | 0 | 0.45 | n/a (<6 deg) | 0.03 | 0.13 |
| wave | rig8 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | rig8 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | rig8 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | rig12 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | rig12 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| wave | rig12 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | ref | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| look | ref | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | ref | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig8 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig8 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig8 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig12 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig12 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| look | rig12 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | ref | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | ref | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | ref | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig8 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig8 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig8 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig12 | current | 0 | 0/37 | 0 | 0 | 0.29 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig12 | A | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| idle | rig12 | B | 0 | 0/37 | 0 | 0 | 0.23 | n/a (<6 deg) | 0.00 | 0.00 |
| reach | ref | current | 2.0 | 0/37 | 0 | 0 | 0.56 | n/a (<6 deg) | 0.24 | 1.63 |
| reach | ref | A | 2.0 | 0/37 | 0 | 0 | 0.28 | n/a (<6 deg) | 0.00 | 0.00 |
| reach | ref | B | 2.0 | 0/37 | 0 | 0 | 0.43 | n/a (<6 deg) | 0.02 | 0.12 |
| reach | rig8 | current | 8.0 | 37/37 | +0.44 (strand_07/apose/(5, 1),(5, 2),(6, 0)) | +5.92 (strand_01_tip/right/f09/loop1) | 1.00 | 40 | 0.55 | 2.23 |
| reach | rig8 | A | 8.0 | 0/37 | 0 | 0 | 0.55 | 0 | 0.00 | 0.08 |
| reach | rig8 | B | 8.0 | 26/37 | +0.03 (strand_07/apose/(4, 1),(4, 2),(5, 2)) | +5.19 (strand_01_tip/right/f06/loop1) | 1.00 | 8 | 0.07 | 0.43 |
| reach | rig12 | current | 12.0 | 37/37 | +0.48 (strand_07/apose/(4, 1),(5, 0),(5, 1)) | +5.87 (strand_01_tip/right/f09/loop1) | 1.00 | 43 | 0.52 | 2.20 |
| reach | rig12 | A | 12.0 | 0/37 | 0 | 0 | 0.55 | 2 | 0.00 | 0.08 |
| reach | rig12 | B | 12.0 | 31/37 | +0.13 (strand_07/apose/(4, 1),(4, 2)) | +5.22 (strand_01_tip/right/f06/loop1) | 1.00 | 10 | 0.07 | 0.43 |
| twist | ref | current | 14.0 | 37/37 | +0.74 (strand_07/apose/(3, 1),(4, 0),(4, 1)) | +6.00 (strand_01_tip/right/f08/loop1) | 1.00 | 48 | 0.53 | 2.17 |
| twist | ref | A | 14.0 | 0/37 | 0 | 0 | 0.56 | 3 | 0.00 | 0.08 |
| twist | ref | B | 14.0 | 31/37 | +0.25 (strand_01/tpose/(3, 1),(3, 2),(4, 1)) | +5.31 (strand_01_tip/right/f06/loop1) | 1.00 | 15 | 0.07 | 0.42 |
| twist | rig8 | current | 8.0 | 37/37 | +0.31 (strand_01_tip/right/(10, 0),(10, 1),(10, 2)) | +5.75 (strand_01_tip/right/f09/loop1) | 1.00 | 43 | 0.52 | 2.27 |
| twist | rig8 | A | 8.0 | 0/37 | 0 | 0 | 0.56 | 0 | 0.00 | 0.12 |
| twist | rig8 | B | 8.0 | 0/37 | 0 | +5.02 (strand_01_tip/right/f06/loop1) | 0.99 | 8 | 0.08 | 0.48 |
| twist | rig12 | current | 12.0 | 37/37 | +0.32 (strand_01_tip/right/(10, 0),(10, 1),(10, 2)) | +5.83 (strand_01_tip/right/f08/loop1) | 1.00 | 45 | 0.51 | 2.23 |
| twist | rig12 | A | 12.0 | 0/37 | 0 | 0 | 0.56 | 0 | 0.00 | 0.12 |
| twist | rig12 | B | 12.0 | 0/37 | 0 | +5.09 (strand_01_tip/right/f05/loop1) | 1.00 | 9 | 0.07 | 0.47 |
| collapse | ref | current | 140.0 | 37/37 | +1.72 (strand_03/right/(2, 0),(2, 1),(2, 2)) | +6.06 (strand_01_tip/right/f06/loop0) | 1.00 | 52 | 0.68 | 2.12 |
| collapse | ref | A | 140.0 | 0/37 | 0 | 0 | 0.62 | 15 | 0.00 | 0.15 |
| collapse | ref | B | 140.0 | 31/37 | +0.60 (strand_03/right/(1, 1),(1, 2),(2, 1)) | +5.61 (strand_01_tip/right/f04/loop1) | 1.00 | 45 | 0.05 | 0.47 |
| collapse | rig8 | current | 8.0 | 37/37 | +0.30 (strand_01_tip/right/(7, 0),(8, 0),(9, 0)) | +5.37 (strand_01_tip/right/f07/loop0) | 1.00 | 45 | 0.47 | 2.28 |
| collapse | rig8 | A | 8.0 | 0/37 | 0 | 0 | 0.57 | 0 | 0.00 | 0.15 |
| collapse | rig8 | B | 8.0 | 0/37 | 0 | +4.74 (strand_01_tip/right/f05/loop1) | 0.97 | 8 | 0.08 | 0.52 |
| collapse | rig12 | current | 12.0 | 37/37 | +0.30 (strand_01_tip/right/(7, 0),(8, 0),(8, 1)) | +5.54 (strand_01_tip/right/f08/loop1) | 1.00 | 47 | 0.47 | 2.27 |
| collapse | rig12 | A | 12.0 | 0/37 | 0 | 0 | 0.56 | 0 | 0.00 | 0.15 |
| collapse | rig12 | B | 12.0 | 0/37 | 0 | +4.79 (strand_01_tip/right/f05/loop1) | 0.97 | 9 | 0.08 | 0.52 |

Bun (limit 0.3*4 = 1.2 deg): it clamps at -1.2 deg in every view under current (worst demand +0.21 deg over, collapse/ref, right view) and slightly under B (<= +0.07 deg). It never clamps under A.

### Summary of task 1
- **Current settings:**
  - Every head input that passes 6 deg (hinge, collapse, twist, and reach with rig8/12) pins **all** strands and the bun at their limits.
  - Demand is up to **+1.72 deg** over the limit (collapse/ref, strand_03 right, frames 1-2). Under rig8/12 it is ~+0.3-0.5 deg.
  - Tip chain sums reach **16.2 deg vs the tip maxSwayDeg 10.1 (+6.06 deg)** (right strand_01_tip, hinge f07 / collapse f06). In apose, strand_03_tip reaches 15.2 vs 10 (+5.2) and strand_06_tip 14.1 vs 10 (+4.1). In left, strand_04_tip reaches ~14.7 vs 10. In tpose, strand_06_tip reaches 11.4 vs 10.
  - Overshoot is 40-52% past the gravity target, rebound 0.47-0.68 of the limit, and **settle 2.1-2.3 s**. The 1 s clips never settle between loops.
- **BodyLean 12 vs 8:** almost no difference. Gravity saturates at a 6 deg head angle, so both limits give the same targets. Only the velocity kicks rise slightly (reach clamp demand +0.44 -> +0.48 deg; B reach 26 -> 31 clamped parts).
- **A:** nothing clamps in any clip or view. Peak is <= 0.62 of the limit, no chain sum passes a tip limit, overshoot <= 15%, no rebound, and settle is 0.08-0.15 s. Motion is small (roughly half the swing), and it moves almost rigidly with the head. That matches the earlier clean-room finding (hair rigid with the head, lag < 1 frame).
- **B:** with rig8/12 input, roots do not clamp except in reach, where 26-31/37 parts clamp by only +0.03 to +0.13 deg. With ref input, roots still clamp by +0.25 to +0.60 deg. Tip chain sums still pass the tip maxSwayDeg by +4.7 to +5.7 deg in every lean clip. Rebound is <= 0.08 and settle 0.42-0.52 s.
- idle, look and wave: nothing clamps under any setting (wind only, or <= 3.8 deg of head motion).

## Task 2: eye/mouth crossing and ear/neck gaps (all five views)
- For each view and setting I took the sim frame with the largest total sway of each sign, plus the 4 envelope corners (all parts at s = +-1 and sy = +-1; every setting is bounded by these because of the clamp). Each was composited with the real PNGs in renderer order: hair <200, then base_body, then face parts, then hair >=200.
- **Eye/mouth crossing: 0 px in every pose and view, including a 2 px dilated zone.** The forbidden mask is the union of all eye and mouth PNG alphas (back has none). The tip chain sums above therefore do **not** reach the face.
- **Revealed pixels at peak sway** (where a swaying strand covered pixels at rest that it no longer covers):
  - Front and 3/4-front views: the revealed pixels are cheek and temple skin that the strands lie on (magenta on the sheet). This is the drawn face, not a hole.
  - Side views: skin in front of the ear and on the cheek. No white shows behind the ear.
  - Back: background beside the neck, where the nape wisps hang free outside the silhouette.
  - **No white/unpainted pixels (0 px everywhere).**
  - Enclosed see-through pockets are tiny: <= 64 px back and <= 48 px right, 1-2 px slivers between a wisp and the neck edge.
  - **No visible ear or neck gap.** The earfill/base_body under the hair holds at the envelope.
- Sheet: `worst_frames_sheet.png`. Colours: red = hair on eye/mouth (none), cyan = eye/mouth zone, magenta = revealed skin, yellow = revealed background, orange = enclosed hole.

## Task 3: clean-room hair.png stills (20 sampled across the 273, plus 12 side/back)
- Every still shows the same hairstyle as ours: a **high updo with a round top bun**, pulled-back sides, and thin loose face-framing tendrils hanging to about the jaw or upper neck. Side and back stills show the bun at the top-back and short nape wisps.
- **None of the sampled stills show long hanging hair.** The earlier "side/back refs are much longer" impression does not hold for the clean-room stills or for the turn video (task 5).
- The hair.png layers are dirty and are not a usable layer standard:
  - Many include non-hair: bra/top straps, face and jaw lines, shoulder outlines, even arms (set-16-10p2, xknee, set-17-3).
  - Boxes are loose.
  - Their bbox height is 0.24-0.32 of figure height vs ours at 0.16-0.19. That difference comes from the contamination, not longer hair.
- Useful for reference only, e.g. tendril placement and bun silhouette.

## Task 5: apose-turn frames (shared extract, not decoded by me)
- **Yaw estimate.** The waist-row width extremes give the keys: f001 = 0 (front), f061 = 90 (profile, face screen-left = her left side = our `left`), f109 = 180 (back), f161 = 270 (our `right`), and f229-f241 = 360 (a front hold, identical to f001).
  - Frames in between are interpolated with acos of the normalized width.
  - An independent check from the bun offset (bun_dx ~ 0.30*sin(yaw)) agrees within ~5 deg at 25-60 deg (f025 25 vs 30, f034 43 vs 46, f041 57 vs 61).
  - Treat the estimate as +-10 deg. The turn is eased: 60 frames for 0-90, 48 frames for 90-180, and so on.
- **Matched views** (the metric is identical for ours and the video; lengths are fractions of figure height, bun offsets are in skull widths):

| yaw | video frame | video hair lowest pt | ours | ours lowest pt | bun dx video / ours | visible bun height / skull W video / ours |
|---|---|---|---|---|---|---|
| 0 | f001 | 0.166 | apose | 0.180 | -0.01 / 0.00 | 0.24 / 0.28 |
| 90 | f061 | 0.164 | left | 0.161 | +0.29 / +0.23 | 0.20 / 0.20 |
| 180 | f109 | 0.172 | back | 0.152 | -0.02 / 0.00 | 0.29 / 0.27 |
| 270 | f161 | 0.166 | right | 0.159 | -0.29 / -0.20 | 0.24 / 0.20 |

- **Disagreements** (a flag list only; nothing changed):
  1. **Back:** the video's nape hair and wisps hang lower (0.172 vs 0.152 of figure height, ~2% of figure, ~30 px on our canvas). Hair area is ~11% larger (127 vs 113, normalized). This is *slightly* longer at the nape, not long hanging hair.
  2. **Side views:** the video bun sits further back on the head (0.29-0.30 vs 0.20-0.23 skull widths behind the skull centre). In our left/right the bun is ~25% closer to the crown. Video side hair area is ~10% larger (116-118 vs 105-109), mostly a fuller back-of-head.
  3. **Front:** our face-framing tendrils hang slightly lower (0.180 vs 0.166) and our bun reads ~15% taller. Otherwise the front matches closely.
  4. **Ears:** in both, ears are uncovered at 90/270 with hair swept behind them and a wisp in front. From the back, both show small ear tips. Consistent.
- **Bun layer switch (101 -> 650).** bun_dx follows ~sin(yaw) and peaks at the profiles (+0.299 at f065, -0.29 at f157-f165). That means the bun is centred directly behind the head.
  - It is behind the head centre for yaw < ~90 (f001-f061) and in front of it for ~90-270 (f062-f160). It goes back behind after ~270 (f161-f229).
  - So the switch is at the profiles: **~f061-f065 going in, ~f157-f161 coming out**.
  - Our side views, at exactly 90, use 650. That is consistent (the bun outline overlaps the back skull in f061). 3/4-front parts (30-60 deg) should keep 101. 3/4-back parts (120-150) should use 650.
- **Clean frames for future parts** (from the hair's point of view):
  - 0 deg: f001-f005, or f229-f241 (static hold).
  - 30: f025 (f024-f026). Mirror: f200.
  - 45: f034 (f033-f035). Mirror: f191.
  - 60: f041 (f040-f042). Mirror: f182.
  - 90: f061 (f057-f065 plateau). Mirror: f157-f163.
  - 180: f105-f109.
  - 3/4-back: f086 (~135) and f132 (~225).
  - Frame-to-frame difference is smooth with no spikes, so there are no pops or morph glitches.
  - Every frame has a blue key fringe on hair edges, so any trace needs a despill.
  - Head-crop sharpness is lower for f062-f158 only because those frames show mostly flat black hair, not because of blur.
- Sheet: `turn_sheet.png`. Top row: video frames at 0/30/45/60/90/135/180/225/270/300/315/330. Bottom row: our apose/left/back/right under the matching yaw.

## User's new tools (reference/grok_build)
- **0596d8a itself adds no scripts.** It adds:
  - `src/lib/puppet/clips.ts`: `sampleClip`, `CLIP_KEYS`, `eyeFor`, `gazeFor`, the sampler behind the export JSONs. `hair: null`.
  - `public/clean-room/index.html`: layer-lane visibility toggles, an eye/blink compositor preview, and `drawRig`.
  - `clean-room/layers/anim/index.json`: one decoded 1.2 s frame per video, "not rig layers".
  - `clean-room/rig/apose.json` and `eyes/rig.json`.
- The helper tools arrived in 1dc06ca (the first export):
  - `freebuff/Shadowveil_Freebuff_Handoff/tools/verify_bundle.py`: read-only SHA-256 check of the handoff against PACKAGE_MANIFEST.
  - `extract_art.py`: extracts hash-verified embedded images from the catalog HTML and refuses to overwrite.
  - `driver-work/scripts/build-driver.mjs`: builds the standalone Driver Foundation HTML.
  - `activate-driver.mjs`: **writes** Studio.tsx and package.json, with a backup.
  - `serve-driver.py`: a loopback server, **default port 8765, the same port as our rig server**, so don't run both at once.
- **Useful for hair: essentially none.** Every channel has `hair: null` and the clips declare no hair channel. The only hair data is the rough hair/eyes/mouth boxes per view in `driver-work/src/lib/puppet/driver/arm-views.ts` (512-px puppet space). `extract_art.py` could pull catalog art if we ever need it.

## Conclusions
1. No clip, setting or BodyLean limit makes any part *render* past its maxSwayDeg. Under current settings, however, every lean clip (hinge, collapse, twist, reach) pins all strands and the bun at the clamp, overshoots ~50%, rebounds ~0.5-0.7 of the limit, and needs ~2.2 s to settle. Tip chain sums reach +4 to +6 deg past the tip limit.
2. **A removes all clamping, all chain-over, overshoot and rebound.** It matches the rigid-with-head reference but halves the visible swing. **B** fixes rebound and settle (~0.5 s) but still clamps roots on large head motion and keeps the tip chain sums over the limit. BodyLean 12 changes nothing material.
3. There is no eye/mouth crossing and no ear/neck gap at any reachable pose, so the tip chain sums are cosmetic, not a contract break.
4. The turn video and clean-room stills agree with our updo. The only flags are the slightly longer nape wisps in back (~2% of figure height) and the bun sitting ~0.07 skull widths further back in the side views.
