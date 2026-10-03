# Line art with the CURRENT renderer (rig/index.html @ main 6d5b239), LINEAR display quality, Fri Oct 2 2026, 9:28 PM PT

Checker: `hair/staged/lineart_fix/work/lineart_r18.py`. It renders in headless Chrome with the rig's own `drawM` and QUAL='linear'; rest uses the exact rest path. The ink, piece, break and corner metrics are the same as in `../SUMMARY.md`. Sway s ∈ {−1, −0.5, +0.5, +1}.
- **Baselines** are measured at the same absolute angle, with no joint:
  - (rigid) the same child+parent art drawn rigidly;
  - (line1/line2) a plain anti-aliased 1 px / 2 px line, 17 px long, along the local line direction;
  - (static) the known-good static part (hair_front, or hair_back in the back view);
  - (s0) the joint posed at s=0. At linear this is identical to rest, so it adds 0.
- **Pass mark: no worse than the baseline.** The 1 px line alone makes 0–14 "new corners" from its own stair-stepping, so a verdict that excludes line1 (the strict one) is also reported.
- Data:
  - `lineart_r18_live_linear.json` (live);
  - `lineart_r18_staged_both_linear.json` (speck + lineart_fix staging);
  - `lineart_r18_live.json` / `lineart_r18_staged_speck*` (the older 2x supersampled run, for reference).
- Crops: `crops/` (2x run).

## The joints that failed before (old Python mirror), re-scored at linear (live hair)
Each cell is measured / baseline max: new pieces dC and new sharp corners (corner baseline shown with line1, then without it).
| joint | s=−1 | s=−0.5 | s=+0.5 | s=+1 | verdict |
|---|---|---|---|---|---|
| apose strand_03_tip ← strand_03 | dC 0/0, c 0/2,0 | 0/0, 0/0,0 | 0/0, 0/0,0 | 0/0, 0/0,0 | **clean** (no fix) |
| apose strand_06_tip ← strand_06 | 0/0, 0/0,0 | 0/0, 0/5,0 | 0/0, 0/7,0 | 0/0, 0/8,0 | **clean** |
| tpose strand_03 ← hair_front | 0/0, 0/4,0 | 0/0, 0/0,0 | 0/0, 0/3,0 | 0/0, 0/4,0 | **clean** |
| tpose strand_02 (part) | pieces +1 (sub-px shift baseline +1) | +1 | +1 | +1 | **resampling artifact**. It goes clean with the speck staging, whose 8 px bridge the neck. |
| left strand_03 ← hair_front | 0/0, 0/0,0 | 0/0, 0/0,0 | **1/1**, 0/0,0 | **1/1**, 0/1,1 | **resampling artifact** (the rigid copy splits the same piece) |
| right strand_02 ← hair_front | 0/0 everywhere | | | | **clean** |
| right strand_02_tip ← strand_02 | 0/0, 0/0,0 | 0/0, 0/6,0 | 0/0, 0/6,0 | 0/0, 0/13,0 | **clean** |
None of these joints breaks at any s.

## Joints that fail only with the current renderer at linear (new; the old mirror passed them)
| joint | measured (corners at s=−1/−0.5/+0.5/+1) | baseline | verdict | fix |
|---|---|---|---|---|
| apose strand_02 ← hair_front | 1/0/0/0 | 0 | real defect | **STAGED**: pivot → (608.5, 121.5), then clean |
| apose strand_04 ← hair_front | 4/0/2/3 | 0 | real defect | pivot −6 to +6 px: no fix |
| tpose strand_04 ← hair_front | 3/0/3/4 | 0 | real defect | no fix |
| tpose strand_05 ← hair_front | 2/0/0/0 | 0 | real defect | no fix |
| right strand_01 ← hair_front | 0/0/0/4 | 0 | real defect | no fix |
| right strand_03 ← hair_front | 0/0/0/3 | 0 (line1: 3) | artifact (with line1) / real (strict) | no fix |
| left strand_01 ← hair_front, **speck staging only** | pieces 0/2/1/1 | 0/1/1/0 | real defect: the faint speck strokes separate at s=−0.5 and +1 | none (no base px is left to bridge them) |
All of these are 2–4 contour points turning more than 60° within 8 px of the seam, where a swinging strand crosses the static hair_front line. There are no breaks, and width stays within 1 px (no part fails width).

## Status vs the new absolute pass mark (no breaks, no new sharp corners)
- No breaks anywhere, and line width is within 1 px.
- **Not passing yet:** new sharp corners at the 5 joints above, plus +1 split pieces at left strand_03 and tpose strand_02 (both resampling, the same as the no-joint baseline).
- Next lever to try: longer overlap caps and seam re-cuts from base.png along the crossing line. The earlier r=4 cap trial did not clear any corner. These need art judgement on the crops before more automated loops.

## Job D result (10:34 PM PT, STAGED): every listed joint is clean
apose strand_04, tpose strand_04, tpose strand_05, right strand_01, right strand_03 and left strand_01 are all **clean** at LINEAR with caps and re-cuts (`hair/staged/lineart_fix/README.md`, Job D). No view has a REAL DEFECT joint. Width change is ≤0.49 px. Rest is 0 px, with 0 new face px. Crops: `crops/jobD_*.png`.
