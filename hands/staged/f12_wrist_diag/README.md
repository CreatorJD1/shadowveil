# F12: diagonal wrist flaps for 45 and 315 (staged)

Status: **PASS** on all four hands (45 L/R, 315 L/R): rest 0 px, 0 chroma, 0 off-palette, and a seam gap of 0 at every tested bend. Run date 2026-10-03, about 03:30–03:45 PT.

## Files
- **Frame-scale flaps:** `<angle>/frame_scale/{L,R}_wristflap.png`, on her f033/f191 frame canvas (768×1168). They match `hands/staged/f8_diagonals/<angle>/frame_scale/`.
- **View-scale flaps:** `<angle>/{L,R}_wristflap.png` (1365×1739), made with view_fit from `body_tools/work/diag_body/<angle>/wrist_cuts.json`. Nearest-neighbour inverse map, so the colours are exact.
- **Rig addition:** `<angle>/rig_addition.json`, entries for `hands/staged/f8_diagonals/<angle>/rig.json`:
  - id `<S>_wristflap`, parent `<S>_palm`;
  - pivot = palm pivot (view, plus `pivot_frame` = f8_palm_pivot_frame);
  - layer = palm layer − 1 (R 299, L 319), so it draws under the palm and under the forearm;
  - maxCurlDeg 0.
- **Checks:** `check.json` (all numbers) and `before_after_sheet.png` (wrist ±25°, without and with the flap, per hand).
- **Tools and log:** `f12.py`, `find4.py`, `run.log`. Crops are in `<angle>/crops/`.

## Method (F7 style, radius 20, line 2 px)
**Where the flap goes.** Flap px are her figure px on the forearm side of Body's `boundary_line_fit`, within 20 px of `f8_palm_pivot_frame`.
- They lie only under the forearm (`fg` minus the union of the F8 parts; 0 px elsewhere) and are connected to the hand.
- The flap's outer edge against the background gets a 2 px line. Her forearm/hand line width at rest is 2.0 px.

**Colours.** Flat colours, each side from its own px (no mirroring). Skin is the mode of her non-key px with lum > 110, and line is the mode of px with lum < 60, taken from that side's hand and forearm near the wrist.

| hand | skin | line | flap px | line px | view px |
|---|---|---|---|---|---|
| 45 L | (188,128,85) | (44,18,54) | 364 | 80 | 856 |
| 45 R | (186,128,87) | (36,8,59) | 331 | 82 | 783 |
| 315 L | (190,130,87) | (59,23,47) | 348 | 80 | 829 |
| 315 R | (189,129,86) | (49,23,53) | 360 | 81 | 861 |

- Every flap colour exists in that side's own frame px. Off-palette 0, chroma (B − max(R,G) > 25) 0, at frame and view scale.

**Composite tested.** Both F8 frame_scale hands are drawn first. Then the body layer on top: her frame px on `fg` minus the union of the F8 parts (Body's rule). The tested hand, with its flap underneath, is rotated about `f8_palm_pivot_frame` (premultiplied bilinear).

**Bend range** (same as F7/F10, wristMaxDeg 25): ±25° (wrist ±1), anger +3.5°, jump −5° / +7.42°, run ±3°.

## Results (max over the 7 bends; per-bend numbers in check.json)
| hand | rest change with flap | seam gap no flap → flap | holes no flap → flap | max abs line-width change with flap | breaks: rest / no flap / flap |
|---|---|---|---|---|---|
| 45 L | 0 px | 21 → **0** | 5 → **0** | 0.17 px | 16 / 33 / 15 |
| 45 R | 0 px | 25 → **0** | 4 → **0** | 0.30 px | 27 / 42 / 22 |
| 315 L | 0 px | 25 → **0** | 5 → **0** | 0.20 px | 18 / 33 / 14 |
| 315 R | 0 px | 17 → **0** | 4 → **0** | 0.18 px | 14 / 30 / 15 (+1 vs rest, in 1 case) |

**Definitions.**
- **Seam gap:** transparent px (alpha < 0.5) in the wrist interior that close with a 5 px disk and were not already gaps at rest. The wrist interior is 6 px either side of Body's boundary line, at least 2 px inside each end of the cut.
- **Holes:** enclosed transparent areas within the seam band and its two ends.
- **End notch** (reported, not part of the pass): at the two outline corners of the seam, a bent wrist leaves a concave sliver in the outline. With flaps it is 5–8 px max (without, up to 11).
  - It cannot be filled from under the forearm without showing at rest.
- **Breaks:** outline px with no line within 1 px. Her rest outline in this zone already has 14–27 such px (her lineless outline), and the flap never makes it worse than no flap.

## 315 L: Body's 4 nonhand px (task 3, revised 03:40 PT: her exact colours, no snap)
**The 4 px** (f191 frame px): (590,548) (33,0,60), (591,548) (64,31,91), (590,549) (47,14,74), (591,549) (32,0,59).
- A 2x2 block of her line ink about 64 px past the wrist, at a finger edge, enclosed by hand px.
- B - max(R,G) = 27, so F8's key removed them; Body's rule (enclosed key islands < 6 px = ink) kept them as figure.

**Fix.**
- **Part:** 315 L is a far hand (whole sprite, `L_palm` only). The px went into `hands/staged/f8_diagonals/315/frame_scale/L_palm.png` at alpha 255 with her **exact** frame colours. The earlier snap is undone.
- **View-scale copy:** F8's resample of the new frame part. Only the px whose resample changed are re-snapped (F8 palette + her 4 colours); every other view px is identical to F8. That is 25 px changed, view bbox x 1015-1019, y 793-797.
- **Backups:** `315/backup_f8_315_L/`.

**Gates** (`315/L_4px_fix.json`, also in `check.json` under `315_L_4px`):
- Rest at frame scale: **0 px** vs the pre-fix composite, and 0 px vs her frame at the 4 px.
- Exact #0000FF px: **0** at frame and view scale.
- Off-palette against her f191 colours for this hand: **0** at frame and view scale.
- **Flagged:** the F8 key test (B - max(R,G) > 25) flags **4 frame px and 2 view px**: her own colours (32,0,59) and (47,14,74) at view scale, and all 4 at frame scale (each B - max(R,G) = 27). They are her art, not key; not snapped, per instruction.
- The F12 flap numbers above are unaffected. These px are about 64 px from the wrist seam, and the flaps do not touch them.

## Merged rig (staged)
`<angle>/rig.json` = F8 `hands/staged/f8_diagonals/<angle>/rig.json` + the two `<S>_wristflap` entries (layers 299/319, parent palm, pivot = palm pivot).
- Flap file paths are relative to the F8 angle folder (`../../f12_wrist_diag/<angle>/...`).
- F8's rig.json is unmodified (md5 recorded in `staged_merge.base_md5`).

## Caveats
- The flap pass mark is from this scratch composite, not the live rig. Coder's `?diag=1` slots do not exist yet.
- F8's own rig.json is not modified; the merged copy is staged here.
