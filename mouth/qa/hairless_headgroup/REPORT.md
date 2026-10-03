# Mouth QA: hairless slot + head-group handoff re-measure (Base Mouth, Fri Oct 2 2026, ~11:15 PM PT)

Captures come from headless Chrome (puppeteer-core) on `http://127.0.0.1:8765/rig/?view=<v>&quality=linear&mouthfade=0[&hairless=1|&headgroup=1]`.
Params were set the same way the driver sets them: `RigManual(); set(k,P[k][2]) for all; set('MouthOpen',o); set('MouthForm',f); draw()`, then a wait of more than 120 ms for the mouth hold, then `draw()` again.
I read the frame from the rig's full-res `FR` canvas. `mouthState.cur` was checked for every shape, and every capture showed the intended shape.
For the rest check I also used the rig's own exact-rest path (`restPixels()`, the same one the Rest-check button uses). It matched the drawn rest frame.
Scripts: `scripts/capture.js`, `scripts/job1.py`, `scripts/job2.py`, `scripts/sheets.py`. Raw numbers: `job1_results.json`, `job2_results.json`. Captures: `caps/`.
Nothing outside `mouth/qa/hairless_headgroup/` was written. The Chrome processes I launched (PIDs 773664 and 791707) have exited.

## Job 1: hairless=1 vs live (linear): **PASS, all views**

Hairless files really loaded (verified network requests: `body_tools/work/hairless_division_staged/<v>/live_patch_staged/base_body(_skin).png`, staged hair, apose staged palms + hand_mask). `RigHairless.missing` = [].

| view | rest vs base.png: in lock | out of lock | shapes checked | hairless≠live px in 6 px-dilated mouth region | bright blue key in region |
|---|---|---|---|---|---|
| apose | 0 / 2407 | 6182 (premultiply only, see below) | rest, AA, M, smile, AA_half, anger | **0** in all shapes (max abs 0) | 0 |
| tpose | 0 / 2373 | 11445 (premultiply only) | rest, AA, M, smile, AA_half, anger | **0** in all shapes | 0 |
| left  | 55* / 1512 | 4502 (premultiply only) | rest, AA, M, smile | **0** in all shapes | 0 |
| right | 46* / 1466 | 4313 (premultiply only) | rest, AA, M, smile | **0** in all shapes | 0 |

- The live and hairless numbers are identical. The **whole hairless frame is byte-identical to the live frame** in all 4 views at all of these shapes, so no hairless skin or background shows around the lips or interior.
  The staged hairless body differs from the live `base_body` by only 334/54/68/23 px (apose/tpose/left/right). There are 0 changed px in the lock, and 0 in the union of all mouth shapes dilated by 6 px. All the changed pixels are under the hair.
- *Every rest-vs-base difference, both inside and outside the lock, is a semi-transparent edge pixel where RGB differs and alpha is equal. **The premultiplied values match exactly (0 mismatches)**. This is canvas premultiplied-alpha storage, not a content change.
  In the profiles these pixels are the lip/chin silhouette edge, which falls inside the lock (alpha 1..253). The live rig has the same numbers, so this is not a hairless regression.
- "Blue" pixels found in the profile regions (10/3/7 px) are dark-navy outline pixels such as (11,0,63) or (2,0,45). They are in `base.png` itself and identical in live. There is no bright key colour (b>150, r,g<80) anywhere in any rendered frame.
- Caveat: these are static poses, so the hairless body under the hair is never uncovered. This check does not test exposure when the head or hair moves.

Sheet: `hairless_sheet.png` (each tile: live | hairless | diff, with differing px in red and the dilated region in green).

## Job 2: turn-handoff mouth re-measure with headgroup=1

How the rig applies it: `?headgroup=1` + `RigHeadGroup.applyHandoff(view)` reads `rig/partmesh/staged/headgroup.json` and sets `HG={dx,dy}`. `headApply` then pre-multiplies `T(dx,dy)` (pivot 681.5,318; rot 0, scale 1) onto the head-bone matrix, and the mouth uses that matrix.
Verified: in the headgroup render the lips sit at exactly live + (0,-10), (-2,+1) and (+5,-6), so the rig applies the head group to the mouth correctly.
The residual is the turn-frame mouth minus the headgroup render, in canvas px (+y down). Frames are warped to base coordinates with Body's angle_map handoff scale/offset. Search range is ±25 px.

