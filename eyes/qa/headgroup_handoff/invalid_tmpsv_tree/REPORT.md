# Eye handoff offsets with the staged head group (Base Eyes, Fri Oct 2 2026, ~11:50 PM PT)

Read-only QA. Nothing outside `eyes/qa/headgroup_handoff/` was written except the registry entry (`status/update.py register`).
Captures: headless Chrome (one instance, exited) on `rig/?view=<v>&quality=linear[&headgroup=1]`, `RigHeadGroup.applyHandoff(view)`, all params at default, FR canvas (`caps/`).
Frames warped into view px with Body's `angle_map.json` handoff (same as Mouth). Residual = turn frame minus rig render with the head group on, view px (+x right, +y down).
Sanity check: the head-group render's eyes sit at exactly live + head offset (NCC 1.0), so the rig applies the group to the eyes correctly.

Methods (scripts/measure.py, opening.py):
- iris: iris colour inside the eye opening under the lash band (green: a* below skin; amber: hue yellower than skin), same rule for rig and frame (rig mask checked against the iris part: within 2 px)
- lash band: centroid of the near-black upper-lash band, plus its corners
- upper-lash chamfer (symmetric, truncated), all-lid chamfer, lid-edge profile
- masked luminance NCC of the eye
- nearest cheek mole as a face landmark

| eye | head offset | iris | lash band | lash chamfer | NCC | best (mean of iris, band, NCC) | Mouth face residual |
|---|---|---|---|---|---|---|---|
| apose f001 EyeR (amber) | (0,-10) | (+1.2,-0.1) | (-0.1,+0.8) | (+1,+1) | (0,+1) | **(+0.4,+0.6)** | (0,+1) |
| apose f001 EyeL (green) | (0,-10) | (+0.3,+1.0) | (+0.5,+0.6) | (-1,+1) | (0,+1) | **(+0.3,+0.8)** | (0,+1) |
| left f062 EyeL (green) | (-2,+1) | (+3.9,+9.9) | (-0.1,+10.2) | (+7,+9) | (+1,+10) | **(+1.6,+10.0)** | (+8,+11) |
| right f160 EyeR (amber) | (+5,-6) | (-4.0,+10.5) | (-0.9,+11.7) | (-1,+12) | (0,+12) | **(-1.7,+11.4)** | (-7,+11) |

Profile eye shape: the frame eye is shorter than the rig's (0.71 left, 0.75 right). Both corners move toward the middle (left: front +4, back -5; right: front -4, back +5), so the eye's centre stays nearly fixed in x.
Cheek mole: left (-11,+8), right (+5,+12). These are forward, not back. apose EyeR (-2.5,+0.5); apose EyeL is ambiguous because of the mole cluster.

## Reading
- **apose: PASS.** Both eyes are at (0..+1, +1), the same as the mouth.
- **Vertical (profiles): whole-face.** The eyes are +10 (left) and +11..12 (right) low, which matches Mouth's +11 within about 1 px.
- **Horizontal (profiles): eye-specific, not whole-face.**
  - The mouth, nose and chin are 7-8 px back. The eyes are only 0-4 px back: the eye centre is about 0..-1 and the iris about 4 px back.
  - The moles move forward.
  - Eye minus mouth is dx -6.4 (left) and +5.3 (right).
  - So the video's profile face is foreshortened, not rigidly shifted.
- **For Coder:**
  - Mouth's face-basis head offsets (left ≈ (+6,+11), right ≈ (-3,+5)) would fix the eyes' dy but put the eyes 5-6 px too far back.
  - Eye-only residuals after the head group: apose (0,+1), left (+2,+10), right (-2,+11).
  - Eye totals vs live: apose (0,-9), left (0,+11), right (+3,+5).
- Caveats:
  - The frame profile eyes are about 22-27 px wide and soft, so expect ±1-2 px.
  - The right frame has hair strands crossing the eye, and one strand is merged into the frame's lash-band blob (about 1 px bias in x).
  - The amber colour-only centroid locked onto the yellow key fringe at the right silhouette and was rejected.
  - The pupil dark-core estimate was noisy and was rejected (both are kept in report.json under `rejected`).

Files: `sheet.png` (registered: eyes reports 'Eye handoff offsets with head group'), `report.json`, `work/measure_raw.json`, `scripts/`, `caps/`.
