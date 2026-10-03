# Mouth QA re-run on my own Shadowveil server (not 8765)

Base Mouth, Fri Oct 2 2026, 23:34 to 00:05 PT. This was measurement only. Nothing under `rig/`, `views/`, or another team's folder was written, and git was not used.
- **Server.** `python3 -m http.server 8785 --bind 127.0.0.1 --directory /workspace/shadowveil` (PID 874111), stopped at about 00:04 PT.
  - I first started a server on 8809 (PID 860707). I stopped it at 23:39 PT when the port rule changed, and no data from it was used. The renders that had started against it were killed and rerun.
  - 8797 was already taken by another process (PID 854533). I did not touch it.
- **Rig version check.** Before every page load, the copied scripts checked that the served `rig/index.html` was byte-identical to `/workspace/shadowveil/rig/index.html`. It matched on every load (md5 `ad2e7083…`, the 23:36 PT version, which includes the staged `?mouthfix=1` code, off by default). Log: `rig_md5_checks.log`.
- **Process hygiene.** The Chrome PIDs I started are in `render_v2/work/my_pids.txt` and `hairless_headgroup/caps/chrome_pid*.txt`. All of them have exited, and no other process was touched.

## Job 1: which old checks were rendered through 8765
| old result | how it was rendered | status |
|---|---|---|
| `mouth/qa/hairless_headgroup/` (caps/meta.json, scripts/capture.js, verify_hl.js → job1/job2 results) | **http://127.0.0.1:8765/rig/** (11 URLs in caps/meta.json) | **suspect → rerun** |
| `mouth/qa/render_v2/` live render QA (work/run_*/meta.json, final_*.json) | my own `serve.py` on **8781**: a scratch copy of `rig/` (md5 `17167b7d…`, 22:39 PT version) plus the rest read from /workspace/shadowveil | not 8765. I reran it anyway because `rig/index.html` has changed twice since then |
| render_v2 anger-clip check (`anger_clip_results.json`) | pixel-only, from files `rig/previews/actions/v1/work/*` | still valid, not rerun |
| render_v2 `mouthPick` tie | code reading only | rechecked in the current code (see below) |
| `mouth/staged/mesh_bend/iterations.json` | numpy only, no browser | still valid |

## Job 2: re-run results (old → new)
### render_v2
Same `harness.mjs`, `--port=8785 --quality=linear --fade=35`, with the same boxes. The current live `rig/index.html` was served directly.
- **Raw crops: 956/956 (apose) and 956/956 (tpose) are byte-identical to the old run.** `run_*/meta.json` is identical.
- `final_{apose,tpose}.json` and `talk_aligned.json` are byte-identical. `summary.json` is semantically identical; only the key order differs.
- So every number is **unchanged**:
  - Rest: 0 px vs base.png (rest path). The posed default frame is 0 px in the mouth region, and the full frame is 419 / 2474 px, all outside the mouth.
  - Sweep: exact, 0 px vs the authored composite, with 0 nearest-rule mismatches.
  - Line width: p90 1 px = rest for all 9 grid shapes; anger is 3 px (+2).
  - Blue spill: 0.
  - Talk picks: rest/AA_half/OH_half/M/AA only.
  - Crossfade: every pair doubled from 0 to 17.5–30 ms. At 30 fps there is one doubled frame per switch: 38/38 apose and 31/38 tpose talk-frozen, 13/17 timed sweep.
  - Sharp/soft flicker at rotation 0: 4 toggles per 8 s, at t = 2.300 / 6.900 s.
  - Fade alphas match the code (aIn = 0.25 + el/35; aOut held at 1 until 17.5 ms).
- `mouthPick` tie, in the current code (rig/index.html:347): the default is unchanged, so rest still *loses* exact ties (`rest?1:0`). Only `?mouthfix=1` flips it so rest wins.
- Anger clip timing/position: these were file-based, so they stay as reported (f9 = 0.300 s set-in, Δ 0.03 px, f9 doubled).

### hairless / head group
Same `capture.js`, `verify_hl.js`, `job1.py` and `job2.py`, pointed at 8785. Flags: `?quality=linear&mouthfade=0[&hairless=1|&headgroup=1]`.
- **Hairless (job1): all 272 numbers are identical to the 8765 run.**
  - Rest vs base.png in the lock: apose 0/2407, tpose 0/2373, left 55*/1512, right 46*/1466. The starred profile counts are premultiply-equivalent edge pixels with 0 premultiplied mismatches, the same as before.
  - Hairless ≠ live: **0 px** in the 6 px-dilated mouth region, in all 4 views and all shapes. Bright key colour: 0.
  - verify_hl: the staged hairless `live_patch_staged/base_body(_skin).png`, the staged hair and the apose palms loaded; `missing` = [].
