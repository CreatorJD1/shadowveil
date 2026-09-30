# Shadowveil mouth – idle QA (measure only)

Measured 2026-09-30 ~02:40–03:15 PT. Nothing under `views/` or `rig/` was modified; nothing was drawn on the character.
Sources: `rig/previews/idle/keys/<clip>_<view>.mp4` (12 keyed clips) and `<view>_idle.mp4` (auto idle) for apose/tpose/left/right,
processed one video at a time from a 360x340 head crop (≈110 MB RSS). Every number was cross-checked on the harness's lossless PNG frames
(`rig/previews/idle/frames/.../f*.png`, the frames the MP4s were encoded from) and against the harness `meta.json` (rig mouth state, fade t0, head bone).
`idle_all.mp4` / `idle_keys_all.mp4` / `*_all5.mp4` are half-scale tilings of the same renders, so they were not re-measured.

## Method
* **Head**: ECC Euclidean fit (rotation + translation) of each frame to the rig's own rest render (`frames/<view>/rest.png`). The mask is face skin only
  (hair, eyes, mouth and hands layers dilated 5 px are masked out; no neck). Checked against the rig's head bone: ≤0.42 px error at the mouth anchor (0.1–0.2 px typical).
* **Mouth drift**: in head-stabilised coordinates, sub-pixel translation of the mouth patch against the matching shape (shape PNG composited on the rest render),
  masked to that shape's opaque pixels. Also measured against a **nose-tip landmark** patch (tracked the same way). Crossfade frames and low-confidence matches
  (ECC cc < 0.95, which only happens on mid-fade frames) are left out of the headline number.
