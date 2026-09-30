# Idle hand bend: diagnosis (diagnose only; no live file changed)
Render path: rig/index.html unchanged, driven headless by hb_render.mjs (render()/handChain/frameOf of the page itself).
Scratch data is served only through --hands=<dir>. Live md5s of every hands rig.json and index.html were re-checked OK afterwards (live_md5_before.txt), and masks.md5 is OK.

## Cause
- The curl value does not mean the same thing in every view.
  - In apose, left, right and back, the bend is drawn into f1/f2: the whole finger is one foreshortened silhouette in seg1 and seg2/3 frames are empty. maxCurlDeg is only a 12/8/6 lean, and only the seg1 lean is visible.
  - In tpose, f1/f2 are drawn straight: the drawn axis stays within about 2 deg of f0 and pivot->childPivot is unchanged. All of the bend comes from rotation at maxCurlDeg 90/95/15, applied at every segment and compounded down the chain, so the tip lands at 200*curl deg.
- The idle hold (0.3-0.55, written for "f1 = 0.5 relaxed") is fine in apose. In tpose the same hold gives a 45+47.5 deg knuckle pair, with the tip at 100 deg at 0.5.
- (a) Double bend: rejected. The apose f1 is pre-bent, but the rotation added on top is only 3.6-8.4 deg. tpose f1 is not pre-bent.
- (b) Accumulation: confirmed for tpose. It is the reason for the dislocated look.
- Label check: the coder's reported frames "apose arm_settle f71 / weight_shift f182" are the tpose crops (keys_idle_*_tpose_worst_f0071 and _f0182). apose renders at those frames look clean.

## Measured knuckle angles (L hand; pixel PCA of the rendered layers, rotation from handChain in brackets)
tpose  Index  palm->s1 / s1->s2: 0:0/0  .2:17.9/19.5 [18/19]  .3:29.5/25.0 [27/28.5] f1  .5:47.8/44.7 [45/47.5]  .7:65.4/63.9 [63/66.5]  1:92.4/91.3 [90/95] f2; tip 0/40/60/100/140/200
tpose  Middle palm->s1 / s1->s2: .2:18.2/17.9  .3:28.6/37.4  .5:46.8/56.8  .7:64.9/75.4  1:95.6/100.3
apose  Index  palm->s1 (in-plane): .2:2.9 .3:3.4 .5:6.3 .7:8.3 1:14.6. s1->s2 is only visible at f0 (.2: 2.3); seg2/3 are empty at f1/f2.
apose  Middle palm->s1: .2:2.7 .3:3.7 .5:6.0 .7:8.8 1:14.4
Implied by the apose drawings: seg1 f1 pivot->childPivot is 21.3/28.9 px (about 43 deg MCP pitch), and the whole finger is shortened to 0.45 (f1) and 0.15 (f2), about 63 and 81 deg.
Nearest-frame selection shows that f1 from curl 0.25 up, so Index 0.3 already shows the "0.5" drawing. That is overshoot, but it does not look dislocated.
right: f1 0.46-0.49, f2 0.22-0.29.

## Specks
They are not chroma fringe: the f1 PNGs have 0 bluish px. They come from knuckle overlap and pivot geometry:
- tpose: the L_palm top outline has anti-aliased pixels with alpha<250 (60 px in 16 enclosed bits, at y 391-398, including (1250,397) and (1254,398)) right at the Middle1 pivot (1249.2,398.3). There is also the palm's hidden under-fill outline. Once seg1 rotates they are exposed, along with the Ring1_f1 stand-in fill poking above the knuckle. QA-style new holes/tears/seam at the pivots: .3 -> 2/69/12, .5 -> 20/9/29.
- At f0 small curls, the square-cut rest pieces and hidden Ring/Pinky stand-ins show as stacked outline fragments.
- apose: a notch between the rounded Middle/Ring f1 bases sits below the edge of the palm (palm alpha 0), giving 17-25 px of partial alpha. At f0 the opposite +/-12 deg lean of Middle and Ring opens an 82 px hole at 0.2.

