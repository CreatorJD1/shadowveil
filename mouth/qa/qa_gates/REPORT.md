# Mouth: rig/qa_gates.py results (Base Mouth, Sat Oct 3 2026, ~03:00 PT)

- rig/index.html md5 **562c32a7** (562c32a70c4fe5aeba6b278976b45c81). It was checked at the start and again at the end, and matched both times. qa_gates.py md5 6a5427ae. Every result below used 562c32a7.
- The tool is file-level only. It renders nothing, uses no server, and takes no URL flags, so `?hairless=1` was not involved. The room's hairless heads-up does not apply here.
- Commands used: `qa_gates.py --gate all --part mouth --staged-dir mouth/staged/tone_fix` (gates_all_tonefix.*) and `--gate leak` on all systems (gates_leak_allsystems.*). I also ran qa_gates' own palette functions read-only on `mouth/staged/mesh_bend`, because the tool's file sets don't include it (meshbend_px.*), and on `diagonals_snap` (diagonals_snap_gate.json).
- **Tool verdict: PASS.**

## Pass/fail per gate per view
| gate | apose | tpose | left | right | back | diag 045 | diag 315 |
|---|---|---|---|---|---|---|---|
| G1 weights | N/A (body only) | N/A | N/A | N/A | N/A | - | - |
| G3 scale | N/A (hands/feet only) | N/A | N/A | N/A | N/A | - | - |
| G2 leak, live | PASS 0/0 (10 files incl. anger) | PASS 0/0 (10 incl. anger) | PASS 0/0 (9) | PASS 0/0 (9) | no mouth files | - | - |
| G2 leak, staged tone_fix | PASS 0/0 | PASS 0/0 | PASS 0/0 | PASS 0/0 | - | - | - |
| G2 mesh_outside_mask | 0 (rigid drawImage, holds by construction) | 0 | 0 | 0 | - | - | - |
| G2 diagonals (staged, ours) | - | - | - | - | - | **FAIL 31 off-pal**, 0 chroma | **FAIL 34 off-pal**, 0 chroma |
| after diagonals_snap | - | - | - | - | - | PASS 0/0 | PASS 0/0 |
| mesh_bend (staged, ours; not in tool sets) | **179 off-pal** in renders, parts 0, chroma 0 | **249 off-pal** in renders, parts 0, chroma 0 | - | - | - | - | - |

Cells read off-palette/chroma at tol 2. Soft edges are counted for information and do not fail the gate: live 2582/2523/1785/1765 and diagonals 13067.

## Failures and owner
1. **Diagonal mouth renders: 65 off-palette px, 0 chroma. This is our staged work** (`mouth/staged/diagonals`, made by diag.py).
   - Per file, 045: o0.75_f-0.5 3, o0.75_f-1 1, o0.75_f0.5 2, o0.75_f0 1, o0.75_f1 2, o1_f-0.5 5, o1_f-1 4, o1_f0.5 5, o1_f0 4, o1_f1 4. Located at x 619-640, y 270-282.
   - Per file, 315: o0.75_f-0.5 1, o0.75_f-1 2, o0.75_f0.5 3, o0.75_f1 2, o1_f-0.5 4, o1_f-1 5, o1_f0.5 7, o1_f0 4, o1_f1 6. Located at x 731-749, y 275-286.
   - Each px with its RGB and nearest palette colour is in px_045.json / px_315.json. Distances run 2.24-4.12. They are bilinear-warp blends of two of her tones, found only in the open shapes (o0.75 and o1). The rest and o0-0.5 files have 0.
   - Cross-check: Coder's `baseline_leak.json` gives 65 for mouth, and Eyes' report says the same. My per-file counts are identical to the baseline file.
   - **Fix staged:** `mouth/staged/diagonals_snap/` (snap.py, snap_log.json). The 65 px are snapped to their nearest palette tone (max RGB change 3, alpha untouched). 19 files changed, and the other 31 are byte copies (the rest files included). Rerunning the gate gives **0 off-palette and 0 chroma**. Live files were not touched.
2. **mesh_bend preview renders: 179 off-palette px in apose and 249 in tpose, 0 chroma. This is our staged work.**
   - The 25 renders per view are affected, but the 5 parts per view are clean (0).
   - Rest o0_f0 is 0 in both views. The rest scale with opening: o1 has 18-27 per file. All of it is inside the mouth box (apose x 658-705, y 279-300; tpose x 665-703, y 269-293).
   - Locations and RGB are in meshbend_px.json. The cause is the same bilinear blending, dist ≤5.5.
   - Proposed fix (not applied): render mesh_bend with nearest sampling, or palette-snap the renders the way diagonals_snap does. Stage it only.
3. **Her original drawing: no failures.** For information only: with her own live files removed from the palette (a stricter check than the tool's), 213 px in 25 live files have no match in base.png or the expression sheet. By view: apose 74, tpose 42, left 80, right 17. Anger has 3 in apose and 2 in tpose. They are her drawn tones, so I left them as drawn.

## Eyes' fault (turn-frame blue background copied into parts): mouth count per file
- **Visible px: 0 in every file.** I checked 102 files: 50 diagonal renders, 50 diagonals_snap renders, and the 2 diag_*_rest_lips cuts.
- The test used was α>0 with B > max(R,G)+20, which is looser than the chroma rule. It found 0 bluish px and 0 chroma.
- Hidden only: `diag_045_rest_lips.png` keeps the frame's RGB, blue key included, under α=0 (1,759,044 bluish px). `diag_315_rest_lips.png` does the same (1,757,206).
  - Those px are invisible. The files are intermediates the rig does not load, so the blue can't reach the screen.
  - I staged clean copies anyway in `diagonals_snap/diag_*_rest_lips.png`, with RGB zeroed under α=0. Visible px and alpha are unchanged.
- Details are in diag_crosscheck_blue.json.

## Flags / turn / handoffs
- qa_gates has no `&mouthfix=1` or `&headgroup=1` mode.
- The rendered checks of those flags are in `mouth/qa/mouthfix_verify/REPORT.md`: 0 blue spill, 1 px lines, rest 0 px, and the handoffs f001/f062/f160. They ran on rig 00892ccb. The 562c32a7 change (`?armsub=1`, off by default) touches no mouth code.
- Coverage: the full turn is covered by the 045/315 diagonals, and every shape in all 4 mouth views was checked, anger included.

Files: summary.json, gates_all_tonefix.{json,txt}, gates_leak_allsystems.{json,txt}, px_045/315.json, meshbend_px.{py,json}, meshbend_and_strict.json, diagonals_snap_gate.json, diag_crosscheck_blue.json, list_px.py.
