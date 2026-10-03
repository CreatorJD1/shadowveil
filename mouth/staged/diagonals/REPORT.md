# Job B: diagonal mouths (45° = f033, 315° = f191). STAGED PROPOSAL

> **THIS IS A PROPOSAL THAT REUSES FRONT ART.** The talking mouths here are her *front apose* mouth parts (from the Job A mesh-bend)
> squashed onto the diagonal rest lips. They are not her diagonal drawings, and nothing here is live.

Written 2026-10-02 PT. Inputs, all read-only:
- `reference/apose_turn/frames/f033.png` and `f191.png` (768×1168)
- the view fits from `body_tools/work/apose_turn/diagonals/diagonals.json` (base = scale·frame + (dx, dy); not edited)
- the Job A parts and meshes in `../mesh_bend/` (final config it16)

All sampling is bilinear.

## 1. Her closed rest lips cut from the frames (`lipcut.py` → `diag_<045|315>_rest_lips.png`, `_rest_mask.png`, `rest_lips.json`)
- **Detection.** The lips are found by RGB distance from her local skin colour (median of the bright, non-blue pixels around the mouth),
  with a ramp from 25 to 75 that gives 0–1 coverage. The detector takes the largest component and fills its holes, so the lower-lip
  highlight counts as lip.
- **Mapping.** The cut is resampled to view space with the fit, using the pixel-centre convention. RGB is her frame pixels; alpha is the coverage.

| | f033 → 45° | f191 → 315° | front apose rest (base.png, same rule) |
|---|---|---|---|
| Fit (scale, dx, dy) | 1.54468, 83.62, −55.77 | 1.54468, 104.47, −52.68 | — |
| Frame bbox (frame px) | x344–370, y208–220 (26×12) | x397–421, y208–221 (24×13) | — |
| View bbox (view px) | x615–655, y266–284 (**40×18**) | x718–755, y269–289 (**37×20**) | x655–707, y277–301 (52×24) |
| Area (coverage px) | 447 | 419 | 749 |
| Centroid (view) | (633.0, 273.7) | (739.0, 277.7) | (681.4, 287.7) |
| Offset from apose anchor (681, 286) | (−48.0, −12.3) | (+58.0, −8.3) | — |
| Seam corners (view) | (616.5, 269.5) – (653.5, 269.5) | (719.5, 272.5) – (753.5, 273.5) | — |
| Seam centre row | 272.2 | 275.6 | 286.2 |
| Sharpness: 20–80 edge width, top / bottom (view px) | 1.24 / 1.34 | 1.22 / 1.42 | 0.60 / 0.60 |
| Sharpness in frame px | 0.60 / 0.60 | 0.63 / 0.60 | — |
| Seam line FWHM (view px) / darkness vs lip tone | 3.0 / 35 | 3.0 / 30 | 2.9 / 54 |
| Mean lip RGB | (97, 55, 33) | (99, 57, 31) | (118, 77, 49) |

The frame lips are as crisp as the front in their own pixels, about 0.6 px edges. The ×1.545 upscale to view space softens them to about
1.2–1.4 px, and the seam is about 35 % less dark. Her diagonal lips are also darker and redder than the front lips.

## 2. Proposal: front parts bent to the diagonal rest lips (`diag.py` → `sheet.png`, `grid_<tag>.png`, `<tag>/renders/`, `results.json`)
**Pipeline.** For each (Open, Form), the Job A strip meshes bend the front parts. A front→diagonal map G then moves the result:
- G is a dense 2 px triangle grid.
- **G = H + per-column knots.** H is a homography (an affine was also fitted for comparison), fitted by maximising the soft IoU of her
  front rest lip silhouette against her diagonal one. The perspective is limited to ±15 % projective scale over the ±90×±60 crop;
  without that limit the 315° fit put its horizon line inside the crop and folded 161 triangles.
- **Knots.** On top of H, each column gets vertical residual knots for its top edge, seam and bottom edge, measured against her frame lips
  (median-3 then box-3 smoothed, clamped to ±3 px).
- **Sampling.** Bilinear at 4× supersampling, then a 4×4 box filter. The mouth is minified about 0.75×, and plain bilinear drops 1 px lines when minifying.
- **Clip.** The result is clipped to her own face silhouette in the frame. Unclipped, the open mouths ran past the jaw: max 15 px at 45°, 53 px at 315°.

**Rest: silhouette IoU against the frame's own lips**

| | 45° | 315° |
|---|---|---|
| Affine only | 0.875 | 0.895 |
| Homography only (perspective-limited) | 0.861 | 0.891 |
| **Homography + mesh** | **0.934** (soft 0.912) | **0.920** (soft 0.914) |
| Median edge error top / seam / bottom (px) | 0.27 / 0.13 / 0.12 | 0.26 / 0.20 / 0.12 |
| Largest residual knot top / seam / bottom (px) | 2.9 / 0.8 / 1.9 | 2.1 / 2.6 / 1.1 |
| Flipped triangles in G | 0 | 0 |
| Proposal size | 38×19 | 34×20 |
| Proposal edges 20–80, top / bottom | 1.14 / 1.13 | 1.08 / 1.14 |
| Proposal seam FWHM / darkness | 3.0 / 39 | 3.0 / 41 |
| Lip colour MAE vs her frame (inside both masks) | 25.5 | 24.5 |
| Front skin pad minus frame skin (RGB) | (−2, +1, 0) | (−3, +2, 0) |

**Talking grid** (Open 0,.25,.5,.75,1 × Form −1,−.5,0,.5,1, over her frame), both diagonals:
- 0 holes (≥2 px inside the outer edge)
- 0 key-blue spill
- 0 flipped triangles

The gaps-between-parts, interior-clip and line-width marks are inherited from Job A, which passes them all. G warps the already-stacked
mouth, so it cannot open gaps between the parts.

## Problems / not solved
- **It is front art.** At 45°/315° the far half of the mouth should be foreshortened and the near corner should wrap around the cheek. A
  homography plus vertical knots only roughly approximates this (IoU 0.92–0.93). Her far corner at 315° is a thin point, which the front corner does not reproduce.
- **Colour.** The front lips are lighter and less saturated than her diagonal lips (MAE about 25). No colour transfer was done, because it would change her pixels.
- **Sharpness.** The proposal's edges (about 1.1 px) are a little crisper than her upscaled frame lips (about 1.3 px). The seam is darker (39–41 vs 30–35).
- **Rest is not 0 px.** There is no diagonal base.png to rebuild. If a diagonal view is adopted, her own frame lips (the cut in step 1) should be
  the rest drawing, and the bent front mouth should be used only for non-rest shapes, or redrawn by the art team.
- The homography is a local optimum: at 45° it scores slightly below the affine because of the perspective limit. The mesh knots recover the difference.
- **FORMAT.md** would need a projective (4-corner) part transform, or per-vertex dst override, plus a clip-to-silhouette mask, to express this.

## Files
- Sheet: `sheet.png` (labelled PROPOSAL). Talking grids: `grid_045.png`, `grid_315.png`.
- Renders (full canvas): `045/renders/`, `315/renders/`.
- Rest cuts: `diag_045_rest_lips.png`, `diag_315_rest_lips.png`, and their masks.
- Data: `rest_lips.json`, `results.json`. Code: `lipcut.py`, `diag.py`.
- The frames resampled to view space are cached as `mouth/work/diag_<tag>_frame_in_view.npy`.
