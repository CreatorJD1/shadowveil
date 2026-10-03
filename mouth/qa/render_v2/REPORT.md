# Mouth v4 render QA v2, plus a check of the regenerated anger clip

Base Mouth, 2026-10-02, about 22:45 to 23:40 PT. This was measurement only. Nothing went live, and nothing under `rig/`, `views/`, or another team's folder was edited.
- Renderer: a **copy** of `rig/index.html` (md5 `17167b7d…`, taken at 22:4x PT from the 22:39 PT version), plus copied `rig/partmesh/staged/*.json`, `rig/twist_masks/` and `rig/hand_angles/`. These are in `scratch/rig/`. There are no symlinks.
- Server: my own static server on 127.0.0.1:8781 (`work/serve.py`). It serves `/rig/` from the scratch copy and everything else read-only from the tree.
- Browser: headless Chrome (puppeteer-core, swiftshader), using `?quality=linear` and the default `mouthfade=35`. The Chrome and server PIDs I started are listed in `work/my_pids.txt`. All of them are closed now, and no other Chrome process was touched.
- Mouth crops were read with `getImageData`, so they are raw RGBA. The expected images were composited in the same browser (base.png plus the shape PNG at identity), so both sides go through the same premultiply round trip.

## 1. Regenerated anger clip
**Location.** The clip JSONs are `rig/previews/actions/v1/clips/anger.json` and `anger_stress.json`. Their MouthOpen/MouthForm keys match `mouth/actions/mouth_actions.json` exactly: `[0,0],[0.299,0],[0.3,0.25],[3.0,0.25]` and `[0,0],[0.299,0],[0.3,-1],[3.0,-1]`.
- The renders are `rig/previews/actions/v1/work/{normal,stress}_anger_{apose,tpose,back}/` and were produced by `rig/previews/idle/harness/queue_anger_redo.sh`. Each is 90 lossless PNG frames at 30 fps, with `meta.json` and ss2 quality. File mtimes are 2026-10-01 23:24–23:27 PT.
- The older renders are in `work/stale_pregate/*_premouth`.
- No MP4 exists. There are no renders for left/right.
- Coder also ran a state-only check, `rig/work/qa_post6d5b239/clip_check.json` (2026-10-02 20:55 PT).

| check | apose | tpose | result |
|---|---|---|---|
| shown shape over time | rest f0–f8. Anger from **f9 = 0.300 s** (fade frame), full anger from f10 = 0.333 s through f89 = 2.967 s (the last frame of the 3.0 s clip) | same | PASS |
| params during anger | MouthOpen 0.25 / MouthForm −1 on every frame from f9 to f89 | same | PASS |
| position vs live anger.png | Anger frames fit anger.png at (+0.125, +1.10) px. Rest frames under the same head offset fit rest at (+0.15, +1.125), so **Δ = 0.03 px** (the whole head carries the ~1.1 px RootY offset). My current-rig static render at (0.3,−1): **0 px** differ vs base+anger.png in the mouth region | Δ = 0.00 px; static 0 px | PASS (0 px) |
| doubled outline in the crossfade | **f9 is doubled.** The rest lips stay at 100% and anger is at 25% on top: the outgoing contour shows at 0.75 and the anger contour at 0.24 of full contrast (346 px of anger-only outline). f10 is clean. | same (0.68 / 0.24) | **FAIL (1 frame, 33 ms)** |
| blue key spill (B>max(R,G)+20, mouth bbox) | 0 px on every frame checked | 0 | PASS |
| auto-talk off for anger | `mouthTalk=false` on all 90 frames of all 4 runs. `TALK_EXCLUDE` contains `'anger'` (rig/index.html:337). In my 2×240 talk frames (talk on), anger was never picked. | same | PASS |
| back view | Has no mouth. The rest shape is kept at (0.25,−1), as expected | — | OK |

The normal and stress renders give identical mouth numbers. The anger line is 3 px (p90) against rest's 1 px, and the lips are plum. That is the user decision already pending in HANDOFF; it was not re-litigated here.

## 2. Live mouth render QA (apose and tpose, linear)
### Rest
- Rig rest path, `render(g,true)`: **0 px** vs base.png on the full frame, in both views.
- `rig/rest_check.py`, run on a scratch copy: **0 px in all 5 views**.
- Posed path at default params (`renderFinal`, linear): **0 px in the mouth region.** The full frame differs by 419 px (apose) and 2474 px (tpose), all outside the mouth. In the crop these were semi-transparent jaw/face outline pixels off by 1–5 levels; the rest are in body or skin. That is Coder's posed-vs-rest display issue, not the mouth.

### Sweep: MouthOpen 0..1 step 0.1 × Form −1/0/1, settled (33 frames per view)
- Picks follow the nearest rule with 0 mismatches:
  - Form −1: M M anger anger OH_half×4 OH×3
  - Form 0: rest×3 AA_half×5 AA×3
  - Form +1: smile×3 EE_half×5 EE×3
- **0 px** vs the authored composite in the mouth region on every frame, in both views.
- Blue spill: 0. Key-blue pixels: 0. The authored PNGs have no bluish semi-transparent edges.

### Outline width vs rest (limit 1 px)
Measured as the binary skeleton width of the darkest-line pixels, with the threshold set to each shape's darkest luminance + 0.06.
- All 9 grid shapes: p90 **1.0 px = rest** (Δ 0). PASS.
- **anger: p90 3.0 px (Δ +2 px). FAIL**, but this is already known.
- On moving-head (resampled) talk frames the line stays at about 1.0 px (apose). In tpose OH_half reaches 1.75 px.
- The binary width is not reliable on resampled frames. In 68 tpose frames the faint rest line falls below the threshold, so treat soft-frame widths as indicative only.

