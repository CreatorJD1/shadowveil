# A-pose turn video: measurement report (measure-only)
Source: `reference/grok_build/public/clean-room/videos/apose-turn.mp4` (768×1168, 24 fps, 241 frames, one full 360° turn, blue key).
Frames used: Coder's extraction `/workspace/shadowveil/reference/apose_turn/frames/f001–f241.png`. These are pixel-identical to my own decode (checked all 241), so I deleted my copies.
Nothing in the video, `reference/` or `views/` was modified.

## Files
- `turn_table.csv` has, for every frame: angle and range, raw top/foot/H, rig-normalised widths (shoulder/bust/waist/hip/knee/ankle), bust/waist/hip y, leg length, arm reach, and quality metrics.
- `turn_measure.json` has the full per-frame data. `joints_rig_calibrated.json` has per-frame joint proxies in rig px. `ours_measure.json` and `ours_pivots.json` hold our views' reference values.
- `candidates/` contains 8 PNGs (plain copies), `notes.md`, and `candidates.json` (joints for the candidate ±3 frames).
- Scripts: `seg.py` (mask), `measure.py`, `run_all.py`, `joints.py`, `joints2.py`, `write_report.py`.

## Method
- **Mask:** a pixel counts as body when blue − max(r,g) ≤ 120. Components ≥ 200 px are kept and holes filled. Every frame is a single component.
- **Normalisation:** each frame is scaled so its top of head is at y40 and its foot line at y1682 (front, back, three-quarter) or y1681 (profile ±30°). x is centred on 681.5. The scale is about 1.54–1.59 rig px per video px.
- **Turn angle:** two cues.
  1. Silhouette span at 0.40·H (arm level) fitted to s(θ) = a|cosθ| + d|sinθ|, with a taken from f001/f109 and d from the profiles. The quadrant is set by anchors: f001 = 0°, f062 = 90° (min span), f109 = 180° (max span in the back half), f160 = 270°, f241 = 360°.
  2. Leg-centre separation at 0.60·H, which varies as |cosθ| (valid up to about 55°).

  The best estimate is the mean of the two cues, and the range between them is recorded as the uncertainty (±5–8°). Within about 25° of 0° or 180°, span barely changes, so those angles are interpolated between anchors. Visually the frames look closer to the lower (leg) cue.
  The turn is not uniform: 0–90° takes 61 frames, 90–180° takes 47, 180–270° takes 51, and 270–360° takes about 75. f230–f241 are front (≈360°).
- **Joints:** a silhouette can't show elbow, knee or wrist creases, so these are proxies.
  - Joint y is fixed per half, because turning about the vertical axis keeps y. Front-half y comes from f001, back-half y from f109. Placement along each limb uses our rig's own ratios.
  - x is measured per frame as the centre of the separated limb run at that y. Shoulder x = torso-run edge ∓22 px. Hip x = thigh centre at 0.53·H.
  - A constant offset makes f001 equal our apose rig and f109 equal our back rig, so the numbers compare with neighbouring angles.
  - '–' means the limb is merged into the torso or the other leg at that angle.
  - Knee and ankle y are placed by ratio, so they cannot show a mismatch.

## Height and foot line (before normalisation)
| frame | angle | raw H | vs f001 | raw foot | foot shift in rig px |
|---|---|---|---|---|---|
| f001 | 0 | 1055 | – | 1115 | – |
| f062 | 90 (faces viewer-left) | 1063 | +0.76% | 1119 | +6 |
| f109 | 180 | 1035 | −1.9% | 1087 | −44 |
| f160 | 270 (faces viewer-right) | 1061 | +0.57% | 1119 | +6 |

The figure shrinks and rises about 2% in the back half (camera/zoom drift). After per-frame normalisation every frame meets top 40 / foot 1682 (1681 for profiles) exactly. If a single fixed scale were used instead, the back frames would come out 31 px short with the foot line 44 px high.

