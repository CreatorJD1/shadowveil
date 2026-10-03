# Diagonal eyes vs Base Hair v3: lash trim + sway (Eyes, Sat 2026-10-03 ~03:25 PT)

Decision: Base Hair's source turn frame wins. Hair stays where it is, and Eyes removes the lash px under her strand. Nothing new was painted.

## Coordinates
- Eye parts are full-canvas 768x1168 in FRAME px. Hair v3 parts and her `src_hair_key_view.png` are 1365x1739 in VIEW px.
- Frame px are mapped to view px with each eye `rig.json` viewFit, using the same nearest mapping as `hair/staged/diagonals_v3/work/common.py`:
  - 045: s 1.54468, dx 83.62, dy -55.77
  - 315: s 1.54468, dx 104.47, dy -52.68
- Hair's boxes are in view px. In frame px they are:
  - 315: x432–437, y170–178
  - 045: x326–331, y166–177

## Trim (`trim_lash.py`, `trim_lash.json`)
- Trim set = lash px where her frame is hair by Base Hair's key rule (frame alpha>0 and B−max(R,G)>60, the rule behind `src_hair_key_view.png`).
- These are the dark navy key/lash blend px.
- In view px the trim set matches Hair's numbers exactly: 315 = 42 px, 045 = 45 px.

| file | trimmed px (frame) | view px | bbox (frame) |
|---|---|---|---|
| 315/EyeL_lash.png + _chroma (her left, green, far eye; outer corner) | 18 | 42 | x432–437 y170–178 |
| 045/EyeR_lash.png + _chroma (her right, amber) | 20 | 45 | x326–331 y166–177 |

- Keyed files: the trimmed px are now (0,0,0,0). Chroma files: the trimmed px are now #0000FF.
- These files have 0 px over her hair key and were not changed: the other eye's lash, white, iris and lid_1..7.
- Lid frames have 0 px in the trim set, so no lid frame was trimmed.
- Not trimmed (outside scope, flagged): lid_0 has px over her key outside Hair's boxes.
  - 315 EyeL_lid_0: 16 frame px at x432–433, y180–186.
  - 045 EyeR_lid_0: 2 px at (330–331, 179).
  - These are lid-skin silhouette-edge px, not lash. They include the known `outside_face_edge` rest px.
- Backups are in `eyes/staged/diagonals/backups_lash_hair_trim/`:
  - 045/EyeR_lash(+_chroma)
  - 315/EyeL_lash(+_chroma)
  - rest/: the previous rest_check.json and check_diag_chroma_fix.json
- 8-connected components of lid_k ∪ lash are unchanged: 045 EyeR [1,2,2,2,2,2,2,2], all others 1.

## Rest (`eyes/qa/qa_gates/check_diag_chroma_fix.py` → `rest_check.json`, two-number format)

| | inside_face | outside_face_edge |
|---|---|---|
| 045 | **0** | 2 (was 6; the 4 lash px at x326–327 y168–169 were trim px) |
| 315 | **0** | 5 (unchanged; lid_0 edge px) |

- On the turn frame, a trim can never open a hole, because the frame shows through.
- In view space (`sway_compare.json`, REST rows):

| | eyes-only, lash on her hair | + hair v3 as staged, holes | + hair refill sim, holes |
|---|---|---|---|
| 045 | 45 → 0 | 0 → **45** | 1 (44/45 covered) |
| 315 | 42 → 0 | 0 → **42** | 0 (42/42 covered) |

- Why there is a hole with hair v3 as staged: v3 removed hair inside the eye "opening", which was built from my *untrimmed* lash. So at the trimmed px there is now neither lash nor hair.
- Hair can fill these px by rerunning `hair/staged/diagonals_v3/work/build_v3.py` (it rebuilds the opening from my staged white+iris+lash). Its v2 pre_eyecut has hair (alpha≥128) at:
  - 315: strand_06, 42/42 px
  - 045: hair_front 18 + strand_03_tip 26 → 44/45 px