### Sharp/soft flicker, frame to frame
- **Static head** (sweep; 30 fps timed sweep, 126 frames; 8 s talk with body frozen, 240 frames): 0 toggles. Every non-fade frame is pixel-exact (186 of 186). PASS.
- **Talk + body life**, 8 s at 30 fps:
  - The mouth travels ±15 px and the head rotates ±1.76°.
  - Sharpness relative to the authored shape, after aligning each frame with its head matrix, is **0.87–1.00 (apose) and 0.88–1.00 (tpose)**. It tracks a bilinear model of the same transform (median RMSE 0.6/255), so the measurement is trustworthy.
  - There are **4 toggles of more than 5% per 8 s**, at t = 2.300 and 6.900 s. On those frames the head rotation is exactly 0 with an integer offset, so drawImage is exact (sharpness 1.00) while the neighbouring frames are 0.93.
  - This is the "sharp/soft at exactly 0" flicker, still present under linear. **FAIL (rig-side)**.

### Doubled outlines during crossfades
Method: find the contour pixels unique to the outgoing shape and those unique to the incoming shape. "Doubled" means at least 15 px of each are visible at ≥20% of full contrast. Validated on pure frames (outgoing 0.0–0.1 against incoming 1.0).
- Step-through every 2.5 ms over 14 pairs: **every pair is doubled from 0 ms to 17.5–30 ms** of the 35 ms fade.
  - Doubled up to 30 ms: anger→rest, AA→rest, smile→rest (tpose), EE_half→rest (tpose).
  - Doubled up to 17.5–22.5 ms: the others.
- At 30 fps, every shape switch produces exactly **one doubled frame**:
  - talk with body frozen: 38 of 38 switches (apose), 31 of 38 (tpose)
  - timed sweep: 13 of 17 switches
  - The switches that were not flagged are pairs whose outlines nearly coincide, with fewer than 15 px of unique contour on one side: OH_half↔AA_half in tpose, and the smile/EE_half/EE moves. Their blend is still 25/100.
- Cause: the rig's crossfade rule (rig/index.html:664). The incoming shape starts at 25% on top, and the outgoing shape stays at 100% until 17.5 ms.
- **FAIL (rig-side)**.

### Fade timing
- The fitted alphas match the rig code exactly:
  - Incoming aIn = 0.25 + el/35: fitted 0.25 / 0.325 / 0.525 / 0.75 / 0.975 / 1.0 at 0 / 2.5 / 10 / 17.5 / 25 / 30 ms.
  - Outgoing aOut = 1 until 17.5 ms, then a ramp to 0 at 35 ms (fitted 0.45–0.58 at 25 ms, 0.1–0.28 at 30 ms).
- At 30 fps the switch frame shows incoming at 0.25 or 0.726, depending on the 60 Hz sub-step phase. It is never drawn at 0%, so the old "switch frame at 0%" issue is fixed.
- On the next frame (el = 33.3 ms) the outgoing shape is still at 9.5%, wherever it is larger than the incoming one (for example 223 px for anger→OH_half).
- Shape changes land on the same frame as the param change: 0 lag frames in the timed sweep.
- Minimum hold is 133 ms (rig minimum 120); there were 74 holds.
- **Contract mismatch:** `views/*/mouth/rig.json` says `crossfadeMs: 60`, but the renderer uses 35 ms.

### Blue spill
0 px in every frame of every test, both views (sweep, timed, fades, talk, talk with frozen body). PASS.

### Talk picks
With talk on, the shapes used are rest, AA_half, OH_half, M and AA. EE, EE_half, smile and anger never appear. PASS.

## Needs Coder (rig side)
1. **Crossfade doubles the outline.** This affects one frame per switch, including the anger set-in at f9. Options: start incoming at 0 and fade outgoing out together (no 25% lead and no 100% hold), or use a hard cut (`mouthfade=0` already exists). Also reconcile the 35 ms fade with the 60 ms in the mouth contract.
2. **Sharp/soft flicker when the head rotation is exactly 0** under linear (t = 2.300 and 6.900 s in an 8 s talk). The fix needs the same resampling path at 0, which is the ss2/"consistent resampling" item.
3. The posed default frame is not 0 px vs base outside the mouth (419 / 2474 px, at the jaw edge and in body/skin). This is not mouth-owned.
4. Code reading only, not rendered: the `mouthPick` tie key `s.name==='rest'?1:0` makes rest *lose* exact ties, while the contract says "prefer rest". This only matters at exact midpoints such as (0.25, 0).

## Needs the user
- The anger art: plum lips and a 3 px line against the 1 px rule. Keep, recolour, or remove. This is unchanged from HANDOFF.

## Files
- `sheet.png`: sweep grids, crossfade strips (doubled frames in red), anger clip f8/f9/f10, and the moving-head flicker strip.
- `work/summary.json`, `work/final_{apose,tpose}.json`: per-frame numbers. `work/talk_aligned.json`: head-aligned talk sharpness. `work/anger_clip_results.json`: the anger clip numbers.
- Scripts: `work/harness.mjs`, `work/serve.py`, `work/analyze.py`, `work/analyze_final.py`, `work/summarize.py`, `work/talk_aligned.py`, `work/anger_clip.py`, `work/sheet.py`.
- Raw crops: `work/run_{apose,tpose}/crops/*.rgba` (128×89 and 126×88 RGBA) and `meta.json`.
