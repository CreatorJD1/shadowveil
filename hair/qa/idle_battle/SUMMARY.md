# Base Hair: idle battle QA (Shadowveil), read-only

Run 2026-09-30, about 02:35–03:35 PT. Inputs are the v1 renders in `rig/previews/idle/`. Nothing was changed outside `hair/qa/idle_battle/`.

**Method**
- Each video was decoded one at a time with `ffmpeg -threads 1`, cropped to the head ROI (about 400×430 px), and streamed one frame at a time. Peak RSS was about 300 MB.
- The composites (`idle_all`, `*_all5`, `idle_keys_all`) were checked per tile at their native half scale. Tile and row order was verified against `base.png` and the `all5` clips.
- The videos are the RGBA frames over flat grey #808080, not #0000FF. So a transparent hole shows as grey in the video, and it would show as key blue in a keyed render. Check 1 therefore counts new white, new blue **and** new background grey.
- The priority wisp check and the seam counts also used the renderer's lossless RGBA frames (`frames/<name>/frames/*.png`, read one at a time).
- Head motion is compensated with the per-frame head bone from `meta.json`: a rotation of up to 3.76° about (681.5, 706), which moves the head up to about 40 px. After compensation the face-template residual is below 0.3 px in non-blink frames.
- Hair positions were recomputed exactly from `rig.json` plus the per-frame hair drives, using the transform chain from `rig/index.html`. This matches video-tracked strand tips with a correlation of 0.87–0.999.
- **Frame numbers are 0-based. `t` is the sim time from meta:** idle and hair-variant clips use t = (frame+1)/30, keys clips use t = frame/30. Video PTS is frame/30.

## PRIORITY: tpose wisp above EyeR's outer corner (Base Eyes report). FAIL
- **Part:** `views/tpose/hair/hair_front.png`, id `hair_front`, **layer 600, swayWeight 0 / maxSwayDeg 0, so it never sways.** The wisp is the 40 px drawn in `hair/tpose_eye_crossing_wisp_mask.png` (bbox x622–638, y194–212). It is a static part and is exempt in `validate_hair.py` (`wisp_exempt_px` 40). The live `hair_front` and erase mask are the `pending/*_with_wisp` versions.
- **What is under it at rest:** the eye parts have alpha 0 on all 40 wisp px (they were cut out). `base_body` is erased there by the hair erase mask (only 15 of 40 px are opaque). There is no `hair_back` and no underlay. At rest `hair_front` is alpha 255 on all 40 px, so rest is exact.
- **Why the gap opens:** it is **not** sway, because the wisp never moves relative to the eyes (both ride `headM`). It opens whenever the head is rotated by at least 0.01°. The renderer then draws `hair_front`, the eyes and the body with smoothing. The 1–2 px wisp and the cut edges of the eye parts all get partial alpha. Nothing opaque sits underneath, so the background (key blue) shows through.
  - It happens in **every soft (rotated) frame and in no sharp (axis-aligned) frame.**
  - tpose idle: 228 of 240 frames (= all soft frames). **Max 54 px/frame with alpha<255 at the wisp (±2 px), min alpha 184 (about 28% bleed).** Worst frame is f20 (t=0.700 s); for comparison, f60 (t=2.033 s) is 54 px and f67 (sharp) is 0 px.
  - keys_idle_breathe_tpose: 228 of 240 frames, max 54 (f15). keys_idle_weight_shift_tpose: 240 of 240, max 54 (f2). keys_idle_arm_settle_tpose: 232 of 240, max 54 (f2).
  - Counting only clearly visible bleed (alpha<235): up to about 43–50 px. That is consistent with Base Eyes' 1–19 px of visibly blue pixels.
- **Recommended fix (hair side):**
  - Add an opaque **underfill beneath the wisp**, the same idea as the behind-the-ear skin fill. Paint the wisp mask, dilated 2–3 px, into `hair_back.png` (layer 100, static, rides the same head transform). Use colours sampled from `base.png` around each pixel (eye white, lid or lash line, skin).
  - It stays hidden at rest under `hair_front` (alpha 255) and the eye parts, so rest stays exact. It fills exactly the cut that Base Hair's wisp exemption created.
  - The alternative is for Base Eyes to extend their parts under the cut. That also works, but the cut and exemption are Base Hair's, so the hair side should own the fill. These are proposals only; no file was changed.