- `v3_refill_sim` simulates that refill in memory only. Nothing was written to hair/.

## Sway (`sway_compare.py`, `sway_compare.json`)
Setup:
- Base = her turn frame (f033/f191) in view px. On top: my eye parts (white, iris atop, lid_k, lash; layers 400–413), then hair v3 front parts (layers ≥600; hair_back and bun are behind the body).
- There is no renderer in diagonals_v3, so this is a Python mirror of contract §4 (slider path):
  - angle = swayWeight·maxSwayDeg·HairSwayX about each pivot, chained through the parents
  - dy = round(HairSwayY·swayY·swayYMaxPx), with swayYMaxPx = 3
  - nearest inverse sampling with hard alpha
- Sweep: HairSwayX ∈ {−1, −.5, 0, .5, 1} × HairSwayY ∈ {−1, 0, 1} × lid {0 open, 7 closed} × 7 gaze settings (0, X±1, Y±1, (−1,−1), (1,1)). That is 210 states per angle per variant.
- The segments' `s` values were not swept independently.

Metrics (view px):
- **lash vis on src hair**: lash showing (not under hair) where her frame draws hair. This must be 0.
- **hair over opening**: hair over the visible white/iris.
- **holes**: trimmed px covered by neither hair nor any eye part.
- **lash under hair**: lash hidden under hair because of draw order. This is info only.

Results (each cell is the max over all states):

| angle / hair | lash vis on src hair | hair over opening: sway 0 / max (state, part) | holes: sway 0 / max | lash under hair, max |
|---|---|---|---|---|
| 045 v3 as staged | 0 | 0 / 5 (X−0.5…−1, strand_03_tip) | 45 / 45 | 2 |
| 045 v3_refill_sim | 0 | 0 / 14 (X−0.5 Y+1, strand_03_tip) | 1 / 27 | 17 |
| 315 v3 as staged | 0 | 0 / 27 (X+1 Y−1, strand_06; X+0.5: 6–12) | 42 / 42 | 9 |
| 315 v3_refill_sim | 0 | 0 / 32 (X+1 Y−1, strand_06) | 0 / 42 | 26 |

- Hair-over-opening happens only with open eyes (lid 0). Closed eyes give 0.
  - 045: 35 of 210 states
  - 315: 42 of 210 states
- Per X (open, gaze 0, Y 0), v3 as staged:
  - 045 hair over opening: X−1: 1, X−0.5: 5, others 0. Holes: 37 / 45 / 45 / 45 / 45.
  - 315 hair over opening: X+0.5: 6, X+1: 18, others 0. Holes: 42 / 42 / 42 / 39 / 28.
- Holes at sway ≠ 0 (refill sim) are expected under the decision. When her strand swings away, skin shows where the lash was trimmed (up to 27 px at 045 and 42 px at 315).

## Sheet
`eyes/qa/hair_v3_eyes/eyes_vs_hair_v3_zoom.png`:
- View px, 8x nearest. For each angle there is one row block for v3 as staged and one for refill_sim.
- Tiles: src frame (trim px outlined in magenta), pre-trim, post-trim, then X −1…+1 open and closed.
- Colours: magenta = hole, cyan = hair over white/iris, yellow = lash over her hair.

## Problems / for Base Hair
1. The rest hole (045: 45 px, 315: 42 px) remains until Hair reruns build_v3 against the trimmed lash. Expected result: 1 px at 045 and 0 at 315.
2. At sway, hair goes over the eye white/iris. This breaks contract §4 ("no hair on eyes at any sway"):
   - 315 strand_06 at X ≥ +0.5: up to 27 px (32 px after refill)
   - 045 strand_03_tip at X ≤ −0.5: up to 5 px (14 px after refill)
   This is in Hair's files and was not touched.
3. The lid_0 edge px over her key (315: 16 px, 045: 2 px) were left in place. If Hair wants them removed, trimming them is Eyes' job.
