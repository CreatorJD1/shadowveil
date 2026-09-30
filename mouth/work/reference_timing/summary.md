# Reference mouth timing and shape measurement (Grok clean-room clips)

This was measurement only. Nothing under `views/` or the rig was changed, and nothing was painted.

## Sources and method
- **Source:** the clean mp4s in `reference/grok_build/public/clean-room/videos/` (768x1168, 24 fps, 6.04 s, 145 frames; idle-long is 241 frames). I did not use the webm screen captures (they have a blue key fringe).
- **Clips measured (12):**
  - talk (the only talk clip).
  - Idle for contrast: idle, idle-long.
  - Smile/expression: smirk, tongue (ends in a wide grin), cheeks, gasp, startle, glare, angry, worry, hem.
  - There is no clip named smile, laugh or emotion. "Point and laugh" and the emotion faces are stills, not videos.
- **Excluded:** sad and nod (her head bows and the tracker loses the mouth), yawn (a hand covers the mouth).
- **Per frame:**
  - ffmpeg decodes a head crop. Around the tracked mouth, a window of about 80x52 video px is upscaled 4x (bicubic).
  - Lips and mouth are pixels darker than the local skin, with holes filled.
  - The opening is near-black cavity (lum < 25), teeth (brighter than skin, low chroma) or tongue, but only in blobs that contain cavity or teeth.
- **Metrics per frame:**
  - W: mouth width.
  - Hmouth: outer mouth height.
  - openH: opening height, the largest top-to-bottom span in the middle 40% of columns.
  - cornerLift: centre seam y minus mean corner y. Positive means corners up.
- **Normalisation:** every value is divided by her rest-mouth width. That is 34.25 px in idle, rescaled per clip by the distance between her irises (orange and green), because the clips are framed up to 12% differently (iris distance 47.2 to 54.2 px).
- **Our shapes:** `views/apose/mouth/*.png` over base.png, measured with the same geometry at native resolution.
  - Our rest width is 48 px.
  - The opening is classified by our flat palette colours.
  - Our 1-2 px teeth slits and the anti-aliased line/cavity mixes measure unreliably. So `o` for ours is the build's design opening (build5.py FRONT, Sl-Su at the centre), with the measured value alongside.
- **Mapping to our grid:**
  - MouthOpen is 0 if o < 0.089, 0.5 if o < 0.255, else 1. These are midpoints between our closed, half and full shapes.
  - MouthForm is -1 if w < 0.875, +1 if w > 1.042, else 0. These are midpoints between OH_half/AA_half and AA/EE.

## Our 9 shapes (apose)
| shape | w (width/rest) | o design | o measured | h (outer height/rest) | corner lift |
|---|---|---|---|---|---|
| rest | 1.00 | 0 | 0 | 0.40 | 0.07 |
| M | 0.98 | 0 | 0.06* | 0.25 | 0.07 |
| smile | 1.19 | 0 | 0.02 | 0.44 | 0.20 |
| OH_half | 0.73 | 0.17 | 0.15 | 0.38 | 0.03 |
| AA_half | 1.02 | 0.18 | 0.15 | 0.40 | 0.10 |
| EE_half | 1.19 | 0.06 | 0.02* | 0.42 | 0.17 |
| OH | 0.48 | 0.31 | 0.25 | 0.52 | 0.04 |
| AA | 0.94 | 0.36 | 0.33 | 0.54 | 0.12 |
| EE | 1.15 | 0.12 | 0.13 | 0.42 | 0.19 |

\* Measurement artefacts: on M, the anti-aliased seam line reads as cavity; on EE_half, the 1-2 px teeth slit is missed.

Her rest (idle) measures w 1.00, h 0.39–0.41, lift 0.04–0.07. That is the same drawing as our rest (0.40 / 0.07), so the two scales agree.

