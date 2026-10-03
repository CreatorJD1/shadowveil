# rig/hand_angles: "144.7 vs 156.6 px" is mostly how it is measured, not drift (2026-10-03, PT)

**Short answer:** the qa_gates G3 numbers compare two different things.
- All 8 sprites come out at exactly 144.7 because of how physicalLength is set, not because of a measurement.
- The −11.9 px gap comes from three things: different wrist and fingertip definitions, and a length that is not what is drawn on screen.
- Real drift does exist, but only in the rendered sprites after the rig's fitHand rescale. It is the far-side hands (about +33 px) and the 180° back donor (−14 to −17 px), not a uniform −12. Numbers are in `scale.json`, section `turn_angles`.

## 1. Why all 8 are identical: the length is set that way
- `physicalLength` is not a measured per-hand length.
  - tools/calibrate-hand-size.py keeps a *shared physical hand length* (rig/hand_angles/README).
  - L and R at the same angle carry the same value: 45 = 93.88, 135 = 92.30, 225 = 92.12, 315 = 93.70 frame px.
  - Each one is exactly 144.7 / (turn_measure.json scale for that frame): ×1.5418, 1.5683, 1.5713, 1.5447. So `physicalLength × scale` = 144.7 by construction.
- The per-hand reference lengths are stored in `sizeCalibration` (tools/hand-art/reference-size.json): near side 91–98 and far side 61–73 frame px. physicalLength ignores them.
- The gate is effectively reading back one shared constant eight times.

## 2. Definition gap in the 156.6 "truth" (apose)
G3 truth = palm pivot → Middle1 pivot, plus Middle1→2→3 pivots, plus Middle3 tip reach (a polyline). My audit measures a straight line from the wrist (flare onset on her silhouette) to the farthest tip px. On her apose base.png:

| side | G3 chain (palm pivot → tip, polyline) | straight palm pivot → tip | audit L (flare wrist → tip) | palm pivot is proximal of the flare wrist by |
|---|---|---|---|---|
| L | 156.6 | 155.4 | 148.6 | 7.1 |
| R | 156.7 | 155.2 | 148.8 | 6.5 |

- The polyline adds about 1.3 px, and the palm pivot sitting proximal of the visible wrist adds about 7 px.
- On a flare-wrist → tip basis, apose is **148.6/148.8**, so the "sprite drift" falls from −11.9 to about −4.
- Even that −4 is not comparable: the sprites' physicalLength is measured from their own wrist cut (`wristEdges`) in sprite-local frame px, and the wrist cut definition differs again.

## 3. 144.7 is not what's drawn
- At runtime `fitHand(target, donor)` rescales every sprite: sLen = HAND_ATTACH[view][side].length / physicalLength.
  - In apose the targets are 153.82 (R) and 153.91 (L), i.e. about 1.64× for frame-px physicalLength.
  - The result is that every sprite, near or far, is drawn at about 152–157 px.
- Rendered through the live rig (WristTwist = deg/180, apose view), audit definition, view px:

| angle | near hand: rig / her frame | far hand: rig / her frame |
|---|---|---|
| 45 | L 153.1 / 151.2 (+1.9) | R 154.5 / 122.0 (**+32.5**) |
| 135 | L 156.9 / 157.4 (−0.6) | R 152.1 / 119.4 (**+32.7**) |
| 225 | R 152.5 / 158.4 (−6.0) | L 157.3 / 123.9 (**+33.4**) |
| 315 | R 153.4 / 154.0 (−0.5) | L 156.4 / 121.9 (**+34.5**) |

- Calibration: at 0° the rig equals her apose drawing, but her turn video is about 1.8% larger (−3.2 / −2.3 px), so treat ±3 px as noise.

## Verdict
- **Measurement artefact:** "−11.9 px, all 8 identical."
  - The identical value comes from the shared physicalLength.
  - About 8 px comes from definitions (palm pivot vs visible wrist, plus the polyline).
  - The rest is pre-fit sprite length, which the runtime overrides.
- **Real drift,** visible only in rendered output:
  - Far-side sprites are fitted to a full near-side length, so foreshortening is lost (about +33 px).
  - The 180° back donor is −14 to −17 px.
  - Near-side sprites have the right length but a wrong palm/finger split: 45 L palm −3 / finger +4.9 / width −9, and 315 R palm +8.3 / finger −8.8.
- **Suggested G3 fix (Coder's call):**
  - Measure the sprite after fitHand, as drawn length in view px from the rendered layer.
  - Use the visible flare wrist, or the same pivot, on both sides.
  - Compare against her per-hand turn-frame length (sizeCalibration.length × scale), not the apose chain. Far hands should come out at about 95–115, not 153.
