# Mouth fix (`?mouthfix=1`) and head-group `sub.mouth` verification

Base Mouth, Sat Oct 3 2026, 00:41 to 02:4x PT. This was measurement only. Nothing in `rig/`, `views/` or another team's folder was written, and git was not used. The only folder written was `mouth/qa/mouthfix_verify/`.

## Setup
- **Server.**
  - At first: my own `python3 -m http.server 8785`, PID 989330, 00:41 to 01:30 PT.
  - When the user asked, I moved to **8786** (PID 1113609). I also killed the user's stray 8785 server (PID 1119888), with permission.
  - PIDs are logged in `my_pids.txt`. Every Chrome I started was closed or killed by me. Hung page loads were killed and rerun, and each kill is logged with its reason.
- **Rig md5.** Before every page load, served `rig/index.html` was checked against the on-disk file (`rig_md5_checks.log`). It matched on every load. The rig changed twice during the run:
  - db5cf270 → **0ce6fecc** at 01:05:47 PT. This added hair/bun `HG.sub`, which is only active with `?headgroup=1`.
  - 0ce6fecc → **00892ccb** at 02:01:29 PT. This added `?handorder=1`, which needs `?hairless=1`.
  - 00892ccb → **562c32a7** at 02:38:30 PT, after my last render. This added `?armsub=1`, which is off by default (`armSub` returns 0 without the flag). I did **not** re-render on 562c32a7. A copy is kept as `rig_562c32a7_copy.html`.
  - The diffs touch no mouth code. Copies of all three versions are kept here as `rig_*_copy.html`.
- **Which md5 each result used** (also in `summary.json` → `provenance`):
  - db5cf270: the harness runs fix/off apose and tpose, off_left, off_right and fix_left; the linear anger clips for apose and tpose.
  - 0ce6fecc: the harness run fix_right; fix2_apose (**1120/1120 crops byte-identical** to the db5 fix_apose run); the linear anger clips for left and right; the ss2 anger clip for apose.
  - **00892ccb (current until 02:38 PT):**
    - all full-frame captures (live, fix, hg, hgfix in 4 views)
    - the tie checks
    - the head-group rest path, placement and turn-frame residuals
    - fix3_apose: the full harness run, **1120/1120 crops byte-identical** to the db5 fix_apose run
  - The head-group captures were started on 0ce6fecc but spanned the 02:01 change, so I redid all of them on 00892ccb. The 0ce6 set is kept in `caps_0ce6/`, and the db5 set in `caps_db5/`.
- **`?hairless=1` was not used in any result here.** So the room's heads-up about hairless not loading on 00892ccb does not affect anything in this report.
- **Method.** The scripts are copies of `rerun_shadowveil` / `render_v2` (harness.mjs, analyze*, talk_aligned, job2, anger_clip, capture), pointed at my port, with `&quality=linear`.
  - Doubled-outline frames were re-detected on every shape switch from pixels alone, independent of the rig's own fade flag. Run with the flag off, the same detector reproduces the old counts exactly: 38/38, 31/38 and 13/17.