- The same mechanism (soft-frame partial alpha along cut edges with nothing opaque beneath) also appears along every hair cut. See "Seams" below; it is a renderer-wide resampling effect.
- Note: my video check 1 left out the eye and mouth boxes on purpose, because iris moves and blinks make false hits there. That is why this defect only showed up in the lossless alpha check.

## Results per view and clip (P = pass, F = fail)

| video | 1 white/blue/holes (head/neck) | 2 hair over eyes/mouth | 3 bun max offset (geo/video px) | 4 sharp frames (flicker) |
|---|---|---|---|---|
| apose_idle | P | P | 0.14 / 0.22 | 0,67–69,136–138,224–228 |
| tpose_idle | P video; **F lossless (wisp, above)** | P (wisp static, present at rest) | 0.17 / 0.26 | same |
| left_idle | P | P | 0.26 / 0.26 | same |
| right_idle | P | P | 0.25 / 0.31 | same |
| back_idle | P | n/a (no face) | 0.24 / 0.24 | same |
| apose hair_stiff / hair_middle | P | P | 0.12 / 0.23, 0.12 / 0.24 | same |
| idle_breathe ×5 views | P (tpose F wisp) | P | ≤0.27 / ≤0.34 | 0–3, 42, 104–106, 119–121, 239 |
| idle_weight_shift ×5 | P (tpose F wisp) | P | ≤**0.42** (back f47) / ≤**0.45** (right f52) | none (head always rotated, always soft) |
| idle_arm_settle ×5 | P (tpose F wisp) | P | ≤0.24 / ≤0.32 | 49, 70, 142, 163–167 |
| composites: idle_all, 3× all5, idle_keys_all (40 tiles) | P (white 0, blue 0, hole blobs ≤2 px) | P | covered by the per-view runs | covered by the per-view runs |

**Check 1: new near-white, chroma blue or background inside the head/neck mask** (hair alpha dilated 30 px, head-compensated, versus rest `base.png`):
- **White 0 px and blue 0 px in every frame of every video.** The earlier behind-the-ear white patches have **not** come back in any view, including at max sway in weight_shift left/right/back (see sheet rows).
- New background inside the closed silhouette: at most 1–3 px/frame, as isolated 1–2 px specks. That is below the 3 px blob threshold and is H.264 noise.
- New background outside the silhouette is legitimate: strands hanging over the background move away from where they were. The largest is 105 px in keys_idle_weight_shift_apose f56 (t=1.867 s), at the strand_01 and strand_06_tip edges. Idle apose max is 52 px (f161).
- Lossless fully transparent (alpha 0) px inside the silhouette: at most 1–14 px as scattered single pixels on the outer hair outline. That is an edge effect of the rotated-mask comparison, not holes.

**Check 2: hair over eyes or mouth.**
- Geometric test of hair parts drawn above the face (layer ≥600, alpha ≥0.25): **0 new px in every frame of every clip.**
- Video hair-colour test: at most 16 px in blink- and mouth-free frames. All of these are compression pixels on the lip and profile outline and the eyelid edge, already present at frame 0, and none are hair (sheet row).
- Minimum clearance of moving hair to the eye/mouth boxes:

| view | EyeR (rest → min) | EyeL (rest → min) | mouth (rest → min) |
|---|---|---|---|
| apose | 4.0 → 4.0 px | 4.0 → 3.0 px (f81) | 35.6 px |
| tpose | 0 at rest (the static exempt wisp) | 5.0 → 3.0 px (weight_shift f177) | 36.6 px |
| left | — | **2.2 → 1.4 px** (left_idle f114, t=3.833 s; closest, worth watching) | 27.6 px |
| right | 9.8 → 8.0 px | — | 28.4 px |

**Check 3: bun drift relative to the head.**
- Overall max: **0.42 px geometric (keys_idle_weight_shift_back f47, t=1.567 s) / 0.45 px video-tracked (keys_idle_weight_shift_right f52, t=1.733 s).**
- It is never detached: 0 new background px at the bun/hair seam in any frame.

