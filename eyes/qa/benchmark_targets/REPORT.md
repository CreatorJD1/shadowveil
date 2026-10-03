# Eye targets for the six benchmarks (Eyes, 2026-10-03 PT)

Files: `sheet.png` (one row per benchmark: benchmark crop | rig at the closest settings | note), `targets.json`, `tiles/`, and scripts `crops.py` + `make_targets.py` (inputs `targets_in.json`, `source_art.json`).
The benchmarks are targets only. Their crops appear on the sheet for comparison and are never used as paint.
Nothing in `rig/` or `views/` was changed. No parts were made.

**Method.** Each benchmark (1120x2240) is cropped to a fixed 200x110 px window centred between the eyes, then zoomed x2.
Rig tiles use the same view-space zoom: apose is a 144x80 view-px window, and the 315 diagonal is a 93x52 frame-px window (view px / 1.54468). Every tile is 400x220.
Renders are Python compositing only. Apose uses `eyes/tools/render_eyes.py` over `views/apose/base.png`. The 315 diagonal uses `eyes/staged/diagonals/render_diag.py` over its turn frame `reference/apose_turn/frames/f191.png`. No browser was used.
Lid frame = round((1-Open)*7).

## Per benchmark
| # | benchmark | view | EyeROpen | EyeLOpen | X | Y | gaps (rig can't) |
|---|---|---|---|---|---|---|---|
| 1 | laugh | 315 | 0 (lid 7) | 0 (lid 7) | 0 | 0 | happy upward closed arch; lower-lid/cheek rise; brow raise; head tilt back (not eyes) |
| 2 | side-eye, annoyed | 315 | 0.71 (lid 2) | 0.71 (lid 2) | +1 | 0 | flat annoyed brow (her R); brow down/in + furrow (her L); lower-lid squint; gaze range (iris only moves 2 frame px) |
| 3 | smirk | apose | 0.86 (lid 1) | 0.86 (lid 1) | 0 | 0 | smug lower-lid rise |
| 4 | cheering | 315 | 1 (lid 0) | 1 (lid 0) | +1 | 0 | wider-than-rest open; brow raise |
| 5 | angry yell | apose | 1 | 1 | 0 | -0.5 | brow down/in + furrow (needs user's OK); upper lid slanted toward the nose; tense lower lid; wider-than-rest glare |
| 6 | sad | apose | 0.43 (lid 4) | 0.43 (lid 4) | +0.5 | +1 | brow inner-up; outer-corner lid droop |

## Where each missing shape exists in her art (boxes are x0,y0,x1,y1 in source px)
Every source below is a **front** view. For the 315/045 diagonals and the left/right profiles, each shape is **to be made**. Plan: a new keyed part on #0000FF, flat colour, using her exact base.png tones, matching her lid/lash (or brow) line weight, the same size in every view, staged only. None has been made yet.

| shape | her sheet (`reference/test_sheet_expressions.jpg`) | Clean room (`reference/grok_build/...`) |
|---|---|---|
| happy upward closed curve | yes: top row, 3rd face [1012,165,1192,265] | **none**: only relaxed/downward closes (`public/clean-room/sheets/faces-locked.jpg` [568,191,788,296], `public/puppet/blink/closed.png` [180,220,520,380], wink in `sheets/reactions-2.jpg` [68,147,288,252]) |
| lower-lid squint/rise | yes: anger face [1441,165,1621,265] | `sheets/reactions.jpg` [775,147,995,252] (laugh squint); `public/puppet/emotions/focus.png` and `smirk.png` [180,220,520,380] |
| wider-than-rest open | yes: bottom row, 3rd face [1012,635,1192,735] | `sheets/reactions.jpg` [75,147,295,252]; `sheets/faces-locked.jpg` [1421,652,1641,757]; `puppet/emotions/shock.png` [180,220,520,380] |
| brow down/in (anger; needs user's OK) | yes: [1441,165,1621,265] | `sheets/reactions-2.jpg` [429,147,649,252]; `puppet/emotions/anger.png` [180,220,520,380]; `sheets/emotions.jpg` [98,47,198,112] (small) |
| brow inner-up (sad) | **no** | `sheets/emo-2.jpg` [115,208,335,313]; `sheets/reactions.jpg` [415,151,635,256]; `puppet/emotions/sorrow.png` [180,220,520,380] |
| flat annoyed brow | **no** | `sheets/emotions.jpg` [715,47,815,112] (small); `sheets/emo-2.jpg` [1023,208,1243,313] (one flat, one raised); `puppet/emotions/focus.png` [180,220,520,380] |
| brow raise | yes: [1012,635,1192,735] | `sheets/reactions.jpg` [75,147,295,252] |
| upper lid slanted in (anger) | yes: [1441,165,1621,265] | `sheets/reactions-2.jpg` [429,147,649,252] |
| outer lid droop (sad) | **no** | `sheets/emotions.jpg` [83,756,183,821] (small, low res) |

The `sheets/` paths are under `public/clean-room/`. The `expr-*.png` screenshots are no help: `expr-anger.png` shows a tiny face, clipped at the top, with a joint dot over the forehead. `expr-joy` and `expr-neutral` show no usable eye shapes.
Gaze range is a rig limit, not art. The 315 diagonal allows +2 frame px at X=+1. Widening it means changing `irisLimitsPx` in the staged diagonal; that is a Coder/user call.

## Odd things
- `public/puppet/rig/expr/*.png` (9 files) are byte-identical placeholders (same md5).
- `public/puppet/emotions/*` and `faces/*` are in a different, more painterly style (purple lips, rendered nose). Treat them as shape guides, not tone sources. `puppet/faces/*.png` are lower-face crops that cut the eyes off.
- `public/clean-room/hires/faces-locked-2.jpg` has open eyes, but panel 2 of `sheets/faces-locked.jpg` has them closed. The hires set is a full-body regeneration, not an upscale of the sheet.
- No head-tilt view exists for the laugh. 315 is the nearest view.
- The 315 diagonal eyes are soft (12-21 px wide in the frame), so they look blurrier than the benchmark at the same zoom.
- The benchmark smirk/sad heads turn slightly to her left. They are rendered in apose because the user called them front.
