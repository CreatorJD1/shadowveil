# Grok build clips: hand gestures vs our curl frames (read-only survey, 2026-09-30 PT)

Source: `reference/grok_build/public/clean-room/videos/*.mp4` (39 clips, 768x1168, h264 yuv420p, 24 fps, 145 frames = 6.04 s; idle-long and walk are 241 frames = 10.04 s).
Note: the mp4s are h264 4:2:0 (lossy), not truly lossless, but they have no key fringe; all numbers come from them. 1 frame = 41.7 ms.
L/R below = her side (her L = image right in front views). Frame ranges from 1-frame dense strips unless marked "±3" (6-frame sheets).

## Method
- Hands located with MediaPipe HandLandmarker (tiled 2x crops + tracking), crops checked by eye on sheets.
- Spread = PCA axis of each finger's silhouette (hand silhouette minus a morphological opening), open hands against the blue key only (`fingers.py`, `spread.py`). Same PCA on our rest parts.
- Wave period = oscillation of the index-finger axis angle per frame (`wave_t.py`).
- MediaPipe 3D joint angles were NOT used: on clearly straight fingers (stop f0-77) they read 50-80 deg total curl, so they are too noisy for this art. Per-joint curl angles of fists cannot be measured in 2D (joints are hidden); fist curl is reported as a state (fingertips hidden in the palm).

## Clips with visible finger pose change or held gesture (measured)
| clip | hand | sequence (frames) | timing |
|---|---|---|---|
| wave | L | open waving f0-89 -> curl f89-93 -> curled f93-97 -> uncurl f98-102 -> relaxed hang f103+ | wave period 11.1 fr = 462 ms (troughs f13.5, 25.5, 36.5, 47.5, 58.5, 69, 80); ~8 cycles; index axis swings 49 deg peak-to-peak (-66..-115 deg image angle, includes forearm); curl 4 fr/167 ms, hold 5 fr/208 ms, uncurl 4-5 fr/~188 ms; fingers stay open & spread during the wave |
| wave | R | flat on hip f0-99 -> off hip f100-105 -> hang | 6 fr/250 ms |
| point | L | point (index straight, 3 fingers fisted, thumb over them) held still f0-50, arm lowers still pointing f51-63, release f64-71, relaxed f72+ | hold 51 fr/2125 ms static (64 fr/2667 ms total pose); release 8 fr/333 ms |
| point | R | flat on belly f0-56, leaves f58-76 (±1) | ~18 fr/750 ms |
| stop | both | open + spread held f0-86, fingers close f87-89, hands turn/lower f90-103, hang | hold 87 fr/3625 ms; close 3 fr/125 ms; lower 14 fr/583 ms |
| inspect | R | claw (palm up, fingers bent up) f0-12, uncurl+rotate f14-30, soft half-curl f32-94, curl f96-110, curled f110-120, release/drop f122-128, hang | 13 fr/542 ms; 16 fr/667 ms; 63 fr/2625 ms; 14 fr/583 ms; 11 fr/458 ms; 6 fr/250 ms |
| angry | both | fist whole clip f0-144 | 145 fr/6042 ms, no uncurl |
| ready | both | fist whole clip f0-144 | 145 fr/6042 ms |
| run | both | fists throughout while pumping arms | whole clip |
| shrug | both | open palms, spread, whole clip (hands move with the shrug, fingers do not change) | whole clip |
| startle | both (±3) | hang -> rise f12-24 -> claw at chest f30-60 -> lower f66-78 -> hang | ~12 fr rise, ~30 fr hold, ~12 fr lower |
| hem | both (±3) | fingers gripping the hem f0-72 -> release/lower f78-102 -> hang | hold ~72 fr/3 s |
| hip | L (±3) | hand flat on hip f0-96 -> off f96-102 -> hang | |
| strap | R (±3) | pinching strap f0-54 -> lower f60-72 -> hang | |
| clasp | both | hands clasped at the belly whole clip, re-grip f30-48 (±3) | |
| brace | both | arms crossed over face f12-84 (hands not trackable), loose curl at sides f102+ (±3) | |
| dodge | both | open hands during the stretch (f24-48 L); spread not measurable (1 valid frame of 26) | |

