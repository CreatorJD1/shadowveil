# Diagonal turn frames: can her own hands be cut? (Step 4, read-only, 2026-10-02 ~21:40 PT)

Frames: Base Body picks 45°=f033, 135°=f087, 225°=f131, 315°=f191 (reference/apose_turn/frames, 768×1168), scale from body_tools/work/apose_turn/diagonals/diagonals.json view_fit.
Tool: hands/work/turn_check/diagonals.py → diag_check.json, crops diag_fNNN_{R,L}.png (4× nearest; red = proposed wrist cut, yellow = frame wrist, green = current generated hand wrist, magenta = blue spill px), sheet diag_sheet.png.
Hand geometry (wrist, axis, L, tips, palm) is the sweep2.json measurement from notes.md §3; hip gap from diagonals.json. Side = her side (R/L). Nothing outside hands/work/turn_check was written; no rig file or turned-hand PNG touched.

Columns: L = wrist cut to farthest fingertip (frame px → view px after scale). outline = share of the hand contour (excluding the cut) that has a dark line px (lum<95) within 1 px. spill = bluish px (B − max(R,G) > 25) kept as foreground in a 2 px ring around the hand.
Generated-hand offset = rig/hand_angles/<angle>_<side>.json wrist/axis (in its own source frame) minus the hand measured in Base Body's frame; view px = × scale. Note the generated hands were built from f035/f086/f133/f189, so part of each offset is the 1–2 frame turn difference, and their "axis" is the wrist→hand axis of the mesh, not wrist→farthest tip.

| angle | frame | hand | L px (view) | palm len / w | wrist w px (view) | tips auto | fingers/thumb visible (crop check) | thumb side | hip gap | outline | spill px | wrist cut (frame px) | gen dx, dy frame (view) | gen rot | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 45° | f033 | R | 74.0 (114.3) | 59.4 / 22.0 | 25.6 (39.6) | 4 | thumb + 4 fingers; Ring/Pinky partly overlap (foreshortened near-edge hand). Index/Middle separable, Ring/Pinky only as a pair | +v (expected +v) | clear, 86 px | 0.721 | 107 | [211.1, 495.9]–[191.2, 479.8] | 11.6, -0.6 (17.9, -0.9) | -6.4° | CUTTABLE, foreshortened (whole-hand sprite; fingers not separable for per-finger rig) |
| 45° | f033 | L | 95.0 (146.7) | 63.3 / 37.6 | 25.6 (39.6) | 4 | thumb + all 4 fingers, spread and separable | -v (expected -v) | clear, 132 px | 0.739 | 222 | [607.6, 487.6]–[587.9, 503.9] | -9.5, -0.0 (-14.7, -0.0) | 8.8° | CUTTABLE |
| 135° | f087 | R | 64.0 (100.5) | 41.9 / 30.2 | 28.8 (45.3) | 2 | thumb + 4 fingers, strongly foreshortened; Ring/Pinky overlap, only 2 tips resolve automatically | -v (expected -v) | clear, 124 px | 0.706 | 85 | [575.9, 487.8]–[551.7, 503.5] | -5.1, 1.9 (-8.0, 2.9) | 6.3° | CUTTABLE, foreshortened (whole-hand sprite; fingers not separable for per-finger rig) |
| 135° | f087 | L | 96.0 (150.8) | 56.4 / 38.9 | 26.9 (42.3) | 3 | thumb + all 4 fingers separable (long open hand) | +v (expected +v) | clear, 102 px | 0.794 | 127 | [173.2, 509.9]–[155.2, 489.8] | 6.1, -0.1 (9.5, -0.1) | -15.0° | CUTTABLE |
| 225° | f131 | R | 99.0 (155.8) | 56.9 / 41.9 | 27.0 (42.5) | 5 | thumb + all 4 fingers separable (long open hand) | -v (expected -v) | clear, 102 px | 0.8 | 198 | [603.4, 487.4]–[585.9, 507.9] | -10.7, -0.1 (-16.8, -0.2) | 12.9° | CUTTABLE |
| 225° | f131 | L | 70.0 (110.1) | 56.2 / 23.9 | 28.0 (44.1) | 4 | thumb + 4 fingers, foreshortened; Ring/Pinky overlap | +v (expected +v) | clear, 122 px | 0.729 | 99 | [209.1, 502.9]–[185.7, 487.5] | 9.8, 1.5 (15.4, 2.4) | -12.5° | CUTTABLE, foreshortened (whole-hand sprite; fingers not separable for per-finger rig) |
| 315° | f191 | R | 94.0 (145.2) | 66.0 / 30.5 | 25.6 (39.6) | 4 | thumb + all 4 fingers, separable | +v (expected +v) | clear, 130 px | 0.724 | 149 | [175.3, 505.7]–[155.4, 489.5] | 7.2, 2.4 (11.1, 3.6) | -17.7° | CUTTABLE |
| 315° | f191 | L | 73.0 (112.8) | 49.6 / 30.8 | 27.7 (42.7) | 2 | thumb + 4 fingers, foreshortened; Middle/Ring/Pinky partly overlap | -v (expected -v) | clear, 86 px | 0.792 | 92 | [572.5, 479.5]–[551.6, 497.5] | -7.4, 1.8 (-11.4, 2.7) | 11.0° | CUTTABLE, foreshortened (whole-hand sprite; fingers not separable for per-finger rig) |

## Findings
- All 8 hands are clear of the hips (86–132 px raw) with the thumb on the correct side, so every one can be cut from her own frame. None is occluded.
- Near-side open hands (45 L, 135 L, 225 R, 315 R) are full length (L 94–99 px raw, 145–156 view px, same as the painted apose hand ~155 view px) with all four fingers and the thumb separable: good per-finger rig sources.
- Far-side hands (45 R, 135 R, 225 L, 315 L) are foreshortened (L 64–74 px raw, 100–114 view px) and Ring/Pinky (and on 315 L Middle) overlap: usable as a whole-hand sprite with palm-level curl only, not per-finger segments.
- Outline: the video hands have a soft dark contour on 71–80 % of the edge; the rest (mostly the lit side and fingertips) is anti-aliased skin straight onto the key, so a cut needs her line added on those stretches (and the frame is ~1.55× smaller than the view, so lines thicken on upscale).
- Blue spill: 85–222 px of bluish fringe per hand in the 2 px ring; key it out (B − max(R,G) > 25) and re-matte before use. No enclosed key islands inside any hand.
- Wrist cut: the red lines in the crops, perpendicular to the forearm axis at the sweep2 wrist point; width 25.6–28.8 px raw (39.6–45.3 view px).
- Current generated hands sit 5–12 px raw (8–18 view px) off along x from the hand in Base Body's frame, dy within 2.4 px raw (3.6 view), and are rotated 6–18° from the frame's wrist→tip axis (sign alternates by side, i.e. they are all turned toward the vertical relative to her hands).
