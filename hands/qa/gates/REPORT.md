# Hand parts through rig/qa_gates.py: live + staged F5 v2, F7, F10, F11, F8 (2026-10-03, ~03:00 PT)

## How this was run
- rig/index.html md5 = **562c32a7** (checked before the runs).
- qa_gates.py (md5 6a5427ae) is file-only: it opens no port and changes nothing.
- The renders behind the scale numbers came from my own server on 8779, with an md5 check before each one.
- Command, once per set: `PYTHONDONTWRITEBYTECODE=1 python3 rig/qa_gates.py --gate leak,scale --part hands --staged-dir <set> --json hands/qa/gates/runs/<set>.json`.
- **Layout workaround:** F7 and F10 keep their palms without a `<view>/` subdir, which staged_lookup cannot find. So `--staged-dir` pointed at a scratch symlink tree, `/workspace/scratch/gates/{f7/apose,f10/tpose}/hands/*_palm.png`, that links to the unchanged staged files. `runs/*.json` confirms every staged file was really swapped in: F5 v2 8 files, F7 2, F10 2, F11 4.
- **What qa_gates does not reach:** F8 diagonals and the hand-mesh weights. These were run through `gates_extra.py`, which imports qa_gates unchanged and uses its own `file_report` and palette, plus the G1 bleed rule.
- **Scope:**
  - The held hairless F10/F11 results are released and included.
  - The 53/24 px wrist-line overlap under `?handorder=1&hairless=1` is Body's forearm skin, which Body is trimming. It is not counted or changed here.

## Per-gate counts
| set | files | G2 chroma | G2 off-palette | G2 soft edge (info) | G1 weight bleed | G3 scale (1 px gate) |
|---|---|---|---|---|---|---|
| live hand parts (5 views) | 488 | **0** | **0** | 22362 | n/a (rigid parts) | base views = truth (info only) |
| live rig/hand_angles sprites | 8 (qa_gates covered 6; 45_L/R added by me) | **0** | **0** | 0 | **74 / 17191 verts** (135_L 3, 135_R 17, 225_L 19, 225_R 0, 315_L 11, 315_R 14, 45_L 4, 45_R 6) | **8/8 flagged**, −11.9/−12.0 (see hand_angles_note: mostly definition) |
| F5 v2 (v2_ring_width) | 8 | **0** | **0** | 22299 total (−63 vs live) | n/a | **PASS**: Ring1 +0.45 / +0.90 (v1 was +1.34 / +2.24) |
| F7 apose palms | 2 | **0** | **0** | 89 + 89 | n/a | **PASS**, Δ 0 |
| F10 tpose palms (hairless+handorder) | 2 | **0** | **0** | 292 + 293 | n/a | **PASS**, Δ 0 (real rig render) |
| F11 left/right/back palms (hairless+handorder) | 4 | **0** | **0** | 0 / 0 / 268 / 263 | n/a | **PASS**, Δ ≤ 0.5 (real rig). If drawn OVER the forearm (default order): left +2.6, right +9.7 FAIL |
| F8 diagonals (staged) | 68 | **0** | **0** | 11597 | n/a (rigid, no mesh) | 45L/45R/135R/315R **PASS**; 135L 2.0, 225L 1.5, 225R 1.5, 315L 1.5 **FAIL** (palm/finger split or palm width; hand length ≤ 0.83 everywhere) |

## Notes
- **qa_gates exits 1 for every hand run.** The only cause is G3 flagging the 8 live hand_angles sprites. All the staged leak checks pass, with 0 chroma and 0 off-palette.
- **Two qa_gates issues for Coder.** I did not edit the script.
  1. The diagonal glob uses `DIAG_FRAME` keys `'045'`, so `rig/hand_angles/45_*.png` is never checked. I checked them separately and they came out at 0 / 0.
  2. `staged_lookup` misses flat staged layouts like F7 and F10.
- **G1 weight bleed is reported only for the turned-hand meshes.** It is my own G1-equivalent rule (weight > 0.001 on a bone that is not the vertex's dominant bone, its parent, child or sibling), applied to the hand meshes because qa_gates G1 covers only body skin.json. The 74 vertices are information and need Coder's review; it is not an official gate result. All the staged hand parts are rigid PNG parts with no weights.
- The G3 scale numbers for staged parts come from hands/qa/scale_audit, because qa_gates' G3 measures only base views and hand_angles.
- Raw output: `runs/{live,f5v2,f5v1,f7,f10,f11}.{json,txt}` and `runs/extra.{json,txt}`.