## 1. Opening and width per frame
| clip | open level (closed/half/full) | o max | w range | lift range | notes |
|---|---|---|---|---|---|
| talk | 32% / 37% / 30% | 0.48 | 0.61–1.03 | −0.08…0.15 | teeth show in 70 of 145 frames |
| idle | 100% closed | 0 | 0.98–1.01 | 0.04–0.07 | rest |
| idle-long | closed | 0.08 | 1.00–1.10 | up to 0.12 | one soft closed smile |
| smirk | closed | 0.02 | settles at 1.20 | 0.12–0.17 | closed smile; narrowing to 0.95 is head roll up to −33° |
| tongue | 36% / 51% / 13% | 0.55 | 1.32–1.44 | up to 0.29 | wide grin + tongue out, then a wide teeth grin |
| gasp | 18% / 41% / 41% | 0.32 | 0.60–0.77 | down to −0.13 | slow round O, h up to 0.85, corners down |
| startle | 61% / 36% / 3% | 0.39 | 0.46–1.05 | down to −0.17 | small O, corners down |
| glare | closed | 0 | 0.70–0.79 | ≈ −0.03 | pressed, narrow, flat |
| angry | closed | 0.02 | 0.81–0.85 | ≈ 0 | pressed |
| worry | closed | 0.01 | ≈ 0.82 | down to −0.11 | pressed, corners down |
| cheeks, hem | closed | ~0 | ≈ 1.0 | 0.05–0.08 | rest |

**Talk in detail:**
- **How open:** when open, the median opening is o 0.235, between our half (0.18) and full (0.36). The 90th percentile is 0.41 and the max 0.48. 19% of all talk frames open further than our AA. Outer height reaches h 0.83 against our AA's 0.54.
- **Width:** her mouth narrows as it opens. Median w is 0.84 when open and 0.94 when closed. She never goes wider than 1.03 while talking.
- **Per-frame grid shapes:** rest 30%, OH 24%, AA_half 22%, OH_half 15%, AA 6%, M 2%. EE, EE_half and smile never occur.

## 2. Talk timing
- **Cadence:** the talk clip is animated on threes. Of 49 mouth drawings in 6.04 s, 48 last exactly 3 frames (125 ms), which is 8 drawings/s. The in-between frames are near-repeats, with only small encoder or AI wobble (pixel diff 1–4 against about 20–35 at a cut).
- **Transitions:** every change is a hard cut. There are no in-between blends.
- **Shape changes:** grouping consecutive drawings with the same grid shape gives 43 runs, or 7.0 shape changes/s.
- **Hold times:**
  - median 125 ms, p25 125, p75 125, mean 141, max 375.
  - Histogram: 125 ms ×37, 250 ms ×4, 375 ms ×1, plus 42 ms ×1 (the clip end).
- **Closing:** she closes fully 15 times in 6 s (2.5/s, about every 400 ms). The median closed hold is 125 ms. The longest open run is 250–375 ms.
- **Time at each level (per frame):** closed 32%, half 37%, full 30%.
- **Frame-level caveat:** labelling every frame instead of every drawing gives 9.4 changes/s with many 42 ms runs. That is threshold flicker on the in-between frames, not real shape changes.
- **Against our driver** (70 ms minimum hold, 60 ms crossfade):
  - Her shortest real hold is 125 ms, so a 70 ms minimum allows up to about twice her rate.
  - A 60 ms crossfade on a 125 ms hold keeps the mouth mid-transition for about half of every hold. She cuts instantly.

## 3. Smile
- **Closed smile (smirk, steady state):** w 1.20, corner lift 0.15–0.16, h 0.47.
  - Our smile.png is w 1.19, lift 0.20, h 0.44.
  - The width matches. Our corners lift about 25% more than hers, so ours reads slightly more curved.
- **Soft smile (idle-long):** w 1.08, lift 0.10.
- **Wide teeth grin (tongue, end of clip):** w 1.44, lift 0.29, opening 0.17, fully filled with teeth. That is far wider and more curved than our smile (1.19 / 0.20) or EE (1.15 / 0.19).
- **Ramp in:**
  - idle-long soft smile: about 420 ms (frames 53→63; w 1.03→1.08, lift 0.03→0.10).
  - tongue grin: about 290 ms (frames 98→105, in about 3 steps). 90% is reached after about 250 ms.
  - smirk starts already smiling.
- **Ramp out:** not captured. No clip releases a smile.

