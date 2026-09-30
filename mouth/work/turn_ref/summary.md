# apose-turn reference: mouth through the turn (measurement only)

Source frames: `/workspace/shadowveil/reference/apose_turn/frames/f001–f241.png` (241 frames, 24 fps, 10 s, 768×1168). These are pixel-identical to a decode of `apose-turn.mp4`, where frame index i = f(i+1). All measurements are in source pixels. CE is the distance from the chin to the eye line; front CE = 58.26 px (eye line y 176.74, seam y 212.75, chin y 235.0). The head barely pitches: the seam stays at y 212.1–213.6 for the whole turn.
Nothing under views/ or rig/ was modified, and nothing was painted.

## Angle convention and method
- θ = 0 is front. θ = 90 faces screen-left (green iris visible), which is our **left** view. θ = 180 is the back. θ = 270 faces screen-right (orange iris), which is our **right** view. θ increases with frame number.
- Keyframes come from the arm-span silhouette. The profile minima are at f060.5 and f158.5, and the back maximum is at about f108.5. Between keyframes I used piecewise-linear time plus an empirical span-vs-|cos θ| curve. Near the front (θ < 30° or > 330°) the angle comes from a face cue instead: the mouth's offset inside the jaw contour ≈ −0.806·sin θ. The two methods are blended across 10–30°.
- The turn eases in and out. f001–f004 are static, the front is reached again at about f229, and f233–f241 hold at the front. Mid-turn speed is about 1.8°/frame. Angles are good to about **±5°**; for example, the width at "315°" matches the width at about 49°.

## Frame ↔ view matches
| view | frames | θ |
|---|---|---|
| apose (front) | f001–f005, f229–f241 | 0 |
| left | f060–f061 | 90–91 |
| back | f108–f109 | 179–181 |
| right | f158–f159 | 269–270 |

## Mouth over the turn
- **Visible:** f001–f070 (to about 108°) and f149–f241 (from about 253°). It is hidden behind the head at f071–f148.
- **Closed** in all 163 visible frames: no cavity and no teeth. It is already closed when it reappears at f149, and it never opens. It can't be checked while hidden, but nothing suggests it opens.
- **Both corners visible:** f001–f041 (to about 55°) and f185–f241 (from about 310°). From f042/f044 to f070, and from f149 to f184, the lip front sits on the face silhouette, so only one corner shows.
- **Crispness:** 111 frames are crisp and 48 are soft. The soft frames are the near-profile ones, f050–f070 and f149–f184, which include the profile matches f060/f061 and f158/f159. Four frames are **smeared**: f064 (96.6°), f066 (100.3°), f067 (102.2°) and f167 (279.4°).
- **Frame-to-frame residual:** the median is 2.75. It is worst at the visibility edges, f067–f069 (9.7–11.2) and f149–f150. There are small shape jumps in H at f048, f051, f053 and f162, and in lift at f151 and f183.

