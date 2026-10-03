# Diagonal turn frames: staged hair cuts (STAGED ONLY), Base Hair, Fri Oct 2 2026, 10:03 PM PT

Sources: `reference/apose_turn/frames/f033/f087/f131/f191.png`. Each frame is mapped into the 1365x1739 view space with `body_tools/work/apose_turn/diagonals/diagonals.json` `view_fit`, per frame, not `handoff_interp`.
The resample is premultiplied bicubic (cv2.INTER_CUBIC). Nothing outside `hair/staged/diagonals/` was written.

## Method (`work/key.py`, `work/toview.py`, `work/split.py`, `work/build.py <frame>`)
1. **Key + despill.** Alpha comes from each pixel's blue excess over the key (0,0,253). The key colour is then unmixed out: F = (C − (1−a)K)/a. Blue is capped at max(r,g)+20, which keeps the navy tint and removes the key cast.
2. **Loops keyed on blue.** The enclosed blue islands inside hair loops (Body's spill.py definition: blue excess > 120 inside the filled silhouette, top 22%) are set fully transparent.
3. **Hair mask.** Dark ink connected to the hair mass is hair, plus vertical thin lines hanging from it, plus loose flyaways close by. These stay body:
   - the face and neck outline (dark ink with skin on one side and key on the other);
   - eyes, brows, lashes, moles and lips (holes in the skin);
   - brown linework that is not a hanging strand;
   - the nape micro-curls on the back diagonals (they are enclosed by skin).
4. **Parts.**
   - Bun: an ellipse per frame.
   - Strands: thin hanging pieces below the mass hull, named after the front-view (`views/apose`) strands they correspond to.
   - Front diagonals: the mass is split at the ear into `hair_front` (face side, layer 600) and `hair_back` (layer 100). Back diagonals: the mass is `hair_back` (layer 100), like `views/back`.
   - Strands keep apose layers and sway values. `strand_03`/`strand_06` get a `_tip` child split at 20% of the strand height. `extra_N` pieces have no front-view counterpart and are static.

## Results (per angle: `<angle>/hair/*.png`, `<angle>/hair/rig.json`, `<angle>/hair_mask_view.png`, `<angle>/result.json`; sheet `diagonals_hair_sheet.png`)

| angle | frame | blue-tinted hair px before (Body metric) → after | key in loops keyed | bun layer | parts (px) | front strands hidden / merged | rest: parts vs mapped frame hair |
|---|---|---|---|---|---|---|---|
| 045 | f033 | 1237 (3217 incl. edges) → 0 | 56 → 0 opaque left | 101 | hair_back 6637, bun 8083, hair_front 11280, strand_03_tip 2204, strand_03 142, strand_04 335, strand_06_tip 620, strand_06 59, extra_1 152 | strand_01, strand_02, strand_05, strand_07 | 0 px, overlap 0 |
| 135 | f087 | 1286 (3397 incl. edges) → 0 | 52 → 0 opaque left | 650 | hair_back 32230, strand_06_tip 2189, strand_06 499, extra_1 638, extra_2 381, bun 8151 | strand_01, strand_02, strand_03, strand_03_tip, strand_04, strand_05, strand_07 | 0 px, overlap 0 |
| 225 | f131 | 1206 (3190 incl. edges) → 0 | 80 → 0 opaque left | 650 | hair_back 31340, strand_01 1772, strand_03_tip 916, strand_03 162, extra_1 618, extra_2 120, bun 9105 | strand_02, strand_04, strand_05, strand_06, strand_06_tip, strand_07 | 0 px, overlap 0 |
| 315 | f191 | 1177 (3248 incl. edges) → 0 | 44 → 0 opaque left | 101 | hair_back 2979, bun 8135, hair_front 15078, strand_03_tip 575, strand_03 106, strand_04 369, strand_05 267, strand_06_tip 752, strand_06 2340, extra_1 128 | strand_01, strand_02, strand_07 | 0 px, overlap 0 |

## Hidden strands
- **045 (f033):** strand_01 is merged into the far-side lock, which is cut as strand_03 + tip. strand_02, strand_05 and strand_07 are hidden or merged into the mass.
- **315 (f191):** strand_01, strand_02 and strand_07 are hidden. strand_06 on the far side is mostly soft flyaway edge.
- **135 (f087):** only her-left strand_06 (+ tip) shows, beside the ear. Two nape wisps are cut as extra_1/extra_2. All other front strands are hidden.
- **225 (f131):** only her-right strand_01 and strand_03 (+ tip) show. Two nape wisps are cut as extra_1/extra_2. All other front strands are hidden.

## Softness after scale-up (alpha AA band px per silhouette edge px, hair above y150; lower = crisper)

| angle | raw frame | cubic (used) | lanczos4 | linear | nearest | views/apose base.png |
|---|---|---|---|---|---|---|
| 045 | 2.894 | 3.711 | 3.732 | 3.961 | 3.303 | 0.998 |
| 135 | 3.268 | 4.056 | 4.089 | 4.315 | 3.916 | 0.998 |
| 225 | 2.941 | 3.761 | 3.723 | 4.018 | 3.559 | 0.998 |
| 315 | 2.861 | 3.766 | 3.735 | 3.995 | 3.332 | 0.998 |

The frames are already soft at source: about 2.9–3.3 px of AA per edge px, against 1.0 in the drawn views. The ×1.545–1.573 scale-up adds about 0.8, so the diagonal hair edges come out ~3.7–4.1, roughly 4× softer than the drawn views.
Cubic and lanczos4 are equal and better than linear. Nearest only looks lower because it is stair-stepped. Nothing here repaints or sharpens.

## Requirements for Base Body / limits
- Strand mapping uses the component ids printed by `split.hanging()` on the final cut (`work/split_<frame>.png`). After any rebuild, check them against the bboxes in `rig.json`; the 225 ids shifted once and were fixed.
- `hair_back` (100) and `bun` (101 at 045/315) sit below base_body (220). The diagonal body plate must be alpha 0 inside `<angle>/hair_mask_view.png`, or carry the identical pixels, as in `views/back`. Otherwise those parts are hidden.
- The hair_front/hair_back split at 045/315 is a straight seam at the ear x (720 / 615). It is invisible at rest because the two parts are an exact partition.
- Strand names are a judgement from `diagonals_hair_sheet.png`. Checked by eye; review welcome.
- At 045, part of the near ear's inner lines passes the hanging-strand rule and sits in `hair_front`.
- Not checked: sway holes, which need Body's diagonal plate, and hair over eyes/mouth, which needs diagonal face parts (none exist yet). The cut leaves the frame's eyes, brows and lashes in the body.

Sheet legend: hair_back slate, hair_front green, bun red, strand_01 orange, strand_03 magenta, strand_03_tip dark pink, strand_04 cyan, strand_05 blue, strand_06 yellow, strand_06_tip olive, extra_1 brown, extra_2 teal.
