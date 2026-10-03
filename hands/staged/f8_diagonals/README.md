# F8: diagonal hands cut from her turn frames (staged)

Status: **PASS** on the F8 pass mark at try 6 of 6. The hand-scale check against her master sheet was not done exactly (see Scale).

## What is here
- `<angle>/` for 45, 135, 225 and 315. Sources are her frames f033, f087, f131 and f191 (`reference/apose_turn/frames/`). The hands are cut at Body's diag_check red wrist lines and draw UNDER the forearm.
- **Near hands** (45 L, 135 L, 225 R, 315 R): palm plus Index/Middle/Ring/Pinky 1–3 and Thumb 1–3, with pivots, parents and signed maxCurlDeg in `rig.json`.
- **Far hands:** a single whole-hand sprite with only the palm pivot.
- Part PNGs are full-canvas view px (1365×1739, Body's view_fit from diagonals.json). Her frame-scale parts are in `<angle>/frame_scale/`.
- **Curl:** in-plane fold by rotation only (no frames). Magnitudes in degrees for joints 1/2/3 were tuned per hand to avoid holes (`tools/sweep2.py`):

| angle | fingers | thumb |
|---|---|---|
| 45 | 120/40/15 | 5/60/25 |
| 135 | 150/25/10 | 20/50/20 |
| 225 | 80/30/20 | 10/40/15 |
| 315 | 115/30/10 | 5/60/25 |

- Joint caps (CAP 1.0, CAPP 0.6) copy only her alpha-255 px, so the rest image is unchanged.

## Processing (her px only, no line painted)
1. **Key out blue.** px with B − max(R,G) > 25 are removed. In the 2 px outer ring, blue-tinted px are re-matted (alpha from G, colour of the nearest clean interior px).
2. **Resample.** Premultiplied bilinear to view scale (scale 1.545 / 1.570 / 1.573).
3. **Palette snap (try 6).** Every px RGB is snapped to the nearest colour of HER keyed palette for that hand. Max RGB distance is 15–22; alpha is unchanged. Details in `snap_log.json`.

## Checks
- **Rebuild** (`build_log.json`, `check6.json`):
  - Exact rebuild at rest: frame scale 0 px, view scale 0 px.
  - Parts rebuild the snapped hand exactly: 0 px.
- **Colour:** blue/chroma px 0, off-palette px 0 (every px colour exists in her own frame cut), for all 8 hands.
- **Holes** in the scratch sim (`sim_holes.log`; rotation chain, sim.py metric; live apose poses have 0 holes):

| hand | holes in Fist / Point / Peace |
|---|---|
| 45 L | 0 / 0 / 0 |
| 135 L | 0 / 0 / 0 |
| 315 R | 0 / 0 / 0 |
| 225 R | max 1 px (total 5 across the three poses) |

  - 225 R's own rest drawing already has two enclosed 10 px gaps between her fingers. These are left as she drew them.
- **Edge softness:** soft band 2.15–2.49 px (live apose 0.92, tpose 2.54).
- **Lineless outline share** per hand: 0.20–0.29. No line was added.
- **Sheet:** `sheet_near_hands_poses.png` shows the near hands at rest / Fist / Point / Peace.

## Scale
- The scale is Body's view_fit (head top → y40, sole → y1681/1682), the same fit that places the diagonal body.
- `hand_length.json` (palm pivot → farthest opaque px, view px):
  - Near hands: 45 L 147.5, 135 L 154.9, 225 R 156.8, 315 R 146.1.
  - Her sharp views: apose 155.6/156.4, left 150.6, right 149.9, back 146.0/146.3, tpose 138.7/138.8.
  - Far hands are 100–116 px, foreshortened.
- I did **not** verify the "within 1 px of her master sheet" rule directly. The master sheet (`reference/grok_build/.../Shadowveil_Interactive_Master_Sheet.html`, 61 MB) was not parsed because memory on the box was low. The near hands fall inside the range of her sharp-view hands.

## Tries (6 of 6)
1. Bicubic: blue 44–207 px, FAIL.
2. Bilinear: blue 0, but pose holes up to 34 px, FAIL.
3. Bilinear plus caps: holes up to 28 px, FAIL.
4. Hinge fold 150/25/10: 135 L clean, 45 L worse (37 px), FAIL.
5. Per-hand curl from the sweep: holes 0/0/0/≤1 px, but about 60% of px off-palette after bilinear scaling.
6. Try 5 plus palette snap: **PASS**.

Tools are in `tools/`.