### 5° table (W = corner-to-corner width in source px; lift = seam centre minus corner mean, + means the corners are up)
| target | frame | θ est | W px | W/CE | lift px | corners | closed | crisp |
|---|---|---|---|---|---|---|---|---|
| 0° | f003 | 0.0 | 31.5 | 0.541 | 2.16 | both | yes | crisp |
| 5° | f010 | 4.5 | 31.25 | 0.534 | 1.89 | both | yes | crisp |
| 10° | f015 | 10.2 | 30.5 | 0.524 | 1.78 | both | yes | crisp |
| 15° | f018 | 15.4 | 30.0 | 0.515 | 2.34 | both | yes | crisp |
| 20° | f021 | 19.7 | 29.75 | 0.512 | 2.47 | both | yes | crisp |
| 25° | f024 | 25.3 | 29.0 | 0.508 | 2.16 | both | yes | crisp |
| 30° | f027 | 30.0 | 28.25 | 0.492 | 1.95 | both | yes | crisp |
| 35° | f030 | 34.5 | 27.0 | 0.472 | 2.0 | both | yes | crisp |
| 40° | f033 | 40.0 | 26.0 | 0.455 | 1.94 | both | yes | crisp |
| 45° | f036 | 45.3 | 24.25 | 0.427 | 1.88 | both | yes | crisp |
| 50° | f038 | 49.2 | 22.75 | 0.399 | 1.81 | both | yes | crisp |
| 55° | f041 | 54.7 | 22.0 | 0.398 | 1.98 | both | yes | crisp |
| 60° | f044 | 60.7 | 21.5 | 0.386 | -0.09 | one (on contour) | yes | crisp |
| 65° | f046 | 64.5 | 19.5 | 0.347 | -0.94 | one (on contour) | yes | crisp |
| 70° | f049 | 69.8 | 17.75 | 0.291 | -1.75 | one (on contour) | yes | crisp |
| 75° | f052 | 75.7 | 15.75 | 0.252 | -1.71 | one (on contour) | yes | soft |
| 80° | f054 | 79.7 | 15.0 | 0.262 | -1.5 | one (on contour) | yes | soft |
| 85° | f058 | 85.4 | 12.75 | 0.219 | -1.12 | one (on contour) | yes | soft |
| 90° | f060 | 90.0 | 11.75 | 0.202 | -1.0 | one (on contour) | yes | soft |
| 95° | f063 | 94.7 | 9.5 | 0.151 | -1.22 | one (on contour) | yes | soft |
| 100° | f066 | 100.3 | 8.75 | 0.158 | -1.0 | one (on contour) | yes | smeared |
| 105° | f068 | 104.1 | 7.75 | 0.133 | -1.19 | one (on contour) | yes | soft |
| 110–250° | f071–f148 | — | hidden | | | | | |
| 255° | f150 | 254.7 | 4.75 | 0.082 | 1.15 | one (on contour) | yes | soft |
| 260° | f153 | 260.1 | 7.5 | 0.129 | -0.63 | one (on contour) | yes | crisp |
| 265° | f156 | 265.5 | 10.0 | 0.172 | -1.37 | one (on contour) | yes | soft |
| 270° | f159 | 270.0 | 11.75 | 0.202 | -4.56 | one (on contour) | yes | soft |
| 275° | f163 | 275.1 | 12.75 | 0.219 | -0.79 | one (on contour) | yes | soft |
| 280° | f167 | 279.4 | 14.0 | 0.24 | -0.59 | one (on contour) | yes | smeared |
| 285° | f170 | 284.9 | 15.5 | 0.266 | -0.66 | one (on contour) | yes | soft |
| 290° | f173 | 290.2 | 16.5 | 0.283 | -0.69 | one (on contour) | yes | soft |
| 295° | f176 | 294.8 | 17.75 | 0.305 | -0.22 | one (on contour) | yes | soft |
| 300° | f179 | 300.0 | 20.25 | 0.355 | -0.32 | one (on contour) | yes | soft |
| 305° | f182 | 304.8 | 21.25 | 0.373 | 1.13 | one (on contour) | yes | crisp |
| 310° | f185 | 309.8 | 22.0 | 0.402 | 1.42 | both | yes | crisp |
| 315° | f188 | 314.4 | 22.75 | 0.407 | 1.64 | both | yes | crisp |
| 320° | f192 | 320.6 | 24.5 | 0.432 | 1.75 | both | yes | crisp |
| 325° | f195 | 325.5 | 26.0 | 0.459 | 1.39 | both | yes | crisp |
| 330° | f198 | 329.3 | 27.0 | 0.474 | 1.52 | both | yes | crisp |
| 335° | f203 | 335.3 | 28.75 | 0.497 | 1.17 | both | yes | crisp |
| 340° | f205 | 339.2 | 29.25 | 0.514 | 1.47 | both | yes | crisp |
| 345° | f210 | 344.7 | 30.25 | 0.522 | 1.69 | both | yes | crisp |
| 350° | f216 | 350.6 | 31.0 | 0.532 | 1.69 | both | yes | crisp |
| 355° | f220 | 355.3 | 31.0 | 0.529 | 1.77 | both | yes | crisp |
The full per-frame data is in `turn_mouth_frames.csv`: centre, seam, nose, chin, jaw position, sharpness and more.

## Front: video vs ours (views/apose, mouth/rest.png over base.png)
| | video f001–f005/f229–f241 | ours apose |
|---|---|---|
| W | 31.5 px, W/CE 0.541 | 48.5 px at CE 90.7, W/CE 0.535 |
| corner lift | 2.14 px (0.037 CE) | 3.09 px (0.034 CE) |
| seam below eye line | 0.617 CE | 0.618 |
| chin below seam | 0.383 | 0.382 |
| seam below nose | 0.223 | 0.218 |
| mouth x − nose x | 0.012 | −0.006 |
| position within the jaw (0 = left edge, 1 = right) | 0.50 | 0.495 |

**The front matches** to within about 1–2% on every measure.

