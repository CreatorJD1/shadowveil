# Shadowveil anger mouth (10th mouth shape): summary

Built 2026-09-30, about 04:35–04:55 PT, by the Mouth executor. Scripts are in this folder: measure.py, build_anger.py, proposal.py, register.py, checks.py, nearest_sim.py, sheet.py.

## What is live
| view | anger shape | at (MouthOpen 0.25, MouthForm −1) the rig shows |
|---|---|---|
| apose | **live**: views/apose/mouth/anger.png, registered | anger |
| tpose | **live**: views/tpose/mouth/anger.png, registered | anger |
| left | none. The anger art is front-only. PROPOSAL copy in proposal/left/ (not live) | **M** (fallback) |
| right | none. The anger art is front-only. PROPOSAL copy in proposal/right/ (not live) | **M** (fallback) |
| back | no mouth | – |

## Source art
- Approved Clean-room (Grok build) anger face: `reference/grok_build/public/puppet/emotions/anger.png`, 704×704 RGBA, sha256 017d0171…ca73.
  - `public/puppet/export/faces.json` points to this file (kept → id anger, mouth "closed").
  - The file is byte-identical in 0596d8a and in the current checkout, HEAD ce53208. The repo has two newer exports since 0596d8a, and neither changes this file.
- The faces.json path is `public/puppet/export/faces.json`. The task gave `puppet/export/faces.json`, which does not exist.
- **There is no side or 3/4 view of the anger face.** The other anger files are all front-facing: faces/anger.png (264×130 crop), rig/expr/anger.png (full body), and clean-room layers/anim/angry.png plus videos/angry.mp4 (a front full-body clip, not the approved face still, so unused).
- Source crop: `anger_source_crop.png`.
- The cut is the lips plus a 1 px anti-aliased rim, taken from the source pixels. The green outline in the right panel of the crop shows it.
  - Lip mask: luminance below 70, excluding the brown under-lip shadow (R−B > 25 and lum > 20), filled.
  - The drop shadow under the lower lip and the skin are **not** cut.

## Measurements (px)
| | source anger | apose rest | tpose rest | apose anger (placed) | tpose anger (placed) |
|---|---|---|---|---|---|
| lip bbox W×H | 96×50 | 48×20 | 48×19 | 49×26 | 49×26 |
| seam row / lip top / lip bottom | 436 / 415 / 464 | 286 / 279 / 298 | 277 / 272 / 290 | 286 / 275 / 300 | 277 / 266 / 291 |
| corner tilt | 0.0° (both corners at row 436.5) | 0° | 0° | 0° | 0° |
| nostril bottom → lip top gap | 21 (≈10 at 0.5) | 10 | 9 | 6 | 3 |
| seam line weight (vertical dark run, median [range]) | 5–6 (≈3 at 0.5) | 1 [1–3] | 1 [1–2] | 3 [1–4] | 3 [1–4] |
| outer lip outline (top / bottom) | thin black | none (no outline, like the anger top) | none | 0 / 1 | 0 / 1 |
| line colour | (8, 3, 4) | #220C00 (34,12,0) | #220C00 | same as source (not recoloured) | same |
| lip fill colour | plum (40, 24, 33) | upper #523017 / lower #633B22 (brown) | same | plum (source) | plum (source) |

Seam line thresholds: ours counts pixels with lum < 36 (between line lum 17 and upper-lip lum 55). The anger mouth counts lum < 14 (between line lum ≈4 and plum fill ≈28).

## Placement transform (uniform scale + translate, rotation 0)
`dst = dstCentre + s·(src − srcCentre)`, in pixel-edge coordinates.
- **srcCentre** = (371.0, 436.5): the centre of lip columns 323–418 and the seam row 436.
- **s** = rest drawn width / source width = 48/96 = **0.500**. The same s is used for both views.
- **apose**: dstCentre = (681.0, 286.5). That is the rest centre (lip columns 657–704) and the rest seam row 286, which is also the rig anchor (681, 286).
- **tpose**: dstCentre = (682.0, 277.5). That is lip columns 658–705 and seam row 277. The rig anchor is (682, 277).
- **Rotation** = 0: the source corners are level, and so are our rest corners.
- **Cross-check**: the face-size ratio (anger iris spacing ≈147 px vs ours ≈68) is 0.46, close to the width match of 0.50.
- **Height**: a uniform scale cannot match both width and height. Width is matched exactly. The anger lips come out **26 px tall vs rest 20/19** (+4 above the seam, +2 below), so the gap to the nostrils shrinks from 10 to 6 px (apose) and from 9 to 3 px (tpose).
- **Resampling**: 8×8 supersampled nearest source pixel, then averaged over each area (the same SS=8 pipeline as build5.py). No pixel is painted.

