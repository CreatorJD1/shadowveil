# Job 5: colour-leak and weight-bleed sweep (Base Hair, 2:45 AM PT Oct 3)

**Setup**
- Server: Hair's 8780, rooted at /workspace/shadowveil. Served index.html == disk, checked before every run.
- **The sweep renders used index.html 0ce6fecc** (01:48–02:00 PT).
  - Live changed to **00892ccb** at 02:01 PT.
  - The diff is a hand draw-order change behind an opt-in `?handorder=1` flag that these runs do not set, so hair rendering is identical.
- **Sets compared:**
  - *live* = views/*/hair.
  - *final* = `?hairless=1` staged set (speck_fix + lineart_fix + hairfront_holes + tone_fix, plus the ear_strands hair_front for tpose/left/right/back via request interception).
- **Renders:** each hair part drawn solo (LP.solo) at rest + 14 sway extremes (sx ±1 × sy 0/±1, sy ±1, whip ±1 × sy 0/±1). Also all hair after each body bone at ±1, and head-group frames (handoff offset, rot ±6°).
- **Palette** = every colour in that view's base.png.
- Files:
  - Data: `results.json`, `envelope_exact.json`, `near_chroma.json`.
  - Scripts: `work/sweep_render.py`, `work/analyze.py`, `work/envelope_exact.py`.

| Set | Parts | Static chroma / near-chroma | Max blue excess | Static off-palette | Static partial α | Render chroma | Render off-palette, opaque (15 poses; at rest) | Render partial α | Outside own envelope | Arm/leg bones move hair | BodyLean moves hair | Head-group rigid mismatch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| apose_live | 12 | 0 / 0 | 40 | 5410 | 1160 | 0 | 108302 (5410) | 45337 | 0 | 0 | 30112 | 0 |
| tpose_live | 10 | 0 / 0 | 40 | 257 | 3030 | 0 | 12777 (257) | 71973 | 0 | 0 | 29986 | 0 |
| left_live | 8 | 0 / 0 | 40 | 0 | 922 | 0 | 8227 (0) | 32139 | 0 | 0 | 33705 | 0 |
| right_live | 9 | 0 / 0 | 40 | 10 | 883 | 0 | 9066 (10) | 32901 | 0 | 0 | 34270 | 0 |
| back_live | 8 | 0 / 0 | 40 | 12 | 1390 | 0 | 5034 (12) | 39096 | 6 | 0 | 34223 | 0 |
| apose_final | 12 | 0 / 0 | 58 | 0 | 1195 | 0 | 27912 (0) | 46645 | 0 | 0 | 30819 | 0 |
| tpose_final | 10 | 0 / 0 | 66 | 0 | 3053 | 0 | 9359 (0) | 72081 | 0 | 0 | 30400 | 0 |
| left_final | 8 | 0 / 0 | 88 | 0 | 1523 | 0 | 8215 (0) | 40488 | 0 | 0 | 34089 | 0 |
| right_final | 9 | 0 / 0 | 90 | 0 | 1469 | 0 | 9144 (0) | 41715 | 0 | 0 | 34732 | 0 |
| back_final | 8 | 0 / 0 | 85 | 0 | 1902 | 0 | 5148 (0) | 45522 | 0 | 0 | 34352 | 0 |

## Reading the table
- **Chroma: 0 everywhere**, static and rendered, live and final, including head-group rot ±6.
  - Near-chroma (b ≥ 150 and b − max(r,g) > 100) is 0.
  - The "blue excess" up to 90 in final comes from her deep-navy outline ink, e.g. (0,0,64) … (10,16,89). These are exact base.png px in the ear_strands/speck strands, not key spill.
- **Static off-palette:**
  - Final is **0** in every view.
  - Live has 5410 (apose), 257 (tpose), 10 (right) and 12 (back) off-palette px; tone_fix/speck_fix remove them.
- **Render off-palette and partial alpha at sway poses: NOT 0, in either set.**
  - The renderer draws rotated parts with bilinear filtering (`quality=linear`), which blends neighbouring colours and alpha at every rotated edge.
  - At rest the final set is 0 off-palette.
  - Staged art cannot fix this. Meeting gate (1) literally ("no off-palette at any angle") needs a renderer change, which is the Coder's call: nearest sampling for hair, or a palette snap after compositing. Hair has not touched rig/.
  - Static partial alpha (≈900–3000 px per view) is her own anti-aliasing from base.png in both sets.
- **No colour outside a part's own mask:**
  - For each part × pose, the renderer's exact matrix was rebuilt (chain rotAt, whip rule, swayY dy) and the part's own rest mask warped.
  - Every rendered px lies within 1 px (8-neighbour, bilinear reach) of that mask: **0 px outside in all final sets.**
  - Live back strand_04 has 6 px outside, the known specks that speck_fix removes.
- **Weight bleed (gate 2):**
  - Skin: `views/<v>/body/skin.json` (15 bones, headBone=head) contains no hair. No hair part is in any skin weight set.
  - Renderer: every hair part is drawn with `headM × T(0,dy) × own spring chain`. In live 00892ccb it is `hgSub(hair|bun, …)`, a head-group sub-offset. No other bone enters. Every rig.json chain ends at hair_back/hair_front with parent null.
  - Shoulder, elbow, hip, knee, ankle and toe at ±1 move **0 hair px** in all 5 views, both sets.
  - Only **BodyLean** moves hair (≈30–35k px). It rotates the torso→neck→head chain, so the hair rides the head bone. That is not a weight on hair.
  - Head-group handoff offset: the hair moves **rigidly**, with 0 px mismatch at the exact offset (apose (0,−9), left (0,11), back (2,11), right (3,5)).

## Diagonals v2 (`hair/staged/diagonals_v2/`, see its README)
Hard-edged (α 0/255) and palette-snapped copies of the 4 diagonal sets.
- Partial α: ~10k → 0 per angle.
- Off-palette: ~9.4–10.9k → 0.
- Chroma: 0 → 0. Blue excess > 60: 0.
- Shape: the outline equals the soft 50% iso-line exactly (xor 0, within 1 px = 100%).
