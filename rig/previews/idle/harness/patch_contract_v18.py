import sys
src,dst=sys.argv[1],sys.argv[2];s=open(src).read()
def R(a,b):
    global s
    if s.count(a)!=1: raise SystemExit('anchor x%d: %r'%(s.count(a),a[:80]))
    s=s.replace(a,b)
R("# Shadowveil base model: runtime contract (v1.7.1)\n\n## Changelog\n",
"""# Shadowveil base model: runtime contract (v1.8)

## Changelog
- **v1.8** (2026-09-30): renderer only; no `rig.json` or part change, rest is still exact (0 px in all five views). New `RootX`/`RootY` root translation and an optional foot plant (section 3, section 7). Posed frames no longer flip between pixel-exact and smoothed drawing on tiny rotations (section 7, Drawing). Auto mode has an `idle` style (default: rest mouth with Base Mouth's soft smile, slow gaze drift that leads the head, Base Eyes' blink timing, readable body idle with foot plant) and a `talk` style (Base Mouth's talk driver: 120 ms minimum hold, 35 ms crossfade or hard cut, no EE/EE_half/smile). Hair: switchable spring presets `default` (unchanged) / `A` / `B`, and every chained segment is clamped to its own limit after chaining. New reference-only section 12 (three-quarter measure targets).
""")
R("| `Wrist{L,R}` | -1 to 1 (±25° about the forearm `wristPivot`; override with hands `wristMaxDeg` or palm `maxWristDeg`, `wristDegAtPlus1`/`wristDegAtMinus1`) | 0 | Base Hands / Base Body (v1.4) |\n",
"""| `Wrist{L,R}` | -1 to 1 (±25° about the forearm `wristPivot`; override with hands `wristMaxDeg` or palm `maxWristDeg`, `wristDegAtPlus1`/`wristDegAtMinus1`) | 0 | Base Hands / Base Body (v1.4) |
| `RootX`, `RootY` | -40 to 40 px (+x right, +y down; applied in whole px) | 0 | renderer / clip player (v1.8) |

**Root (v1.8).** `RootX`/`RootY` translate the body root (the pelvis) and so everything that rides it: every body bone or cut part, the hands, the face and the hair. It is a pure translation of authored images, applied in whole pixels, and only when a body rig (cut parts or skin) is active. At rest it is always 0, so rest is unchanged. A clip may key `RootX`/`RootY`; if it leaves both unkeyed and foot plant is on, the renderer computes them per frame (section 7, Foot plant).
""")
R("- **Hold:** a shown shape stays up at least 70 ms before the next switch, whatever the input, and the 60 ms crossfade finishes inside that hold.",
  "- **Hold:** a shown shape stays up at least 120 ms (v1.8; target 125 ms, was 70 ms) before the next switch, whatever the input, and the crossfade (35 ms in v1.8, was 60 ms; or a hard cut, UI `Mouth switch` / URL `mouthfade=0`) finishes inside that hold.")
