# Base Hair: lineart under deformation (read-only check on live hair + the staged speck fix)

Run 2026-09-30, about 04:30 to 05:30 PT. Nothing under `views/` was modified. Heavy jobs ran one at a time.

## Result
- **Live hair: FAIL.** 7 of 37 joints fail and 1 of 46 parts fails (tpose strand_02). There is **no line break (child/parent disconnect) at any joint in any view**. Outline width holds everywhere: worst p95 coverage-width change is 0.62 px, limit 1 px.
- **Staged speck fix: FAIL (worse than live).**
  - It fixes 1 existing failure: tpose strand_02, where the specks bridge a thin neck.
  - It adds 4 new failures:
    - left strand_01 (part and its joint to hair_front): +3 ink pieces at s=-0.5
    - back strand_04: +1 piece
    - back strand_05: +1 piece
  - All 7 live joint failures remain.
- The 3 hair-side fixes I tried in scratch copies (joint caps, static underfill, halved sway angle) **did not clear any failing joint**. So nothing is staged as a fix. See "Proposed fixes".

## Method (`work/lineart_check.py`)
- **Renderer:** Python mirror of the renderer (`hair/tools/render.py`: chained `rotAt` matrices, bilinear drawImage).
- **Sway values:** HairSwayX = s for every part, s ∈ {−1, −0.5, +0.5, +1}, compared with rest. HairSwayY = 0.
- **Ink:** alpha ≥ 96 and max(r,g,b) ≤ 60. For hair_front, hair_back and bun, whose fill is navy, the outline core is max ≤ 18.
- **(1) Width.** At each rest skeleton point of a line section (≤ 6 px wide):
  - Coverage width = ink mass (alpha × dark) in a 3 px disk ÷ skeleton px in that disk.
  - The disk moves with the part's own transform into the swayed image.
  - PASS if p95 |Δw| ≤ 1 px, and (for strands and tips) the part's count of ink pieces (≥ 6 px) does not grow.
  - Coverage width is used because thresholded width reads a crisp 1 px line as 2 to 3 px once it is bilinear-resampled, although its ink mass stays the same (mass ratio 0.95 to 1.04).
