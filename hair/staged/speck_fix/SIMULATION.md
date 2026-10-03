# Speck fix: staged files and scratch simulation

STAGED ONLY. Nothing under `views/`, the hair erase masks, `base_body*`, `body_tools/`, or the live `hair/validate_hair.py` was modified. The sha256 of every live file was checked before and after the run. Simulation ran in overlays under /tmp/speckwork (symlinked tree, staged files as real copies, validator path redirected). Heavy jobs ran one at a time.

## Staged
- `views/<view>/hair/<strand>.png`: 17 strand PNGs, at the same paths as the live files. Each has the speck px set to the exact `base.png` RGBA. They differ from live **only** at the 413 speck px (checked: 0 other px).
- `hair/<view>_hair_erase_mask.png`: live mask OR the speck px. Each is identical to `hair/qa/wisp_fix/erase_mask_proposal/<view>_hair_erase_mask_PROPOSED.png`.
- `validate_hair.py` plus `validate_hair.diff`: the chroma exemption (a 2-line change).
- `apply.sh`: manual only; requires `--apply`. It runs preflight, backup, copy, rest check, validator and the lineart gate, and restores automatically on failure.
- `manifest.json`: the live sha256 at staging time and the staged sha256.
- `PIXELS.md` and `for_base_body/`: the pixel list for Base Body.
- `work/`: the scripts and logs.

## Numbers (speck px per view: apose 58, tpose 54, left 68, right 23, back 210)
| check | apose | tpose | left | right | back |
|---|---|---|---|---|---|
| rest_check, staged + **current** body (not rebuilt) | 0 | **23** | **48** | **10** | **120** |
| rest_check, staged + body with speck px cleared to alpha 0 (the expected rebuild) | **0** | **0** | **0** | **0** | **0** |
| rest_check, staged + a copy of clear_hair.py (R=3, skin fill) on the current body | 934 | 1531 | 1316 | 1691 | 704 |
| … same clear_hair copy with the LIVE mask (control) | 991 | 1585 | 1384 | 1712 | 914 |
| … px failing only with the staged mask (not in the control) | 1 | 0 | 0 | 1 | 0 |
| staged validator (rebuilt body) | PASS | PASS | PASS | PASS | PASS |
| staged validator (current body) | PASS | PASS | PASS | PASS | PASS |
| specks left behind at s∈{±0.5,±1} × sway-Y∈{−1,0,1}, rebuilt body | **0** | **0** | **0** | **0** | **0** |
| … same, current body (i.e. before Base Body clears them) | 53 | 51 | 62 | 20 | 187 |
| hair over eyes/mouth, NEW px (41 s × 3 sway-Y) | **0** | **0** | **0** | **0** | **0** (no face) |
| lineart gate (no new failures vs live) | pass | pass (fixes strand_02) | **FAIL** (strand_01 part + joint) | pass | **FAIL** (strand_04, strand_05) |

- **Staged validator:** ALL PASS. file_problems [] (the chroma exemption covers all 410 navy px), clamps [], rest_overlap {}, sway overlap 0, mask-vs-sway-union mismatch 0, erase_mask_uncovered 0, rest_stack diff 0.
- **The 201 rest px with the current body** are exactly the speck px with base alpha < 255. The strand copy composites over the identical body px. That is why this must wait for Base Body.
- **The clear_hair copy** is not what Base Body's full rebuild produces: even with the live mask it breaks rest by 900 to 1700 px per view. It is reported only as a delta. The staged mask adds at most 1 failing px per view (apose 1, right 1), and those are still inside that emulation's noise.
- **Lineart:** see `hair/qa/lineart/SUMMARY.md`. The live hair already fails 7 joints plus 1 part, so an absolute lineart pass is not possible for any hair state today. `apply.sh` gates on "no new lineart failures", and as staged that gate fails in left and back.

## FINAL (Fri Oct 2 2026, 8:55 PM PT, checked with the current renderer at main 6d5b239)
The pixel list is **final at 413 px** (apose 58, tpose 54, left 68, right 23, back 210). It is unchanged from the list above.

The six faint clusters that split off at sway were re-checked with the current renderer:
- left strand_01: four clusters, around (576,151), (583,180), (586,193) and (572,200);
- back strand_04: around (756,309);
- back strand_05: around (782–786,224–228).

All the base.png px that connect them to their strand are already in the staged strand as exact copies. The only other base px within 3 px of the split pieces are at the left strand_01 root, where hair_front/hair_back own them. See `work/connect_probe.py` and `work/connect_probe.json`. So no px was added.

The split is the faint 1 px stroke dropping under the ink threshold after resampling. It happens even at s=0 posed (pure ss2 resampling, no rotation). Whether that counts as a defect is scored against the resampling baseline in `hair/qa/lineart/` (step 2).

Consistency check (`work/verify_final.py`): ALL CONSISTENT.
