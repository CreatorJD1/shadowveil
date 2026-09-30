# Idle render body checks (measure-only), 03:20 PT
Renders: `rig/previews/idle/frames/keys_idle_<clip>_<view>/frames/f0000–f0239.png` (Coder, 30 fps, 8 s, keys from the old idle_clips.json). Frame numbers below are fNNN of those folders.
Data: `<name>.check.json` (per frame), `final_summary.json`, `<name>.holes.json` (right view), `flicker_*.json`. Scripts: `idle_check.py`, `final_summary.py`, `holes.py`, `flicker.py`. Nothing in views/ or rig/ was modified.
Classification: patches within 110 px beyond a posed wrist count as hand. Patches at y<320 are moving hair/head, because the hair mask comes from rest. Tears = cracks that a 3 px closing seals.

## 1. Right view: the "far forearm" hole (priority)
- **Clip / frames:** `idle_arm_settle`, right view, f163–f174 (5.43–5.80 s). One enclosed hole per frame, 46 → 164 → 261 → 343 → 392 → **415 px (f168)** → 413 (f169) → 384 → 310 → 231 → 132 → 27 px (f174).
  - Position: bbox x688–706, y599–647 (elbow height, torso back contour behind the near arm).
  - f169, flagged by Hands, is this same hole (413 px).
  - Crop: `arm_f168.png`.
- **It is not the far forearm.** forearm_L barely moves (world −3°). The near arm (ShoulderR world −22.5°, forearm_R −32° at f168) swings forward. Coder's QA assigned the hole to forearm_L only because forearm_L's pivot (648,638) is the nearest pivot.
- **Cause: skin weights, with the underlay as a secondary factor. Missing far-limb art is not a factor.**
  - At rest, torso.png owns all 931 px of the box.
  - The torso-group (220) vertices there carry blurred upperArm_R weight: 0.42 at x688, 0.27 at x692, 0.18 at x696, 0.11 at x700, 0.06 at x704, 0.01 at x712.
  - At −22.5° those vertices are dragged up to about 30 px forward, which empties the band. The drag also shows as a torn dark contour line (new interior navy px up to 44 at f168).
  - The underlay covers only 177/931 px of the box, stopping at about x692.
- **Proposed fix (not applied):**
  - **(a) Primary.** In build_skin for profile views, zero upperArm_R/forearm_R weight on torso-group (220) vertices below the armpit (y > ~520) and more than ~4 px from the arm/torso seam. Shoulder cap weights stay as approved.
  - **(b) Backup.** Extend the torso-hosted underlay under the near arm to x≤714 for y560–700 (e.g. `--parts-bg upperArm_R:*:24` or an explicit torso band).
  - Then run rest_check, check_underlay and check_body_rest, and re-render arm_settle right f150–f180.
- **Same seam in the left view, much smaller.** arm_settle left shows 20–31 px open cracks (not enclosed) at x586–595, y721–789 (f063, f068, f079). Same fix, mirrored.

## 2. Right view: hip slit (idle_weight_shift, and Coder's own idle)
- A 1–3 px wide crack, x695–698 × y775–801. It reaches **48 px** at f169, f191 and f192 and appears in most frames where thigh_R ≤ −4°.
- **Cause: split seam in the skin mesh.** Group 250 (near forearm, 100% forearm_R) and the hip groups 242/246 (thigh_R 0.5–0.76, pelvis rest) don't share vertices: there are 187 duplicate-position vertex pairs at y710–858. The hip side rotates with thigh_R (−4.5° to −7°) while the forearm stays still. The underlay behind the seam is half thigh_R-hosted (157 of 330 verts), so it moves away too.
- **Proposed fix:** a static, pelvis-hosted underlay strip of about 6–8 px along the forearm_R back edge over the hip (y710–858), or rehost that strip to the pelvis. Then rest_check and a re-render of weight_shift right.
- Left view, same type: 10 px at x667, y766–775, f122.

## 3. Wrists (apose "f71/f182", which Hands says are really the tpose crops, plus all tpose)
- apose arm_settle f071 and weight_shift f182: no body defects at the wrists. The only flagged pixels are between the fingers.
- tpose arm_settle f071 and weight_shift f182: forearm and wrist joins are clean. Every flagged patch is 60–110 px past the wrist, in the knuckles and fingers (Hands' compounded tpose curl). The tpose ×0.32 finger override addresses it.
- No body holes or tears at any wrist in any tpose frame.

## 4. Per view, worst frames (body only, hands and hair excluded)
| clip | view | body holes (px @ frame) | body tears | new interior navy | foot |
|---|---|---|---|---|---|
| arm_settle | right | **415 @f168** (hole §1) | 44 @f163 (fingers of the moved hand over the thigh, x769) | 44 @f168 | 0 |
| arm_settle | left | 2 @f098 | 31 @f063 (arm/torso seam) | 11 | 0 |
| arm_settle | apose / tpose / back | 0 | ≤4 (2 px AA speck at the neck, 771,255) | ≤14 @f168 apose | 0 |
| weight_shift | right | **48 @f169/f191/f192** (hip slit §2) | 34 @f041 (hair edge) | ≤0 | lift 6 px @f178 |
| weight_shift | left | 10 @f122 (hip seam) | hair only | ≤0 | lift 3 px @f159; the 13 px "dx" at f127 is a heel/toe lowest-row swap, ankle fixed |
| weight_shift | apose / tpose / back | hair only (y<320) | hair only | ≤22 @f187 apose | **lift 15 px @f179 apose, 15 @f177 tpose, 14 @f176 back** (pelvis root, 12° peak) |
| breathe | all | ≤4 px specks (left 730,710) | ≤16 (hair) | ≤3 | 0 |

- **Foot line:** at rest, frames sit on y1682 (apose) and y1681 (left, right, back). tpose has one extra anti-aliased row (1683). Foot slide at the ankle is ≤1 px everywhere, because the planted solve keeps the ankle x.

## 5. Head sharp-to-soft flicker
- Toggle frames (body params come from the clip keys, so the frames are the same in every view):
  - **arm_settle:** f049, f070, f142, f163–f167.
  - **breathe:** f000–f003, f042, f104–f106, f119–f121, f239.
  - **weight_shift:** none.
- **It reaches the neck and the shoulders.** Measured on arm_settle right and breathe apose, sharpness relative to rest:
  - Axis-aligned frames: head 0.99–1.00, neck exactly 1.00, shoulder band 0.97–1.00.
  - Neighbouring frames: head 0.87–0.95, neck 0.95–0.97, shoulders 0.88–0.95.
  - The shoulder step is up to 12% (breathe apose f040 → f042).
- The trigger is BodyLean crossing exactly 0, which renders the whole torso chain unresampled for that frame. So it's not head-only. The render side (Coder) should resample consistently.

## 6. Naturalness read
- **arm_settle:** the arms move smoothly with follow-through. In the right view, f160–f175 shows the torso back contour dragging forward with the near arm, plus the hole. Behind the swung arm, the flat underlay's bra/brief bands show as flat blocks, so the fill is visible.
- **weight_shift:** reads fine except the 12° peak at about 5.9–6.1 s, where both feet float 14–15 px in front/back (known pelvis-root limitation).
- **breathe:** subtle and clean. The flicker frames are the most visible artefact.
