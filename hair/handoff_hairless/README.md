# Hairless-base areas for Base Body (from Base Hair), Fri Oct 2 2026, about 8:55 PM PT; re-measured at LINEAR display quality 9:10 PM PT

These sheets come from the live hair: `views/*/hair/` at GitHub main 6d5b239, unchanged since that commit. The rig is `rig/index.html` at main 6d5b239. The staged speck fix is not included; it adds hair px inside these areas only (see the note at the end).
Everything outside `hair/` was only read. Canvas is 1365×1739, 0-based. Each mask is an 8-bit greyscale PNG, 255 = in the set.

## Files (per view: apose, tpose, left, right, back)
| file | what it is |
|---|---|
| `<view>_hair_rest_mask.png` | (a) What the hair covers at rest: the union of alpha>0 over every part in `views/<view>/hair/rig.json`. That is hair_back (with the behind-the-ear skin fill and, in tpose, the wisp underfill, which both live inside `hair_back.png`), bun, hair_front, strands and tips. |
| `<view>_hair_sway_envelope.png` | (b) Every px the hair can reach anywhere in its sway range, in rest coordinates. **The hairless fill must cover this area.** It contains the rest mask. |
| `<view>_uncovered_at_sway.png` | (c) Envelope px the hair leaves completely uncovered (rendered hair alpha = 0) in at least one extreme pose. Here base_body or the fills show through fully. |
| `<view>_uncovered_at_sway_partial.png` | (c, wider) The same, but counting any px where hair alpha < 255 at an extreme, so see-through anti-aliased edges are included. |
| `hairless_sheet.png` | Overview of the head crop per view. Navy = rest hair, yellow = envelope, pink = partial, red = fully uncovered. |
| `work/` | `build.py` (makes everything here), `lean_dump.py` (BodyLean data from the renderer), `summary.json` (all counts, per pose and per part), `lean_*.npz`. |

## Pixel counts
| view | (a) rest mask | (b) envelope | envelope − rest | (c) uncovered (alpha 0) | … of which inside the rest mask | (c) partial (alpha < 255) | … of which inside the rest mask |
|---|---|---|---|---|---|---|---|
| apose | 20020 | 33259 | 13239 | 14987 | 1853 | 15412 | 2173 |
| tpose | 19551 | 32265 | 12714 | 15181 | 2554 | 16233 | 3519 |
| left | 28682 | 35426 | 6744 | 7790 | 1195 | 8410 | 1666 |
| right | 29868 | 37045 | 7177 | 8314 | 1266 | 8957 | 1780 |
| back | 31625 | 38767 | 7142 | 8094 | 1068 | 8645 | 1504 |

"Inside the rest mask" means px that hair covers at rest and leaves bare at sway. These are the most important ones for the hairless base: the scalp edge, the strand roots and the bun rim. The rest of (c) is where a strand swings over px that were already uncovered at rest (background, cheek, neck), which base_body already shows.

Part sizes at rest (alpha>0 px):
- apose: hair_back 17828, hair_front 12418, bun 5096, strand_01 392, strand_02 119, strand_03 143, strand_03_tip 519, strand_04 287, strand_05 129, strand_06 196, strand_06_tip 594, strand_07 106
- tpose: hair_back 16011, hair_front 10462, bun 5567, strand_01 617, strand_02 158, strand_03 603, strand_04 343, strand_05 165, strand_06 590, strand_06_tip 693
- left: hair_back 26952, hair_front 18233, bun 9209, strand_01 328, strand_02 138, strand_03 316, strand_04 239, strand_04_tip 195
- right: hair_back 28052, hair_front 19254, bun 9263, strand_01 232, strand_01_tip 205, strand_02 259, strand_02_tip 165, strand_03 202, strand_04 226
- back: hair_back 30120, hair_front 0, bun 9767, strand_01 158, strand_02 282, strand_03 165, strand_04 311, strand_05 137