* **Shape / switches**: least-squares rest↔smile blend coefficient in the mouth window (normalised to the clip's own held rest = 0, held smile = 1). A switch is a 0.5 crossing, and
  its time is interpolated. For auto idle, the nearest of the 9 shapes per frame is used and 1-frame labels (fades) are merged.
* **Crossfade / gap**: on the lossless frames around each switch, compared against the clip's own held rest and smile (mean of stabilised frames). Counted: "mid" px that match neither shape,
  "gap" px lighter than both shapes inside the mouth footprint (skin or base showing), and smile-only corner px still at full smile during smile→rest.
* **Chroma**: pixels with B − max(R,G) > 60 and B > 100 inside the mouth plus a 10 px ring, on every frame, in both MP4 and PNG.
* **Sharpness**: mean gradient magnitude, raw frame, over the head face mask and over the mouth window. Each is relative to the rest render or the shape composite.

## Key numbers (MP4 / PNG where two values)

| clip | view | switches | visible switch times (0.5 crossing, video time) | mouth drift vs face, max px (mp4/png) | vs nose tip, max px | head travel px | blue px (mp4/png) | head sharp↔soft toggles | lip sharpness p5 on soft frames (sharp = 1.00) | fade frame f81 "mid" px | f144 smile corners still 100% | gap px |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| idle_breathe | apose | 2 | rest->smile @ 2.701s; smile->rest @ 4.779s | 0.38 / 0.39 | 0.29 | 6.7 | 0 / 0 | 8 | 0.92 | 150 | 3/8 | 0 |
| idle_weight_shift | apose | 2 | rest->smile @ 2.697s; smile->rest @ 4.781s | 0.33 / 0.31 | 0.21 | 26.5 | 0 / 0 | 0 | 0.91 | 133 | 7/8 | 2 |
| idle_arm_settle | apose | 2 | rest->smile @ 2.700s; smile->rest @ 4.782s | 0.34 / 0.37 | 0.36 | 5.5 | 0 / 0 | 8 | 0.94 | 140 | 3/8 | 0 |
| AUTO | apose | 48 (rig 48) | min hold 83.3 ms | 0.51 / 0.50 | 0.75 | 2.3 | 0 / 0 | 7 | 0.86 | - | - | - |
| idle_breathe | tpose | 2 | rest->smile @ 2.701s; smile->rest @ 4.780s | 0.35 / 0.23 | 0.60 | 7.7 | 0 / 0 | 8 | 0.93 | 178 | 5/14 | 0 |
| idle_weight_shift | tpose | 2 | rest->smile @ 2.700s; smile->rest @ 4.780s | 0.33 / 0.33 | 0.50 | 27.1 | 0 / 0 | 0 | 0.92 | 159 | 7/14 | 3 |
| idle_arm_settle | tpose | 2 | rest->smile @ 2.700s; smile->rest @ 4.781s | 0.29 / 0.23 | 0.58 | 4.5 | 0 / 0 | 8 | 0.94 | 167 | 5/14 | 0 |
| AUTO | tpose | 48 (rig 48) | min hold 83.3 ms | 0.57 / 0.52 | 0.69 | 1.8 | 0 / 0 | 7 | 0.85 | - | - | - |
| idle_breathe | left | 2 | rest->smile @ 2.704s; smile->rest @ 4.798s | 0.25 / 0.30 | 0.46 | 8.5 | 0 / 0 | 8 | 0.85 | 57 | 26/106 | 0 |
| idle_weight_shift | left | 2 | rest->smile @ 2.699s; smile->rest @ 4.806s | 0.29 / 0.35 | 0.51 | 9.1 | 0 / 0 | 0 | 0.85 | 38 | 45/106 | 0 |
| idle_arm_settle | left | 2 | rest->smile @ 2.700s; smile->rest @ 4.805s | 0.38 / 0.36 | 0.43 | 4.9 | 0 / 0 | 8 | 0.86 | 34 | 44/106 | 0 |
| AUTO | left | 47 (rig 48) | min hold 83.3 ms | 0.54 / 0.50 | 1.19 | 1.6 | 0 / 0 | 7 | 0.83 | - | - | - |
| idle_breathe | right | 2 | rest->smile @ 2.701s; smile->rest @ 4.798s | 0.53 / 0.53 | 0.56 | 8.4 | 0 / 0 | 8 | 0.86 | 41 | 24/101 | 1 |
| idle_weight_shift | right | 2 | rest->smile @ 2.702s; smile->rest @ 4.806s | 0.64 / 0.54 | 0.64 | 9.1 | 0 / 0 | 0 | 0.86 | 33 | 24/101 | 0 |
| idle_arm_settle | right | 2 | rest->smile @ 2.703s; smile->rest @ 4.805s | 0.64 / 0.56 | 0.62 | 5.0 | 0 / 0 | 8 | 0.86 | 31 | 42/101 | 2 |
| AUTO | right | 46 (rig 48) | min hold 83.3 ms | 0.76 / 0.75 | 0.74 | 1.7 | 0 / 0 | 7 | 0.83 | - | - | - |

### 1–2. Mouth locked to the head
* All 16 videos: **max drift 0.64 px** keyed and 0.76 px auto on held frames. No trend with head motion: weight_shift moves the head up to 27 px and 3.8° and still shows ≤0.33 px (front).
  This is at the tracker's noise floor, so the mouth is rigidly attached. Against the nose tip the max is 0.64 px keyed. It rises to 1.19 px on a low-confidence auto
  mid-fade frame (left_idle f74), which is a measurement artefact of the mixed shape, not drift.
* The earlier 0.6 px "worst" values in tpose (f81) fall exactly on crossfade frames, where the template is a mix. Held-frame tpose is ≤0.35 px.

### 3. Switches
* **Every keyed clip, every face view: exactly 2 switches** (rest→smile, smile→rest), and no other shape ever appears. This agrees with the rig log (switch frames 80 and 143, one 2083 ms hold).
* Timing: rest→smile becomes visible at **2.70 s** (video f81 at 56%, f82 at 100%). The key crosses 0.5 at 2.65 s, but form = 0.5 is a tie that resolves to *rest*, so the switch fires at the next
  60 Hz sub-step (2.667 s = f80, drawn at opacity 0). smile→rest fires on time at 4.75 s. It is visible at **4.78 s (front) / 4.80 s (profile)**: f143 at 28%, f144 at 83%, f145 done.
  Both are within 1–2 frames of spec.
* Crossfade: **1 mixed frame for rest→smile (f81) and 2 for smile→rest (f143, f144)**. **No gap**: skin/base-lip-coloured px are 0–3 on every fade frame, and 0 on most.
  The 14 px flagged at f142 in left/right arm_settle is the sharp-snap frame, not a gap.
  **Ghost/doubling – yes, one real one, renderer side:** because the outgoing smile stays 100% opaque underneath, its wider outline (the part rest doesn't cover) stays at full strength
  while rest fades in on top. In the profiles that is 24–45 of ~105 smile-only px on f144 (4.800 s), so for 1–2 frames you see the rest lip line *plus* the smile outline.
  In front views it's only 3–7 of 8–14 corner px, which is barely visible. The rest→smile direction has no doubling, because smile fully covers rest. f81 in front views reads as two half-strength seams
  (a normal 1-frame dissolve).
* Auto idle (reference): measured 46–48 shape changes. The rig log shows 48 frame-level changes (Coder's "47" is the harness holdLog length, which omits the first change). Min hold is 83 ms, so the 70 ms rule is respected;
  the problem is the *count*, not flicker per switch.

### 4. Chroma blue
* **0 chroma-blue px** around the mouth on every frame of every video (MP4 and lossless). The mouth PNGs themselves contain no bluish px.
* FYI (not mouth, not chroma): in **left/right**, 7 and 3 px of very dark navy (≈ #0B0046, B−max(R,G) ≤ 54) sit on the face silhouette line just in front of the lips.
  They come from `base.png`/`base_body_skin.png` (e.g. left (590,253), right (783,269)), are visible in the rest render, and are static.

### 5. Sharp↔soft head flicker vs the lip line
* The soft/sharp state is exactly the rig's pixel-snap rule (`index.html` l.160–166): the head bone angle is exactly 0 → pixel-snapped, no smoothing (sharp); any rotation → smoothed (soft).
  My measured head-sharp frames match the head-angle==0 frames 99–100%. The **mouth layer goes through the same path, so the lip line flickers in lockstep with the head**. It is at 1.00 on sharp frames.
  On soft frames it averages 0.96 (front) / 0.90 (profile), dropping to 0.83–0.86 at worst (p5). This is a mild blur (~½ px), but visible as a pop when it snaps back.
* Sharp islands (same in all four views). The lip line is crisp on these frames and soft on every other frame (video frame, t = f/30):
  * idle_breathe: f0–3 (0–0.100 s), f42 (1.400 s), f104–106 (3.467–3.533 s), f119–121 (3.967–4.033 s), f239 (7.967 s) → 8 toggles.
    It softens again at f4, f43, f107, f122.
  * idle_arm_settle: f49 (1.633 s), f70 (2.333 s), f142 (4.733 s), f163–167 (5.433–5.567 s) → 8 toggles; it softens again at f50, f71, f143, f168.
  * idle_weight_shift: never axis-aligned → **0 toggles**. The lip is uniformly soft (never flickers), with worst held-frame lip at 0.84 (left f74, 2.467 s).
  * auto idle: f0, f67–69 (2.233–2.300 s), f136–138 (4.533–4.600 s), f224–228 (7.467–7.600 s) → 7 toggles (matches Coder's ~7).
* Note f142 in arm_settle falls one frame before the smile→rest switch, so on the profiles the snap and the fade land back to back (4.733→4.800 s).

### 6. Judgment
Keyed idle: the mouth is **correct but stiff**. It is locked to the head, has the right two switches, and shows no blue or gaps. But it is a single 2.1 s smile hold done with a hard 1–2-frame dissolve.
With nothing else moving in the mouth, it reads as a switch rather than an expression, and the profile smile→rest has a visible 1–2-frame double outline.
The periodic sharp/soft pop of the whole face (lip line included) is more noticeable than anything the mouth does.
Auto idle: ~48 shape changes in 8 s reads as chattering/mumbling, not idle. That is not natural, and it is a driver problem, not a shape problem.

## Where the problems sit
* **Renderer side (rig/index.html)**:
  1. The sharp/soft toggle from pixel-snapping when the angle is exactly 0 (lip line included).
  2. The "outgoing fully opaque underneath" rule makes the smile→rest doubling in profile.
  3. The switch frame is drawn at 0% incoming, which adds 1 frame of latency.
  4. Ties at form = 0.5 resolve to rest, which makes the up-switch ~17 ms late.
  5. The auto-idle mouth driver switches ~48×/8 s.
* **Keys side (idle_clips.json)**: timing is as authored. A softer MouthForm ease or a longer smile would help the stiffness, but the keys are not wrong.
* **Mouth side**: no defect found. Registration, coverage (smile fully covers rest, so no gap on rest→smile) and colour are clean. The only mouth-side lever is optional: the profile smile shapes
  extend ~100 px beyond rest, so a smile→rest intermediate (or a slimmer smile outline) would reduce the doubling if the renderer rule stays as is.

## Files
* `idle_mouth_worst_contact_sheet.png`: 7 worst frames, each an MP4 crop next to the same canvas crop of the rest render (3× nearest).
* `results.json`: all per-clip numbers (mp4, png, rig). `data/*.json`: per-frame series. `data/fades_*.json`: per-fade-frame details.
* Scripts: `measure.py`, `fades.py`, `report.py`, `contact.py`, `run_all.sh` (read-only on the rig).
