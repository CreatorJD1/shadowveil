# Base Body handoff (Oct 3 2026, 03:54 PT)

Everything here is STAGED. Nothing is live without the user's OK.
Rules: rest must be 0 px vs her art; palette only (skin apose/tpose (186,129,86), left (185,122,78), right (183,120,76), back (183,122,77));
no new shading or folds; outline within 1 px; no visible shape change; 0 overlap with the hands/eyes/mouth/hair locks.

## Status
- diag_body/{045,315}/: rigid diagonal pieces from turn frames f033/f191. Rest 0 px, 0 holes at ±25°.
  REJECTED by the user for unnatural bends (waist step, hip dent, jagged shoulders/elbows, head-neck gap). Bends stay locked.
- diag_body_fix/{045,315}/: DONE 04:28 PT, waiting on the user's verdict. Lumps and gaps are gone at the shoulders, hips, elbows and neck; the waist still turns as a block (~5 px pelvis corner) and the hips show a small sharp corner. Rest 0, holes 0. Was: Fixes for exactly those 4 defects using the same pieces and setup
  (joint caps, underlaps, pivots), plus the 045 neck key set to alpha 0. Before/after sheets will go here.
- natural_bend_proto/: smooth-mesh idea. DROPPED by the user; do not continue.
- 135/225 diagonals: paused, not started.
- crotch_candidates/: ulnb (--crotch 0, no --bgk) recommended. It reduces the notch but doesn't close it. On the user's OK list.
- handorder_wrist_trim/: fails (underlay rejected, elbow holes). Coder will draw the palm over the forearm on those wrist rows instead.
- weight_bleed/: rejected (visible shape change). Coder owns the weights fix.
- regen_staged/spot1_right_hip_armpit/v2/: rest 0, but combined ShoulderR±25 + HipR±25 leaves ~650 px open; needs a skin.json weights fix.
- hairless_division_staged/<view>/live_patch_paired_hairfront/: must go live together with Hair's new hair_front.

## Open issues and how to fix them
1. **Diagonal bends look unnatural (045/315).** Finish diag_body_fix/: shape a hidden rounded cap at each joint in her skin and line tone,
   move pivots to the true joint centres, and widen the underlap flaps so the outline stays continuous at ±25°. Set the 045 neck key to alpha 0.
   Accept only if the before/after sheet shows no step, dent or gap at the waist, hips, shoulders, elbows and neck, and rest stays 0 px.
2. **Crotch notch** (live, apose/tpose wide stance). Take ulnb; it's on the user's OK list. Closing the rest of the notch needs a hidden inner-thigh
   underlap drawn in her skin and line tone, under the pelvis, 0 px at rest.
3. **Spot-1 right armpit/hip.** The combined shoulder + hip bend opens ~650 px under the f11 palm (rest-space x656–704, y844–871). Fix it in rig skin.json weights
   (Coder). Don't grant a lock exception against Hands' wrist flap.
4. **Profile forearm/hip weight bleed** (left 9, right 21 vertices at the elbow over the torso). Coder needs a weights fix that keeps her shape.
   The zero-cross-limb option was rejected because vertices moved up to 31 px.
5. **Handorder wrist rows.** Coder draws the palm over the forearm on those rows only. Don't trim the body skin.
6. **Hair ear masks** (left/right/back). The live patch in live_patch_paired_hairfront/ must ship together with Hair's hair_front, never alone.
7. **135/225 diagonals.** Not started. Use the 045/315 method only after item 1 is approved.

## Checks to run before anything goes live
- The served rig/index.html md5 must be 562c32a7. Load from files or use ports 8770–8774, never 8765/8766.
- Rest diff 0 px in all 5 views, both with ?hairless=1 and without.
- Run rig/qa_gates.py (see rig/work/qa_gates/README.md): 0 off-palette, 0 chroma, 0 weight bleed, hand/foot scale unchanged.
- Lock overlap 0: eye lock, mouth lock, hair masks, hands/<view>_hand_erase_mask.png, and the wrist flaps f7/f10/f11/f12.
- Pose extremes ±25° on every joint: 0 holes, and the outline continuous within 1 px.
- Every fix needs a before/after sheet with a crop from her master sheet, and the user's OK.
