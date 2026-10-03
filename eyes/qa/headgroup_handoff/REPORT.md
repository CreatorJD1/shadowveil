# Eye handoff offsets with the staged head group — shadowveil-rooted rerun (Base Eyes, Fri Oct 2 2026, ~11:40 PM PT)

Supersedes the earlier run (moved to `invalid_tmpsv_tree/`), whose captures came from port 8765 serving `/workspace/tmpsv_tree`.

Server: own scratch `python3 -m http.server 8781 --bind 127.0.0.1`, root `/workspace/shadowveil` (cwd checked), stopped after capture.
Served `rig/index.html` sha256 a27a1a7a…986ad = `/workspace/shadowveil/rig/index.html` (tmpsv_tree's is c67aa65c…, different).
Capture: one headless Chrome, `?view=<v>&quality=linear[&headgroup=1]`, `RigHeadGroup.applyHandoff(view)`, `RigManual()`, all params default, `draw()`, FR canvas (`caps/`, `caps/meta.json`). No page errors.
Residual = turn frame (warped with Body `angle_map.json` handoff) minus rig render with head group on, view px (+x right, +y down).

| eye | head offset | iris | lash band | lash chamfer | NCC | best (mean iris, band, NCC) | Mouth face residual | eye − mouth |
|---|---|---|---|---|---|---|---|---|
| f001 apose EyeR (amber 400-403) | (0,-10) | (+1.2,-0.1) | (-0.1,+0.8) | (+1,+1) | (0,+1) | **(+0.4,+0.6)** | (0,+1) | (+0.4,-0.4) |
| f001 apose EyeL (green 410-413) | (0,-10) | (+0.3,+1.0) | (+0.5,+0.6) | (-1,+1) | (0,+1) | **(+0.3,+0.8)** | (0,+1) | (+0.3,-0.2) |
| f062 left EyeL (green) | (-2,+1) | (+3.9,+9.9) | (-0.1,+10.2) | (+7,+9) | (+1,+10) | **(+1.6,+10.0)** | (+8,+11) | (-6.4,-1.0) |
| f160 right EyeR (amber) | (+5,-6) | (-4.0,+10.5) | (-0.9,+11.7) | (-1,+12) | (0,+12) | **(-1.7,+11.4)** | (-7,+11) | (+5.3,+0.4) |

Eye totals vs live (head offset + residual): f001 (0,-9), f062 (0,+11), f160 (+3,+5).

## Verdict vs Mouth
- f001: AGREE (within 1 px).
- Profiles, dy: AGREE with Mouth's whole-face residual (+10 vs +11, +11.4 vs +11).
- Profiles, dx: DISAGREE by 5-6 px. The eyes sit ~0-2 px back; mouth/nose/chin sit 7-8 px back. Profile face in the video is foreshortened, not rigidly shifted.
- Against Mouth's face-fit head offsets (left (+6,+11), right (-3,+5)), which are totals vs live: eye totals are left (0,+11) → dx off by 6, dy agrees; right (+3,+5) → dy agrees, dx off by 6.

## Same as the invalid run
Every capture PNG is pixel-identical to the tmpsv_tree captures (0 differing px in all 6). So `work/measure_raw.json` is byte-identical and all numbers match the old run. tmpsv_tree differs from shadowveil in rig/index.html and some hair/body PNGs (e.g. apose hair_front 241 px, base_body 334 px). None of that changed the FR render at rest in these 3 views (the hair-loading paths in index.html come from the HAIRLESS/staged maps). Both index.html files were modified at 23:27-23:28 PT, after the old captures (23:15-23:16).

Caveats (unchanged): the profile frame eyes are 22-27 px wide and soft (±1-2 px). A hair strand crosses the right frame eye (~1 px x bias in the lash band). The amber colour-only centroid and the pupil dark core were rejected (kept in report.json `rejected`).
