# Line-art fix (STAGED ONLY, not live), Fri Oct 2 2026, 9:28 PM PT

Staged change: `views/apose/hair/rig.json`, which is the live file with **one value changed**. The strand_02 pivot moves from (606.0, 122.9) to **(608.5, 121.5)**, 3 px up its line onto a straight run. No PNG is changed and no new paint is added.
- At linear quality: apose strand_02 ← hair_front goes from REAL DEFECT (1 new sharp corner at s=−1, against a baseline of 0) to **clean**. Every other joint in apose is unchanged. Data: `work/trials/pivot_apose_strand_02.json`.
- Rest: 0 px in all five views, simulated together with the speck staging and the body cleared at the speck px (`work/mk_overlay.py --lineart`, rig/rest_check.py). A pivot does not affect rest.
- Eyes and mouth: the swept strand_02 footprint overlaps the eye and mouth parts by 0 px, both live and staged, so it adds **0 new px**.
- To apply: copy `views/apose/hair/rig.json` over the live one. This is the Coder's call; nothing is live.

Tools (work/):
- `r18.py`: headless current renderer, linear by default.
- `lineart_r18.py`: the checker, with baselines.
- `pivot_trial.py`: the pivot search loop.
- `crops_r18.py`: zoomed crops.
- `mk_overlay.py`: the scratch simulation tree.

Not fixed (pivot moves of −6 to +6 px along the line did not clear them; see `work/trials/pivot_*.json`):
- apose strand_04;
- tpose strand_04 and strand_05;
- right strand_01;
- right strand_03 (only if the 1 px-line baseline is excluded);
- left strand_01 with the speck staging.
Details are in `hair/qa/lineart/r18/SUMMARY.md`.

## Job D: joint caps and seam re-cuts (STAGED ONLY, 10:34 PM PT)
Each joint uses `work/cap_trial.py` (recut d : cap L : radius w, all in px). Every moved px is an exact copy: cap px are parent px that equal base.png (alpha 255), and recut px move verbatim from child to parent. No new paint. Settings and px counts are in `work/jobD_stage_log.json`.

| joint | setting | px | staged files (views/<v>/hair/) |
|---|---|---|---|
| apose strand_04 ← hair_front | cap 0:2:10 | 51 cap | strand_04.png (+ the existing rig.json with the strand_02 pivot) |
| tpose strand_04 ← hair_front | 0:2:10 | 36 cap | strand_04.png |
| tpose strand_05 ← hair_front | 2:3:12 | recut 32 + cap 54, pivot → (720.5, 152.5) | strand_05.png, hair_front.png, rig.json |
| right strand_01 ← hair_front | 0:2:10 | 19 cap | strand_01.png |
| right strand_03 ← hair_front | 0:2:10 | 15 cap | strand_03.png |
| left strand_01 ← hair_front | 8:4:16 | recut 84 + cap 9, pivot → (580.5, 146.5) | strand_01.png, hair_front.png, rig.json |

Checks, all at LINEAR quality and all with the speck staging included:
- Joints (`hair/qa/lineart/r18/lineart_r18_staged_jobD_linear.json`, plus `..._staged_jobD_right_linear.json` after the right strand_03 cap): all 6 joints are **clean**. Every view has 0 REAL DEFECT joints. The part verdicts that remain are resampling artifacts only (tpose strand_05, left strand_01, back strand_04/05).
- Width (`work/jobD_width.json`): the change from rest width is at most 0.49 px staged (live: 0.77). Pieces are 1 everywhere, except left strand_01, where it goes from 2 at rest to 3 at sway under the strict ink threshold (≤60). That extra piece is the faint 1 px inner stroke dotting. At ink ≤80 or ≤100 it is 1 piece in every pose, live and staged (`work/jobD_width_left_th.json`). lineart_r18 scores this joint clean (dC ≤ 0, so pieces merge rather than split).
- Rest: 0 px in all 5 views. This was simulated in the `/tmp/hairsim` overlay with `rig/rest_check.py` copied, not symlinked, and no symlinks under its rig/. The live `rig/rest_diff_*.png` md5s and the `git status` of rig/ and views/ were the same before and after.
- Eyes/mouth: 0 new px over 129 sway poses (`work/jobD_face_<v>.json`).
- Holes: the blue sway gaps at these joints are fewer than live (compare the crops). What remains is Body's uncovered-at-sway (transparent base_body).
- Crops: `hair/qa/lineart/r18/crops/jobD_*.png`.
- Conflict: `hair/staged/brow_strand/apose/` also changes apose strand_04.png. If both are applied, the two need merging (the cap px and the brow px do not overlap the same pixels, but each file replaces the whole file).
