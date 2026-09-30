# Handoff frames: hands check (READ-ONLY)
Mapping is Base Body's `body_tools/work/apose_turn/angle_map.json` → `handoff` (base = scale·frame + (dx,dy)):
apose f001 1.55492/86.00/−53.30, left f062 1.54135/101.91/−45.32, right f160 1.54520/100.08/−49.62, back f109 1.58301/80.36/−41.32.
All offsets are in base/view px (1365×1739) and read frame − view. Data: `handoff.json`. Crops: `handoff_<frame>_<view>_<hand>.png`, each showing view | mapped frame | frame with the view-hand outline in yellow.
Crossfade is about 80 ms, which is about 2 frames at 24 fps. The criterion I use: an offset of 8 px or less (under a finger width, about 13 px) hides inside the fade. A larger offset shows as a jump or double image.

## 1. f062 (90° left) and f160 (270° right): near-hand checks
| check | f062 (her L, near) | f160 (her R, near) |
|---|---|---|
| five fingers | NO. Edge-on: thumb knuckle plus about 2 stacked finger outlines. Same as f057/f164 | NO. Same |
| thumb side | forward (image-left = her facing direction). Correct | forward (image-right). Correct |
| pose vs f057/f164 | unchanged: fingers straight and together, thumb tucked at the knuckle | unchanged |
| blends into hip | YES. The hand lies on the buttock/hip, skin on skin, with no silhouette separation (no separable arm component in f058–f067 or f158–f167) | YES |
| far hand | hidden behind body | hidden behind body |
| faces same way as body/feet | YES. Face, toes and thumb all point image-left | YES. All point image-right |

## 2. Hand offset at the handoff frames (mapped frame vs live view at rest)
| frame → view | hand | wrist d | fingertip d | centroid d | scale (frame L / view L) | axis rot | IoU mapped / wrist-aligned | hides in 80 ms fade? |
|---|---|---|---|---|---|---|---|---|
| f001 → apose | R | (−4.3, −5.3) | (−2, −5) | (−2.1, −6.5) | 138/140 = 0.986 | +0.4° | 0.619 / 0.901 | YES |
| f001 → apose | L | (+1.4, −6.6) | (+3, −5) | (+1.6, −7.3) | 142/140 = 1.014 | −0.2° | 0.616 / 0.912 | YES |
| f109 → back | L | (−31.3, +6.4) | (−47, +3) | (−38.1, +4.3) | 146.2/141 = 1.037 | +7.9° | 0.296 / 0.570 | NO. 31–47 px outward and rotated 8° |
| f109 → back | R | (+33.4, +6.9) | (+50, 0) | (+40.5, +2.3) | 144/140.1 = 1.028 | −7.8° | 0.283 / 0.547 | NO. 33–50 px outward and rotated 8° |
| f062 → left | L (manual, ±2 px) | wrist not visible | (−4.5, −136) | – | tip-to-thumb 105 vs 44 px; front-back width 30 vs 68 px (0.44) | – | – | NO. The hand sits 136 px higher and has a different shape |
| f160 → right | R (manual, ±2 px) | wrist not visible | (+19.7, −137) | – | tip-to-thumb 106 vs 45 px; width 27 vs 69 px (0.39) | – | – | NO. Same as f062 |
f109: the arms are wider than in views/back, so the whole hand is shifted outward, rotated about 8° and about 3% longer. f062/f160: the frame's fingertips reach the buttock crease (y≈862), while the view's reach mid-thigh (y≈998). In the frame the hand is edge-on. In the view it is broad with the back of the hand to camera (4 nails visible).
f191 (315°, no live view, dropped as handoff): both hands are separate from the body, show 5 fingers, and have the thumb on the correct side. Her R L = 94 px, palm 66 px; her L is foreshortened, L = 73 px, palm 50 px (frame px).

## 3. Live views vs the turn frame at the same angle
| view | turn frame | thumb side | palm/back facing | result |
|---|---|---|---|---|
| apose | f001 | match (lateral/up for both hands) | palm to camera (creases, no nails) in both | MATCH |
| back | f109 | match (lateral) | back of hand to camera (nails) in both | MATCH (position is off, see §2) |
| left | f062 | match (forward) | view: back of hand to camera, broad, 4 nails. Frame: edge-on (width 0.44×) | MISMATCH in facing |
| right | f160 | match (forward) | view: back of hand to camera, broad, 4 nails. Frame: edge-on (width 0.39×) | MISMATCH in facing |
| tpose | none (the turn has no T-pose). Closest is f001 | view thumb sits under the horizontal hand | view hand edge-on/palm-down. f001 is palm-forward | no matching frame; differs from f001 as expected for a T-pose |
Nothing was changed. The masks still match masks.md5 (5/5).
