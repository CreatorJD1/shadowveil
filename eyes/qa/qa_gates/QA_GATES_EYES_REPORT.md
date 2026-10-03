# QA gates on eye parts (Base Eyes, Sat Oct 3 2026, PT)

These checks only read files. Writes went only to eyes/qa/qa_gates/.

## Commands run
- `PYTHONDONTWRITEBYTECODE=1 python3 rig/qa_gates.py --gate all --part eyes --staged-dir eyes/work/lashfix/staged --json eyes/qa/qa_gates/qa_gates_eyes_all.json`. Exit code 0, PASS=True.
- `python3 eyes/qa/qa_gates/eyes_diag_leak_supplement.py` writes `eyes_diag_leak_supplement.json`. It uses qa_gates' own palette and leak functions on the staged diagonal eyes, because qa_gates' `diag_sets` covers hair, mouth and hands only.

## Results
| check | set | files | off_palette | chroma | soft_edge (info) | verdict |
|---|---|---|---|---|---|---|
| G3 hand/foot scale | eyes | - | - | - | - | n/a: the gate does not apply to eyes and was not run for --part eyes |
| G1 weight bleed | eyes | - | - | - | - | n/a: eyes are rigid drawImage parts, not in skin.json, so the gate was not run for --part eyes |
| G2 live | apose/tpose/left/right (back has no eyes) | 66 | 0 | 0 | 3530 | PASS (0 by construction for live files) |
| G2 staged (lashfix: lid_1..7 swapped, 42 files) | same views | 66 | 0 | 0 | 341 | **PASS** |
| G2 mesh_outside_mask ("colour leak in rotation") | eyes | - | - | - | - | total 0. n/a by construction: rigid parts drawn under one matrix |
| G2 diagonals (qa_gates) | eyes | **0** | - | - | - | not covered: the tool has no eye diagonals |
| G2 staged diagonal eyes (supplement) | 045 + 315 | 44 | 0 | **167** | 0 | **FAIL on chroma (eyes' own)** |
| G2 composited diagonal eyes, 9 gaze x 8 lids x {current, diag} | 045 + 315 | 288 renders | 0 | eye px: 82/85 at k0, 34/40 at k1-7 | - | the same chroma px. The raw totals in the JSON (22536 / 29520) also count the frame's blue background inside the crop, so ignore them |

### Chroma failure details (staged diagonal eyes; these are the eyes' own px)
- 045 EyeR (far eye, amber):
  - `EyeR_lash.png`: 34 px at x 326-331, y 168-178.
  - `EyeR_lid_0.png`: 48 px at x 326-331, y 179-186.
  - Colours range from (7,0,127) to (0,0,250).
- 315 EyeL (far eye, green):
  - `EyeL_lash.png`: 40 px at x 434-438, y 165-178.
  - `EyeL_lid_0.png`: 45 px at x 432-438, y 179-186.
  - Colours range from (21,13,166) to (0,0,192).
- All 167 px are identical to the turn frame (f033 / f191). They are the frame's blue key background at the silhouette edge, cut into the far eye's lash and lid_0. They are not off-palette, because the frame is in the palette. lid_1..7 carry none.
- The diagonal rest check on the frame stays 0 px, because the frame shows the same blue underneath. Composited on anything else, they would show as key spill. They also blink away on k>=1, because only lid_0 has them.

## Coder's baseline diagonal leak: 209 off-palette px and 1 chroma px (`rig/work/qa_gates/out/baseline_leak.json`)
- I recounted them independently and got the same totals.
- By system:
  - hair: **144** off-palette and **1** chroma (315 strand_04).
  - mouth: **65** off-palette.
  - hands: 0.
  - So the mix is mostly hair, not mostly mouth.
- No eye file is in that set, so 0 px come from eye files.
- I mapped each px from view space to frame space with each eye rig's viewFit. **11 off-palette hair px land on eye parts.** The test used white ∪ iris (±4 px shift) ∪ lid_0..7 ∪ lash, dilated by 1 px. The chroma px does not land on an eye part.
  - 045, over EyeR (far eye, amber):
    - `hair_front.png`, view (590,203) rgb(23,2,19); (591,205) rgb(38,25,60); (591,206) rgb(37,26,58).
    - `strand_03_tip.png`, view (593,207) rgb(54,47,71); (594,207) rgb(49,43,67); (597,221) rgb(49,35,52); (598,221) rgb(72,56,75).
    - In frame space these are about x 328-333, y 167-179.
  - 315, over EyeL (far eye, green):
    - `strand_06.png`, view (760,216) rgb(3,14,7); (763,217) rgb(29,62,36); (764,217) rgb(23,53,30); (757,219) rgb(4,46,7).
    - In frame space these are about x 422-427, y 174-176.
    - These are green, iris-like tones inside a hair strand.
- These 11 px are in hair files (Hair's). They overlap the eyes' area, but they are not eye-part px. Nothing was fixed.

## Update: chroma fix on the staged diagonal far-eye files (Base Eyes, Sat Oct 3 2026, ~3:10 AM PT)
- **Files changed:**
  - `eyes/staged/diagonals/045/EyeR_{lash,lid_0}.png` and `315/EyeL_{lash,lid_0}.png`
  - their `_chroma.png` files, regenerated exactly as before: part RGB where α>0, (0,0,255) elsewhere
- **Originals** are in `eyes/staged/diagonals/backups_chroma_fix/{045,315}/`. To revert, copy them back.
- **Script:** `fix_diag_chroma.py`, log in `fix_diag_chroma.json`. For each px it records the original colour, t_blue, the palette tone it was unmixed to, and the action taken.
- **Rule:**
  - Each px is unmixed against the frame's local key blue, using qa_gates' palette for the angle with bluish tones removed. This gives a blue fraction t and a palette tone P.
  - t ≥ 0.9, or 0.5 < t < 0.9 (mostly blue): made fully transparent.
  - t ≤ 0.5: set to P, at α 255.
  - Exception (connectivity guard): a mid-t px needed for 8-connectivity is set to P instead.
  - A set-to-P px left as a floating island is cleared.

| file | chroma before → after | cleared | set to palette tone | kept for continuity | specks cleared | 8-conn components |
|---|---|---|---|---|---|---|
| 045 EyeR_lash | 34 → 0 | 30 | 4 | 0 | 0 | 4 → 4 |
| 045 EyeR_lid_0 | 48 → 0 | 46 | 2 | 1 | 0 | 1 → 1 |
| 315 EyeL_lash | 40 → 0 | 40 | 0 | 0 | 0 | 2 → 2 |
| 315 EyeL_lid_0 | 45 → 0 | 40 | 5 | 0 | 3 | 1 → 1 |
| **total** | **167 → 0** | **156** | **11** | 1 | 3 | unchanged |

- **Supplement rerun** (`eyes_diag_leak_supplement.py`): diagonal eye files 045 and 315 (44 files) have **off-palette 0, chroma 0**. Composites have off-palette 0.
- **Line continuity:** components of lid_k ∪ lash per eye, for k0..7, are unchanged before vs after (045 EyeR [1,2,2,2,2,2,2,2]; all others 1).
- **Rest on frame** (lid 0, gaze 0; `check_diag_chroma_fix.py`):
  - **0 px differ inside her face.**
  - 11 px differ outside it (045: 6, 315: 5). These are exactly the 11 px set to palette tones, on the far-eye silhouette edge, where the frame px is itself a key-blue blend:
    - 045: (326..327, 168..169) and (330..331, 179)
    - 315: (432, 180..182) and (432..433, 186)
  - The 156 cleared px show the frame's own blue underneath, so they are identical to the frame.
  - Note: the rule that rest is exactly the frame now reads 6 / 5 px for these two rigs. Clearing those 11 px instead would restore 0, at the cost of the 1 continuity px and a slightly thinner edge.
- **Composite over neutral grey** (9 gaze × 8 lids × current/diag = 144 renders per angle): qa_gates chroma went from **5760 / 6570 to 0 / 0**.
  - Caveat: **62 dark-navy fringe px** remain in the fixed files that are below the chroma threshold. Their blue exceeds max(r,g) by more than 30, with b ≤ 131:
    - 045 EyeR_lash: 24
    - 045 EyeR_lid_0: 1
    - 315 EyeL_lash: 26
    - 315 EyeL_lid_0: 11
  - They show as a faint navy edge in the sheet. The near eyes have 0. They were not changed, because this fix covered the 167 px only. The same rule can be applied to them on request.
- **Iris-limit checker rerun:** 0 px outside the opening and 0 on the lid line or lash, in all 288 renders. Diag vs current at rest is still 0 px.
- **Sheet:** `diag_chroma_fix.png`. Each file shows before and after on grey and on a checker, the frame, and a change map (red = cleared, green = set to palette tone).