R("""- **Blinks:** random intervals of 2–6 s. Each blink closes fast (75 ms, ease-in), holds 35 ms and opens more slowly (170 ms, ease-out). About 18% become a double blink.
- **Gaze:** saccades of 30–90 ms with eased moves, holds of 0.5–2.7 s between, occasional small corrective saccades and returns to centre.
- **Talk:** phrases of 3–10 syllables, each 130–270 ms, eased open→close with a random peak and a random form. There are short gaps inside a phrase and pauses of 0.35–1.45 s between phrases. Shape switching follows the 70 ms hold.
- **Body idle** (only with jointed body parts): slow breathing (4.6 s period) on `BodyLean`, the shoulders and the elbows. Every 7–14 s there's a weight shift, eased over 1.6 s, on the hips and knees (knees counter the hips so the shins stay near vertical), with a slight toe lift on the unloaded side.
- **Hair:** hierarchical damped springs, as in section 4 (Hair).
""",
"""- **Style (v1.8).** UI `Auto style`, URL `auto=idle|talk`. `idle` is the default; `talk` must be selected explicitly.
- **Blinks (v1.8, Base Eyes):** about 330 ms per blink: snap shut in 42 ms, hold 165 ms, reopen in 125 ms (ease-out). Random intervals of 2.5–5 s, both eyes together, upper lid frames only, no double blinks. A head turn that reverses (a `BodyLean` direction change of at least 0.05) also triggers a blink if the last one ended at least 1.5 s ago.
- **Gaze, idle style (v1.8, Base Eyes):** a slow drift of about 0.1 eye width (eye width from the eyes' `measurements.<E>.opening_bbox`, else the white part) that follows the head sway and leads it by 0.1 s (3 frames at 30 fps), plus a slow 9.3 s wander of 20% of that. No big glances. The iris offset is still `irisLimitsPx` rounded to whole px, so in narrow profile eyes it may move 0–2 px only.
- **Gaze, talk style:** saccades of 30–90 ms with eased moves, holds of 0.5–2.7 s between, occasional small corrective saccades and returns to centre (v1.3 behaviour).
- **Mouth, idle style (v1.8, Base Mouth):** `MouthOpen` 0 and `MouthForm` from Base Mouth's keys: rest, then a soft smile (ramp 2.5–2.8 s, hold, ramp 4.6–4.9 s), once per 8 s loop. No talk.
- **Talk style (v1.8 talk driver, Base Mouth):** phrases of 3–10 syllables, each 130–270 ms, eased open→close with a random peak and a random form. Short gaps inside a phrase and pauses of 0.35–1.45 s between phrases. While talk is running, `EE`, `EE_half` and `smile` are never picked (nearest of the remaining shapes). Shape switching follows the 120 ms hold and the 35 ms crossfade or hard cut.
- **Body idle (v1.8, only with jointed body parts; rig units ×25° limbs, ×8° lean):** breathing (4.6 s) on `BodyLean` ±0.22 (±1.76°), minus 0.06 (0.5°) of the weight shift. Shoulders: ±0.03 with the breath plus an independent slow drift ±0.07 (7.1 s / 6.4 s), so each arm moves up to about 2.5°. Elbows: ±0.06 (1.5°) lagging the shoulder drift by 0.35 s. Hips: the weight shift (every 7–14 s, eased over 1.6 s) at 0.1 (2.5°) plus a ±0.02 drift, both hips together, knees countering (`Knee = −Hip`) so the shins stay parallel to rest; slight toe lift on the unloaded side. The root comes from foot plant.
- **Foot plant (v1.8).** UI `Foot plant`, URL `footplant=xy|y|off` (default `xy`). It is applied in auto mode after the body step, and by clip players through `footPlantApply()` whenever a clip leaves `RootX` and `RootY` unkeyed. Sole points are the posed rest-lowest vertices (within 30 px of each foot's lowest point) of the skin vertices dominated by `foot_*`/`toes_*`, or the bottom edge of the `foot_*`/`toes_*` cut parts. `RootY` puts the lower foot's lowest sole point back on the rest foot line. With `xy`, `RootX` also keeps the planted foot's sole centre at its rest x; the two feet are blended smoothly by height (logistic, 2 px), so the planted foot can change without a pop. Both are clamped to ±40 px and drawn in whole px. It is never applied at rest, and not on slider input.
- **Hair:** hierarchical damped springs, as in section 4 (Hair).
  - **Presets (v1.8):** UI `Hair spring`, URL `hair=default|A|B`. Values are roots f / ζ, children f / ζ, child low-pass, gravity: `default` 1.1 Hz / 0.3, 1.0 Hz / 0.3, 0.09 s, 0.8 (unchanged, still the default until the user picks); `A` 4.0 Hz / 0.8 (both), 0.03 s, 0.4; `B` 2.0 Hz / 0.6 (both), 0.05 s, 0.8.
  - **Chained limit (v1.8):** after a segment's drive is computed, its total angle (the sum of its ancestors' angles plus its own) is clamped to its own `swayWeight × maxSwayDeg`, so a tip can never swing further than its own limit relative to the head. When the clamp acts, that segment's spring velocity is reset. This applies to every preset. The slider path (`HairSwayX` without auto) is unchanged.
- **Drawing (v1.8).** Rest is drawn as before, with axis-aligned parts pixel-snapped and exact. In posed frames, only an exactly zero rotation is identity (the old 0.01° snap is gone), and an axis-aligned transform is drawn pixel-exact only if its offset is already whole px; otherwise it is drawn smoothed at its exact position. The root is always whole px. So small rotations no longer flip parts between pixel-exact and smoothed drawing.
""")
R("  - **Both passes:** report blink count, mouth switches and the minimum shape hold. Anything under 70 ms is flagged as FLICKER.",
  "  - **Both passes:** report blink count, mouth switches and the minimum shape hold. Anything under the hold (120 ms in v1.8) is flagged as FLICKER. The passes use the selected auto style.")
s=s.rstrip('\n')+"""

## 12. Three-quarter measure targets (reference only, measure-only)
All five owners agreed to measure the three-quarter angles from the turnaround frames:
- 45°: `reference/apose_turn/frames/f033.png`
- 315°: `reference/apose_turn/frames/f191.png`

Notes:
- (a) f034 was rejected because its body edges are softer (Base Body).
- (b) These edges have a blue fringe, so they need despill before tracing (Base Hair).
- (c) The far eye sits tight to the cheek edge (amber at f033, green at f191). Native angle stills must keep that far eye whole and unclipped, or its lid can't be rigged (Base Eyes).
- (d) The real angle stills must still be native 1365×1739, lossless, with the same camera, height and foot line. Upscaled video frames are for measuring only.

Nothing here is a deliverable format or a renderer change.
"""
open(dst,'w').write(s);print('ok')