- **(2) Breaks.** In a 25×25 window at the joint (the child's pivot, carried by the parent):
  - If the child's ink and the parent's ink within 6 px of the pivot are 8-connected at rest, they must stay connected.
  - FAIL also if the window's count of ink pieces (≥ 6 px) grows, meaning a piece of line split off.
- **(3) Kinks.** Take the alpha-0.5 contour in the window and compute the turning angle over 3 px arms.
  - A sway point turning > 60° counts as a NEW sharp corner if neither the child's nor the parent's inverse transform maps it within 2 px of a rest corner (≥ 30°).
  - The relative rotation at the seam is also reported (`rel_rot_deg`).
- **Caveat:** these are pixel-level thresholds, and the failures are small (+1 to +3 pieces, 1 to 6 corner px). They persist at half the angle, so much of this is bilinear resampling of 1 px, partly transparent strokes and pixel-stair edges, not the pivot geometry alone. Please judge with the crops.

## Crops (10× zoom)
- Layout per file:
  - Top row: rest | s=−1 | −0.5 | +0.5 | +1, hair over `base_body` on #0000FF.
  - Bottom row: ink mask (black), 6 px joint circle (green), turning points > 60° (red).
- Files:
  - `live_<view>_<child>__<parent>_{FAIL|pass}.png`: current live hair
  - `staged_speck_<view>_<child>__<parent>_{FAIL|pass}.png`: with the staged speck fix
  - The two worst passing joints per view are included for comparison.
- Data: `lineart_live.json` and `lineart_staged_speck.json`. Fix trials: `work/lineart_caps4.json` and `work/lineart_deg_half.json`.

### Joints (child <- parent): line breaks, split-off ink pieces, new sharp corners

| view | joint | live | breaks | max +pieces | max new corners | fails at s | staged speck fix | +pieces | new corners |
|---|---|---|---|---|---|---|---|---|---|
| apose | bun ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_01 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_02 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_03 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_03_tip ← strand_03 | **FAIL** | 0 | 0 | 3 | 1 | **FAIL** | 0 | 3 |
| apose | strand_04 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_05 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_06 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| apose | strand_06_tip ← strand_06 | **FAIL** | 0 | 0 | 4 | -1,-0.5 | **FAIL** | 0 | 4 |
| apose | strand_07 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | bun ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_01 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_02 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_03 ← hair_front | **FAIL** | 0 | 0 | 3 | 0.5,1 | **FAIL** | 0 | 3 |
| tpose | strand_04 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_05 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_06 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| tpose | strand_06_tip ← strand_06 | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| left | bun ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| left | strand_01 ← hair_front | PASS | 0 | 0 | 0 | - | **FAIL** | 2 | 0 |
| left | strand_02 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| left | strand_03 ← hair_front | **FAIL** | 0 | 1 | 0 | 0.5,1 | **FAIL** | 1 | 0 |
| left | strand_04 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| left | strand_04_tip ← strand_04 | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| right | bun ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| right | strand_01 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| right | strand_01_tip ← strand_01 | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| right | strand_02 ← hair_front | **FAIL** | 0 | 1 | 0 | 1 | **FAIL** | 1 | 0 |
| right | strand_02_tip ← strand_02 | **FAIL** | 0 | 1 | 0 | 0.5,1 | **FAIL** | 1 | 0 |
| right | strand_03 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| right | strand_04 ← hair_front | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | bun ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | strand_01 ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | strand_02 ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | strand_03 ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | strand_04 ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |
| back | strand_05 ← hair_back | PASS | 0 | 0 | 0 | - | PASS | 0 | 0 |

### Parts: outline width (coverage width, p95 |Δ| over the line, px) and ink pieces (≥6 px)

| view | part | live p95 Δw | live pieces rest→max | live | staged p95 Δw | staged pieces rest→max | staged |
|---|---|---|---|---|---|---|---|
| apose | hair_back | 0 | 25→25 | PASS | 0 | 25→25 | PASS |
| apose | hair_front | 0 | 25→25 | PASS | 0 | 25→25 | PASS |
| apose | bun | 0.56 | 8→6 | PASS | 0.56 | 8→6 | PASS |
| apose | strand_01 | 0.33 | 5→5 | PASS | 0.35 | 2→2 | PASS |
| apose | strand_02 | 0.33 | 1→1 | PASS | 0.38 | 1→1 | PASS |
| apose | strand_03 | 0.51 | 1→1 | PASS | 0.51 | 1→1 | PASS |
| apose | strand_03_tip | 0.38 | 1→1 | PASS | 0.34 | 1→1 | PASS |
| apose | strand_04 | 0.38 | 3→3 | PASS | 0.38 | 3→3 | PASS |
| apose | strand_05 | 0.24 | 1→1 | PASS | 0.23 | 1→1 | PASS |
| apose | strand_06 | 0.43 | 1→1 | PASS | 0.43 | 1→1 | PASS |
| apose | strand_06_tip | 0.29 | 1→1 | PASS | 0.29 | 1→1 | PASS |
| apose | strand_07 | 0.25 | 1→1 | PASS | 0.21 | 1→1 | PASS |
| tpose | hair_back | 0 | 35→35 | PASS | 0 | 35→35 | PASS |
| tpose | hair_front | 0 | 33→33 | PASS | 0 | 33→33 | PASS |
| tpose | bun | 0.61 | 6→8 | PASS | 0.61 | 6→8 | PASS |
| tpose | strand_01 | 0.4 | 5→4 | PASS | 0.51 | 5→4 | PASS |
| tpose | strand_02 | 0.33 | 1→2 | **FAIL** | 0.43 | 1→1 | PASS |
| tpose | strand_03 | 0.33 | 2→2 | PASS | 0.36 | 2→2 | PASS |
| tpose | strand_04 | 0.45 | 2→2 | PASS | 0.45 | 2→2 | PASS |
| tpose | strand_05 | 0.57 | 2→2 | PASS | 0.57 | 2→2 | PASS |
| tpose | strand_06 | 0.41 | 5→5 | PASS | 0.42 | 5→5 | PASS |
| tpose | strand_06_tip | 0.32 | 2→2 | PASS | 0.33 | 1→1 | PASS |
| left | hair_back | 0 | 14→14 | PASS | 0 | 14→14 | PASS |
| left | hair_front | 0 | 14→14 | PASS | 0 | 14→14 | PASS |
| left | bun | 0.56 | 7→6 | PASS | 0.56 | 7→6 | PASS |
| left | strand_01 | 0.34 | 2→2 | PASS | 0.4 | 3→6 | **FAIL** |
| left | strand_02 | 0.24 | 1→1 | PASS | 0.24 | 1→1 | PASS |
| left | strand_03 | 0.47 | 1→1 | PASS | 0.47 | 1→1 | PASS |
| left | strand_04 | 0.27 | 1→1 | PASS | 0.27 | 1→1 | PASS |
| left | strand_04_tip | 0.45 | 1→1 | PASS | 0.45 | 1→1 | PASS |
| right | hair_back | 0 | 16→16 | PASS | 0 | 16→16 | PASS |
| right | hair_front | 0 | 16→16 | PASS | 0 | 16→16 | PASS |
| right | bun | 0.59 | 6→5 | PASS | 0.59 | 6→5 | PASS |
| right | strand_01 | 0.3 | 2→2 | PASS | 0.3 | 2→2 | PASS |
| right | strand_01_tip | 0.6 | 1→1 | PASS | 0.6 | 1→1 | PASS |
| right | strand_02 | 0.32 | 1→1 | PASS | 0.32 | 1→1 | PASS |
| right | strand_02_tip | 0.59 | 1→1 | PASS | 0.59 | 1→1 | PASS |
| right | strand_03 | 0.4 | 1→1 | PASS | 0.4 | 1→1 | PASS |
| right | strand_04 | 0.25 | 2→2 | PASS | 0.3 | 2→2 | PASS |
| back | hair_back | 0 | 9→9 | PASS | 0 | 9→9 | PASS |
| back | bun | 0.59 | 10→10 | PASS | 0.59 | 10→10 | PASS |
| back | strand_01 | 0.24 | 1→1 | PASS | 0.47 | 1→1 | PASS |
| back | strand_02 | 0.29 | 2→2 | PASS | 0.45 | 2→2 | PASS |
| back | strand_03 | 0.62 | 2→2 | PASS | 0.62 | 2→2 | PASS |
| back | strand_04 | 0.38 | 2→2 | PASS | 0.61 | 2→3 | **FAIL** |
| back | strand_05 | 0.36 | 1→1 | PASS | 0.41 | 1→2 | **FAIL** |

### Fix trials on the failing joints (staged speck hair as the base)

| view | joint | as staged | joint caps/underfill r=4 | tip/strand maxSwayDeg halved |
|---|---|---|---|---|
| apose | strand_03_tip ← strand_03 | FAIL (+0 pieces, 3 corners) | FAIL (+0 pieces, 2 corners) | FAIL (+0 pieces, 2 corners) |
| apose | strand_06_tip ← strand_06 | FAIL (+0 pieces, 4 corners) | FAIL (+0 pieces, 3 corners) | FAIL (+0 pieces, 2 corners) |
| tpose | strand_03 ← hair_front | FAIL (+0 pieces, 3 corners) | FAIL (+0 pieces, 3 corners) | FAIL (+0 pieces, 3 corners) |
| left | strand_01 ← hair_front | FAIL (+2 pieces, 0 corners) | FAIL (+2 pieces, 0 corners) | FAIL (+2 pieces, 3 corners) |
| left | strand_03 ← hair_front | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) |
| right | strand_02 ← hair_front | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) |
| right | strand_02_tip ← strand_02 | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) | FAIL (+1 pieces, 0 corners) |


