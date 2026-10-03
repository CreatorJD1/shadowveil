# Shadowveil mouth handoff (Base Mouth), Oct 3 2026

Plain-English status of the mouth, for whoever picks this up next. Older notes are in `mouth/HANDOFF.md`; this file supersedes them.

## Rules (from the user)
- Mouth only. Never paint or draw a new mouth over her real mouth, and never redraw her.
- Six shapes (rest, AA, EE, OH, M, smile) as separate chroma-keyed parts (#0000FF key), layer 500, parented to the head group.
- Only two controls: MouthOpen (0..1) and MouthForm (-1..1). No third control.
- Flat colour, no shadows, 1 px line art with no breaks.
- Rest must match her art exactly (0 px difference).
- Never mirror or flip her art, not even behind a flag.
- Nothing goes live without the user's OK. Every new thing gets its own OK-list line.
- Fill gaps with her Clean room art first. The Clean room anger art is approved and stays as drawn.
- Current direction: fix her main model only. The angled (diagonal) views, the benchmark sheet and the new expression shapes are parked.

## What's live
- The mouth rig in apose/tpose/left/right/back (`mouth/<view>/`, `mouth/mouth_rig.json`), driven by MouthOpen/MouthForm. Live mouth passes Coder's qa_gates in every view: 0 off-palette, 0 chroma (`qa/qa_gates/REPORT.md`).

## Waiting on the user's OK (staged, not live)
1. **Mouth tone snap** - `staged/tone_fix/`. Snaps a few off-tone mouth px back to her real lip tones. Rest stays 0 px.
2. **`?mouthfix=1`** (Coder's flag, verified by me) - `qa/mouthfix_verify/REPORT.md`. Removes doubled/flickering lip outlines during shape changes. Doubled outlines 0, flicker 0, rest 0 px with flag on or off, 1 px lines, 0 blue, flag-off output byte-identical. +-2 deg tilt moves the mouth at most 1 px. Lip seam within 1 px with `&headgroup=1`. Suggested to become the default.

## Parked (do not resume without the user asking)
- **Diagonals 045/315** - `staged/diag_posable/{045,315}/` (REPORT.md, sheet.png, rig.json). Rest = her own lips cut from f033/f191, 0 px, 0 on key blue or outside her silhouette. Frame-scale parts (768x1168) are fully clean. Open shapes are front art bent onto the diagonal lips (not drawn for that angle, ~25x10 px) behind flag `diagmouth`, off by default, each needs its own OK. View-scale rest at 045 has 21 off-palette px from bilinear resample, so the rig must draw `frame_scale/` parts with the frame transform (Coder agreed). Parent is Body's diagonal `head` piece. 135/225: no lips visible, no parts (`135_225_NONE.md`).
- `staged/diagonals/`, `staged/diagonals_snap/` - earlier diagonal attempts; `diagonals_snap` has the palette snap ("mouth diagonal palette snap" OK line).
- `staged/mesh_bend/`, `staged/mesh_split/` - mesh-format previews. Smooth mesh was dropped by the user; previews only.
- `benchmarks/` - mouth benchmark sheet, parked.

## Open issues and how to fix them
1. **Talk driver loses M.** The driver's M press lands on the rest/M tie, so M shows in only 4 of 240 frames instead of 22. Fix (Coder, rig side): push MouthForm to about -0.6 for M presses. The driver should also use posed frames during handoffs.
2. **Palette snap for mesh_bend previews.** Smooth sampling left 179 (apose) / 249 (tpose) off-palette px. Coder planned a post-render palette snap behind a flag. The mouth palette must include teeth #efe4da, tongue #9c5a4a, profile interior #3f2319, with anger on the Clean room palette. Rerun mouth qa_gates once the flag exists; test AA and OH at Open 1 during a +-2 deg tilt and the 1 px M seam.
3. **Poser (`rig/poser.html`) asks:** a drag pad for Form/Open plus fine sliders, an active-shape label plus shape buttons (anger greyed out in left/right), reset-to-rest, mouthfix default, mouth keys held (stepped) on the timeline (accepted). Check: reset gives 0 px on the mouth, and scrubbing matches playback.
4. **Body fixes at the head/neck.** If the head-neck gap fix changes the head group, recheck that rest is still 0 px and the mouth stays on her lips when she tilts. The face must stay fully weighted to the head.

## Checks to run before anything goes live
- Rest vs her art: 0 px in every view, flag on and off.
- Coder's `qa_gates.py`: 0 off-palette, 0 chroma (#0000FF), 0 soft edges.
- Line art: one unbroken 1 px line per shape.
- No opaque mouth px on key blue or outside her silhouette.
- No mirrored/flipped art anywhere.
- Served `rig/index.html` md5 matches disk before any render (mouth uses ports 8785-8789 only).

## Files to push
`mouth/push_manifest.txt` lists every mouth file to push (all exist). Folders named `renders/` are git-ignored except the real shapes in `staged/{diagonals,diagonals_snap}/{045,315}/renders/`.