## Front f001 vs views/apose (rig px; video − ours)
| | video | ours | Δ px | Δ % |
|---|---|---|---|---|
| shoulder width | 370.4 | 359 | +11.4 | +3.2 |
| bust | 214.8 | 215 | −0.2 | 0 |
| waist | 161.9 | 156 | +5.9 | +3.8 |
| hip | 286.4 | 286 | +0.4 | +0.1 |
| knee | 73.2 | 74 | −0.8 | −1.1 |
| ankle | 46.7 | 47.5 | −0.8 | −1.7 |
| leg length (crotch to ankle row) | 698.8 | 694 | +4.8 | +0.7 |
| arm reach (armpit to fingertip) | 527.3 | 522.6 | +4.7 | +0.9 |
| armpit y / shoulder joint y | 454 / 431 | 462 / 439 | −8 | |
| elbow y / wrist y | 557 / 700 | 565 / 706 | −8 / −6 | |
| hip joint y (crotch − rig offset) | 786 | 791.5 | −5.6 | |
| joint x (shoulder, elbow, wrist, hip, knee, ankle) | | | within ±2 | |

The front view is a close match. The video's shoulders are 3% broader, the waist 4% wider, and the shoulder line sits about 8 px higher.

## Profiles vs views/left and views/right
**Facing:** f062 (≈90°) faces viewer-left with toes toward −x, the same as our `left` view (toes x628 < ankle x710). f160 (≈270°) faces viewer-right, the same as our `right` view (toes x763 > ankle x655–663). No mirroring is needed to compare them.

| | f062 | ours left | Δ px (%) | f160 | ours right | Δ px (%) |
|---|---|---|---|---|---|---|
| shoulder depth | 148.2 | 164 | −15.8 (−9.6) | 148.5 | 164 | −15.5 (−9.5) |
| bust depth | 176.0 | 191 | −15.0 (−7.9) | 170.1 | 194 | −23.9 (−12.3) |
| waist depth | 132.8 | 146 | −13.2 (−9.0) | 120.6 | 142 | −21.4 (−15.1) |
| hip/butt depth | 169.8 | 181 | −11.2 (−6.2) | 173.2 | 178 | −4.8 (−2.7) |
| knee | 98.8 | 94 | +4.8 (+5.1) | 80.4 | 92 | −11.6 (−12.6) |
| ankle row* | 89.5 | 65 | +24.5 | 102.1 | 58 | +44 |
| bust y | 483 | 493 | −10 | 487 | 488 | −1 |
| waist y | 670 | 697 | −27 | 662 | 706 | −44 |
| hip (widest) y | 780 | 801 | −21 | 775 | 805 | −30 |

\*In profile the ankle row crosses both feet and the heel, so it is not a real ankle width.

In profile the video body is 6–15% slimmer front-to-back than ours. Its waist sits 27–44 px higher and its hip 21–30 px higher. The video's two profiles aren't mirror-consistent with each other (bust 176 vs 170, knee 99 vs 80), while our left and right agree within 4 px.

In profile the arm overlaps the torso and the legs overlap each other, so shoulder, elbow, hip and knee positions and limb lengths can't be measured from the silhouette. Only the front and three-quarter frames give joint x values.

## Back f109 vs views/back
| | video | ours | Δ |
|---|---|---|---|
| shoulder width | 358.5 | 361 | −0.7% |
| bust | 231.6 | 217 | +6.7% |
| waist | 155.5 | 162 | −4.0% |
| hip | 295.1 | 291 | +1.4% |
| knee | 82.5 | 78 | +5.8% |
| ankle | 41.2 | 48 | −14% |
| leg length | 661.6 | 712 | −50 px (−7.1%) |
| crotch y | 873 | 840 | +33 |
| arm reach | 544 / 540 | 513 | +6% |
| armpit / shoulder y | | | +16 |
| elbow y, wrist y | | | +14, +10 |
| elbow x | | | 15 px wider each side |
| wrist x | | | 36 px wider each side |
| ankle stance | 200 | 175 | +25 px |

The back frame has a lower crotch, a shorter leg, and arms spread wider. The back half is also the drifted-scale half.

## Three-quarter candidates (see candidates/notes.md)
- **Front side:** f023 (≈30° [23–37]), f033 (≈44° [37–51]), f041 (≈64° [59–69], far elbow hidden).
- **Back side:** f085 (≈134° [125–143]).
- **Mirror side:** f203 (≈329°), f191 (≈314°), f183 (≈298°), f129 (≈220°).