## Proposed hair-side fixes, per failure (proposals only; nothing applied, and nothing staged because no trial cleared a joint)
| failure | what the crops show | proposal |
|---|---|---|
| apose strand_03_tip ← strand_03 (3 corners at s=+1) | Seam notch: the tip's edge turns 9.5° against the parent's cut edge, and a stair-step appears on the right side of the line at the pivot. | Move the pivot about 3 to 5 px up the line, to where both edges are straight, and re-cut the joint perpendicular to the line. Use a longer joint cap (child root copied into the parent, r ≈ 6 to 8 along the line; hidden, rule 4). r=4 cut corners 3→2 only. Or a per-tip clamp near 5° (halving still left 2 corners). |
| apose strand_06_tip ← strand_06 (4 corners at s=−1, 1 at −0.5) | Same seam notch, 8.8°. | Same: move the pivot to the straight part of the line, and use a longer cap along the line. r=4 gave 4→3, half angle gave 4→2. |
| tpose strand_03 ← hair_front (3 corners at +0.5/+1) | The strand root swings against the static hair_front edge. At rest, child and parent ink do not meet near the pivot (reported as `None`). | Move the pivot to the point where the strand enters hair_front, and add a static underfill in hair_front (exact base.png copies under the root, cut along the strand). r=4 had no effect, so it must follow the line. |
| left strand_03 ← hair_front (+1 piece at +0.5/+1) | A faint 1 px side stroke next to the root drops below ink alpha when resampled and separates. | Cut that faint stroke into strand_03, or into hair_front if it belongs there, so the cut does not split it. |
| right strand_02 ← hair_front (+1 piece at +1) | As above: a faint stroke at the root. | As above. |
| right strand_02_tip ← strand_02 (+1 piece at +0.5/+1) | A faint stroke at the seam. | Re-cut the seam so the stroke is not divided, or use a longer cap. |
| tpose strand_02, part (1 → 2 pieces at every s, live only) | A 1 px neck in the strand breaks when resampled. | Fixed by the staged speck fix (its 8 px bridge the neck). |
| **Speck fix:** left strand_01, part and joint (3 → 6 pieces) | The added specks are faint trailing hair strokes (alpha 36 to 253) that separate when resampled. Main clusters: (579,147) 14 px, (580,177) 8 px, (582,191) 21 px. | Decide between: (a) accept, since the pieces move with the strand; (b) hold these clusters back from the speck fix, which leaves them on the body and so behind at max sway; (c) move them into strand_01 together with the connecting faint base.png pixels so they form one stroke. |
| **Speck fix:** back strand_04 (2 → 3 pieces) | Clusters (759,305) 14 px and (754,313) 9 px. Without either one, the part passes. | Same choice. |
| **Speck fix:** back strand_05 (1 → 2 pieces) | Cluster (782,225) 16 px. Without it, the part passes. | Same choice. |

The builder for the cap/underfill trial is at `hair/staged/lineart_fix/work/build_caps.py`. Its output went only to /tmp scratch, and no PNGs are staged.