## 4. Shapes she makes that our 9 don't cover
1. **Wide teeth grin or laugh:** w 1.44, lift 0.29, teeth showing. The clearest gap.
2. **Tall round O with corners down (gasp/startle):** w 0.60–0.77, h up to 0.85, lift −0.10 to −0.17.
   - Our OH is narrower (0.48) and shorter (h 0.52), with slightly up corners.
   - This could be handled by redrawing OH taller and slightly wider with neutral or down corners, rather than adding a shape.
3. **Pressed, narrow closed mouth (glare/angry/worry):** w 0.76–0.83, flat or down corners (−0.03 to −0.11). Our M is full width (0.98). This is an expression shape, not a talk viseme.
4. **Teeth-together talk frames:** 70 of the 145 talk frames show teeth, some with both rows at w 0.83 and o about 0.2. Our AA_half shows only a thin upper-teeth strip.
5. **Tongue out (tongue clip):** a one-off novelty.
6. **Not observed or not measurable:** F/V (lower lip under the upper teeth) and pout. Neither could be seen at this resolution; no clear frames of either.

## Caveats
- **AI video:** these are generated clips, not an animator's timing. The 125 ms cadence reflects how the video was generated (on threes) and may not be a deliberate style. Gasp and startle morph continuously instead, AI in-betweening style.
- **Repeated frames:** in talk, 2 of every 3 frames repeat the drawing. Timing is therefore quantised to 42 ms, and effectively to 125 ms.
- **Low resolution:** her mouth is about 34 px wide in the video. Values are ±0.25 video px after the 4x upscale, or about ±0.01–0.02 in normalised units, and opening classes can flicker at the thresholds.
- **Framing:** framing differs per clip, corrected by iris distance (±2%). Head roll in smirk (up to −33°) and the bows in sad and nod distort width; sad, nod and yawn were excluded.
- **Our shapes:** measured at our resolution with palette classification. The design openings are exact; the measured ones carry the ±1 px artefacts noted above.

## Recommendation
- **Talk driver:**
  - Hold each shape at least about 120 ms, target 125 ms, with occasional 250–375 ms holds on emphasis.
  - Change shape about 7 times/s.
  - Force a full close (rest or M) about every 3–4 shapes: about 2.5 closes/s, closed about 30% of the time, each close about 125 ms.
  - Spend about 37% of the time at half and about 30% at full.
  - Use a hard cut or at most a 30–40 ms crossfade instead of 60 ms. Her talk has no blends, and a 60 ms fade shows the base lips through for half of each 125 ms hold.
  - Weight forms toward OH_half/OH and AA_half. She narrows when she opens, and never uses EE, EE_half or smile while talking.
- **How open:** her "full" talk opening (p90 0.41, max 0.48) is beyond our AA (0.36). Either accept that, or let AA open about 15–30% more. Our half (0.17–0.18) sits a little under her open-frame median of 0.235.
- **Shapes worth adding (in priority order):**
  1. A wide teeth grin or laugh (w about 1.4, lift about 0.28, teeth), for smile and laugh expressions.
  2. A taller OH with neutral or down corners for gasp and surprise. Redraw OH rather than add a new shape if the grid must stay at 9.
  3. Optionally, a narrow pressed mouth for anger or worry, as an expression layer rather than a viseme.
  - Not worth adding: F/V or pout (no evidence) and tongue-out (a one-off).

## Files
- `reference_mouth_frames.csv`: 1,836 rows. Columns: clip, frame, time, raw px measures, teeth and tongue px, roll, iris distance, frame diff, normalised w/h/o/lift, and the grid MouthOpen/MouthForm/shape.
- `reference_stats.json`: per-clip statistics, our shape table, thresholds, and the talk drawing sequence.
- `reference_contact_sheet.png`:
  - Row 1: our 9 shapes.
  - Rows 2–3: talk, one tile per drawing.
  - Rows 4–5: key frames (rest, soft smile, smirk, wide grin, tongue out, talk teeth grin and max open, gasp O, startle, glare, angry, worry).
- Scripts: `measure.py` (per-frame video measurement), `ours.py` (our shapes), `analyze.py` (normalisation, grid mapping, timing, CSV and JSON), `sheet.py` (contact sheet), `checksheet.py` (segmentation QA sheets in `tmp/check_*.png`).