- **Head group with the old offsets** (apose (0,−10), left (−2,+1), right (+5,−6), applied in-page with `RigHeadGroup.set`): **all job2 numbers are identical to the 8765 run.**
  - apose f001 (0,+1); left seam (+8,+11); right seam (−7,+11).
- **Head group with the new eye-fit offsets.** These were staged in `rig/partmesh/staged/headgroup.json` at 23:39:57 PT: apose (0,−9), left (0,+11), back (+2,+11), right (+3,+5).
  - I rendered with `&headgroup=1` reading that file, and again with `RigHeadGroup.set()` from my copy (`hairless_headgroup/headgroup_new_offsets.json`, byte copy `headgroup_staged_2339_copy.json`). The two renders are pixel-identical (0 px).
  - The **mouth-only residual on top of the new head group** is the turn frame minus the rig, in canvas px with +y down:

| handoff | seam chamfer | lip-outline chamfer | lip centroid | seam centroid | front / back seam corner | lower face (lips masked) NCC / silhouette chamfer | eyes NCC (low conf.) |
|---|---|---|---|---|---|---|---|
| apose f001 | **(0,0)** | (0,0) | (+0.2,+0.1) | (−0.3,−0.1) | (0,0) / (+1,0) | (0,0) / (+1,0) | (0,0) |
| left f062 | **(+6,+1)** | (+7,+1) | (+7.3,+1.2) | (+4.6,+0.5) | (+5.3,−2.5) / (+2,0) | (+4,−1) / (+6,−1) | (−1,0) |
| right f160 | **(−5,0)** | (−9,+1) | (−9.9,+1.2) | (−6.3,+0.6) | (−6.8,−1.3) / (−5,−1) | (−4,0) / (−8,−1) | (+3,+2) |

- **Mouth's own dx,dy:**
  - apose (0,0).
  - left about **(+5..+7, +1)**, i.e. toward the face front.
  - right about **(−5..−7, 0..+1)**.
  - The vertical error is gone (it was +11). What remains is sideways, as expected.
- The lower face (nose/chin) shifts in the same direction but by less: (+4..+6,−1) and (−4..−8,0..−1). Relative to the face, the mouth is about (+1..+2, +2) left and (−1..0, 0..+1) right.
- The lip-centroid and outline numbers are biased by about 2–4 px in x by the thinner, foreshortened video lips (16 vs 23 px wide). I take the seam chamfer and seam centroid as the best mouth estimate.

## Job 3: Body's staged hairless bases vs views/<v>/base.png inside the mouth lock
Script: `body_lock/lockcheck.py`, results in `body_lock/lock_results.json` (checked at 23:37 PT). Comparisons are exact RGBA and also premultiplied.

| file (body_tools/work/hairless_division_staged/…) | mtime PT | in-lock px changed vs base.png |
|---|---|---|
| tpose/hairless_tpose.png | 23:19 | **0 / 2373** |
| tpose/live_patch_staged/base_body.png | 23:19 | **0 / 2373** |
| tpose/live_patch_staged/base_body_skin.png | 23:19 | **0 / 2373** |
| apose/hairless_apose.png (re-toned) | 23:19 | **0 / 2407** |
| apose/live_patch_staged/base_body.png (re-toned) | 23:19 | **0 / 2407** |
| apose/live_patch_staged/base_body_skin.png (re-toned) | 23:19 | **0 / 2407** |

- These files are also 0 in the lock against `views/<v>/base_body.png` and against `base_body_skin.png`.
- Re-tone check inside the lock:
  - tpose: 13 px of (186,129,85) remain, the same 13 that base.png has (her art, kept); 29 px are (186,129,86).
  - apose: 0 px of 85; 31 px of 86, identical to base.png.
- Outside the lock, the live patch differs from the live `base_body` by 54 px (tpose) and 334 px (apose), as Body reported.
- In both views the two `live_patch_staged` copies are byte-identical to each other (same md5).

## Status registration / check
- Registered with `python3 status/update.py register mouth reports mouth/qa/rerun_shadowveil/REPORT.md '<label>'`.
- `update.py check` defaults to 8765, so I ran `python3 status/update.py check http://127.0.0.1:8785/` against a briefly restarted 8785 server. Result: **checked 352 paths, 0 broken** (`status_check_8785.txt`). That server was stopped afterwards.

## Files
- `render_v2/work/` holds the copied harness and analysis scripts, `run_{apose,tpose}/`, `final_*.json`, `summary.json` and `talk_aligned.json`.
- `hairless_headgroup/` holds `scripts/` (copies pointed at 8785, plus `capture_hgnew.js`), `caps/` with meta.json and meta_hgnew/hgold.json, `job1_results.json`, `job2_results.json` (staged file, new offsets), `job2_newhg_results.json`, `job2_oldhg_results.json`, and the offset copies.
- `body_lock/` holds `lockcheck.py` and `lock_results.json`.
- `rig_md5_checks.log`, `rigcheck.sh` and `my_pids.txt` are in the top folder.
