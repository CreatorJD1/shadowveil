# Hair handoff (Base Hair), Wed Sep 30 2026, 5:10 AM PT

All hair work is stopped. Nothing is half-written in the live files.

## Session Fri Oct 2 2026 (Base Hair), started 8:33 PM PT

### Step 0: sync check (done, 8:40 PM PT)
- Compared all 803 files of `hair/` and `views/*/hair/` in GitHub main 6d5b239 with the working tree, byte for byte (git blob hashes, read-only, using the already-fetched objects in `/workspace/.shadowveil-git`). **0 differ, 0 missing, 0 extra** (only git-ignored render frames are extra). Nothing was downloaded, so `hair/backups/pull_6d5b239/` was not needed.
- Local HEAD is 9458143; main 6d5b239 is 2 commits ahead, but those commits touch no hair files.
- **rig/ is behind main**: `rig/index.html` and `rig/index.v18-wip.html` differ, and `rig/hand_angles/` is missing. The Coder is pulling, so no renderer-based checks have run yet.
- `rig/rest_check.py` (a Python compositor that is the same in main) was run from a scratch copy so `rig/rest_diff_*.png` were not overwritten. Result: **0 px in all five views**.

- Update: the Coder then pulled main into the shared folder (HEAD = 6d5b239), so `rig/` now matches main. The hair files are still byte-identical to main, so nothing was downloaded.

### Priority step: hairless-base areas for Base Body (done, 8:55 PM PT)
- Written to `hair/handoff_hairless/` (README, per-view PNGs, sheet, `work/build.py`):
  - rest mask (a);
  - sway envelope (b): the full preset-A/manual sway range plus HairSwayY, swept in fine steps and dilated 1 px for the renderer halo;
  - fully uncovered at the extremes (c), plus a `_partial` variant.
- Counts (rest / envelope / uncovered alpha 0 / of which inside rest):
  - apose 20020 / 33259 / 13296 / 1586
  - tpose 19551 / 32265 / 13590 / 2292
  - left 28682 / 35426 / 6313 / 999
  - right 29868 / 37045 / 6637 / 1026
  - back 31625 / 38767 / 6638 / 712
- Check: at 12 extreme poses per view, rendered with the current renderer, 0 hair px fall outside the envelope.
- BodyLean ±1 (the highest in the action clips) adds 0 px: the skin under the envelope moves exactly with the head matrix (largest gap 0.00 px), and the hair drive is clamped at ±1.

