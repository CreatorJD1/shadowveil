# Benchmark plan: PARKED (2026-10-03 01:51 PT)

**PARKED by user direction** ("keep focus on the main rigging system and locking in her base model"). The work is saved partway:
- No compare page was built, no compare_<n>.png screenshots, and no IoU scores. Headless renders of the live rig ran out of memory on the shared box (other agents' Chrome instances) and were stopped.
- The presets in `presets/*.json` hold control values with signs inferred from rig.json `rotSign` and pivots. They have **not** been checked by rendering.
- Live files are untouched. Nothing was written to rig/index.html, views/ or rig.json.

Path notes: FORMAT.md is at `rig/partmesh/FORMAT.md`, not `rig/FORMAT.md`. The simple driver is at `app/driver/simple.html`, not `rig/simple.html`.

## What the rig has today (read from rig/index.html, `P`)
- Eyes: EyeLOpen and EyeROpen (8 lid frames, flat-skin lids, upper lid only), EyeBallX and EyeBallY (irisLimitsPx).
- Mouth: MouthOpen and MouthForm. Nearest-shape pick from rest, M, smile, OH/AA/EE in half and full, and anger (0.25,-1).
- Body: BodyLean (8°), plus Shoulder, Elbow, Hip, Knee, Ankle and Toe for L and R (25°, toes +20/-30). RootX and RootY (±40 px), HeadTilt (8°), HeadNod (6°).
- Hands: per-finger curl, per-joint offsets, Spread, ThumbSpread, WristL/R, and Wrist/PalmTwist (snaps to authored hand angles).
- Twists for Shoulder, Forearm, Hip, Knee, Ankle and Neck (skin projection).
- Hooks: same-origin `contentWindow.set(k,x)`/`draw()`/`RigManual()` (used by app/rigctl.js), and `render(g,rest)`. Presets can't be set from the URL.

## Features, ordered by how many benchmarks they unlock
| # | feature | unlocks | FORMAT v0.3 proposal | who |
|---|---|---|---|---|
| 1 | Outfit layer (bodysuit + heeled sandals) on the skin.json meshes, same bones and weights; sleeve cuffs cover the wrist seam | 6/6 | `skin.layers:[{"id":"outfit","image":"views/<v>/body/outfit.png","mesh":"same","z":"over:skin"}]`, with the same vertices and weights as the skin. Sandal parts ride foot_L/R and toes_L/R | Body: art + cut. Coder: renderer reads the layer |
| 2 | Pose/expression presets as JSON holding every control value, with a load/save hook | 6/6 | `{"contract":"preset v0.3","view":..,"values":{Param:x}}`, plus `?preset=<url>` and `window.RigPreset.apply(obj)` | Coder |
| 3 | Brow controls (BrowL/R Y and angle, a mesh band on the head) | 5/6 (all except cheer) | `controls:[{"param":"BrowRY"},{"param":"BrowRAngle"}]` as a partmesh angle-deform band with pinned outer corners, or authored brow swaps. One per side, never mirrored | Eyes: brow cuts from the Clean room still (angry, sad, glare, worry). Coder: params |
| 4 | Corrective blend shapes driven by joint angle (shoulder overhead, elbow past 90°), plus wider joint limits | 4/6 (laugh, hip, cheer, angry) | `correctives:[{"driver":"ShoulderL","at":[90,160],"delta":"mesh vertex offsets"}]` on skin.json, with weights from the angle. The limit is raised only after the hole-free test passes | Body: corrective target meshes. Coder: driver + joint test |
| 5 | Eye shapes: a happy-closed curve, a lower-lid squint and a wide lid (EyeOpen>1). These are authored swaps on the existing EyeOpen axis, plus `EyeSquint` | 4/6 | 3.3 swap: `swap:{"param":"EyeROpen","drawing":[...]}`, extended with `happy` and `squint` sets selected by a param | Eyes: from the Clean room (angry = squint, startle = wide, talk-laugh = happy-closed) |
| 6 | Per-pose draw-order overrides (hand over torso, thumb over the curled fingers in a fist; Thumb1–3 already exists as a chain) | 3/6 (hip, cheer, angry) | `layer:{"over":id}` with `when:{"param":"HandLThumb","op":">","value":0.6}` (3.1a + c) | Coder. Hands: confirm the order |
| 7 | Mouth: a one-sided smirk drawing at MouthForm between rest and smile, and frown, open-smile and yell drawings on the same two controls. No third control, no mirroring | 5/6 | `grid:{"smirk":{"MouthOpen":0,"MouthForm":0.5},"frown":{"MouthOpen":0,"MouthForm":-0.5}}` (the grid already exists) | Mouth: art. Coder: none (the grid is read today) |
| 8 | Palm/back hand sets chosen by wrist roll: two part sets per view with the same names, pivots and wrist cut, swapping sprites only | 2/6 (laugh, hip) | `hands.sets:{"back":"<dir>","palm":"<dir>"},"setBy":{"param":"WristTwistL","palmWhen":">0.5"}` | Hands: palm set. Coder: swap |
| 9 | Head back-tilt limit and neck corrective | 1/6 (laugh) | `HeadNod.degAtMinus1` per view, plus a neck corrective | Body |
| 10 | Diagonal-view posing (3/4 body) | 1/6 (hip) | `"view":"315"` slots (3.6) with fit | Body/all: diagonal art acceptance |

Top 5: outfit, presets, brows, correctives with wider limits, eye shapes. The mouth drawings (7) need no code. They wait only on art.
All new art goes on the user's OK list, and Clean room stills come first (`reference/grok_build/public/clean-room/layers/anim/{hip,smirk,angry,sad,startle,stop}.png`).
