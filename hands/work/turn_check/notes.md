# apose-turn hand check (READ-ONLY measure)

Source: reference/grok_build/public/clean-room/videos/apose-turn.mp4 (commit 0596d8a), measured on the team's pre-extracted
frames reference/apose_turn/frames/f001–f241.png (768×1168). f001 is pixel-identical to decoded video frame 0 (mean/max diff 0/0).
24 fps, 241 frames = 10.04 s. Nothing under views/*/hands/, any rig.json or the masks was touched. Frame numbers are fNNN.

## 1. Rotation angle
- Estimated from silhouette width (theta.py → theta.json; widths in silhouette.json). Profiles (width minima) at f057 and f164, back at f109.
- Cross-check from the wrist-to-wrist x separation, cos θ = Δx/Δx(f001) (Δx f001 = 510.2 px), where both hands are separable.
  The two agree within 2 frames at every 45° mark.
- The turn is not constant-speed: 0→90 over f001–f057 (56 frames), 90→180 f057–f109 (52), 180→270 f109–f164 (55), 270→360 f164–f235 (71).
  The end eases out: f221 is 353.8° by width and 0° by hand separation. f235–f241 are 360°.
- Her height (silhouette) is 1034–1068 px across the turn (f109 1034, f057 1068).

## 2. Angle frames: hands, size, verdict
"fingers vis" is my visual count on 3× crops. "auto tips" is contour fingertip peaks and undercounts when fingers overlap in 3/4 views.
L = wrist cut to the farthest fingertip along the forearm axis. palm = wrist to the finger-web valleys. pw = knuckle-level palm width without the thumb. All in source px.
Thumb OK = thumb bulge on the anatomically correct side for that hand and view (palm-forward A-pose: thumb lateral).

| target | frame (silhouette) | frame (hand-sep check) | est θ | H px | her R: fingers vis / auto tips, L, palm, palm_w (px), thumb | her L: same | verdict |
|---|---|---|---|---|---|---|---|
| 0° | f001 | f001 | 0.0 | 1056 | 5 / 5, L 93, palm 54, pw 38, thumb OK | 5 / 5, L 93, palm 55, pw 38, thumb OK | CLEAN both (front, not 3/4) |
| 45° | f035 | f037 | 44.3 | 1066 | 5 / 3, L 73, palm 58, pw 29, thumb OK | 5 / 4, L 95, palm 63, pw 37, thumb OK | CLEAN both (R foreshortened: L 73 px vs 95) |
| 90° | f057 | - | 90.0 | 1068 | hidden / not measurable | thumb + ~2 stacked finger outlines / not measurable | FLAGGED: near L lies on hip/buttock, same skin tone, not separable from body silhouette; far R occluded |
| 135° | f086 | f084 | 135.6 | 1048 | 5 / 3, L 61, palm 49, pw 26, thumb OK | 5 / 3, L 96, palm 61, pw 38, thumb OK | CLEAN both (R foreshortened: L 61 px) |
| 180° | f109 | f109 | 180.0 | 1034 | 5 / 5, L 92, palm 52, pw 33, thumb OK | 5 / 5, L 94, palm 57, pw 38, thumb OK | CLEAN both (back, not 3/4) |
| 225° | f133 | f135 | 224.5 | 1046 | 5 / 5, L 98, palm 63, pw 41, thumb OK | 5 / 4, L 65, palm 54, pw 22, thumb OK | CLEAN both (L foreshortened: L 65 px) |
| 270° | f164 | - | 270.0 | 1062 | thumb + ~2 stacked finger outlines / not measurable | hidden / not measurable | FLAGGED: near R lies on hip/thigh, not separable; far L occluded |
| 315° | f189 | f187 | 314.8 | 1064 | 5 / 4, L 91, palm 64, pw 30, thumb OK | 5 / 2, L 69, palm 50, pw 30, thumb OK | CLEAN both (L foreshortened: L 69 px) |

Palm length (hand size) in px at the angle frames: f001 R54/L55, f035 R58/L63, f057 n/a, f086 R49/L61, f109 R52/L57, f133 R63/L54, f164 n/a, f189 R64/L50.
In foreshortened 3/4 hands the web valleys merge, so the palm number there comes out a larger share of L (e.g. f035 R palm 58 of L 73). Use L plus the crop for 3/4 cuts.

## 3. Sweep, every 5 frames (all 241 frames measured: sweep2.json / sweep2.txt; sheets turn_sweep_a.png, turn_sweep_b.png)
- Finger appearance/disappearance: none unexplained. Fingers only drop out when they overlap in 3/4 or the hand is foreshortened (f031–f046 R, f076–f091 R, f126–f146 L, f176–f196 L). Each time the count comes back smoothly as the hand turns back.
- Profile passes: the far hand is hidden behind the body at f058–f067 (R) and around f161–f167 (L). The near hand crosses the hip in projection: f052 at the back edge of the hip, f058–f061 on the buttock, f064 at the front hip, f067 clear in front. This is continuous and matches the projection (x = a·cosθ + d·sinθ). No pop.
- Thumb side: correct in every frame where the bulge is measurable. Indeterminate at f051, f071, f146, f171–f176, where the thumb is edge-on. One flagged mismatch (f171 her L) is a bad wrist cut (L 131 px, forearm included), not art.
- Pose change during the turn: none measured. Front frames (θ≤20 or ≥340, n=54 per hand): fingertip fan 54–60° (median L 56.7, R 56.6), finger/L 0.39–0.45. Back (160–200°, n≈20): fan 50–60°, finger/L 0.38–0.47. The hands stay open and flat the whole way; no curl or spread change beyond measurement noise.
  (Our apose composite on the same metric: fan L 50.8° / R 50.2°, finger/L 0.421 / 0.433. Back: 52.1 / 53.2°, 0.443 / 0.433. So the video fan is about 6° wider than our apose at the front.)
- Loop: f241 vs f001 wrists within 1.5 px, fingertips within 2 px.

## Size ratios (normalised to her height in that frame; ours normalised to base.png height 1643/1642)
Same measurement code (handgeo.py) on the video hands and on our rest composites (all L_/R_ parts OR'd, rig pivot → Middle1 axis).
| | video median (range) | ours | video/ours |
|---|---|---|---|
| front L hand length L/H | 0.0871 (0.0782–0.0906) | apose 0.0946 | 0.921 |
| front R L/H | 0.0876 (0.0802–0.0915) | apose 0.0945 | 0.926 |
| front L palm/H | 0.0493 | apose 0.0548 | 0.900 |
| front R palm/H | 0.0511 | apose 0.0536 | 0.953 |
| front L palm_w/H | 0.0360 | apose 0.0366 | 0.983 |
| front R palm_w/H | 0.0348 | apose 0.0370 | 0.940 |
| front L finger/H | 0.0364 | apose 0.0398 | 0.915 |
| front R finger/H | 0.0364 | apose 0.0409 | 0.891 |
| back L L/H | 0.0901 | back 0.0887 | 1.017 |
| back R L/H | 0.0898 | back 0.0884 | 1.016 |
| back L palm/H | 0.0530 | back 0.0494 | 1.073 |
| back R palm/H | 0.0501 | back 0.0501 | 1.001 |
| back L palm_w/H | 0.0367 | back 0.0368 | 0.996 |
| back R palm_w/H | 0.0390 | back 0.0368 | 1.058 |
| back L finger/H | 0.0370 | back 0.0393 | 0.941 |
| back R finger/H | 0.0403 | back 0.0383 | 1.052 |
Profile: ours left_L L/H 0.0913, right_R 0.0906 (rig palm pivot→Middle1 0.0472 / 0.0450). The video profile hands (f057, f164) can't be separated from the body silhouette, so there is no video number.
In pixels: at f001 the video hand is 93 px (L) with a 54–55 px palm at H 1056. Our apose L 155.4 px scaled by 1056/1643 is 99.9 px.
Caveat: the video wrist is the distal end of the narrow wrist plateau on the silhouette, while ours is the rig pivot. That is a different landmark, and it can shift L and palm by a few px.

## 4. Grok rig l-hand.png / r-hand.png vs our apose rest composite
The Grok rig uses the same apose.png canvas as ours (1365×1739, figure y40–1682). Grok "l-hand" is the image-left hand (her R), paired with our R_. "r-hand" is paired with our L_.
The Grok wrist pivots are (255,760) and (1110,760). Ours are R(295,706.5) and L(1068,706.5). The Grok pivot sits 66.8 / 68.0 px further down the arm.
The Grok hand parts (99–100×114) hold only the distal hand: fingers plus the outer half of the palm with a round pivot cap. The thumb is cut off except a detached tip fragment (335 / 327 px component). Our composites are 8430 / 8467 px; Grok's are 4838 / 4909 px.
| pair | alignment | IoU | max edge offset | p95 | mean |
|---|---|---|---|---|---|
| our L vs r-hand | pivots aligned (shift −42, −53.5) | 0.336 | 67.8 px | 53.7 | 18.7 |
| our R vs l-hand | pivots aligned (shift +40, −53.5) | 0.346 | 66.4 px | 52.2 | 18.5 |
| our L vs r-hand | as placed in the shared canvas | 0.515 | 58.7 px | 40.1 | 5.5 |
| our R vs l-hand | as placed | 0.522 | 57.9 px | 39.2 | 5.4 |
As placed, 93.2% / 93.4% of the Grok hand pixels fall inside our composite. 88.6% / 88.1% of the Grok outline is within 1 px of our outline, meaning the same base-art pixels. The max offsets come from our proximal palm and thumb, which Grok puts in its forearm.
Pivot-aligned max offsets are at the fingertips (ours (1169,825) / (193,824)) and at the Grok detached thumb fragment. Overlay: outline_overlay.png (grey both, red ours only, blue Grok only, green our pivot).

## Files
turn_hands_sheet.png (angle frames, both hands 3×), turn_sweep_a.png / turn_sweep_b.png (every 5 frames), outline_overlay.png,
sweep2.json, sweep2.txt, theta.json, silhouette.json, ours3.json, ratios.json, outline_match.json; scripts theta.py, locate.py, arm2.py, handgeo.py, shape.py, sweep2.py, sheet.py, ours3.py, outline.py.
