# Hands handoff (Base Hands), Oct 3 2026

The hands are the palm, Index/Middle/Ring/Pinky segments 1-3, and Thumb 1-3 on their own pivot, for each hand and view. They're chroma-keyed on #0000FF, flat colour, and cut only from her art (no redraws, no mirroring).
Everything below is STAGED, not live, and needs the user's OK. Live rig: rig/index.html @ 562c32a7.

## Staged fixes (all pass: rest 0 px, 0 #0000FF, 0 off-palette)
- staged/f5_lineart/v2_ring_width/: line-art width fix (back Ring1). Install steps are in its README. Replaces v1.
- staged/f7_wrist_apose, f10_wrist_tpose, f11_wrist_profile_back/<view>: hidden wrist flaps that close wrist gaps when the wrist bends. They need ?handorder=1 (patch: f10_wrist_tpose/scratch_rig_patch.diff). These are one OK-list item together with handorder.
- staged/f8_diagonals/<45|135|225|315>/: hands cut from the turn frames f033/f087/f131/f191. They come in view scale and frame_scale/, with rig.json. The 315 L 4 px of line ink are restored in her exact colours. The palm width at 135 L, 225 L/R and 315 L is still off by 1.5-2 px.
- staged/f12_wrist_diag/<45|315>/: wrist flaps for the diagonals. rig.json = F8 parts + flaps. They close the gap at +/-25 deg, with a 2-6 px notch at the outline corners (accepted). Diagonal work is PAUSED by the user.

## Reports
- qa/scale_audit/REPORT.md: rest matches her views exactly. The generated turned hands are about +33 px long on the far side (the 1.64x fit).
- qa/gates/REPORT.md: all hand sets show 0 chroma and 0 off-palette.

## Open issues and how to fix them
1. **A-pose fist is flat inside, with a lump at the index-thumb join.** Fix: retune maxCurlDeg per joint in the A-pose hand rig and the joint-cap size at Index1/Thumb2. Use the finger-to-chin pose on her expression sheet as the curl style guide. Gate: rest 0 px, no holes at full curl.
2. **T-pose ring and pinky hide behind the index.** Fix: raise the Ring and Pinky draw layers above Index during curl only, or add a small spread offset. Keep rest identical.
3. **Profile thumbs only rotate.** Fix: give Thumb1-3 in left and right their own pivots and curl limits, cut from her profile art. Don't mirror one side for the other.
4. **Claw pose and thumb-wrapped fist can't be reached.** Fix: add separate curl values for joints 2 and 3 (claw), and a thumb cross-over layer (wrapped fist). Details are in work/clip_gestures.md.
5. **Generated turned hands are about +33 px long on the far side.** Fix: apply the 1.64x fit to near-side hands only, or turn off the generated turned hands. This is on the user's OK list.
6. **Diagonal palm width at 135 L, 225 L/R and 315 L is 1.5-2 px off.** Diagonals are paused, so revisit only if the user restarts them.
7. **F6 finger-joint flaps** are parked until the rig has a mesh format.

## Rules and checks before anything goes live
- Never mirror or flip her art. Never regenerate hand art, and never replace the PNGs in tools/hand-art or rig/hand_angles.
- Rest must be 0 px against her views. Use 0 #0000FF and 0 off-palette, where every colour must exist in her art for that part and view. Line width stays within about 1 px of rest. No weight bleed.
- Her five base views are the scale truth. The master sheet is reference only.
- Before rendering, check that the served rig/index.html md5 matches the file on disk. Run python3 rig/qa_gates.py and hands/qa/gates/gates_extra.py.
- Known qa_gates bugs: the '045' key skips 45_*.png, and staged lookup can't find flat layouts.