## How the sheets were made
- **Sway range.** This is the renderer's own chain (`chain()` + `rotAt()` in `rig/index.html`). Each part turns `swayWeight × maxSwayDeg × x` about its own pivot, and a child also inherits its parent's turn. Both drives are included:
  - the manual slider: the same x all the way down the chain, x ∈ [−1, 1], with no clamp;
  - the auto drive with preset A (`stepHair`): x is independent per part, clamped to [−1, 1], and a tip's chained total is clamped to the tip's own limit.
  - Preset A changes only the dynamics (4.0 Hz, ζ 0.8). The limits are the same, so the range above is its full range in both directions.
  - HairSwayY: each part drops by its own `round(y × swayY × swayYMaxPx)` with y ∈ [−1, 1] (swayYMaxPx = 3), which covers every whole-px drop.
- **Sampling.** Angles are sampled finely enough that the farthest px moves ≤ 0.35 px per step. Every part px is swept as a full square (corners, edge midpoints, centre) together with its whole shape.
  - The union is then dilated by 1 px. At LINEAR display quality (QUAL='linear', becoming the default), the filter still spreads a faint alpha halo up to 1 px past the footprint: without the dilation, up to 5 rendered hair px per extreme pose fell outside (it was 721 to 1,250 at the old 2x supersampled setting).
  - **Check:** at all 12 extreme poses per view, rendered with the current renderer at linear quality, **0 hair px (alpha>0) fall outside the envelope** in any view.
- **BodyLean.** The highest BodyLean in the action clips is ±1 (jump ±1.0, run ±0.98, anger ±0.87, hair actions ±0.42; only stress clips go past ±1).
  - Lean cannot add hair angle, because the drive saturates at ±1 (gravity and inertia are clamped in `stepHair`).
  - The renderer draws the hair with the head matrix. At BodyLean ±1, every skin-mesh vertex under the envelope moves exactly with that matrix (largest gap below), so in her own coordinates the uncovered area does not change with lean:
- apose: head turns -8.0° / 8.0° at BodyLean −1/+1. 1383 skin vertices under the envelope; largest gap between skin and head: 0.0 px
- tpose: head turns -8.0° / 8.0° at BodyLean −1/+1. 1258 skin vertices under the envelope; largest gap between skin and head: 0.0 px
- left: head turns -8.0° / 8.0° at BodyLean −1/+1. 1693 skin vertices under the envelope; largest gap between skin and head: 0.0 px
- right: head turns -8.0° / 8.0° at BodyLean −1/+1. 1812 skin vertices under the envelope; largest gap between skin and head: 0.0 px
- back: head turns -8.0° / 8.0° at BodyLean −1/+1. 1770 skin vertices under the envelope; largest gap between skin and head: 0.0 px
- **Extreme poses for (c).** Each pose was rendered with the current renderer at linear quality (rig/index.html `drawM` with QUAL='linear', 1:1) at y ∈ {−1, 0, +1}:
  - uniform x = −1 and x = +1;
  - in apose, tpose and right, the auto-drive chain extremes as well: strand at ±1 with its tip at the opposite limit.
  - Per-pose counts are in `work/summary.json` → `extremes`.
- **Head controls.** HeadTilt and HeadNod also move the hair by the head matrix only, so they would add 0 px in the same way. They were not swept separately.

## Notes for Base Body
- **Speck fix (staged, not live).** `hair/staged/speck_fix/` moves 413 more px from `base_body` into strands: apose 58, tpose 54, left 68, right 23, back 210. The list is in `hair/staged/speck_fix/for_base_body/`.
  - Today they are on the body, so they are **not** in (a): 0 of the 413 are in the rest masks.
  - **All 413 are inside (b)**, the envelope.
  - Once the fix is applied, (a) grows by exactly these px. Clear them to alpha 0 as listed, and cover them with the hairless fill like the rest of the envelope.
- Nothing here is live, and no file outside `hair/` was written.