## Fix (smallest)
1. Idle keys (owner: idle keys / body_tools/idle/make_idle_clips.py): add viewKeys.tpose with the Index/Middle/Ring/Pinky curl series multiplied by 0.32. Hold becomes 0.096/0.16/0.16/0.176 and the lift peak 0.208/0.208/0.224. Everything stays below the old 0.25 frame switch, and knuckles stay within 18.7/19.8 deg. Other views keep their values.
2. Hands data (owner: hands), tpose rig.json only: finger frame lists [f0,f1,f1,f1,f2]. f1 (the clean rounded segments) then shows from curl 0.125 instead of the f0 cut pieces. Rest and Fist are pixel-identical to live; f2 now starts at 0.875 (tpose f2 is roughly f1).
- No renderer change is required. A per-frame angle compensation field would be a renderer change (coder); it is not needed for this.
- Rest stays 0 px: the rest path ignores v and uses fr[0]. The scratch rest render is identical to live (0 px diff) and the rig loaded the scratch rig.json with 0 warnings.
- Remaining art follow-up (hands): trim the tpose Ring1_f1/f2 fill and the palm top-edge alpha near the knuckle, and extend the apose palm under-fill beneath the Middle/Ring f1 notch. All of it is hidden at rest.

## Right view, arm_settle f169
The near R hand is clean: f1 on all four fingers, no specks in the owner map, and the coder QA also counts hands holes/tears/seam = 0.
The f169 worst crop is a body defect (forearm_L / thigh, body holes 422), not the hands.
A faint light rim along the rotated outline also appears on the forearm. It is resampling of the edges, not something specific to the hands.

## Follow-up: hidden-art cleanup (applied 2026-09-30 ~03:40 PT)
Tool: art_edit.py (dry run first via DRY=scratch/art; live == dry run). Every edit is either
(a) a palm pixel covered at rest by an alpha-255 hand part drawn above it (asserted), or (b) a Ring1 f1/f2 pixel; frames are never drawn at rest.
Colours: palm fill is skinRGB (185,127,83) at alpha 255; everything else is set to alpha 0. No bluish pixels. Backups are in art_backup/<view>__<file>, and the log is in art_edit_log.json.

Changed (tpose only):
- L_palm.png: 18 px (14 hidden px that only ever poked out of the posed silhouette at the knuckle cleared, 4 gap px filled)
- R_palm.png: 11 px (10 cleared, 1 filled)
- L_Ring1_f1.png: 19 px, L_Ring1_f2.png: 6 px, R_Ring1_f1.png: 19 px, R_Ring1_f2.png: 10 px. Filler that stuck out of the silhouette or showed over the palm was cleared. Pixels that fill a gap at any curl (including their bilinear neighbours) were kept.

Rest check: total 0 in all 5 views; masks.md5 OK. The rig loads the live files with 0 warnings. Floating specks after the edit: none.

Pivot counts (holes/tears/partial within 12 px of the seg1 pivots; hand-only composite; new vs rest):
tpose L  .2 0/0/15->0/1/17  .3 2/2/12->0/0/13  .5 4/3/4->0/1/6  .7 1/1/2->0/1/2  1.0 0/0/0->0/2/0
tpose R  .2 0/2/7->0/2/8    .3 0/2/4->0/2/4    .5 6/4/0->3/0/0  .7 1/1/0->1/2/0  1.0 1/1/0->1/2/0
apose L/R: unchanged, no files changed (see below).