Hands at sides/relaxed, no finger change seen at 6-frame (idle-long/walk 10-frame) sampling: idle, idle-long, gasp, sad, look, nod, talk, sway, back, side, walk (arm swing, fingers relaxed), jump, kick, squat, kneel, getup, stumble, sit.
Not trackable (hands on face/head or arms crossed): cheeks, yawn, worry, glare, smirk, tongue (hands on hips, static in strips).

## Spread limits (measured, deg, open hands against blue)
| clip/hand | index-pinky median / max | thumb-index median / max | adjacent max (I-M, M-R, R-P) | valid frames |
|---|---|---|---|---|
| stop R | 38 / 40 | 35 / 37 | 15, 10, 17 | 87/88 |
| stop L | 39 / 43 | 35 / 37 | 18, 10, 18 | 87/88 |
| wave L | 21 / 25 | 25 / 33 | 13, 8, 14 | 75/90 |
| shrug R | 24 / 31 | 30 / 36 | 12, 9, 14 | 65/145 |
| shrug L | 26 / 32 | 33 / 39 | 12, 7, 14 | 72/145 |
Largest seen: index-pinky 43, thumb-index 39, index-middle 18, middle-ring 10, ring-pinky 18.

## Curl limits (measured as states)
- Full fist, fingertips hidden in the palm, thumb across the fingers: angry (both, f0-144), ready (both, f0-144), run, point (3 fingers + thumb, f0-63), inspect f110-120, wave f93-97.
- Claw (MCP near straight, PIP/DIP bent, palm up): inspect f0-12; startle f30-60 (±3).
- Largest curl = full fist. No per-joint angles are claimed (see Method).

## Ours (rig.json, read only)
- apose: v3 drawn frames, f0 rest, f1 = curl 0.5, f2 = curl 1 with FLEX 85/100/65 deg (MCP/PIP/DIP) drawn toward the viewer, plus a 12/8/6 deg lean. Thumb 5/60/25. Layers 320-335 (L), pivots as in rig.json.
- tpose: v2 in-plane frames, curl by rotation 90/95/15 deg (maxCurlDeg), thumb -5/-20/-25. Layers 320-335.
- Renderer check sheets (check_apose.png, check_tpose.png): Fist at curl 1 closes to a full fist in both views (fingertips folded to the palm); Point = index f0 + other three f2.
- Our rest fan (PCA of rest parts): apose index-pinky 19.5, adjacent 7.8/3.1/8.6, thumb-index 30.1; tpose (side view) index-pinky 2.9, thumb-index 10.6.
- Our spread at 1: index 12, ring 8, pinky 16, middle 0; thumb +20 out / 15 across.
  apose reachable: index-pinky 19.5+12+16 = 47.5; I-M 19.8, M-R 11.1, R-P 16.6; thumb-index 50.1.

## Comparison
- Curl: the clips never exceed a full fist; our f2 reaches a full fist in apose and tpose (renderer check), so f2 covers the clip maximum.
- Spread: clip max index-pinky 43 <= ours 47.5; thumb-index 39 <= 50; I-M 18 <= 19.8; M-R 10 <= 11.1; ring-pinky 18 vs ours 16.6 (short by 1.4 deg, about the measurement noise).
- Not reachable with our frames: the claw (inspect f0-12, startle): curl drives MCP/PIP/DIP together from one value, so there is no frame with MCP straight and PIP/DIP bent. Our f1 (half curl) bends all three joints.
- Thumb: the clip fists wrap the thumb across the fingers; our thumb is rotation-only (apose 5/60/25, tpose -5/-20/-25); not measured in the clips, so no claim on a gap.
- tpose: no clip shows a T-pose side-view hand, so tpose spread/curl has no clip reference.
- Timing hints for animation: curl/uncurl 4-8 frames (167-333 ms), slow curls 14-16 frames (583-667 ms), wave period 11.1 frames (462 ms).

Files: contact sheet `views/apose/hands/previews/clip_gestures_ref.png`; tools in `hands/work/clip_gestures_tools/` (MediaPipe venv /workspace/.mpenv, data in /workspace/gb/).