### Step 1: speck move (pixel list FINAL, 413 px)
- The six faint clusters that split off at sway were checked with the current renderer (`hair/staged/lineart_fix/work/r18.py`, which uses rig/index.html's own drawM, ss2, downsample and bleedRGB):
  - left strand_01: ~(576,151), ~(583,180), ~(586,193)/(579,193), ~(572,200);
  - back strand_04: ~(756,309);
  - back strand_05: ~(782–786,224–228).
- Every base.png px that connects them is **already in the staged strand** as an exact copy:
  - `hair/staged/speck_fix/work/connect_probe.py` found 0 base px within 3 px of any split piece that are outside the strand, apart from the left strand_01 root, where the px belong to hair_front/hair_back.
  - The staged strands differ from live only at the listed px, all exact base.png RGBA.
  - So the split is the 1 px faint stroke falling under the ink threshold after resampling. It even happens at s=0 posed (no rotation), and no base.png px is left to add.
- **The pixel list is FINAL and unchanged:** apose 58, tpose 54, left 68, right 23, back 210 = 413. `speck_px.json`, the ADD PNGs, the masks and the strands are byte-identical to before.
  - `work/verify_final.py`: manifest live sha256 still match, strands == live + listed px, masks == live OR ADD, ADD == json. ALL CONSISTENT.
  - apply.sh guard (base_body and base_body_skin alpha 0 at every speck px) kept.
- Simulation (`hair/staged/lineart_fix/work/mk_overlay.py` into /tmp/hairsim, body cleared at the speck px): rest_check is 0 px in all five views.

- Hairless areas re-measured at LINEAR display quality (9:10 PM PT). 0 hair px fall outside the envelope at all extremes, so this job **passes**.
  - Uncovered (alpha 0) / of which inside rest: apose 14987/1853, tpose 15181/2554, left 7790/1195, right 8314/1266, back 8094/1068.
  - The README and sheet are updated.

### Step 2: line art (9:28 PM PT): `hair/qa/lineart/r18/SUMMARY.md`
- Measured with the current renderer at LINEAR (`hair/staged/lineart_fix/work/r18.py` + `lineart_r18.py`), using rigid / 1 px line / 2 px line / static-part / s0 baselines.
- The 7 joints that failed before are no worse than baseline:
  - clean: apose 03_tip, apose 06_tip, tpose 03, right 02, right 02_tip;
  - resampling artifact (+1 piece, same as the rigid copy): left 03, and the tpose strand_02 part.
- New real defects at linear (new sharp corners only, no breaks):
  - apose strand_02: **fixed**, STAGED in `hair/staged/lineart_fix/views/apose/hair/rig.json` (pivot → 608.5,121.5);
  - apose strand_04, tpose strand_04, tpose strand_05, right strand_01: pivot moves did not clear them;
  - left strand_01 with the speck staging (+1/+2 pieces).
- Staged speck + lineart together: rest 0 px in all five views (body cleared at the speck px), and 0 new px over the eyes or mouth.

### Step 3: turn handoff (9:20 PM PT): `hair/qa/turn_handoff/SUMMARY.md`
- back f109 was mis-segmented on the LIVE side: hair_back's mass is duplicated on base_body. `measure.py` v2 fixes this; IoU 0.27 → 0.85.
- Offsets, whole / bun / fringe:
  - apose +1/−10, +1/−10, +1/−10, with the head also at −10 (head placement);
  - left −5/+3, +14/+1, −10/+9;
  - right +13/−2, −1/−6, +17/+1;
  - back +2/+4, −1/−4, no fringe.
- Only back (and the left whole-hair offset) is ≤6 px and hides in the ~80 ms crossfade.

### Job A: ear strands, A-pose (STAGED, 9:39 PM PT): `hair/staged/ear_strands/apose/README.md`
- 276 px copied unchanged from base.png. Crescents beside the outer eye corners go into static `hair_front`: L 90, R 151. Faint flyaways below the lobes go into `strand_03_tip` (3) and `strand_06_tip` (32), built on the speck_fix copies.
- The ear outline, the inner ear lines and the face/neck contour stay body.
- Pixel list for Body: `for_base_body/ear_strand_px.json`, `.png` and `_mask.png`. The 35 flyaway px must be alpha 0 in base_body and base_body_skin; the crescent px may be skin.
- Rest check with Body's delivery: 0 px in all 5 views. With today's base_body: apose has 35 px (the flyaways, drawn twice).
- Eyes/mouth at LINEAR, 129 poses: 0 new px.
- Body note: 14 flyaway px are painted over in hairless_apose.png and should be alpha 0.
- Other views were scanned only (not cut). tpose has the same crescents (~232 + 176 px). Candidates are in `work/other_views.json`.

### Job B: brow strand, A-pose (STAGED, 9:49 PM PT): `hair/staged/brow_strand/apose/README.md`
- This follows Eyes' change: only the strand px above (24) and below (11) the brow are cut into `strand_04`. Eyes keeps the 18 crossing px.
- A 6 px stub at y209–211 stays body. Cutting it would put the strand over the eye at HairSwayY +1.
- Gap at full sway, LINEAR: 0 px with rotation; 2 px at HairSwayY ±1. The lower end breaks from the static stub by up to 6 px at x = −1.
- `variant_above_only/` avoids the lower break.
- Eyes/mouth: 0 new px. Rest: 0 px in all 5 views (with speck_fix + ear_strands).
- Eyes should drop the 35 px from the lock (19 are in v1, 34 in v2).

### Job C: diagonal turn frames (STAGED, 10:04 PM PT): `hair/staged/diagonals/README.md`
- The four frames 045/135/225/315 (f033/f087/f131/f191) are cut in view space with the per-frame `view_fit`. Output: `<angle>/hair/*.png`, `rig.json` and `hair_mask_view.png`.
- Despill: blue-tinted hair px 1237/1286/1206/1177 (Body's metric) → 0. Key in loops: 56/52/80/44 px, all keyed to alpha 0.
- Bun layer is 101 at 045/315 and 650 at 135/225. Parts recompose the mapped frame hair exactly (0 px), with no overlap.
- Hidden or merged front strands are listed in the README.
- Softness after the scale-up is an AA band of 3.7–4.1 px per edge px, vs 1.0 in the drawn views; the frames are already 2.9–3.3 at source.
- Body must keep alpha 0 inside `hair_mask_view.png`, because hair_back and the bun sit under base_body.
- Not verified: sway holes and eyes/mouth. Neither has diagonal body or face parts yet.

### Job D: line art at the joints (STAGED, 10:34 PM PT): `hair/staged/lineart_fix/README.md` (Job D section)
- Caps and seam re-cuts (exact base.png / child px, no new paint) at apose strand_04, tpose strand_04/05, right strand_01/03 and left strand_01. All 6 are now **clean** at LINEAR. Every view has 0 REAL DEFECT joints, and only resampling artifacts remain in the parts.
- Width change is ≤0.49 px. Rest is 0 px in all 5 views (scratch overlay; rest_check copied, no output symlinks; live rig/views unchanged). Eyes/mouth: 0 new px.
- left strand_01: there is +1 ink piece at sway under the strict ≤60 ink threshold only (the faint 1 px stroke). It is 1 piece at ≤80.
- Conflict: apose strand_04.png is also changed by the brow_strand staging. The px are disjoint, but the files need merging if both are applied.
- Incident: an earlier `ear_strands/work/restsim.sh` symlinked live `rig/rest_diff_*.png` into its scratch tree, and my rest sims overwrote them (last at 9:48 PM PT). The parent fixed the script, and the live files are not modified per git.

### hair_front hole fills (STAGED, 11:20 PM PT): `hair/staged/hairfront_holes/README.md`
- Exact base.png px copied into the static hair_front at apose (604,129) and right (780,169). This closes the 2 real 1 px sway holes found in the hairless final set. Rest is 0 in all 5 views, 0 new see-through px, and 0 px touch the eye or mouth locks.
- Load order: apose goes after ear_strands (it replaces that hair_front entry); right is a new entry.

### Sway-over-hairless RERUN on own server 8780 (Oct 3, 1:00 AM PT): `hair/qa/sway_over_hairless_final/SUMMARY.md`
- Supersedes the port-8765 (tmpsv_tree) run, which is kept in `invalid_port8765/`. Every render used index.html db5cf270.
- Rest is 0 in all five views. NEW px are all strand trailing edges outside the static silhouette, with 0 real holes. The hairfront_holes fix closes both holes in every pose. A-pose eye corner: 223 px of flat skin (186,129,86), fully covered.

### T-pose eye-corner strand ink (STAGED, Oct 3): `hair/staged/ear_strands/tpose/README.md`
- The 68 px Eyes trimmed from the lock (L 39, R 29) go into the static hair_front, built on lineart_fix tpose. Pixel list and mask for Body are in `for_base_body/`.
- Rest is 0 with Body's tpose copies. With the live body it is unchanged (23 = the known speck double-composite).

### Hair sub-offsets vs eye-fit head group (Oct 3, 12:50 AM PT): `hair/qa/turn_handoff/subofs_eyefit/SUMMARY.md`
- apose: about 0. back: hair +1/0, bun -3/-15. left: hair -10/0, bun +14/-10. right: hair +13/-1, bun -4/-11.

### Not done
- Group posts (SendToAgent): this agent has no such tool, so the drafts are in the final report.

## Live and verified
- Hair parts live in `views/*/hair/`. Rest check (`rig/rest_check.py`) is 0 px in all five views, with no failing entries.
- Springs: preset A (4.0 Hz, damping 0.8) is the rig default, chosen by the user.
- Behind-the-ear skin fill: live. No white patches at full sway (`hair/qa/idle_battle/SUMMARY.md`).
- Tpose wisp fill: live in `views/tpose/hair/hair_back.png`. 320 px sit under the wisp above EyeR, hidden at rest. The wisp let the background through on 228/240 idle frames before and 0/240 after (`hair/qa/wisp_fix/SUMMARY.md`, with before and after crops in `crops/`).
- `hair/validate_hair.py` got two narrow rule changes for the fill: static hair above `hair_back` counts as covering it, and static fill under the face (layer < 400) is reported as `under_face_static_px`. Backups are in `hair/backups/wisp_fix_20260930/`.
- Keys: showcase `hair/showcase/hair_showcase.json`, actions `hair/actions/hair_actions.json` (jump, anger, run), and checker `hair/showcase/validate_hair_showcase.mjs`.
- Idle QA of the v1 renders passes, apart from the now-fixed wisp (`hair/qa/idle_battle/`). QA scripts accept `idle_arm_sway`.

## Unfinished (not live)
1. **Speck move** (`hair/staged/speck_fix/`). Stray hair pixels (413) left on `base_body.png` get moved into their strands as exact base.png copies, with a matching erase mask and a validator exception. See `SIMULATION.md` and `PIXELS.md`.
   - Blocked on Base Body clearing those pixels to alpha 0 in `base_body.png` and `base_body_skin.png`. The list is in `for_base_body/speck_px.json`.
   - The apply script only runs with `--apply` and backs up and restores on its own.
   - Open item: six faint speck clusters split off at sway (left and back). The decision was to cut them in together with the faint base.png pixels that connect them. That work was stopped before it started, so the staged set does NOT include it yet.
2. **Line-art check** (`hair/qa/lineart/SUMMARY.md`, crops included). Line width stays within 0.62 px and no strand comes apart. 7 live joints break a small piece of line or gain a sharp corner at half and full sway: apose strand_03_tip and strand_06_tip, tpose strand_03, left strand_03, right strand_02 and strand_02_tip, plus the tpose strand_02 part.
   - Next: measure the renderer's resampling baseline (the Coder has these joints in the renderer audit). Then fix whatever is left over by moving the pivots onto straight line runs with longer caps and re-cutting seams from base.png. Nothing is staged for this yet.
3. **Turn handoff hair offsets** (`hair/qa/turn_handoff/`, first pass, stopped before its summary). Offsets are frame minus live view, in view px, using Body's `angle_map.json` handoff fit.
   - apose f001: whole hair +1/−10, bun +1/−10, bun at layer 101.
   - left f062: whole hair −5/+3, bun +14/+1, fringe −10/+9, bun at 650.
   - right f160: whole hair +13/−2, bun −1/−6, fringe +17/+1, bun at 650.
   - back f109: bun −4/−6. The whole-hair numbers are NOT reliable (IoU 0.27, so the hair was probably mis-segmented).
   - Next: redo back f109 and write the overlays up. Most of this should hide in the ~80 ms crossfade. The profile fringe gaps (10–17 px) probably won't, and like the mouth gaps they look like head placement in the turn drawing.
4. **After v1.8 / v2 renders:** rerun `validate_hair.py` and `rest_check.py`. Check every tip's peak against its limit under A. Check the hair in the showcase, action and stress renders. Move the head offsets from BodyLean to HeadTilt/HeadNod once those controls exist.

## Push notes
Push all of `hair/` and `views/*/hair/`, including staged work, QA summaries, sheets, crops and data. Leave out only `__pycache__/` and `hair/qa/wisp_fix/render/` (245 MB of re-render frames and videos; the numbers are in its SUMMARY and data JSON).

## 2026-10-03 session (index 562c32a7; the hairless flag works)
- **T-pose eye-corner strands:** `staged/ear_strands/tpose/views/tpose/hair/hair_front.png` = 181 px (the original 68 + L 52 + R 61). Lock px: 0. Rest = 0, rechecked at 03:20 PT against Body's restored live_patch_staged. Browser PASS on 00892ccb.
- **Job 4 (kept ink → hair_front):** left 621 / right 640 / back 437 px. Body masks: skin vs alpha-0. Proposed flyaway px: right 3, back 67. Rest = 0. Sway: 0 diff. See `staged/ear_strands/<v>/for_base_body/`.
- **Job 5:** see `qa/colour_sweep/SUMMARY.md`; `staged/diagonals_v2/` (README) holds the snapped and eye-cut diagonals; qa_gates results are in `qa/qa_gates_runs/` (v2 = 0/0/0).
- **Job 6 widow's peak:** `qa/widows_peak/` (apose 53 px, tpose 42 px). Hair never covers it, so nothing needed restoring.
- **No-mirror:** `qa/no_mirror/REPORT.md` = PASS.
- **hgSub hair/bun v2:** `qa/turn_handoff/subofs_v2/REPORT.md`. Recommendation: (0,0) in all views until posed frames use a body without baked hair.
- Parked: Job 7 (benchmarks) and Job 8 (gold bun band).