**Check 4: sharp-to-soft head flicker.**
- It **does affect the hair edges.**
- On sharp (axis-aligned) frames, the static hair edges (`hair_front`/`hair_back` outline) are 4–9% crisper: mean gradient ratio sharp/soft is 1.04–1.09 (face control 1.01–1.08).
- The frame-to-frame change in the hair-outline band spikes 1.5–3.4× the median exactly at the toggle frames.
- It also switches the tpose wisp gap on and off (above).
- Toggle frames: idle clips 1, 67, 70, 136, 139, 224, 229; breathe 4, 42, 43, 104, 107, 119, 122, 239; arm_settle 49, 50, 70, 71, 142, 143, 163, 168; weight_shift none.
- Fix is on the renderer side (Coder/rig): e.g. always use one filter for the head.

**Check 5: apose stiff vs middle vs default** (strand tips, head-relative, geometric / video-tracked):

| spring | strand_06 tip max | strand_03 tip max | lag behind head tilt | overshoot vs stiff (strand_06) |
|---|---|---|---|---|
| stiff 10 Hz, ζ0.9 | 5.14 / 6.14 px (f121) | 4.94 px | 0.03–0.10 s | — (tracks the head) |
| middle 2.2 Hz, ζ0.6 | 5.15 / 6.12 px (f124) | 4.96 px | 0.13–0.23 s | rms 0.57, max 1.26 px |
| default 1.1 Hz, ζ0.3 | **5.72** / 6.20 px (f127) | **5.51** px | 0.17–0.27 s | rms 1.14, max 2.41 px (≈11% overshoot) |

- The idle drive is slow head tilt (±0.2°), so all three reach about 5 px. Default is the only one that visibly overshoots and lags, with a small extra wiggle. No variant shows sustained ringing.
- Largest tip travel anywhere is keys_idle_weight_shift_apose strand_06_tip: 10.05 px head-relative (f58), 34 px in world space.

## Additional findings (hair side)
1. **Orphan strand pixels in `base_body.png` get left behind when strands swing.** These are small opaque components (≤20 px) of strand-coloured navy/black pixels right next to a strand, outside both the hair erase mask and the strand part. When the strand moves they stay as detached dots.
   - Seen in the video: apose f127, 3 dots at (750, 321–338) beside strand_06_tip (sheet rows "strand_06 tip").
   - Counts per view (px near swaying strands):
     - apose: strand_01 27, strand_03_tip 20, strand_06_tip 11, strand_05 9, strand_07 9, strand_02 5
     - tpose: strand_01 31, strand_03 15, strand_06 15, strand_06_tip 10, strand_02 8
     - left: strand_01 46
     - right: strand_04 12
     - back: strand_04 82, strand_02 49, strand_05 30, strand_01 26
   - Specks near the bun also exist, but the bun is behind the body in front views and moves ≤0.45 px.
   - Fix: add these pixels to the hair erase mask, or to the strand parts' cuts.
2. **Seams (lossless, every soft frame, all views).** Partial-alpha pixels inside the silhouette along hair cut edges: up to about 400–600 px/frame, plus up to about 270–460 px on other hair edges. Non-hair seams (body/face) are 430–1900 px/frame. These are resampling seams, not moving holes; on a key-blue background they read as a faint blue fringe. Hair-side mitigation: back every static cut with an opaque underfill (as for the wisp).

## Files
- `worst_sheet.png`: contact sheet, crops only. Each row is video frame | same window of rest `base.png` | mask panels; the legend is on the sheet.
- `data/<clip>.json`: per-frame results for all 22 per-view videos.
- `data/composite_*.json`: composite tile results.
- `data/aggregate.json`: per-video summary.
- `data/alpha_<clip>.json`: lossless seam and wisp counts per frame.
- `data/clearance.json`: hair-to-box clearances.
- `tools/`: scripts. `run_all.sh` runs everything in sequence. Its clip list is `idle_breathe idle_arm_sway idle_weight_shift idle_arm_settle`, and missing clips are skipped, so a v2 rerun with `idle_arm_sway` needs no edits (`common.available_names()`).
