# Grok build 0596d8a puppet/export clips vs our body limits (read-only check, 2026-09-30)

Our limits: BodyLean 8°, Shoulder/Elbow/Hip/Knee/Ankle 25°. Mapping (their → ours): hinge → BodyLean; l* → our *R, r* → our *L (their l-eye is amber and sits on the viewer's left, i.e. her right); torso, neck and head → no equivalent; Wrist → WristL/R (Hands, 25°).
"Over our limits" lists frame index:value. All other joints stay within our limits.

| Clip (frames) | Joints that move: their range → our param | Over our limits (frame: peak) | Verdict |
|---|---|---|---|
| idle (108) | none; all joints 0 (eyes blink and gaze only) | – | fits |
| look (108) | none; all joints 0 (the turn is a view yaw) | – | fits (the turn is a view switch) |
| wave (12) | rShoulder 0…95.5 → ShoulderL; rElbow −34.8…0 → ElbowL; neck −7.9 / head 7.9 (none) | ShoulderL f2–10, peak 95.5 @f8; ElbowL f6–7, −34.8 @f6 | needs new art (arm raised above the shoulder); clamping leaves no wave |
| reach (12) | hinge 0…12 → BodyLean; lSh −80…0 → ShoulderR; rSh 0…70 → ShoulderL; elbows 20/−24; hips 8/−12; knees −10/8; torso −6, neck −10, head 6 (none) | BodyLean f3–9, 12.0 @f5–7; ShoulderR f2–10, −80 @f5–7; ShoulderL f2–10, 70 @f5–7 | fits after clamping only as a small gesture; a full reach needs new art |
| twist (12) | hinge 0…28 → BodyLean; shoulders 40/50; elbows 18/−10; hips −8/16; knees −12/10; torso 22, neck −24, head −12 (none) | BodyLean f2–10, 28 @f5–7; ShoulderR f3–9, 40; ShoulderL f3–9, 50 | needs a new param: it is authored as in-plane rotations, and we have no yaw or twist. Clamped, it reads as a lean |
| hinge (12) | hinge 0…87.6; lSh 49.3 / rSh −47.2; lEl 69.3 / rEl −63.3; lHip 27.8 / rHip 21.7; lKnee −39.5 / rKnee 35.5; torso 13.9, neck 27.8, head −8…9.6 (none) | BodyLean f1–11, 87.6 @f7; ShoulderR/L f6–8, 49.3/−47.2 @f7; ElbowR/L f3–10, 69.3/−63.3 @f7; HipR f7, 27.8; KneeR f6–8, −39.5; KneeL f7–8, 35.5 | needs new art (a waist fold of about 88°) |
| collapse (12) | hinge 0…88; lSh 50 / rSh −48; lEl 70 / rEl −64; lHip 28 / rHip 22; lKnee −40 / rKnee 36; torso 14, neck 28, head 10 (none) | BodyLean f1–11, 88 @f5–7; ShoulderR/L f3–9, 50/−48; ElbowR/L f2–10, 70/−64; HipR f4–8, 28; KneeR f3–9, −40; KneeL f3–9, 36 | needs new art or new poses; limits can't cover it |

Notes
1. Units are degrees, relative to the parent (Rig.tsx nests CSS rotate() and sums parentWorld). Positive is clockwise on screen, the same as our canvas rotate(). Rest is 0 on every joint, which is their A-pose bind (clean-room/rig/apose.json), so values carry over 1:1 in degrees after the L/R swap. Their A-pose pivots and arm angles differ from ours, so the poses only match approximately.
2. No equivalent: `torso` rotates the whole figure (their hips are children of torso), and our pelvis root is fixed, so only a stage-level transform could do it. There is no neck param, and our head is rigid (100% head). Twist and yaw don't exist here; `look`'s turn is a view change. The wrists are 0 in every clip.
3. Clips that fit or can be clamped usefully: idle and look (no joint motion), and reach and twist as small, clamped gestures. wave, hinge, collapse and a full reach are beyond what the rig can do (raised arm above the shoulder, a waist fold of about 88°, knees at 36–40°); raising the limits wouldn't fix them, they need new art.
4. Limit raises worth considering for natural motion: BodyLean 8→12° (reach), ElbowL/R 25→35° (wave), HipL/R 25→28°, KneeL/R 25→35° (small crouches).
5. Before raising any limit, run the v1.5.1 joint test at the new angle in all five views, in nearest, linear and ss2. It needs 0 new holes, no more tears than today, 0 dark seam px inside the body (the ElbowR ±25 check at the new elbow angle), and outline width near 100%. Rest must stay 0 px, and check_underlay, check_body_rest and check_skin_rules must pass. BodyLean 12° also needs the hair and hand attachment and the waist/armpit silhouette checked; knee 35° needs a knee blend review (the knee has no underlay).