Not fixable by art under the rules (stopped):
- tpose top-knuckle notch at (1252-1256,398) / mirrored on R, and the palm top-edge alpha 155-220 at (1247-1249,394). These pixels are visible at rest: they sit under Middle1 f0 pixels with alpha 251-253 and palm alpha 0, or they are the visible palm outline anti-aliasing. The notch exists because the seg1 pivot is 4.8 px below the dorsal contour. The data fix is to move the Middle/Index seg1 pivot up to the top contour (hands rig.json pivot, not art).
- tpose gap between Index1 and thumb/palm bottom (1236-1243,415-420): visible at rest.
- apose f1 base notch: 22 of 29 defect px at 0.5 are visible at rest (the V gap between fingers). The few palm-coverable px would each float as a skin speck at f2, where the palm's hidden fill also draws the fist bottom contour, so nothing was applied.
- apose f0 hole at curl 0.2 (82 px): Middle (+12 deg) and Ring (-12 deg) lean into each other and their tips close the natural gap between the fingers. The pixels are visible background at rest, so no palm fill can close it. The data option is Ring/Pinky maxCurlDeg sign or magnitude (rig.json, not art).
- hands/chroma/* work copies were already out of sync with views/ before this edit and were left untouched.

## Follow-up 3 — hands DATA fixes (rig.json only), 2026-09-30 ~03:35–04:20 PT

Backups: `data_backup/tpose_rig.json`, `data_backup/apose_rig.json` (taken before any edit). Scratch rigs: `scratch/data_*/rig.json`.
Renders: `renders/data/<view>_<variant>/` (rest, curl 0.13/0.2/0.3/0.5/0.7/0.87/1.0, Fist/Point/Peace; hand layers dumped).
QA: `pivot_qa.py` (new vs rest holes / tears (3 px closing) / partial alpha inside 4 px erosion; counted within 12 px of the seg1 pivots and over the whole hand;
`knuckle` = defects within 9 px of the Index1/Middle1 pivots on the dorsal side). The counting regions always use the ORIGINAL pivots (backup rig), so before and after are compared the same way. Tables: `qa_table.py`, json `qa_data_*.json`.
Totals below are summed over L+R and all 10 posed cases (knuckle | pivot holes/tears/partial | hand holes/tears/partial).

### 1. tpose Index1/Middle1 pivot up to the top contour: NOT applied (it doesn't close the notch). Stopped as instructed.
- Measured the dorsal contour above the seg1 pivots: Middle1 4.0 px (L) / 3.0–5.0 px (R), Index1 5.75 px. Tested scratch A (Middle +4.0, Index +5.0), B (both +4.8) and C (A plus Ring1/Pinky1 +5.0).
- Why it fails: the notch comes from the art. Middle1_f1's base cap is drawn 2–3 px lower (top y 396–398 at the pivot column) than the palm's top edge (394), and the palm has its own rounded corner (395/396/399 at dx 1..3). Two convex corners meet there. Moving the rotation centre up only slides the finger back by 4.8·sinθ and up by 4.8·(1−cosθ) (≈0.5 px at 27°), so it can't lift the cap to the palm line.
  Silhouette notch area (closing r4, dorsal, Middle1) at 0.13/0.2/0.3/0.5: L 1/1/2/1 before, 1/1/2/1 with A and B; R 3/3/4/1 before, 3/3/4/2 with A.
- It also causes a regression: rotating about a higher point lifts the part of f1/f2 behind the pivot above the palm top line (+1–3 px) from 0.7 up, and it roughens the fist front.
  Totals: before 21 | 13/69/74 | 139/598/294; A 36 | 14/72/50 | 129/622/154; B 40 | 19/69/50 | 133/664/149; C 43 | 5/91/63 | 56/651/173.
  Knuckle/fist tears get worse: L Fist pivot tears 10 to 19 (A).
- Ring/Pinky: they share the Index1 pivot and are hidden behind Index/Middle, so they add nothing to the dorsal silhouette. Moving them (C) did not help the notch and added tears (69 to 91), so they don't need the change.
- Data-only alternative, scratch only and NOT applied (`scratch/data_F/rig.json`): per-frame `pivot` on Middle1's non-f0 entries only (f0 and the part pivot are unchanged, so rest can't change), moved DISTALLY along the finger axis by 4.0/2.5/1.8/1.5 px on frame entries 1/2/3/f2.
  This lifts the base about 1.5 px while curled. The notch at 0.2–0.5 closes and 1.0/Fist get a flat top with no hump.
  Totals: F 7 | 12/46/80 | 141/583/264 (knuckle 21 to 7, pivot tears 69 to 46). Partial alpha at the pivots goes up slightly (74 to 80, +1 px in a few cases). A constant distal shift (E, 4 px on all curled entries) closes the notch but raises a 3–4 px knuckle hump above the palm at 0.5 or more (knuckle 17, but a visible bump).
  Caveat: there are small position steps (≤1 px) where the frame entry switches (curl 0.375/0.625/0.875). Needs approval, because it isn't the change that was requested.
- Sheets: `sheets/data_tpose_{L,R}_knuckle.png` (rows: before / up4 / up4.8 / alt_F), `sheets/data_tpose_{L,R}_ladder.png` (before / up4 / alt_F). Columns: 0.2 0.3 0.5 0.7 1.0 Fist Point Peace. Red = new defect px.
- views/tpose/hands/rig.json is unchanged (md5 matches data_backup).

### 2. apose Ring/Pinky maxCurlDeg sign: APPLIED to views/apose/hands/rig.json
- Change: L_Ring1/2/3 and L_Pinky1/2/3 go from -12/-8/-6 to +12/+8/+6; R_Ring and R_Pinky go from +12/+8/+6 to -12/-8/-6. All four fingers now lean the same way (parallel), so they no longer converge onto Middle.
  Index/Middle, the frames, the pivots and `maxCurlDegRotationOnly` are untouched. Tested on scratch first (G). A "Ring/Pinky 0" variant (H) left the 0.2 closed gap at 0 holes but ~100 tears (111/96 at 0.2). G2 (Pinky +8/6/4) came out slightly worse than G.
- Counts before to after: total 0 | 4/15/33 | 180/274/88 goes to 0 | 2/17/0 | 2/76/0.
  Curl 0.2 hand holes L 82→0, R 83→0. Curl 0.13 tears L 103→4, R 94→10. Partial alpha at the pivots 33→0 (0.3/0.5/0.7 f1 base gaps included). Fist/Point/Peace: +1 tear px per hand on L, −1 on R; the fist silhouette is visually unchanged.
- Live check: live-after hand layers (352 files) are pixel-identical to scratch G.
- Sheets: `sheets/data_apose_{L,R}_ladder.png`, `sheets/data_apose_{L,R}_knuckle.png` (rows before / after).

### Other views' opposite lean (report only, not changed)
All of left/right/back use the same pattern (Index/Middle ±12/8/6, Ring/Pinky opposite sign). Scratch test with Ring/Pinky flipped:
- back: same problem as apose. Curl 0.2 hand holes L 47→0, R 50→0, and curl 0.13 tears 61/67→2/1. But partial alpha goes up (pivot 29→86, hand 83→157) and Fist/Point/Peace tears go up (e.g. L Peace 13→28).
  Needs its own tuning (flip plus a check of the f1 bases) before applying. Sheet `sheets/data_back_check.png`.
- left / right: no closed-off gap from the lean. Flipping makes them worse (left hand holes 35→59, partial 258→428; right 94→122, 212→414). Keep them as they are.

### Rest / masks
`python3 rig/rest_check.py` after the apose edit gives total 0 in all 5 views (apose, tpose, left, right, back) and underlay ok (`rest_check_after_data.txt`). `hands/work/masks.md5`: 5/5 OK.

### Note: environment drift
Full-frame (body) pixels in posed apose renders changed between ~03:47 and ~03:54 PT, independent of hands: a scratch-G re-render at 03:58 matches live-after exactly, and the hand layers are identical. Rest was identical throughout. Another agent was rendering actions at the time.
The hand-only QA above isn't affected.

## Follow-up 4 — back view lean tuning + lineart check (2026-09-30, 04:15–05:05 PT)

Backup: `data_backup/back_rig.json` (md5 2249f6e7…, identical to live). Candidate rigs are in `scratch/back_c*/rig.json` and renders in `renders/data/back_c*/`.
The same QA as follow-up 3 was used (`pivot_qa.py`, counted with the original pivots). `back_eval.py` sums L+R over all 10 posed cases.
Pass criteria: every total ≤ c0 (holes, tears and partial alpha, both near the pivots and over the whole hand), curl-0.2 holes = 0, and every Fist/Point/Peace metric within ±2 px of c0. Lean is given as L seg1 degrees for Index/Middle/Ring/Pinky; seg2 = 2/3 of that, seg3 = 1/2, and R is mirrored.

| cand | change | 0.2 holes L,R | near pivots H/T/P | whole hand H/T/P | max pose Δ | result |
|---|---|---|---|---|---|---|
| c0 | live -12/-12/+12/+12 | 47,50 | 16/17/29 | 149/365/83 | 0 | baseline |
| c1 | Ring/Pinky 0 | 0,0 | 2/29/60 | 57/550/122 | 9 | fail (tears, partial, poses) |
| c2 | Ring/Pinky -6 (same sign, half) | 0,0 | 2/40/128 | 53/475/211 | 18 | fail |
| c3 | Ring/Pinky +6 (opposite, half) | 0,0 | 10/22/49 | 43/486/131 | 3 | fail (tears, partial, poses) |
| c4 | Middle 0, Ring 0 | 0,0 | 64/25/35 | 173/387/44 | 19 | fail |
| c5 | all 0 | 0,0 | 26/35/24 | 121/296/33 | 18 | fail (pivot holes/tears, poses) |
| c6 | Ring 0 | 0,0 | 22/17/68 | 78/621/130 | 8 | fail |
| c7 | Middle -6, Ring +6 | 0,0 | 14/17/86 | 63/569/187 | 7 | fail |
| (fu3) | flip Ring/Pinky (-12) | 0,0 | 18/42/86 | 59/332/157 | >2 | fail |
| c8 | lean as live, frames [f0,f1,f1,f1,f2] | 1,0 | 15/13/40 | 58/340/138 | 0 | fail (partial 29→40 / 83→138) |
| c9 | lean as live, frames [f0,f1,f1,f2] | 1,0 | 17/15/33 | 53/386/120 | 0 | fail (partial, pivot holes +1) |

**Nothing applied to back.** No maxCurlDeg setting passes, for a structural reason: the angle is curl × maxCurlDeg, so any lean change large enough to open the Middle/Ring gap at curl 0.2 turns the curl-1 fist by 5× as much.
Poses therefore always move by more than 2 px (c3 is closest at 3), and the f1/f2 bases pick up partial alpha. c8 and c9 are rig.json frame-list changes rather than maxCurlDeg; they fall outside the brief, so I tested them for information only.
They keep the poses pixel-identical and remove the hole, but the f1 drawing at small angles adds partial alpha, 6→28 px (L) and 15→30 px (R) at curl 0.2. That needs an art fix to the back f1 base fill (hidden at rest), or a renderer-side per-frame angle offset.
Sheets: `sheets/back_candidates_{L,R}.png` (rows c0/c3/c5/c8/c9; columns 0.13 0.2 0.3 0.87 1.0 Fist Point Peace; red = new defect px), `sheets/back_lineart_c8_L.png`.

### Lineart continuity / width check (new criterion)
Tool: `lineart.py`. Line = opaque pixel with luminance < 95. Joints = world position of every finger and thumb segment pivot (per-frame pivot when one is set).
Per joint (10 px zone, compared with the same joint at rest):
- **width:** mean 2×EDT along the line skeleton; fail if it differs from rest by more than 1 px. Mean width per finger is also checked.
- **breaks:** silhouette-edge px with no line px within 1 px, in runs of 2 px or more.
- **new sharp corners:** contour turn > 75° over 4 px chords, only where both chord ends lie on the same finger (crotches between fingers are ignored), within 7 px of the joint.

`sheets/la_vis`-style overlays mark uncovered edges blue and corners with red rings. Results (`la_*.txt` / `la_*.json`):
- **back live (c0): width fails, but only just.** R_Middle1 is 1.17 px wider than rest at curl 0.13/0.2 (that's where the f0 fingers converge). No breaks, no new corners. c8 is clean on lineart; c9 has the same 1.17 at 0.13.
- **apose live (lean flip): PASS on width and breaks.** The R_Ring2 zone flags one "new" corner at 0.87/1.0/Fist/Point/Peace. It is the 104° crotch drawn into the f2 fist art, which is identical before and after the flip. The joint zone just moved over it.
  Whole-hand same-finger corners before→after: L 4→3 (0.87/1.0/Fist) and 3→2 (Point/Peace); R 4→4. Relative to rest (L 3, R 2), the drawn f2 fist has 1–2 extra corners in both versions; that is the art, not deformation. Sheets: `sheets/lineart_apose_R_fist_corners_{before,after}.png`.
- **tpose live (frames5 + data_F): FAILS on breaks.** Width is OK everywhere.
  - Curl 0.2/0.3: L 2/7 px and R 6 px along the underside of the lowest finger, above the thumb gap.
  - Curl 0.87: 5 px (L) and 6 px (R) at the Middle1 knuckle front, plus one new corner on R.
  - Owner in every case: the hidden stand-in **Ring1_f1** (flat skin filler with no outline). It pokes outside the silhouette with no line on it.
  - Pre-F it was the same or worse: the 0.2/0.3 breaks were identical, and Middle1 breaks appeared at 0.7/0.87/1.0/Fist/Point, 3–6 px each. data_F removed the 0.7/1.0/Fist/Point breaks.
  - The fix is art: trim those Ring1_f1 edge pixels. They are invisible at rest, since f1 never shows at rest. A data option, lowering Ring1's lean or pivot so it stays tucked, is untested.
  - Sheets: `sheets/lineart_tpose_L_Ring1_f1_break.png`, `sheets/lineart_tpose_R_Ring1_knuckle_break.png`.

Rest check after follow-up 4: total 0 in all 5 views (`rest_check_followup4.txt`); masks 5/5 OK. Nothing live changed in follow-up 4.