## Results (flag = `?mouthfix=1&quality=linear`)
| check | result |
|---|---|
| Doubled outline | **PASS: 0.** <br>• Talk with body frozen: apose 0/36, tpose 0/36, left 0/36, right 0/36 (default: 38/38, 31/38, 36/38, 36/38). <br>• Timed sweep: 0/17 apose and tpose, 0/15 profiles (default 13/17, 6/15). <br>• Fade step-through: 0/294 and 0/210 (default 130–137/294). <br>• Every switch frame is pixel-exact to the incoming shape (36/36). The detector flagged 4 OH_half→AA_half frames in apose, but those frames are pixel-exact AA_half, so this is a false positive. |
| Sharp/soft flicker (8 s talk with body life) | **PASS: 0 toggles** in all 4 views (default: 4 in apose/tpose/right, 7 in left). Max frame-to-frame step 0.026–0.037. |
| Rest wins exact ties | **PASS.** Tie points (0,−0.5), (0,0.5) and (0.25,0) give rest in all 4 views, with and without headgroup (default: M / smile / AA_half). Checked on 00892ccb. |
| Anger first frame (clip f9, 0.300 s) | **PASS.** <br>• Linear: alpha_in **1.000** (resid 0.13); the rest line is at 0 visibility (old: 0.253, with rest at 0.72). <br>• ss2 (page default): **0.988** (resid 4.21 from ss2 resampling). This matches Coder's ~0.988. <br>• Step-through at el=0 and the 30 fps switch frame: 0 px vs base+anger. <br>• left/right clip shows **M** from f9 to f89, confirmed: there is no anger shape there, and talk was never on. |
| Rest 0 px vs base.png, flag on and off | **PASS.** <br>• Rest path `render(g,true)`: 0 px full frame in all 4 views, with the flag on and off, and with `&headgroup=1` (before a handoff, at w=0 and after reset). <br>• Posed default in the mouth region: apose/tpose 0 px. Profiles show 15 / 11 px, at most 2 levels on semi-transparent silhouette edge pixels. This is identical with the flag off, so it predates the fix. <br>• Static settled captures, flag on vs off: 0 px in all 24 (4 views × shapes, plus the rest path). |
| Shape sweep | **PASS** for apose/tpose: 33/33 picks match the nearest-shape rule, 0 px vs the authored composite. <br>Profiles: picks match, but the frames are 15–31 px off the authored composite. The sweep crops are **byte-identical with the flag off (33/33)**, so this predates the fix (premultiplied mismatches up to 60 levels at the lip/silhouette edge). |
| 1 px lines | **PASS.** All 9 grid shapes have p90 = 1.0 px = rest (Δ0) in apose/tpose; talk frames are 1.0. Anger stays at 3 px (+2), which was already known. |
| Blue | **PASS: 0** key-like blue pixels in every frame of every test. Talk frames contain 3–5 (apose) and 19–32 (profiles) dark navy hair pixels, which are byte-for-byte the same with the flag off and the same as the old run. |
| Talk picks | **Same shape set.** Picks are rest/AA_half/OH_half/M/AA only, and anger is never picked. <br>**Note:** 18/240 frames change from M to rest (M 22→4, rest 127→145, switches 38→36) in every view. The talk driver's M press lands exactly on the (0,−0.5) rest/M tie, so with rest-wins-ties most talk M closures disappear. This needs a decision: either the driver uses form < −0.5, or accept it. |
| Tilt/nod ±2° (41 steps of 0.1°) | **PASS.** <br>• The lip-seam anchor is always on whole pixels. The largest jump between adjacent frames is **1 px**, and the unsnapped motion is 0.14 px per step. <br>• The largest deviation from the unsnapped position is **0.50 px** (all views). <br>• Pixel registration, flag on vs off: the measured shift is at most 0.55 px and agrees with the logged snap to within 0.22–0.33 px. <br>• Face outside the mouth: 0 px change. <br>• So there is no drift or stair-step above 1 px. The 1 px snap steps are inherent to whole-pixel snapping. HeadTilt does not move the mouth in the profiles, so only HeadNod applies there. |
| Default output unchanged | **PASS.** <br>• Flag-off harness crops: **956/956 byte-identical** to the old baseline (apose and tpose). <br>• Flag-off full-frame captures (4 views, 24 files): byte-identical to the old ad2e7083 captures, on both 0ce6 and **00892ccb**. |
| `&headgroup=1` sub.mouth | **PASS.** <br>• The staged values are (0,0), (+6,+1), (−5,0) for apose / left / right. <br>• The rendered mouth layer moves by exactly group + sub: (0,−9), (6,12), (−2,5), with 0.0 mean diff. At w=0.5 it moves by half; at w=0 / reset it is 0 px vs flag off. |
| Handoff residual vs turn frame | **PASS by seam chamfer**, which I take as the primary metric: apose f001 (0,0), left f062 (**−1,0**), right f160 (0,0). This was (0,0) / (+6,+1) / (−5,0) before the sub. <br>The secondary metrics are biased by the thinner, foreshortened video lips: seam centroid (−0.3,−0.1) / (−2.1,−0.4) / (−1.3,+0.6); lip outline chamfer (0,0) / (+4,0) / (−7,+1). <br>`?mouthfix=1&headgroup=1` gives identical numbers. With mouthfix, the mouth at w=0.5 is whole-pixel exact (0.0 diff); without it, it is half-pixel resampled (diff 12.4). |

## Notes and open items
1. **Talk M presses become rest at the exact tie** (see the Talk picks row). This needs a decision.
2. **While a handoff is active (w=1), the rest path itself moves.** `headApply` applies the head group in the rest path too: 44k px in apose and 52k in profiles, 1.2–2.2k of them in the mouth box. `sub.mouth` is posed-only, so on the rest path the mouth carries the group offset but not the sub. The driver should only use posed frames during a handoff. Rest is 0 px once w=0.
3. The profile posed-path mouth-region differences (sweep 15–31 px, rest 11–15 px) are not caused by the fix; they are identical with the flag off.
4. The rig's own `crossfadeMs: 60` in `rig.json` is unused when the flag is on, because the fix forces a hard cut.

## Files
- `summary.json`: all numbers plus md5 provenance.
- `sheet.png`, four rows:
  - an apose talk switch, default (doubled) next to mouthfix
  - anger f9, old ss2 next to mouthfix
  - the mouthfix tilt at −2/−1/0/+1/+2°
  - the head-group mouth next to the turn frame (apose / left / right)
- `runs/` holds the harness crops and meta, `final_*`, `fix_extra_*`, `talk_aligned_*` and `tilt_*`. `caps/` holds the 00892ccb captures. Also `anger/`, `job2_hg*_results.json`, `hg_mouth_placement.json`, `hg_rest_results.json`, `default_vs_old_caps.json`, `crop_identity_vs_old.json` and `caps_flag_compare.json`.
- `scripts/` holds copies of the scripts, plus `fix_extra.py`, `tilt_px.py`, `tilt_reg.py`, `hg_place.py`, `hg_rest.js`, `cap.js`, `mksheet.py` and `build_summary.py`.