## Build (same rules as the nine existing shapes)
- Full canvas 1365×1739 RGBA, layer 500, parent base, pivot = anchor, file anger.png. It is registered in `views/<v>/mouth/rig.json` and mirrored in `mouth/mouth_rig.json`.
- Registration: partsBBox.anger, grid.anger = {MouthOpen 0.25, MouthForm −1}, and a parts entry mouth_anger.
- `mouth/mouth_rig.json` also gets a top-level `anger` note: views, grid, source, profile fallback, and the renderer note.
- **Underlay**: skin (the view's rig colors.skin: apose #B88155, tpose #B98155) under dilate2(rest drawn lips ∪ anger lips), fully opaque, with a σ=0.6 px feather out to dilate3.
  - build5 rule applied: drawn-lip pixels with alpha above 0.5 are set opaque.
  - The skin underlay is not painting: it hides the rest lips, exactly as M and the half/open shapes do.
- **Chroma**: a preview on #0000FF is at `mouth/<v>/anger_chroma.png`.
  - Keying: feather pixels are unmixed against skin. Pixels with alpha 0 have RGB 0. Despill: B ≤ max(R,G).
- **apose**: bbox [651, 270, 710, 306]; 1140 opaque + 371 semi-transparent px; key max alpha error 0.0078; blue-spill px 0; pure-blue px 0; RGB at alpha 0 max 0.
  - Rest lip pixels not fully covered: **0** of 543. Dark rest pixels under partial alpha: **0**, so no rest line shows through.
- **tpose**: bbox [652, 261, 711, 297]; 1127 opaque + 362 semi-transparent px; key max alpha error 0.0052; blue-spill px 0; pure-blue px 0; RGB at alpha 0 max 0.
  - Rest lip pixels not fully covered: **0** of 524. Dark rest pixels under partial alpha: **0**, so no rest line shows through.

## Deviations from the brief (need your decision)
1. **Lip colour.** The approved art has **plum/aubergine** lips, about (40,24,33) with a black line. Her drawn lips are **brown** (#523017 / #633B22).
   - I kept the art's own colours. The brief allows colour matching for the line only.
   - So the anger mouth reads as dark lipstick against rest/M, and a cut between rest/M and anger changes the lip colour.
   - A recoloured variant would need your OK to colour-match the fill as well.
2. **Seam line weight: rule FAILS by about 1–2 px.** The anger seam is **3 px** (range 1–4). Hers is **1 px** (range 1–3).
   - The source seam is 5–6 px thick. At the scale fixed by the width (0.5), that becomes about 3 px.
   - Hitting ±1 px would need scale ≤0.33 (a 32 px wide mouth), or thinning her line, which would mean redrawing it. I did neither.
   - The outer outline is fine: none on top (hers has none either) and 1 px at the bottom.
3. **Seam continuity.** The line has no gaps along the lips, except the art's own light glint in the centre of the seam (lum up to about 104, 4–8 px wide).
   - At the strict threshold, column [679] (apose) / [680] (tpose) splits into an upper line (row 284) and a lower line (row 287) around the glint. At 6× it reads as a highlight, not a break.
4. **Line colour** is (8,3,4) vs hers (34,12,0). Both read as black at 1:1, so I did **not** colour-match it. Nothing was recoloured.
5. **Flat colour.** The cut keeps the art's own gloss and soft shading (about 777 distinct colours in the part). It is not a flat 9-colour palette like the others. The art's drop shadow under the lip is excluded.
6. **Fuller lips.** See the height note under the transform: 26 px vs 20 px, and a smaller nose gap.

## Profiles
- There is no real side view of the anger face, so **nothing is live in left or right**. At (0.25, −1) the renderer picks **M** in those views.
  - M and OH_half tie at distance 0.25, and the closed shape wins the tie.
- The PROPOSAL copies are clearly labelled and not registered: `proposal/left/anger.png`, `proposal/right/anger.png`, plus chroma previews and proposal_report.json.
  - **left**: the FRONT mouth squashed horizontally, scaleX 0.260, scaleY 0.487 (0.5 × the profile/front CE ratio), centred on the profile lips (600.5, 270.5) and clipped to her silhouette. Rest lips uncovered: 0.
  - **right**: the FRONT mouth squashed horizontally, scaleX 0.260, scaleY 0.492 (0.5 × the profile/front CE ratio), centred on the profile lips (772.5, 274.5) and clipped to her silhouette. Rest lips uncovered: 0.
  - They look like a front mouth pasted onto a profile: both corners, symmetric lips, and a few skin specks at the lip front where the underlay follows her anti-aliased edge. **Not recommended.** A real profile needs side-view anger art.

## Nearest-shape simulation (mirror of rig/index.html mouthPick: Euclidean distance, then rest first, then more closed, then manifest order)
| grid point | shape | before (9 shapes) | front after (10) | profile (9) | talk before | talk after |
|---|---|---|---|---|---|---|
| (0, 0) | rest | rest | rest | rest | rest | rest |
| (0, -1) | M | M | M | M | M | M |
| (0, 1) | smile | smile | smile | smile | rest | rest |
| (0.5, -1) | OH_half | OH_half | OH_half | OH_half | OH_half | OH_half |
| (0.5, 0) | AA_half | AA_half | AA_half | AA_half | AA_half | AA_half |
| (0.5, 1) | EE_half | EE_half | EE_half | EE_half | AA_half | AA_half |
| (1, -1) | OH | OH | OH | OH | OH | OH |
| (1, 0) | AA | AA | AA | AA | AA | AA |
| (1, 1) | EE | EE | EE | EE | AA | AA |
| (0.25, -1) | anger | M | anger | M | M | anger |

"Talk" means the renderer's auto-talk filter, which excludes EE, EE_half and smile. Every existing grid point picks exactly what it did before. (0.25, −1) picks **anger** in apose/tpose and **M** in left/right.

**Clips sampled at 30 fps. Front and profile picks are identical to before except for the new anger key:**
- **mouth_showcase**: frames changed vs before: 0 of 343. Front runs: (unchanged; 9 held shapes plus talk pass); profile runs: (unchanged).
- **jump**: frames changed vs before: 0 of 49. Front runs: [['rest', 500], ['AA_half', 300], ['OH_half', 300], ['M', 200], ['rest', 333]]; profile runs: [['rest', 500], ['AA_half', 300], ['OH_half', 300], ['M', 200], ['rest', 333]].
- **run**: frames changed vs before: 0 of 61. Front runs: [['AA_half', 400], ['rest', 267], ['AA_half', 400], ['rest', 267], ['AA_half', 400], ['rest', 300]]; profile runs: [['AA_half', 400], ['rest', 267], ['AA_half', 400], ['rest', 267], ['AA_half', 400], ['rest', 300]].
- **anger**: frames changed vs before: 82 of 91. Front runs: [['rest', 300], ['anger', 2733]]; profile runs: [['rest', 300], ['M', 2733]].
  - Previous keys (the M stand-in) gave [['rest', 300], ['M', 2733]]. The 81 changed frames (f9–f90) are exactly the intended M → anger swap from 0.30 s; profile views still show M.
- **Dense check at 0.1 ms steps**, i.e. inside the 1 ms hard-step ramps, which 30 fps sampling never hits:
  - Anger is momentarily nearest for 2.1 ms in total in the showcase talk pass, and 0.5 ms at jump 1.099–1.100 s (OH_half → M).
  - This does not matter for 30 fps renders. A renderer that samples at arbitrary times could, rarely, land in such a 1 ms ramp. Treating ≤1 ms key pairs as hard steps avoids that.
- **Procedural auto-talk** (stepTalk port, 144000 frames at 60 fps): with the current TALK_EXCLUDE, anger would be picked on **6295 frames (4.37%)**. These are syllables rising or falling through open ≈0.25 at form ≈−1, and they would flash plum lips mid-speech.
  - With 'anger' added to TALK_EXCLUDE: **0** frames change vs before.

## Renderer change needed (for Expert Coder Agent; rig/ was NOT edited)
The renderer is data-driven. It reads mouth parts plus grid[name] from views/<v>/mouth/rig.json, so it already loads anger and picks it at (0.25, −1). No shape list or grid change is required.

**One change is needed**, so that auto-talk never picks anger. In `rig/index.html`, line 237:
```
- const TALK_EXCLUDE=new Set(['EE','EE_half','smile']);let mouthTalk=false;
+ const TALK_EXCLUDE=new Set(['EE','EE_half','smile','anger']);let mouthTalk=false;
```
Optional changes:
- Line 221: add `anger:[0.25,-1]` to MOUTH_DEFAULT (documentation only; grid.anger already supplies the coordinates).
- Mirror the TALK_EXCLUDE change in index.v18-wip.html / index.v19-wip.html if those carry their own copy.
- Regenerate `rig/previews/actions/v1/clips/anger.json` (and `anger_stress.json`) with `python3 rig/tools/merge_clips.py anger …`. The current copy still has the M keys.
  - I ran merge_clips into this folder's tmp/ only: anger, jump and run all merge OK (plain and --stress), with no collisions.
  - The jump/run mouth tracks are identical to the existing preview copies.

## Action clips
`mouth/actions/make_mouth_actions.py` changes:
- Adds 'anger':(0.25,−1) to its shape table.
- Anger clip = rest, then anger from 0.30 s to the end (3.0 s): MouthOpen [[0,0],[0.299,0],[0.3,0.25],[3.0,0.25]], MouthForm [[0,0],[0.299,0],[0.3,−1],[3.0,−1]].
- The validation tie-break now mirrors the renderer.

Rerun validation output:
```
jump [('rest', 500), ('AA_half', 300), ('OH_half', 300), ('M', 200), ('rest', 333)]
run [('AA_half', 400), ('rest', 267), ('AA_half', 400), ('rest', 267), ('AA_half', 400), ('rest', 300)]
anger [('rest', 300), ('anger', 2733)]
```
The jump and run clips are key-for-key identical to before. The showcase is unchanged: it still shows the nine shapes, with no anger tile.

## rest_check (`python3 rig/rest_check.py`)
- Before: apose 0, tpose 0, left 0, right 0, back 0 (total 0).
- After: **apose 0, tpose 0, left 0, right 0, back 0 (total 0)**. Mouth region is 0 in all four face views.
- The full before and after JSON reports are identical: rest_check_before.txt, rest_check_after.txt.

## Hashes (sha256; hashes_before.txt / hashes_after.txt)
- The existing nine shapes × 4 views = **36/36 byte-identical**. All base.png files are identical, and left/right rig.json are identical.
- Changed on purpose: views/apose|tpose/mouth/rig.json, mouth/mouth_rig.json, mouth/actions/mouth_actions.json (and its generator .py).
- New: views/apose|tpose/mouth/anger.png and mouth/apose|tpose/anger_chroma.png.
- Backups of every edited JSON/py are in backup/.

| file | before | after |
|---|---|---|
| mouth/actions/mouth_actions.json | ce67dc8e0a4ae85b | aa26f82cd22403f0 **changed/new** |
| mouth/mouth_rig.json | 5f72269fd5a52968 | 7eb2faff5ccf11dd **changed/new** |
| mouth/showcase/mouth_showcase.json | ef37e40ef01ef925 | ef37e40ef01ef925 |
| views/apose/base.png | b64c22dedd677808 | b64c22dedd677808 |
| views/apose/mouth/AA.png | dfc2bbc9db0c3ac0 | dfc2bbc9db0c3ac0 |
| views/apose/mouth/AA_half.png | 12948f0d1ca15b57 | 12948f0d1ca15b57 |
| views/apose/mouth/EE.png | 4f4e88568370fcf7 | 4f4e88568370fcf7 |
| views/apose/mouth/EE_half.png | b4af6d52bb866fd7 | b4af6d52bb866fd7 |
| views/apose/mouth/M.png | 6ae1a37163acab96 | 6ae1a37163acab96 |
| views/apose/mouth/OH.png | 80feb65d1d55d84f | 80feb65d1d55d84f |
| views/apose/mouth/OH_half.png | dce557372196e8ca | dce557372196e8ca |
| views/apose/mouth/anger.png | — | 2dc7ec34696f1603 **changed/new** |
| views/apose/mouth/rest.png | aa22cb3c0b3065a5 | aa22cb3c0b3065a5 |
| views/apose/mouth/rig.json | c854273355d3b7d5 | 8c76563b67155de8 **changed/new** |
| views/apose/mouth/smile.png | eb972a2d7a2eab6f | eb972a2d7a2eab6f |
| views/back/base.png | b2f586e84ce6dd87 | b2f586e84ce6dd87 |
| views/left/base.png | c6d92c5e3c19f152 | c6d92c5e3c19f152 |
| views/left/mouth/AA.png | c41933532895e23c | c41933532895e23c |
| views/left/mouth/AA_half.png | 3141958b94a4e3e9 | 3141958b94a4e3e9 |
| views/left/mouth/EE.png | 23712c15b9719d54 | 23712c15b9719d54 |
| views/left/mouth/EE_half.png | aed096344f84cfc9 | aed096344f84cfc9 |
| views/left/mouth/M.png | 9ca185006e0de276 | 9ca185006e0de276 |
| views/left/mouth/OH.png | 238466c18eb36a36 | 238466c18eb36a36 |
| views/left/mouth/OH_half.png | 5e549ec243bd5b00 | 5e549ec243bd5b00 |
| views/left/mouth/rest.png | a53f14f690a126cd | a53f14f690a126cd |
| views/left/mouth/rig.json | 9b21401e24efa65e | 9b21401e24efa65e |
| views/left/mouth/smile.png | 61538cc9f5edc747 | 61538cc9f5edc747 |
| views/right/base.png | f9f7cd8f69e34a41 | f9f7cd8f69e34a41 |
| views/right/mouth/AA.png | dd2a0c759869a144 | dd2a0c759869a144 |
| views/right/mouth/AA_half.png | 7776087edd8c44d0 | 7776087edd8c44d0 |
| views/right/mouth/EE.png | e7a02151990e8b3c | e7a02151990e8b3c |
| views/right/mouth/EE_half.png | 0db64569bae7ca48 | 0db64569bae7ca48 |
| views/right/mouth/M.png | f707fdc95d38b62f | f707fdc95d38b62f |
| views/right/mouth/OH.png | 3cf01dc29f5eb65b | 3cf01dc29f5eb65b |
| views/right/mouth/OH_half.png | 9a92da17b9ac53b1 | 9a92da17b9ac53b1 |
| views/right/mouth/rest.png | 858c1b7b16539ca5 | 858c1b7b16539ca5 |
| views/right/mouth/rig.json | df60d836f5a7a526 | df60d836f5a7a526 |
| views/right/mouth/smile.png | 86b2096db78f190e | 86b2096db78f190e |
| views/tpose/base.png | 41f3fb9960a72064 | 41f3fb9960a72064 |
| views/tpose/mouth/AA.png | 77149a0cc17c5f86 | 77149a0cc17c5f86 |
| views/tpose/mouth/AA_half.png | e877d030ffa7133f | e877d030ffa7133f |
| views/tpose/mouth/EE.png | 7ce0af241983063e | 7ce0af241983063e |
| views/tpose/mouth/EE_half.png | 1a2a3dc538208ee1 | 1a2a3dc538208ee1 |
| views/tpose/mouth/M.png | 383da22a0c5e3694 | 383da22a0c5e3694 |
| views/tpose/mouth/OH.png | 7c6d104ad5d5fffe | 7c6d104ad5d5fffe |
| views/tpose/mouth/OH_half.png | 077da903c5b62168 | 077da903c5b62168 |
| views/tpose/mouth/anger.png | — | 2a7ae27bad08ca1c **changed/new** |
| views/tpose/mouth/rest.png | e738ad2749297b60 | e738ad2749297b60 |
| views/tpose/mouth/rig.json | 568d612e6720948d | d0fa91ecb781d0c9 **changed/new** |
| views/tpose/mouth/smile.png | 87848de35bab4fde | 87848de35bab4fde |

## Deliverables
- `anger_contact_sheet.png`: rest | M | anger for all four views at the same scale (4× view px). Profile rows show the live M fallback and the PROPOSAL.
- `anger_source_crop.png`: the source face and the mouth crop with the cut boundary.
- `summary.md` (this file), `build_report.json`, `checks.json`, `nearest_sim.json`, `proposal/`.