All eight: raw H within ±1.2% of f001, one component (no tears), about 1 px anti-aliased edges with no motion blur, and flat cel colour with light soft shading. The skin dark fraction is 3.5–5.9% against 2.7% on our apose base, so a little more shading than ours but no cast shadows. The foot line matches after normalisation; before it, the drift is +9 to +16 rig px (front side) and −25 to −31 (back side).

Avoid f130–f131 (softer edges, aa 1.39–1.42) and f034 (aa 1.26).

Joint x moves smoothly across the ±3 neighbours (see candidates.json). For example, the viewer-left elbow goes 455 → 466 → 477 over f020 → f023 → f026, and 492 → 506 → 524 over f030 → f033 → f036.


## Appendix: profile head measurements (added 02:40 PT, measure-only)
Frames: f061–f067 (facing viewer-left, compared with views/left) and f151–f163 (facing viewer-right, compared with views/right). Same per-frame scaling as above (top y40, foot y1681). Script: `head_measure.py`. Data: `head/head_profile.json` (every frame). Debug overlay: `head/dbg.png`.
- **Detectors.** Nose tip = the face-side extreme skin pixel at 0.105–0.140·H. Back of head = the rear silhouette extreme from eye−0.02·H to eye+0.03·H: below the bun, but it includes the hair volume. Ear = the rearmost skin run behind the eye (eye−0.005·H to eye+0.02·H). Eye = the eye opening (sclera + iris), without lashes or lid line. That is why the widths are smaller than Eyes' 24/19 figures.
- **Which frames are used.** Means are over the clean profile frames f061–f064 and f157–f162. f065–f067 and f151–f156 are already turning, so ear distance drifts ±5–15 px there.
- **Eye reliability.** The eye opening is detected reliably only in the left-facing frames (green iris). In the right-facing frames the amber iris is dim and close to skin hue, so the video eye numbers (*) are unreliable.

| measure (rig px) | video left-facing f061–064 | ours left | Δ ours−video | video right-facing f157–162 | ours right | Δ |
|---|---|---|---|---|---|---|
| head depth (nose tip to back of head at eye/ear height, hair incl.) | 201.4 | 215.3 | +13.9 (+7%) | 196.6 | 222.1 | +25.5 (+13%) |
| nose tip to ear front edge | 99.2 | 134.2 | +35.0 (+35%) | 102.2 | 137.1 | +34.9 (+34%) |
| nose tip to ear centre | 103.8 | 135.7 | +31.9 (+31%) | 104.9 | 138.6 | +33.7 (+32%) |
| nose tip to eye front corner (opening) | 23.9 | 29.0 | +5.1 (+21%) | 12.4* | 34.0 | +21.6 |
| nose tip to eye back corner | 33.6 | 48.1 | +14.5 (+43%) | 15.5* | 52.0 | +36.5 |
| eye opening width (sclera+iris) | 11.2 | 20.0 | +8.8 (+79%) | 4.6* | 19.0 | +14.4 |
| eye y | 224.1 | 212.6 | -11.5 (-5%) | 215.0* | 216.3 | +1.3 |
| nose tip y | 258.3 | 238.2 | -20.1 (-8%) | 253.6 | 243.1 | -10.5 (-4%) |

**Findings**
- **Our heads are deeper.** Nose to back of head is +14 px (+7%) on left and +26 px (+13%) on right.
- **Depth alone doesn't explain it.** Scaling the video head uniformly by 1.07–1.13 would move the eye back by only about 2–3 px and the ear by about 7–13 px. Measured, our eye front corner sits +5 px and the back corner +14.5 px further back (left, measured). Eyes' 10–12 px figure uses the lid/lash corner. Our ears sit +34–35 px (+33–35%) further back than the video on both sides. The main mismatch is ear placement (and hair volume behind it), not a uniformly larger head.
- **Our face features sit higher.** Eye y is 8–11 px higher and nose tip y 11–21 px higher than the video (the video's head is proportionally longer in the face).
- **Eye width** (opening only): ours left 20 vs video 11–14 px. The video eye opening is much narrower in profile, so a width mismatch is real regardless of the lash definition.

Nothing was modified.
