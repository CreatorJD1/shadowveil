# Job A: mouth mesh-bend prototype (apose, tpose). STAGED, offline, not live

Written 2026-10-02 PT. Code: `bend.py` (parts, controls, meshes), `mb.py` (bilinear triangle warp), `measure.py`, `run.py`
(every iteration's config, so the history can be rerun), and `final.py` (deliverables). Sampling is **bilinear on premultiplied RGBA**
everywhere, for both the warps and the measurements. Every output pixel is an interpolation of her own pixels: `views/<v>/base.png`,
`views/<v>/mouth/*.png`, or `mouth/staged/mesh_split/<v>/*`. Nothing is painted.

Draw order, bottom to top: upper_flap, lower_flap, interior (clipped to the warped lip gap, only drawn when Open>0), lower_lip, then upper_lip.
`rig/`, `views/*/base.png`, rig.json files and other teams' folders were only read, never written.

## Final config: it16 (16 iterations)
- **Meshes.** One triangle strip per lip, with a vertex column at every pixel column (sx=1). Each column has 7 knots:
  pin, outer edge, outline band, fill, seam band, inner edge, flap. The pin columns are 6 px outside the corners.
  The interior has its own strip, tucked 1.5 px under both lips and extended 2 px past the corners.
- **Weights.** The line-art bands are rigid: the outline (2 rows) and the seam band (widened over the dark anti-aliased pixels, L<50) move as one piece.
  The fill between them can compress, to no less than 25 % of its height (the same thinning her AA/AA_half show). Pins hold the vacated side
  so the lips stretch over skin instead of tearing. The rigid bands move by whole pixels vertically, so the line art is an exact copy;
  x stays continuous because snapping x folded columns under the M squeeze.
- **it16 change.** The extra lift from the min-fill clamp is spread along x (a min/max filter then a box filter, k=1). The outline band
  now moves as one piece instead of a per-column comb, and the clamp still holds at every column.
- **Controls.** MouthOpen is calibrated piecewise from her AA_half (Open .5) and AA (Open 1). For apose the centre gap targets are 6 / 14 px:
  the lower lip moves down 3 / 11 px and the upper lip's inner edge moves up 3 px. MouthForm uses corner (dx, dy) targets plus a curl exponent
  fitted to her M (−1) and smile (+1), with a centre press. See `calib.json`.
- **Flap.** make_mesh_split's upper flap (the 2 px of upper lip that make_mesh_split puts in the overlap) only exists on its few overlap columns.
  It was extended with make_mesh_split's own rule: the upper-lip pixels at and below the seam row. The rule now runs along every column and the
  flap overlaps its owner by 2 rows. It sits on its own layer, `upper_flap`, below the lower lip and the interior. `lower_flap` was built the same way.
- **Derived parts.** All are cut from her pixels and staged in `<view>/parts/`:
  - A 3 px base.png skin pad around the rest lips, split at the seam row: apose upper 250 / lower 288 px, tpose 245 / 284 px.
  - The staged interior's per-column notches (apose 12 px, tpose 11 px), filled with the AA.png pixels at the same place.

## Pass marks (final it16; 25 cells per view: Open 0,.25,.5,.75,1 × Form −1,−.5,0,.5,1)
| Mark | apose | tpose | Result |
|---|---|---|---|
| Rest rebuilds base.png | 0 px differ | 0 px differ | PASS |
| Seam width vs rest (ink per column, px): median / max deviation | 0.081 / 0.560 | 0.080 / 0.490 | PASS (≤1) |
| Outline width vs rest (20–80 edge width, px): median / max deviation | 0.060 / 0.634 | 0.076 / 0.649 | PASS (≤1) |
| Breaks (seam + outline columns) | 0 | 0 | PASS |
| Holes/gaps between parts (core px with coverage <250/255) | 0 (strict <254.5: 1 px, see-through 0.003) | 0 | PASS |
| Interior spill outside the lip gap (>0.5 px) | 0 | 0 | PASS |
| Key-blue spill (#0000FF) | 0 | 0 | PASS |
| Flipped triangles | 0 | 0 | — |

## Silhouette IoU against her shapes (final it16)
| Shape (cell) | apose | tpose |
|---|---|---|
| AA_half (Open .5, Form 0) | 0.853 | 0.881 |
| AA (Open 1, Form 0) | 0.908 | 0.907 |
| M (Open 0, Form −1) | 0.922 | 0.889 |
| smile (Open 0, Form +1) | 0.899 | 0.924 |
| OH_half / OH (Form −1) | 0.775 / 0.691 | 0.812 / 0.697 |
| EE_half / EE (Form +1) | 0.802 / 0.692 | 0.841 / 0.716 |
| Opening IoU, AA / AA_half | 0.787 / 0.618 | 0.813 / 0.624 |

it13 had about 0.02–0.03 higher IoU on AA_half/AA/M (apose .880/.924/.948), but it shows a ragged per-column comb on the upper-lip top edge
when the mouth is open. it15 (k=3) removed the comb but lost more IoU (apose AA_half .829). k=1 is the compromise. All three pass every mark.

## Iterations (all rerun with the final measurement code; `iterations.json`)
Columns: rest px | seam dev med/max | outline dev med/max | breaks | holes | int. spill | blue | flips | IoU AA_half/AA/M/smile | result
| it | view | rest | seam | outline | brk | holes | spill | blue | flip | IoU | result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| it1 | apose | 5 | 0.137 / 1.148 | 0.103 / 3.887 | 18 | 50 | 63 | 0 | 60 | 0.810 / 0.851 / 0.786 / 0.871 | fail: rest,line_width,no_breaks,no_holes,no_interior_spill |
| it1 | tpose | 6 | 0.163 / 0.954 | 0.078 / 3.286 | 0 | 61 | 41 | 0 | 42 | 0.807 / 0.840 / 0.777 / 0.860 | fail: rest,line_width,no_holes,no_interior_spill |
| it2 | apose | 0 | 0.082 / 1.148 | 0.103 / 0.652 | 15 | 50 | 0 | 0 | 60 | 0.814 / 0.848 / 0.787 / 0.871 | fail: line_width,no_breaks,no_holes |
| it2 | tpose | 0 | 0.102 / 0.775 | 0.078 / 0.630 | 0 | 61 | 0 | 0 | 42 | 0.805 / 0.836 / 0.778 / 0.860 | fail: no_holes |
| it3 | apose | 0 | 0.093 / 1.303 | 0.108 / 0.652 | 15 | 49 | 0 | 0 | 30 | 0.832 / 0.860 / 0.817 / 0.885 | fail: line_width,no_breaks,no_holes |
| it3 | tpose | 0 | 0.102 / 0.775 | 0.086 / 0.622 | 0 | 59 | 0 | 0 | 34 | 0.825 / 0.849 / 0.806 / 0.871 | fail: no_holes |
| it4 | apose | 0 | 0.360 / 2.009 | 0.117 / 0.975 | 120 | 45 | 0 | 0 | 0 | 0.929 / 0.919 / 0.932 / 0.906 | fail: line_width,no_breaks,no_holes |
| it4 | tpose | 0 | 0.307 / 2.000 | 0.137 / 0.690 | 35 | 53 | 0 | 0 | 0 | 0.915 / 0.941 / 0.905 / 0.917 | fail: line_width,no_breaks,no_holes |
| it5 | apose | 0 | 0.398 / 2.004 | 0.136 / 0.975 | 193 | 16 | 0 | 0 | 12 | 0.905 / 0.918 / 0.932 / 0.906 | fail: line_width,no_breaks,no_holes |
| it5 | tpose | 0 | 0.307 / 1.940 | 0.127 / 0.692 | 66 | 27 | 0 | 0 | 12 | 0.906 / 0.934 / 0.905 / 0.917 | fail: line_width,no_breaks,no_holes |
| it6 | apose | 0 | 0.209 / 1.136 | 0.136 / 0.975 | 7 | 21 | 1 | 0 | 12 | 0.892 / 0.913 / 0.936 / 0.925 | fail: line_width,no_breaks,no_holes,no_interior_spill |
| it6 | tpose | 0 | 0.268 / 0.835 | 0.127 / 0.692 | 1 | 27 | 0 | 0 | 12 | 0.912 / 0.934 / 0.905 / 0.921 | fail: no_breaks,no_holes |
| it7 | apose | 0 | 0.190 / 1.133 | 0.124 / 0.975 | 5 | 20 | 1 | 0 | 18 | 0.893 / 0.918 / 0.938 / 0.924 | fail: line_width,no_breaks,no_holes,no_interior_spill |
| it7 | tpose | 0 | 0.260 / 0.839 | 0.142 / 0.692 | 1 | 27 | 1 | 0 | 18 | 0.912 / 0.935 / 0.904 / 0.922 | fail: no_breaks,no_holes,no_interior_spill |
| it8 | apose | 0 | 0.190 / 1.133 | 0.124 / 0.975 | 5 | 1 | 1 | 0 | 0 | 0.893 / 0.918 / 0.938 / 0.924 | fail: line_width,no_breaks,no_holes,no_interior_spill |
| it8 | tpose | 0 | 0.260 / 0.839 | 0.142 / 0.692 | 1 | 1 | 1 | 0 | 0 | 0.912 / 0.935 / 0.904 / 0.922 | fail: no_breaks,no_holes,no_interior_spill |
| it9 | apose | 0 | 0.127 / 0.671 | 0.172 / 0.870 | 0 | 1 | 1 | 0 | 0 | 0.884 / 0.914 / 0.950 / 0.898 | fail: no_holes,no_interior_spill |
| it9 | tpose | 0 | 0.160 / 0.724 | 0.144 / 0.728 | 1 | 1 | 0 | 0 | 0 | 0.908 / 0.936 / 0.905 / 0.925 | fail: no_breaks,no_holes |
| it10 | apose | 0 | 0.000 / 0.412 | 0.041 / 0.600 | 0 | 0 | 0 | 0 | 72 | 0.879 / 0.922 / 0.947 / 0.890 | PASS |
| it10 | tpose | 0 | 0.000 / 0.512 | 0.118 / 0.520 | 0 | 1 | 0 | 0 | 48 | 0.903 / 0.930 / 0.904 / 0.920 | fail: no_holes |
| it11 | apose | 0 | 0.096 / 0.476 | 0.113 / 0.821 | 0 | 0 | 1 | 0 | 0 | 0.879 / 0.922 / 0.948 / 0.892 | fail: no_interior_spill |
| it11 | tpose | 0 | 0.089 / 0.525 | 0.140 / 0.754 | 0 | 1 | 1 | 0 | 0 | 0.903 / 0.930 / 0.907 / 0.924 | fail: no_holes,no_interior_spill |
| it12 | apose | 0 | 0.096 / 0.476 | 0.113 / 0.821 | 0 | 0 | 1 | 0 | 0 | 0.879 / 0.924 / 0.948 / 0.892 | fail: no_interior_spill |
| it12 | tpose | 0 | 0.089 / 0.525 | 0.140 / 0.754 | 0 | 0 | 1 | 0 | 0 | 0.903 / 0.930 / 0.907 / 0.924 | fail: no_interior_spill |
| it13 | apose | 0 | 0.096 / 0.476 | 0.113 / 0.821 | 0 | 0 | 0 | 0 | 0 | 0.879 / 0.924 / 0.948 / 0.892 | PASS |
| it13 | tpose | 0 | 0.089 / 0.525 | 0.140 / 0.754 | 0 | 0 | 0 | 0 | 0 | 0.903 / 0.930 / 0.907 / 0.924 | PASS |
| it14 | apose | 0 | 0.127 / 0.671 | 0.172 / 0.870 | 0 | 0 | 0 | 0 | 0 | 0.883 / 0.914 / 0.950 / 0.898 | PASS |
| it14 | tpose | 0 | 0.160 / 0.724 | 0.144 / 0.728 | 1 | 0 | 0 | 0 | 0 | 0.908 / 0.936 / 0.905 / 0.925 | fail: no_breaks |
| it15 | apose | 0 | 0.072 / 0.884 | 0.060 / 0.650 | 0 | 0 | 0 | 0 | 0 | 0.829 / 0.895 / 0.897 / 0.891 | PASS |
| it15 | tpose | 0 | 0.079 / 0.979 | 0.071 / 0.617 | 0 | 0 | 0 | 0 | 0 | 0.861 / 0.887 / 0.882 / 0.921 | PASS |
| it16 | apose | 0 | 0.081 / 0.560 | 0.060 / 0.634 | 0 | 0 | 0 | 0 | 0 | 0.853 / 0.908 / 0.922 / 0.899 | PASS |
| it16 | tpose | 0 | 0.080 / 0.490 | 0.076 / 0.649 | 0 | 0 | 0 | 0 | 0 | 0.881 / 0.907 / 0.889 / 0.924 | PASS |

What changed each time:
1. it1: naive coarse 6×4 grid, rigid lips, interior unclipped.
2. it2: interior clipped to the gap, flaps on their own layers. Rest now 0 px.
3. it3: pins plus the skin pad.
4. it4: feature-aligned strips with rigid bands. The seam broke at thin corner columns.
5. it5: interior tuck and x-overlap.
6. it6: thin-column clamp.
7. it7: sx=1.
8. it8: overlapping flaps on every column, the pad split at the seam row, and the interior extrapolated. Holes went from 50 to 1.
9. it9: the seam band widened over dark AA pixels, and linear smile dx. The seam passed.
10. it10: snap in x and y. It folded 72 triangles.
11. it11: snap y only.
12. it12: interior notch fill. Holes 0.
13. it13: interior clip at 0.5 px. Spill 0, and this was the first iteration to pass every mark in both views.
14. it14: control run without snapping. One tpose seam break.
15. it15: comb fix with k=3.
16. it16: comb fix with k=1. Final.

## Remaining problems
- OH/EE are not reachable with open plus form. There is no pucker or round control, and the teeth aren't a part (IoU 0.69–0.84).
- The opening shape is only roughly matched: opening IoU is 0.62 for AA_half and 0.79 for AA. Her drawn cavity is not a stretched rest cavity.
- The upper lip gets compressed when open, as in her art. The lower-lip highlight gets squashed and is not redrawn.
- Pixel snapping moves the line in whole-pixel steps across Open, so animation steps where a continuous runtime wouldn't (it14 shows the continuous version).
- The skin pad, the interior notch fill and the extended flap are derived parts. They are documented above and staged in `<view>/parts/`.

## What `rig/partmesh/FORMAT.md` (v0.2 draft, read-only) would need for this mouth
- Spines of about 50 points, one per pixel column, or a per-column knot table. The draft allows only 3–5 spine points.
- Rigid and compressible band weights along a spine: rigid outline and seam bands, compressible fill with a minimum fill ratio, and the
  clamp-excess spreading.
- Per-vertex or per-band pixel snapping, with y-only snapping kept separate from x/y snapping.
- A "pin on the vacated side" rule, and a skin-pad drawable cut from base.png.
- The interior clip uses lip spines as its edges. It needs tuck and extension parameters (0.5 px) and an overlap margin.
- Flap layers need a defined owner overlap, and a layer slot below the interior. `visibleWhen` for the interior at Open>0 already works.
- Non-linear control curves: piecewise open targets at .5 and 1, per-side corner dx/dy, and a curl exponent.
- Diagonal views (45°/315°) have no drawings of their own. A projective (homography) part transform and a face-silhouette clip would be needed (see `../diagonals/REPORT.md`).

## Files
- Contact sheet: `sheet.png` (her shapes beside the bent ones, 8x, key blue).
- 5×5 grids: `grid_apose.png`, `grid_tpose.png`, `grid_apose_on_face.png`, `grid_tpose_on_face.png`.
- `results.json` (every cell's measurements, the calibration, and the iteration history) and `iterations.json`.
- Renders: `<view>/renders/o<O>_f<F>.png`. Parts: `<view>/parts/*.png`.
- Code: `bend.py`, `mb.py`, `measure.py`, `run.py`, `final.py`, `calibrate.py`, and `calib.json`.