## Profile: video vs ours (video medians f058–f063 / f156–f161; ours views/left, views/right)
| (÷CE) | video left | video right | ours left (CE 88.4) | ours right (CE 89.2) |
|---|---|---|---|---|
| W px (source) | 11.5 | 11.5 | 23.75 (15.7 at video CE) | 23.5 (15.3 at video CE) |
| W/CE | **0.197** | **0.197** | **0.269** | **0.263** |
| seam below eye line | 0.62 | 0.62 | 0.600 | 0.592 |
| chin below seam | 0.378 | 0.376 | 0.400 | 0.408 |
| seam below nose tip | **0.292** | **0.26** | **0.369** | **0.355** |
| lip front behind nose tip (x) | 0.145 | 0.116 | 0.105 | 0.104 |
| back corner behind nose tip (x) | 0.345 | 0.313 | 0.373 | 0.367 |
| mouth centre behind nose (x) | 0.242 | 0.215 | 0.239 | 0.235 |
| back-corner drop | 1.1 px (0.019) | 4.5 px (0.078) | 6.1 px (0.069) | 5.8 px (0.065) |

H in the video profile is unreliable. The upper lip there is nearly skin-toned, and at f159 the silhouette outline merges into the mask. See `turn_vs_ours_rest.png`.

**Profile mismatches (ours vs video):**
1. **Width:** our profile mouth is **about 35–40% too wide** (0.27 vs 0.20 CE). Our width matches the video at about 77° (f053, W 15.5) or about 285° (f170), not at 90/270. The extra width comes from both ends: the lips stick out further in front (lip front 0.105 vs 0.12–0.145 CE behind the nose tip), and the back corner sits further back (0.37 vs 0.31–0.35).
2. **Vertical:** our seam is **about 0.07–0.08 CE (about 7 px at our scale) further below the nose tip**. The chin also sits a little lower relative to the seam (+0.02–0.03 CE), and the seam is a little closer to the eye line (0.59–0.60 vs 0.62).
3. **Look:** the video's profile mouth is a small, faint notch with a pale upper lip that hardly protrudes past the silhouette. Ours are full, dark and clearly protruding (`turn_vs_ours_rest.png`, compared at the same CE scale). Our back-corner drop is similar to the video's facing-right profile and larger than its facing-left profile.
4. **What matches:** the horizontal mouth centre relative to the nose, and the fact that it's closed.

## Frames usable as a three-quarter closed rest mouth (listed only, nothing cut)
All of these are closed and crisp, show both corners, have a stable width, and have no shape jumps. I checked them visually.
- **Front toward screen-left (θ ≈ 30–50°):** f027 (30.0°, W 28.25), f030 (34.5°, W 27.0), f033 (40.0°, W 26.0), f035 (43.7°, W 24.75), **f036 (45.3°, W 24.25, lift 1.88 px): the 45° pick**, f038 (49.2°, W 22.75). f024–f036 have low residuals (2.1–3.4). f037 (5.18) is slightly less stable.
- **Front toward screen-right (θ ≈ 310–330°):** f186 (311.3°, W 22.25), **f188 (314.4°, W 22.75, lift 1.64 px): the 315° pick**, f189 (316.0°), f191 (318.9°, W 24.0), f192 (320.6°, W 24.5), f195 (325.5°), f198 (329.3°, W 27.0). f188, f191 and f195–f199 have the lowest residuals. f185–f187 are a bit noisier (5.0–5.7).
- **For a width-symmetric pair:** f036 ↔ f191 (about 24 px), or f038 ↔ f188 (22.75 px). The width suggests the return side's angle scale is about 4° off.
- **Not usable as a three-quarter rest:** 55–108° and 253–305° (f042–f070, f149–f184), because the near corner is on the silhouette. The frames there are soft or smeared.

## Caveats
- The video is AI-generated, so its drawing is not strictly consistent. The facing-left and facing-right profiles differ from each other (corner drop 1.1 vs 4.5 px).
- Angles are ±5°, and the turn eases in and out.
- The resolution is low: the mouth is about 31 px wide at the front and about 12 px in profile, so there is ±0.5 px quantisation, which is about 0.01 CE.
- In profile only one iris shows, so the per-frame eye line is unreliable. Profile rows use the front eye line, which is fine because the head doesn't pitch.
- Nose detection is noisy at 50–65° and 295–310°.

## Files (in this folder)
- `turn_mouth_contact_sheet.png`: 72 mouth crops at 5° steps, labelled with frame, angle, W and flags.
- `turn_vs_ours_rest.png`: the video's front and profiles next to our apose/left/right rest mouths at the same CE scale.
- `turn_mouth_frames.csv`: per-frame data, and `turn_stats.json`: summaries and rows.
- `ours_rest.json`: measurements of our three views.
- Scripts: pass1.py, pass2.py, pass3.py, angles.py, facemeas.py, pass4.py, analyze.py, ours.py, sheet.py, compare.py.
- `tmp/`: intermediates and QA images.