| handoff | head offset | old − head | **seam chamfer** | lip-outline chamfer | seam centroid | lip centroid | front / back seam corner | lower face (nose/chin, lips masked) NCC / silhouette chamfer | verdict |
|---|---|---|---|---|---|---|---|---|---|
| apose f001 | (0,-10) | (0,+1) | **(0,+1)** | (0,+1) | (-0.3,+0.9) | (+0.2,+1.1) | (0,+1) / (+1,+1) | (0,+1) / (+1,+1) | **PASS** (≤1 px) |
| left f062 | (-2,+1) | (+10,+12) | **(+8,+11)** | (+9,+11) | (+6.6,+10.5) | (+9.3,+11.2) | (+7.3,+7.5) / (+4,+10) | (+6,+9) / (+8,+9) | **FAIL** vs face, mouth OK relative to face |
| right f160 | (+5,-6) | (-12,+12) | **(-7,+11)** | (-11,+12) | (-8.3,+11.6) | (-11.9,+12.2) | (-8.8,+9.7) / (-7,+10) | (-6,+11) / (-10,+10) | **FAIL** vs face, mouth OK relative to face |

A lip-only masked NCC was also tried. It is unreliable in the profiles (score 0.51/0.53; left locks onto (-7,0)), so I did not use it. The old window NCC (same method as before) still gives (+9,+13) and (-11,+16).

### Why the profile numbers are large
1. **It is real, and it is not a mouth problem.** In both profile frames the **whole lower face sits further back (toward the ear) by ~7–8 px and lower by ~10 px** relative to the head-group-registered live head. This holds for the nose, lips and chin silhouette (lips masked out: (+6..8,+9) left, (-6..-10,+10..11) right).
   The mouth residual from the seam ((+8,+11) / (-7,+11)) matches the face residual to within about 1–2 px. So **mouth relative to face ≈ (+1,+2) left and (0..-1,0..+1) right**, which is within measurement noise.
   The eye region also reads about +10..13 px lower (low-confidence NCC 0.54–0.58). See `headgroup_face_context.png`: hair and bun register, but the face does not.
2. **The head-group offset is hair-driven.** `headgroup.json` comes from an alpha-silhouette IoU over the head region (top..y330). In profile that silhouette is mostly hair and bun, so it aligns the hair and leaves the face ~10 px off.
   The video's profile face is also foreshortened compared with the live art: lips 16 vs 23 px wide and 15 vs 20 px tall, front and back seam corners shift by different amounts, and the frame is not an exact 90° profile. A single rigid transform cannot fit both the hair and the face.
3. **Measurement biases are small, 1–4 px, and they do not explain it.**
   - The old window NCC included the face silhouette against the background (black vs blue key) and overstates x by about 2–4 px (+10 vs +8; -12 vs -7).
   - Thinner frame lips bias the lip-blob centroid by about 1–4 px in x compared with the seam.
   - The profile anchor (the back seam corner) moves 4 px less in x than the seam on left because of foreshortening.
   - The wrong-anchor theory is ruled out: every method agrees on dy ≈ +10..12.

Sheets: `headgroup_handoff_sheet.png` (rig headgroup render | warped frame | seam overlay at 0 | overlay at the seam residual) and `headgroup_face_context.png`.

## For Coder
- **Do not push the profile residual into the mouth.** In profile the lips sit on the face silhouette. Moving the mouth (+8,+11) / (-7,+11) on its own would put the lips off the live nose and chin, while the live face art stays where it is. **Mouth handoff offsets after the head group should be (0,+1) apose and (0,0) for both profiles.** The mouth is consistent with the face.
- The fix belongs in the head-group registration for the profile handoffs. Register on facial features (nose/lips/chin profile edge + eyes) instead of the hair-dominated silhouette.
  On a face basis the head offsets would be about **left (-2,+1)+(+8,+10) ≈ (+6,+11)** and **right (+5,-6)+(-8,+11) ≈ (-3,+5)**. This would misalign the hair and bun by about 10 px. If the hair must also match, it needs its own sub-offset, or the handoff simply has to accept that the video face and the live profile art differ in shape.
- apose f001 is fine: head (0,-10) leaves the mouth at (0,+1).
- Hairless slot: no mouth-side issues and no lock violations. The only "diffs" are canvas premultiply equivalents of edge pixels.
