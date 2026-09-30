# Shadowveil base model: runtime contract (v1.8)

## Changelog
- **v1.8** (2026-09-30): renderer only; no `rig.json` or part change, rest is still exact (0 px in all five views). New `RootX`/`RootY` root translation and an optional foot plant (section 3, section 7). Posed frames no longer flip between pixel-exact and smoothed drawing on tiny rotations (section 7, Drawing). Auto mode has an `idle` style (default: rest mouth with Base Mouth's soft smile, slow gaze drift that leads the head, Base Eyes' blink timing, readable body idle with foot plant) and a `talk` style (Base Mouth's talk driver: 120 ms minimum hold, 35 ms crossfade or hard cut, no EE/EE_half/smile). New head params `HeadTilt` (roll, ±8°) and `HeadNod` (pitch, ±6°) on the body's head part, pivoting at the neck seam, with a renderer-side neck gate so the seam stays closed (section 3). Hair: switchable spring presets `default` (unchanged) / `A` / `B`, every chained segment is clamped to its own limit after chaining, and the springs now also get the head's acceleration (root motion, lean and head params) as an inertia input (section 7). Posed frames use one resampling path (`ss2` default) and an edge seal. Mouth crossfade: incoming from the switch frame, outgoing fades over the last half. Blinks: ease-in reopen, 2.5 s minimum gap including turn blinks. New idle `Life` layer (section 7). Render-only stress bypass for `stressTest` clips. New reference-only section 12 (three-quarter measure targets).
- **v1.7.1** (2026-09-30): documentation only. The five v1.7 outfit-band open items are resolved by the owners (section 11): clips ride the strand root, three profile cloth rules (far body cloth 207–209, far-hand wear 216–218, near and centre cloth = skin + 40), explicit front-view cloth layers, and side-view hair rules for back. Finger parameters corrected to one curl per finger (`Hand{L,R}<Finger>`), with frames switching at curl 0.25 and 0.75. No code or `rig.json` change.
- **v1.7** (2026-09-30): documentation only. Reserved outfit / wear layer bands for a future outfit auto-skinner, plus a planned outfit package format (section 11). Nothing uses these bands yet; no code or `rig.json` change, and nothing new is rejected. No current part layer falls in a reserved band.
- **v1.6.1** (2026-09-30): Layers panel shows separate eye white and iris rows (layers read from the eyes' `rig.json`); unchained single-part hair shows as a plain row; `rest_check.py` takes every eye layer (white, iris, lid, lash) from the eyes' `rig.json`. Rendering and rest are unchanged.
- **v1.6** (2026-09-30): Layers panel in `rig/index.html`, preview only (section 10). No format change and no owner action needed: `rig.json` stays the source of truth, and rest is still exact (0 px in all five views).
- **v1.5.1** (2026-09-29): joint test only. For the hips, only the outer hip outline along the seam is scored. The medial side (the inner crotch edge between the thighs, below the pelvis) is left out of holes, tears, seam alpha and outline width. No format or renderer change; rest is unaffected.
- **v1.5** (2026-09-29): skin underlay, and a seam-based joint test. Rest is still exact (0 px in all five views).
  - Optional `underlay` in `skin.json`: a second textured mesh of a Base Body image, drawn beneath the main skin mesh. It carries flat fill under the limbs that only shows when a limb swings out. It's valid only if its rest footprint is completely hidden by alpha-255 main-skin pixels drawn above it; otherwise it's rejected with a warning and not drawn (section 9).
  - New validator `rig/skin_tools/check_underlay.py`, and a draft generator `rig/skin_tools/make_underlay.py` that writes to the drafts folder only.
  - The joint test now scores every joint along the whole parent/child seam (skin: where the dominant weight switches; cut: the visible part boundary) instead of a disc around the pivot (section 8).
  - `?skin=draft:<view>_<name>.json` and `rest_check.py --skin=draft:<view>_<name>.json` load a named draft for that view only.
- **v1.4** (2026-09-29): weighted mesh skinning for the body, plus robustness fixes. Rest is still exact (0 px in all five views).
  - Optional `views/<view>/body/skin.json`: one triangle mesh over the authored body image, deformed by linear blend skinning (≤4 bone weights per vertex, summing to 1). When it's declared and valid, it replaces the cut body parts. Drawn with WebGL textured triangles of the authored pixels (section 8).
  - New parameters `WristL`/`WristR`: the palm rotates about the forearm `wristPivot`, ±25° by default (section 3).
  - Filtering modes for rotated or deformed pixels: nearest, linear, and 2× supersampled. There's also a joint test that measures holes and outline width at each joint bent to 25° (section 8).
  - Parts with `"file": null` never override, dedupe or re-layer a part that has a file. Per id, the entry with a file wins (section 4).
  - Views without a face (`back`) never request eyes or mouth files. An empty face `rig.json` (no parts) means "no part set". Every optional face field has a null-safe default (section 4).
  - Hands: a finger frame entry may carry its own `layer` (section 4, Hands).
  - No speculative requests: the renderer fetches only files that a `rig.json` lists (plus the fixed per-owner `rig.json`), so a clean load makes no 404s.
- **v1.3** (2026-09-29): renderer quality pass. No new animated parameters, and rest is still exact.
  - Mouth half-open row: optional `<shape>_half` shapes at MouthOpen 0.5, picked by nearest shape, with a 70 ms minimum hold (section 4, Mouth).
  - Eye lid frame count from a top-level `"lidFrames": n` in the eye `rig.json` (default 5). Frame = round((1−Open)×(n−1)) (section 4, Eyes).
  - Crossfade rule: outgoing image at full opacity with incoming on top, everywhere. Finger and lid frames hard-switch (section 5).
  - Body: `ToeL`/`ToeR` parameters on `toes_L`/`toes_R` parts parented to each foot, included lightly in the idle weight shift (sections 3 and 4, Body).
  - Hands: optional per-segment `layerCurled` and `curlLayerAt` so curled segments can tuck behind the palm (section 4, Hands).
  - Hair strands may be chained root→mid→tip. Secondary motion is hierarchical and uses a per-part drive that stays inside the existing sway limits (section 4, Hair).
  - Auto mode: eased, stochastic idle (section 7).
  - Pixel snapping and a fixed smoothing policy (section 1).
  - Motion quality test (section 7).
- **v1.2** (2026-09-29)
  - One global integer `layer` per part with owner bands, including a body-band exception for profile views (section 5). Old numbering still renders the v1.1 way until the owner renumbers.
  - Optional finger frames f0..f2 per finger and thumb segment, listed in the part's `frames` field (a filename, or `{file, pivot, childPivot}`), picked by curl. Children attach at the current frame's `childPivot`, and frames are never scaled (section 4, Hands).
  - Hair: per-part `swayY` weight and top-level `swayYMaxPx` for `HairSwayY` (section 4, Hair).
  - Body joints (placeholder): `views/<view>/body/rig.json`, parameters `BodyLean`, `Shoulder/Elbow/Hip/Knee/Ankle{L,R}`, forearm `wristPivot`, palms parented to the forearm (sections 3 and 4, Body).
- **v1.1**: baseline.

This is what the renderer loads and what each part owner (Base Body, Base Eyes, Base Mouth, Base Hands, Base Hair) must deliver. If a delivery doesn't meet this, the renderer rejects it instead of patching over it.

## 1. The hard rule

The renderer only ever draws authored part images, using `drawImage` of a keyed PNG with a transform (translate, rotate, scale) and opacity. It never uses `arc`, `ellipse`, `stroke`, `fill`, `fillRect`, `lineTo`, paths, gradients or text on the character canvas. It never draws anything over her eyes or mouth, and it never tints, recolours or clips a face part at runtime.

Rendering quality (v1.3):
- Any transform with no rotation or scale is snapped to whole pixels and drawn with smoothing off, so it's an exact copy. That covers rest, iris offsets, `swayY` and `childPivot` offsets.
- A rotated transform is always drawn with high-quality smoothing, so the filter never switches between frames. Rotations under 0.01° count as 0.
- The renderer may crop each loaded part to its alpha bounding box and draw it at the matching whole-pixel offset. That's an exact copy of the authored pixels, done only for speed.

Enforcement:
- The renderer wraps its 2D context so any call other than `drawImage`, `save`, `restore`, `setTransform`, `translate`, `rotate`, `scale`, `globalAlpha`, `globalCompositeOperation` and `clearRect` throws in dev builds.
- A CI check (grep) fails the build if the character renderer contains `arc(`, `ellipse(`, `stroke`, `fill`, `Path2D` or `lineTo`.
- A reference test renders every view at rest and compares it pixel for pixel with the view's original `base.png` (never with `base_body.png`). Rest must be identical: no parts may change the drawing when every parameter is at its default.

## 2. Views and body height

| View id | Base drawing | Face parts |
|---|---|---|
| `apose` | `views/apose/base.png` | both eyes, mouth |
| `tpose` | `views/tpose/base.png` | both eyes, mouth |
| `left` | `views/left/base.png` | the one visible eye, mouth (profile shapes) |
| `right` | `views/right/base.png` | the one visible eye, mouth (profile shapes) |
| `back` | `views/back/base.png` | none |

- Every view's canvas has the same pixel size W×H as `apose`. The top of her head and her foot line sit at the same y in all five views. Base Body owns this and states the two y values in `views/body.json`. The renderer checks every view against them and refuses a view that's off by more than 1 px.
- All coordinates in manifests are in that view's pixels, origin top-left. The loader never rescales one view to fit another.
- Profile views name the eye they show (`EyeL` or `EyeR`), so her amber right eye and green left eye are never swapped.

## 3. Parameters

All parameters are floats that the renderer clamps to their range. Default is the value at which the part shows exactly the drawn face or pose.

| Parameter | Range | Default | Owner |
|---|---|---|---|
| `EyeLOpen` | 0 closed to 1 open | 1 | Base Eyes |
| `EyeROpen` | 0 to 1 | 1 | Base Eyes |
| `EyeBallX` | -1 (her right, viewer's left) to 1 | 0 | Base Eyes |
| `EyeBallY` | -1 up to 1 down | 0 | Base Eyes |
| `MouthOpen` | 0 to 1 | 0 | Base Mouth |
| `MouthForm` | -1 narrow to 1 wide | 0 | Base Mouth |
| `Hand{L,R}{Thumb,Index,Middle,Ring,Pinky}` | 0 to 1 curl (one value per finger; it drives all 3 segments, and drawn frames switch f0→f1 at 0.25 and f1→f2 at 0.75) | 0 | Base Hands |
| `Hand{L,R}ThumbSpread` | -1 across the palm to 1 out | 0 | Base Hands |
| `Hand{L,R}Spread` | 0 together to 1 fanned (index, ring, pinky) | 0 | Base Hands |
| `HairSwayX` | -1 to 1 | 0 | runtime motion input, shaped by Base Hair |
| `HairSwayY` | -1 to 1 | 0 | runtime motion input, shaped by Base Hair |
| `BodyLean` | -1 to 1 | 0 | Base Body (placeholder, v1.2) |
| `Shoulder{L,R}`, `Elbow{L,R}`, `Hip{L,R}`, `Knee{L,R}`, `Ankle{L,R}` | -1 to 1 | 0 | Base Body (placeholder, v1.2) |
| `Toe{L,R}` | -1 to 1 (about −30° to +20° through the part's own limits) | 0 | Base Body (v1.3) |
| `Wrist{L,R}` | -1 to 1 (±25° about the forearm `wristPivot`; override with hands `wristMaxDeg` or palm `maxWristDeg`, `wristDegAtPlus1`/`wristDegAtMinus1`) | 0 | Base Hands / Base Body (v1.4) |
| `RootX`, `RootY` | -40 to 40 px (+x right, +y down; applied in whole px) | 0 | renderer / clip player (v1.8) |
| `HeadTilt` | -1 to 1 (±8° roll about the neck seam; + = clockwise on screen) | 0 | Base Body (v1.8) |
| `HeadNod` | -1 to 1 (±6° pitch; + = chin down / forward) | 0 | Base Body (v1.8) |

**Root (v1.8).** `RootX`/`RootY` translate the body root (the pelvis) and so everything that rides it: every body bone or cut part, the hands, the face and the hair. It is a pure translation of authored images, applied in whole pixels, and only when a body rig (cut parts or skin) is active. At rest it is always 0, so rest is unchanged. A clip may key `RootX`/`RootY`; if it leaves both unkeyed and foot plant is on, the renderer computes them per frame (section 7, Foot plant).

**Head (v1.8).** `HeadTilt` and `HeadNod` move the body's head part (cut part `head`, or the skin's `headBone`) about the neck seam centre, which the renderer finds at load: the centroid of the head-mesh vertices that touch torso vertices (apose 681,364; tpose 673,356; left 693,378; right 678,379; back 682,350), or the head part's pivot for cut parts. Everything that already rides the head moves with it as one block: eyes (400–403, 410–413 and the eye band 450–499), mouth (500, 510–519, 550–599), hair_back 100, the bun (101/650), hair_front 600, strand roots 601–619 with their chained children, and the hair bands 110–199 and 660–699. In the front and back views `HeadTilt` is a rotation of ±8°, and `HeadNod` is a vertical offset of ±4 px (+ = down) with no in-plane rotation, because an in-plane rotation there would read as a tilt. In the profiles `HeadNod` is a real ±6° rotation toward the facing side (left view counter-clockwise, right view clockwise for +1), and `HeadTilt` is not drawn (a roll is about the viewing direction's normal and has no clean in-plane equivalent). **Neck gate:** with a skin mesh the head vertices within 36 px of the seam blend from the torso transform (at the seam) to the head transform (36 px up, smoothstep). The weights are the renderer's own copy; `skin.json` is untouched. At `HeadTilt = HeadNod = 0` the head transform equals the torso transform, so the blend changes nothing (rest and all v1.7 poses render exactly as before). Measured at ±1 of each param alone: 0 px of alpha loss at the seam in all five views. With cut parts (skin off) there is no gate, and the head is a rigid rotation. The eyes and mouth sit at least 60 px from the seam, so they stay rigid with the head. `headPose()` reads the new head angle, so the hair springs react to it.

Nothing else may be animated. A new parameter needs a version bump of this contract.

## 4. Part files and manifests

Layout, one folder per view and owner:

```
views/<view>/base.png
views/<view>/eyes/   rig.json + parts
views/<view>/mouth/  rig.json + parts
views/<view>/hands/  rig.json + parts
views/<view>/hair/   rig.json + parts
views/<view>/body/   rig.json + parts  (v1.2, optional: jointed body; replaces base_body.png when present)
views/<view>/base_body.png  (Base Body: hands and hair cleared, drawn by the renderer)
views/body.json      (Base Body: canvas size, head-top y, foot-line y)
hands/<view>_hand_erase_mask.png, hair/<view>_hair_erase_mask.png  (owners' erase masks; parts must fully cover them at rest)
```

Every part file:
- Chroma key colour is `#0000FF`.
- Hand and hair parts are cut from her drawn pixels in the cleaned `base.png`, so rest matches exactly. Flat-colour repainting is only for areas the drawing doesn't show (a curled finger's hidden side, a mouth's skin underlay).
- Is an RGBA PNG, already keyed off chroma blue, with alpha only. The renderer does no keying. A delivered part with any leftover chroma-blue pixel (within the agreed tolerance) or a white background fails validation.
- Is flat colour, with no shadows or lighting, as the brief says.
- Is cut from, or drawn to match, her existing drawing at the same scale.
- Has its pivot and placement given in the owner's `rig.json`, in view pixels:
  `{ "id", "file", "x", "y", "pivotX", "pivotY", "parent", "layer" }`

**Manifest robustness (v1.4).**
- A part with `"file": null` (hidden or placeholder, e.g. a far thigh that shares the near thigh's pivots) is kept for the joint chain only. It never replaces, dedupes or re-layers a part with a file. For each id, the first entry with a file wins, and later duplicates are ignored with a warning.
- A `rig.json` with no parts (`{"parts": []}`, `[]` or `{}`) means "no part set". The renderer and `rest_check.py` skip it without error and report it as `empty`, not missing.
- Faceless views (`back`) never request `eyes/rig.json` or `mouth/rig.json`, so the file may exist or not.
- Missing face fields get neutral defaults: `irisLimitsPx` → 0 travel, `lidFrames` → 5 (a numeric string is accepted), `eyes` → derived from `<E>_white` part ids, mouth `grid` → `{}`, eye `workRegion` and mouth `partsBBox` → not used.

### Eyes (Base Eyes)
Per visible eye `<E>` in `EyeL`, `EyeR`:
- `<E>_white.png`: the eye white cut from the drawing.
- `<E>_iris.png`: the drawn iris with its own colour (right amber, left green) and the pupil as drawn. Moves inside the white by `EyeBallX` and `EyeBallY`, up to a max offset in px set in `rig.json`, and only shows inside the white. The renderer does that by compositing each eye on its own offscreen layer: it draws `<E>_white`, then draws `<E>_iris` with `globalCompositeOperation = "source-atop"`, so the white's own alpha is the mask. No clip path or shape is ever drawn.
- `<E>_lid_0.png` to `<E>_lid_4.png`: upper lid frames from open (0, which must be empty or match the drawn lid exactly) to closed (4). `EyeLOpen` = 1 shows frame 0, 0 shows frame 4, with nearest-frame selection (no morphing).
- **Lid frame count (v1.3).** Each view's eye `rig.json` may set a top-level `"lidFrames": n`. The files are then `<E>_lid_0` … `<E>_lid_{n-1}`, each listed as a part (planned n = 8). Without `lidFrames`, the count is 5 (`lid_0..4`), as before.
  - Selection: frame = round((1 − `<E>Open`) × (n − 1)), so Open 1 gives `lid_0` and Open 0 gives `lid_{n-1}`.
  - `lid_0` must still match the drawn lid exactly.
  - Lid frames hard-switch to the nearest frame and are never crossfaded.
- `<E>_lash.png`: the drawn lash line and lid edge, on top.
A blink is only the lid frames covering the drawn eye. There is no replacement eye.

### Mouth (Base Mouth)
The six drawn shapes sit on a 2-parameter grid, one PNG each, drawn as real mouths:

| Shape | MouthOpen | MouthForm |
|---|---|---|
| `rest` | 0 | 0 |
| `M` | 0 | -1 |
| `smile` | 0 | 1 |
| `OH` | 1 | -1 |
| `AA` | 1 | 0 |
| `EE` | 1 | 1 |

The renderer picks the nearest shape on the grid, with a small crossfade over 60 ms when switching (opacity only, nothing drawn). Under the v1.3 crossfade rule (below), the outgoing shape stays at full opacity and the incoming shape fades in on top.

**Half-open row (v1.3, optional).** Base Mouth may add shapes at MouthOpen 0.5, named `<shape>_half` and listed in the mouth `rig.json` the same way as full shapes (`"id": "mouth_<shape>_half"`, plus `file` and `layer`):

| Shape | MouthOpen | MouthForm |
|---|---|---|
| `OH_half` | 0.5 | -1 |
| `AA_half` | 0.5 | 0 |
| `EE_half` | 0.5 | 1 |

- **Coordinates**, first match wins:
  1. the shape's own part entry in `rig.json`, if it has `"MouthOpen"` and `"MouthForm"`;
  2. the `grid` entry with that shape's name;
  3. the table above, or the full-shape table.
- Any other half shape (for example `M_half`, `smile_half`) must state its coordinates. A shape without coordinates is ignored with a warning.
- **Selection:** the nearest shape by Euclidean distance in (MouthOpen, MouthForm) over every delivered shape, half row included. Ties go to `rest`, then the more closed shape, then manifest order. With no half shapes delivered, this is exactly the v1.2 six-shape grid.
- **Hold:** a shown shape stays up at least 120 ms (v1.8; target 125 ms, was 70 ms) before the next switch, whatever the input, and the crossfade (35 ms in v1.8, was 60 ms; or a hard cut, UI `Mouth switch` / URL `mouthfade=0`) finishes inside that hold. So a shape never flickers. `rest` at (0, 0) must match the drawn mouth exactly. Each shape covers the drawn mouth fully so no part of the old mouth shows around it.

### Hands (Base Hands)
Per hand `<H>` in `L`, `R`:
- `<H>_palm.png`.
- For each of `Index`, `Middle`, `Ring`, `Pinky`: `<H>_<Finger>1.png`, `2.png`, `3.png` (base, middle, tip segment). 1's parent is the palm, 2's is 1, 3's is 2.
- Thumb, separate chain on its own pivot at the base of the palm: `<H>_Thumb1.png` (base, parent palm), `2.png`, `3.png`.
- Each joint's `rig.json` entry adds `maxCurlDeg`. Curl 1 rotates that segment by `maxCurlDeg` about its pivot. There is no single hand bone and no part spans two joints, so a finger can curl without moving the palm.
- Views where a finger is hidden still list it, with `"hidden": true`.
- **Finger frames (v1.2, optional).** A finger or thumb segment's `rig.json` entry may carry a `"frames"` list (f0..f2, for example `L_Index2_f0.png`, `_f1`, `_f2`).
  - Each entry in a part's "frames" list may be either a filename string or an object {"file": "..._f1.png", "pivot": [x,y], "childPivot": [x,y]} in the part's canvas pixel coords. pivot overrides the part's pivot for that frame; childPivot is where child segments attach for that frame (defaults to the child's own pivot as today). Both forms are supported.
  - Frames are loaded only from the `frames` field. Files are named `<part>_f0.png`, `_f1`, `_f2` by convention, but the renderer doesn't probe for unlisted files. A missing listed file disables that segment's frames with a warning.
  - f0 must be pixel-identical to the part's `file`, and its `pivot`/`childPivot` (if given) must equal the part's pivot and its child's pivot. Otherwise the renderer ignores that segment's frames and warns, so rest never changes.
  - All frames use the same full view canvas (W×H, x=y=0) and the same `rig.json` entry. The segment still rotates by curl × `maxCurlDeg`, about the current frame's pivot.
  - Child segments attach at the current frame's joint point: the child is translated so its pivot lands on the parent frame's `childPivot`, then rotates about its own (frame) pivot. This keeps a foreshortened frame's joint attached.
  - No per-frame scale. Resampling would change her line weight, so foreshortening must be drawn into the frame.
  - Selection is the nearest frame by that segment's curl: index = clamp(floor(curl × (n−1) + 0.5), 0, n−1). With 3 frames that's floor(curl×2+0.5): curl 0 gives f0 and curl 1 (max curl) gives f2. No morphing.
  - A segment's curl is its finger's `Hand{L,R}<Finger>` value (e.g. `HandRMiddle`), which drives all 3 joints. There are no per-joint parameters such as `HandRMiddle1..3`. With 3 frames the switch points are curl 0.25 (f0→f1) and 0.75 (f1→f2).
  - Segments without frames draw their `file` as before. Rest (curl 0) must stay 0 px.
- **Curled layer (v1.3, optional).** A finger or thumb segment may carry `"layerCurled"`, an integer in the same hands band, plus `"curlLayerAt"` (default 0.5).
  - When that segment's curl is at least `curlLayerAt`, it sorts at `layerCurled` instead of `layer`. This lets a folded segment tuck behind the palm.
  - The layer switch is a hard switch, like frames. It applies only to v1.2-numbered hand manifests.
  - A `layerCurled` outside the band is ignored with a warning.
  - Rest (curl 0) always uses `layer`, so rest is unaffected.
  - v1.4: a frame entry may also carry `"layer"` (same band). While that frame shows, the segment sorts at that layer, which takes precedence over `layerCurled`.
- **Hand layers (v1.2):** R hand 300–315, L hand 320–335. A far hand in a profile view uses 210–215 (inside the 210–219 far-hand slot, section 5).
- **Palm parenting:** palms carry `parentExternal: "forearm_L"` or `"forearm_R"`. When that body forearm exists (body rig active), the palm and all its fingers follow the forearm's transform (section 4, Body). With no body forearm, the hand stays where it's drawn, as in v1.1.

### Hair (Base Hair)
- `hair_back.png` (behind the head), `hair_front.png` (fixed, over the forehead), `bun.png`, and `strand_01.png` onwards.
- Each swaying part has `swayWeight` 0 to 1 and `maxSwayDeg` in `rig.json`. Its rotation is `swayWeight × maxSwayDeg × HairSwayX`, about its pivot, and chains through `parent`. Weight 0 means the part never rotates.
- **Vertical sway (v1.2).** Each part may carry `swayY`, a weight from 0 to 1 that defaults to 0 when missing. The hair `rig.json` is an object `{ "swayYMaxPx": <px>, "parts": [...] }`. A bare list is still accepted and means `swayYMaxPx` = 0.
  - Offset: `dy = HairSwayY × swayY × swayYMaxPx`, rounded to whole pixels.
  - The offset only translates that part's authored image vertically. It is applied after the part's sway rotation, is not inherited by child parts, and never scales, stretches or redraws anything.
- **Chained strands (v1.3).** A strand may be split into root→mid→tip segments, each parented to the one above (`parent`). Each segment rotates about its own pivot in its parent's transformed space, so joints can't separate.
- **Secondary-motion drive (v1.3).** The rotation formula stays `swayWeight × maxSwayDeg × s`, but `s` may be a per-part drive in [-1, 1] instead of the single `HairSwayX`. The same applies vertically: `dy = s_y × swayY × swayYMaxPx`. With the slider, every part's `s` equals `HairSwayX`. In auto mode, each part's `s` is a damped spring:
  - **Chain roots** are driven by head tilt (hair keeps hanging), head velocity and a slow wind term. Each chain has its own phase, so strands don't move in lockstep.
  - **Each child** follows its parent's drive through an extra low-pass lag (about 0.2 s per level), so the tip trails.
  - Every part's own `swayWeight` sets how far it actually moves.
- A part's `s` never exceeds ±1, so no part turns further than its own `maxSwayDeg`. **Base Hair validation must sweep each segment's `s` independently in [-1, 1]** (not one shared value), because chained segments can be out of phase.
- No hair part may cover her eyes or mouth in any view at any sway value. The renderer's test sweeps sway from -1 to 1 and fails if any hair pixel lands on an eye or mouth part.

### Body joints (Base Body, v1.2: `apose` delivered; other views keep `base_body.png` until their `views/<view>/body/rig.json` lands)
- `rig.json` is `{ "headPart"?: "torso", "parts": [ { "id", "file", "pivotX", "pivotY", "parent", "layer", "maxRotDeg" (alias "maxDeg") | "degAtPlus1"/"degAtMinus1", "param"?, "wristPivot"? } ], "paramMap"?: { "<Param>": "<partId>" } }`. Part PNGs use the full canvas like hands.
- Expected ids and their default drivers: `pelvis` (root), `torso` → `BodyLean`, `upperArm_{L,R}` → `Shoulder{L,R}`, `forearm_{L,R}` → `Elbow{L,R}`, `thigh_{L,R}` → `Hip{L,R}`, `shin_{L,R}` → `Knee{L,R}`, `foot_{L,R}` → `Ankle{L,R}`, `toes_{L,R}` → `Toe{L,R}` (v1.3; parent defaults to `foot_{L,R}`). A part's `param` (null means not driven) overrides the driver, and so does a top-level `paramMap`.
- Rotation about the part's pivot: `value × degAtPlus1` for value ≥ 0, `|value| × degAtMinus1` for value < 0. `maxRotDeg` (or `maxDeg`) gives the symmetric case (`degAtPlus1 = maxRotDeg`, `degAtMinus1 = −maxRotDeg`).
- Default parents when `parent` is omitted: torso→pelvis, upperArm→torso, forearm→upperArm, thigh→pelvis, shin→thigh, foot→shin.
- **Toes (v1.3).** `toes_L` and `toes_R` are separate parts parented to each foot and driven by `ToeL` and `ToeR`. Limits come from the part's own `degAtPlus1`/`degAtMinus1`, or from Base Body's `maxRotDeg`/`minRotDeg`/`rotDir` rule: deg = rotDir × (v < 0 ? −v × minRotDeg : v × maxRotDeg). This rule applies to every body part; without `minRotDeg` it's symmetric. A toe that can't be separated in a view is listed with `file: null` and `hidden: true` and stays drawn as part of the foot. If none are given, the renderer assumes about +20° at +1 and −30° at −1.
- **Sliders:** only parameters that drive a delivered body part are enabled, so the toe sliders stay disabled until `toes_L`/`toes_R` exist.
- **Idle:** the weight shift lifts the unloaded side's toes slightly, by 0.05 of their range.
- `forearm_{L,R}` carries `wristPivot: [x, y]`. Each hand's palm (`parentExternal`, default `forearm_<H>`) is parented to that forearm, so the whole hand chain follows the arm. The palm's own pivot must sit on `wristPivot` within 2 px, or the renderer warns.
- Eyes, mouth and hair ride on `headPart` (default `head` if present, else `torso`), so a lean moves the face as a unit.
- **Activation:** only when `body/rig.json` exists and lists at least one part whose file loads. Otherwise the renderer draws `base_body.png` exactly as in v1.1 and hides and disables the body sliders.
- Rest (every body parameter 0) must still match `base.png` to 0 px.

## 5. Draw order (back to front)

### v1.2 global layer scheme
Every part has one integer `layer`. All parts from all owners go into one list, and lower layers draw first. Ties keep this order: owner step (hair_back, body, hands, eyes, mouth, hair_front), then manifest order. The renderer sorts only by these numbers and never reorders at runtime. Owners can order freely inside their band.

| Band | Owner / parts |
|---|---|
| 100–199 | `hair_back` and any hair behind the body (for example the bun in front views) |
| 200–299 | body (see the profile exception below). `base_body.png`, while it's still used, sits at 220 |
| 300–399 | hands (near or visible hands) |
| 400–499 | eyes (the current 400–413 is fine) |
| 500–599 | mouth (currently 500) |
| 600–699 | `hair_front`, strands, and the bun when it's in front |

**Profile-view exception inside the body band:**
- far arm and far leg: 201–209
- far hand (Base Hands' parts): 210–219
- torso and pelvis: 220 and up

Because the renderer only sorts by layer, hand parts at 210–219 draw under the torso (and under `base_body.png` at 220 until jointed body parts arrive). Hands are the only non-body owner allowed in the body band, and only in 210–219.

Eyes: `<E>_white` (with `<E>_iris` composited into it, source-atop), the lid frame, and `<E>_lash` each draw at their own `layer`. Mouth shapes draw at their own `layer`. During a crossfade, both shapes draw at the incoming shape's layer, with the outgoing one first.

**Crossfade rule (v1.8, applies everywhere).** The incoming image starts at 25% opacity on the switch frame itself (so no frame is lost) and reaches 100% at 3/4 of the fade. The outgoing image stays at full opacity for the first half, then fades to 0 over the second half. So there is no opaque underlay for the whole fade (v1.3 had one, which doubled the outline in the profiles at smile→rest), and the two never sit at low opacity together. With the 35 ms mouth fade this is one or two 60 Hz steps. A hard cut (`mouthfade=0`) skips both. Shape choice: the nearest grid shape to (`MouthOpen`, `MouthForm`). An exact tie between `rest` and another shape (for example `MouthForm` = 0.5) resolves to the other shape, the target. At the rest point itself `rest` is at distance 0 and always wins.

**Frame sets hard-switch.** Finger frames (`frames`, f0..f2) and eye lid frames (`<E>_lid_k`) always switch straight to the nearest frame. They are never crossfaded or blended.

**Backward compatibility:** a manifest counts as v1.2-numbered when every part that has a `file` carries an integer layer inside its owner's band(s). Otherwise the renderer treats the manifest as old numbering and maps it into the band in the order the v1.1 renderer drew it:
- hair: `hair_back` goes to 100 and up. The rest go to 600 and up, sorted by old layer.
- hands: sorted by old layer, from 300 up.
- eyes: per eye in `eyes` order, white/iris, then lid, then lash, from 400 up.
- mouth: 500.

Old deliveries therefore render exactly as in v1.1 until the owner renumbers. Parts without a `file` (hidden fingers) don't count toward detection.

The v1.1 step list below is the order that old numbering maps to.

Front views (`apose`, `tpose`):
1. `hair_back`
2. `base_body.png` (Base Body: `base.png` with the hand and hair areas from the owners' erase masks cleared; face untouched)
3. Hands: palm, then Pinky, Ring, Middle, Index (1, 2, 3 each), then Thumb (1, 2, 3). A hand in front of the body is drawn after the body; a hand behind it (per `rig.json` `layer`) before the body.
4. Eyes, for each eye: white, iris, lid frame, lash
5. Mouth shape
6. `hair_front`, then strands, then `bun` (only if the bun is in front in that view)

Profile views: same order, with only the visible eye and the far hand drawn before `base_body.png`.

Back view: `hair_back`, `base_body.png`, hands, then hair parts including the bun on top. No face parts.

Order is fixed by each part's global `layer` (v1.2 scheme above). The renderer sorts by layer and never reorders at runtime.

## 6. What each owner hands over
- **Base Body:** five `base.png` views at one W×H, `body.json`, and the rule that head-top and foot line match within 1 px.
- **Base Eyes:** eye parts and `rig.json` for `apose`, `tpose`, `left`, `right`, with rest matching the drawing.
- **Base Mouth:** the six shapes and `rig.json` for `apose`, `tpose`, and profile shapes for `left`, `right`. Optionally (v1.3) the half-open row `OH_half`, `AA_half`, `EE_half` (and other `_half` shapes with explicit coordinates).
- **Base Hands:** both hands, 5 fingers × 3 segments plus palm, per view, with pivots and `maxCurlDeg`.
- **Base Hair:** hair parts with `swayWeight`, `maxSwayDeg`, `swayY` (v1.2), `layer` per view, and `swayYMaxPx` in each `rig.json`.
- **Base Body (v1.2, when ready):** `views/<view>/body/rig.json` and jointed parts per section 4, with forearm `wristPivot`, layered per the body band.

The renderer accepts a delivery only if validation passes: files are listed, every PNG is keyed with alpha, rest renders identical to `base.png`, no hair or hand pixel covers the eyes or mouth at rest, and (v1.2) every finger `_f0` equals its part and all frames share the canvas size.

Open item (v1.2): the dev guard, the grep CI rule and `rig/rest_check.py` (a Python mirror of the renderer's layer, frame and body logic) are the enforcement. The hair-over-face sweep does not yet include `HairSwayY`.

## 7. Auto mode and motion quality (v1.3, renderer only)
Auto mode only sets parameter values (and the per-part hair drive above). Everything on screen is still a transform or frame choice of authored images, and turning auto off returns control to the sliders.
- **Style (v1.8).** UI `Auto style`, URL `auto=idle|talk`. `idle` is the default; `talk` must be selected explicitly.
- **Blinks (v1.8, Base Eyes):** about 330 ms per blink: snap shut in 42 ms, hold 165 ms, reopen in 125 ms with an ease-in, so the lid reads shut (open < 0.5) for about 250 ms. Random intervals of 2.5–5 s after the previous blink ends, both eyes together, upper lid frames only, no double blinks. A head turn that reverses (a `BodyLean` direction change of at least 0.05) also triggers a blink, but only if the last one ended at least 2.5 s ago.
- **Gaze, idle style (v1.8, Base Eyes):** a slow drift of about 0.1 eye width (eye width from the eyes' `measurements.<E>.opening_bbox`, else the white part) that follows the head sway and leads it by 0.1 s (3 frames at 30 fps), plus a slow 9.3 s wander of 20% of that. No big glances. The iris offset is still `irisLimitsPx` rounded to whole px, so in narrow profile eyes it may move 0–2 px only.
- **Gaze, talk style:** saccades of 30–90 ms with eased moves, holds of 0.5–2.7 s between, occasional small corrective saccades and returns to centre (v1.3 behaviour).
- **Mouth, idle style (v1.8, Base Mouth):** `MouthOpen` 0 and `MouthForm` from Base Mouth's keys: rest, then a soft smile (ramp 2.5–2.8 s, hold, ramp 4.6–4.9 s), once per 8 s loop. No talk.
- **Talk style (v1.8 talk driver, Base Mouth):** phrases of 3–10 syllables, each 130–270 ms, eased open→close with a random peak and a random form. Short gaps inside a phrase and pauses of 0.35–1.45 s between phrases. While talk is running, `EE`, `EE_half` and `smile` are never picked (nearest of the remaining shapes). Shape switching follows the 120 ms hold and the 35 ms crossfade or hard cut.
- **Body idle, talk style (v1.8, only with jointed body parts; rig units ×25° limbs, ×8° lean):** breathing (4.6 s) on `BodyLean` ±0.22 (±1.76°), minus 0.06 (0.5°) of the weight shift. Shoulders: ±0.03 with the breath plus an independent slow drift ±0.07 (7.1 s / 6.4 s), so each arm moves up to about 2.5°. Elbows: ±0.06 (1.5°) lagging the shoulder drift by 0.35 s. Hips: the weight shift (every 7–14 s, eased over 1.6 s) at 0.1 (2.5°) plus a ±0.02 drift, both hips together, knees countering (`Knee = −Hip`) so the shins stay parallel to rest; slight toe lift on the unloaded side. The root comes from foot plant.
- **Life (v1.8, idle style, default on):** a layered procedural secondary-motion system. UI `Life` 0–1 (URL `life=`, default 1) scales every amplitude; 0 is still. It is never applied at rest, so rest stays exact. The layers, in rig units: **Base:** Body's `idle_arm_sway` clip (`body_tools/idle/idle_clips.json`, 8 s loop, shoulders ±1.0, elbows up to 0.6 lagging 0.35 s, lean ±0.04, legs 0) × Life. **Breathing** (4.0 s): shoulders +0.04 out on the inhale, lean ±0.04, and the head rises up to 1.2 px (`HeadNod` −0.3, front/back) or pitches ±0.6° (profiles). The root does not breathe, because the feet stay planted. **Weight shift** (a new 6–10 s period each cycle): both hips ±0.08 (±2°), knees `−Hip` in front/back, so the shins stay vertical and the feet flat. In the profiles the loaded leg's knee gives up to 0.04 (1°) of flexion only (never hyperextension), with the hip and ankle compensating so the foot stays flat. Foot plant `xy` turns this into the pelvis sway (`RootX`). The torso counter-tilts (`BodyLean` −0.2 × sway, half in the profiles) through a damped follower (1.6 Hz, ζ 0.6). **Follow-through:** the head is a damped follower (2.2 Hz, ζ 0.55, about 2–3 frames of lag and about 12% overshoot on a step) of 45% of the torso angle plus its own slow drift (±2°, 5.7 s). The lag becomes `HeadTilt` (front/back) or `HeadNod` (profiles). The upper arm, forearm and hand are each damped followers (2.2 Hz, ζ 0.55) of their parent's world angle, so elbows and wrists trail the shoulders. **Hands:** finger curl drift 0.05–0.15 with per-finger phases (capped at 0.12 in tpose). This stays on frame f0 with 3 frames (switch at 0.25) and below the tpose f0→f1 switch at 0.125, so the fingers never pop. Wrist drift ±0.08 on top of the follower. **Eyes:** Base Eyes' blinks, a gaze drift of 0.04 eye width that leads the sway by 0.1 s (3 frames), and micro-saccades of ±0.03 eye width every 0.8–2 s. The iris moves in whole px within `irisLimitsPx` (1–3 px). **Mouth:** rest, with a soft smile (1.6–2.6 s) or a short `M` press (0.5–0.9 s) every 6–12 s, eased over 0.12 s, so there is one switch in and one out and no talk flicker. **Hair:** reacts through the springs, including the inertia input. Preview renders use preset `A` (labelled); the default stays `default`.
- **Foot plant (v1.8).** UI `Foot plant`, URL `footplant=xy|y|off` (default `xy`). It is applied in auto mode after the body step, and by clip players through `footPlantApply()` whenever a clip leaves `RootX` and `RootY` unkeyed. Sole points are the posed rest-lowest vertices (within 30 px of each foot's lowest point) of the skin vertices dominated by `foot_*`/`toes_*`, or the bottom edge of the `foot_*`/`toes_*` cut parts. `RootY` puts the lower foot's lowest sole point back on the rest foot line. With `xy`, `RootX` also keeps the planted foot's sole centre at its rest x; the two feet are blended smoothly by height (logistic, 2 px), so the planted foot can change without a pop. Both are clamped to ±40 px and drawn in whole px. It is never applied at rest, and not on slider input.
- **Hair:** hierarchical damped springs, as in section 4 (Hair).
  - **Presets (v1.8):** UI `Hair spring`, URL `hair=default|A|B`. Values are roots f / ζ, children f / ζ, child low-pass, gravity: `default` 1.1 Hz / 0.3, 1.0 Hz / 0.3, 0.09 s, 0.8 (unchanged, still the default until the user picks); `A` 4.0 Hz / 0.8 (both), 0.03 s, 0.4; `B` 2.0 Hz / 0.6 (both), 0.05 s, 0.8.
  - **Inertia input (v1.8):** the springs get the head's acceleration, taken from the head position of `headPose()` (which includes `RootX`/`RootY`, the lean and the head params) and low-passed over 0.05 s. The chain roots' targets get an offset: vertical `-a_y / 1500 px/s²` (the head accelerating up makes the hair drop), and horizontal `0.5 · a_x / 1500 px/s²` (the hanging tips lag). Each offset is clamped to ±1, and so is the total target, so the limits hold with every preset and with the chained clamp. At rest nothing changes. Vertical travel stays small because it is bounded by the hair's own `swayY × swayYMaxPx` (3 px).
  - **Chained limit (v1.8):** after a segment's drive is computed, its total angle (the sum of its ancestors' angles plus its own) is clamped to its own `swayWeight × maxSwayDeg`, so a tip can never swing further than its own limit relative to the head. When the clamp acts, that segment's spring velocity is reset. This applies to every preset. The slider path (`HairSwayX` without auto) is unchanged.
- **Drawing (v1.8).** Rest is drawn as before, with axis-aligned parts pixel-snapped and exact. Posed frames always take one resampling path: smoothed (linear) drawing at the exact transform for every part and the skin mesh, with no special case for 0° or axis-aligned transforms. `2x supersampled` (`ss2`) is now the default (URL `quality=`). A 0° part and a slightly rotated part are both drawn at 2× and downsampled, so a joint crossing 0° no longer switches a frame between exact and resampled. Before this, `linear` measured 8 steps over 1.5% and 3 sharp pulses in 5 s of apose idle. With `ss2` it measured 0 steps, 0 reversals and 0 spikes, with mean sharpness 0.96 of rest. Rest is always drawn 1:1.
- **Edge seal (v1.8, default on, UI `Edge seal`, URL `seal=0|1`).** Abutting antialiased cut edges composited with source-over leave net partial alpha (a + b − ab < 1) where parts meet, so the background shows through. In posed frames the renderer also builds a coverage buffer: every item drawn again with `lighter`, i.e. premultiplied alphas summed and clamped at 1. The composite is then drawn over itself 8× with `destination-over`, which keeps its colour and drives alpha to 1, and masked `destination-in` by the coverage. Where only one layer is partial (the outer silhouette), coverage equals the composite's alpha and nothing changes. Where abutting partial layers sum past it, the seam becomes opaque in the composite's own colour. It uses drawImage and composite operations only; the dev guard, which forbids pixel writes, is unchanged. QA metric: pixels at least 4 px inside the silhouette with alpha < 255 (and < 240). Measured on a posed tpose/left test frame: < 240 went from 560 to 257 px (tpose) and 410 to 77 px (left). The rest of the count is the authored art's own near-opaque alpha (tpose rest already has 1,440 px < 255).
- **Stress bypass (v1.8, render-only, default off).** `stressEnable(clip)` turns off the ±1 param clamp and widens the root clamp to ±400 px only when the clip carries `stressTest: true` (Body's `body_tools/actions/stress/*_stress.json`, merged with `rig/tools/merge_clips.py --stress`). Normal clips, the UI, rest and the guard are never affected.
- **Motion quality test** (the "Motion quality" button): runs 4 s of simulated auto mode twice, with a fixed seed, fixed 60 Hz steps and rendering at 15 fps.
  - **Face-only pass:** reports every frame with a guard violation or a missing part image. It also reports every pixel where composite alpha drops below rest alpha inside the hand mask, hair mask or rest silhouette.
  - **Full pass:** reports guard violations and missing parts only.
  - **Both passes:** report blink count, mouth switches and the minimum shape hold. Anything under the hold (120 ms in v1.8) is flagged as FLICKER. The passes use the selected auto style.
- Rest is never affected: the rest check renders with every parameter and drive at default.

## 8. Base Body skin mesh (v1.4, optional)
A single skinned mesh over the authored body image, as an alternative to cut body parts. It bends at the joints without seams because neighbouring bones share vertices. It's still only her pixels: WebGL textured triangles sampling `base_body.png`, and nothing is drawn or recoloured.

**Declaring it.** Add `"skin": "skin.json"` at the top level of `views/<view>/body/rig.json` and put the file next to it. The renderer requests `skin.json` only when it's declared (or forced by the `?skin=` URL parameter), so views without one make no request. When the skin loads and validates, it replaces the cut body parts in the renderer and in `rest_check.py`. If it fails validation, the renderer warns and falls back to the cut parts (or `base_body.png`).

**Format.**
```
{ "image": "base_body.png",            // relative to views/<view>/, full W×H canvas, must match base.png at rest
  "headBone": "torso",                 // bone that eyes, mouth and hair ride on (default head, else torso)
  "bones": [ { "name": "upperArm_L", "parent": "torso", "pivot": [x, y], "param": "ShoulderL",
               "maxRotDeg": 25, "minRotDeg"?: 25, "rotDir"?: 1, "degAtPlus1"?/"degAtMinus1"?, "wristPivot"?: {x, y} }, ... ],
  "vertices":  [ [x, y], ... ],        // rest positions in canvas pixels, on the integer grid
  "triangles": [ [i, j, k, layer], ... ],   // layer optional (else "triangleLayers"[t], else "layer", else 220)
  "weights":   [ [ [boneIndex, w], ... up to 4 ], ... ]   // one list per vertex, w sums to 1 (±0.001)
}
```
- **Bones** mirror the cut-part ids (`pelvis`, `torso`, `upperArm_L`, `forearm_L`, `thigh_L`, `shin_L`, `foot_L`, `toes_L`, …) and use the same parameters and limits as section 4 (Body): deg = rotDir × (v < 0 ? −v × minRotDeg : v × maxRotDeg). If `param` is omitted, the default driver is used; `null` means not driven. Each bone rotates about its `pivot` in its parent's space.
- **Skinning** is linear blend skinning: posed vertex = Σ wᵢ · Mᵢ · rest vertex, where Mᵢ is bone i's world transform.
- **Hands and face.** The forearm bone's `wristPivot` and world transform drive the palms (then `WristL`/`WristR`). `headBone` drives eyes, mouth and hair.
- **Layer groups.** Triangles are grouped by `layer` (body band 200–299, including the profile far-limb slots). Each group is its own pass at that layer, so other owners' parts, such as a far hand at 210–215, can sit between groups. Consecutive groups are drawn in one pass.
- **Rest exactness.** Every opaque pixel centre of the image must be covered by exactly one triangle. `rest_check.py` reports `uncoveredOpaque` and `doubleCovered`, and both must be 0. At rest (all bone transforms identity), a skin whose groups draw consecutively is composited as the untouched image. Split passes go through WebGL with NEAREST sampling, which was verified byte-exact (0 px) against the direct image.

**Filtering (renderer "Posed filtering" select).** For rotated cut parts and the deformed mesh:
- `nearest`: no interpolation.
- `linear` (default): bilinear, mip off.
- `ss2`: the posed frame is rendered at 2× (mesh at 2× resolution, parts scaled 2×), then downsampled with high-quality smoothing.

Rest is always rendered 1:1 with nearest, so the filter can't affect rest. Measured results are in the v1.4 hand-off report. The recommended mode is whichever joint-test mode keeps outline width closest to rest.

**Known limitation.** `base_body.png` has no hidden fill under the limbs, while the cut parts carry `addedHiddenPixels` fill. When a limb swings away from the torso, the mesh can only stretch the pixels it has. Base Body could provide a skin image with hidden fill under the arms and thighs, drawn in her style, exact at rest where visible.

**Tools (Base Body).**
- `python3 rig/skin_tools/auto_skin.py <view> [--coarse 6] [--fine 2] [--falloff 14]` builds a draft from the cut parts, with pixel-aligned grid triangles, finer cells near the joints and smoothstep weights across each joint. It writes only to `rig/skin_tools/drafts/<view>_skin.json`, never into `views/`. After review, Base Body copies it into `views/<view>/body/skin.json` and declares it.
- `python3 rig/rest_check.py --skin=draft` checks the draft (default: the declared skin); it must report `total: 0` and zero uncovered or double-covered pixels.
- In the preview: `rig/index.html?view=<view>&skin=draft` loads the draft (`&skin=off` disables a declared skin), and the "Body" select switches between `auto`, `cut` and `skin`.

**Joint test** (the "Joint test" button, renderer only; seam-based since v1.5). Each of shoulder, elbow, hip, knee, ankle and wrist (L and R) is bent to 25° in turn, for every mode {cut, skin, skin+underlay if present} × {nearest, linear, ss2}.
- **Seam, skin:** each vertex's dominant bone (largest weight) is classed as parent bone, child subtree, or other. Every mesh edge whose endpoints are parent on one side and child subtree on the other contributes its midpoint. Posed seam points are the midpoints of the posed (LBS) endpoints.
- **Seam, cut parts:** the visible part boundary. That's the boundary pixels of whichever of parent/child is on top, where the other part is opaque within 2 px and the rest composite is opaque. They're posed with that part's transform. Wrists use the palm boundary against the forearm in both modes.
- **Metrics,** taken in a band around the whole posed seam (8 px for holes/tears, 10 px for outline), and on the rest composite around the rest seam as the baseline:
  - holes: enclosed transparent pixels
  - tears: pixels filled by a radius-3 morphological closing that are transparent, i.e. cracks and notches up to about 6 px wide, including V-notches where the seam meets the silhouette
  - seam alpha<255: seam points that were alpha 255 at rest
  - outline width: at every silhouette edge pixel in the band, measured along the alpha-gradient normal in 0.25 px steps from 1 px outside the edge. Line pixel = α ≥ 128 and max(R,G,B) ≤ 45 (lineRGB ≈ (13,11,29)). Reported as mean, min, p10 and edges without line.
- **Hips (v1.5.1):** only the outer hip outline is scored. For hip_L/hip_R, every pixel on the medial side of that hip's pivot (the vertical line x = pivotX, on the side facing the other hip's pivot) is removed from the hole/tear and outline bands. Seam points there are dropped from the seam alpha count. This applies identically to rest and posed, for cut (part pivots) and skin (bone pivots). The medial side holds the thick double inner-crotch edge, which the thigh swings over at +25° and which then leaves the silhouette. If the two hip pivots are less than 4 px apart in x (profile views), nothing is excluded. In apose: hip_L excludes x < 747 and hip_R excludes x > 618.
- The summary gives new holes and tears (posed minus rest, per joint), the seam alpha<255 %, mean width as % of rest, min width and line coverage. The "best" mode is the one with the fewest new holes+tears, then width closest to rest.
Both skin and cut parts are judged by this same standard.

## 9. Skin underlay (v1.5, optional, Base Body)
Purpose: `base_body.png` / the skin image has nothing painted under the limbs, so a limb that swings out leaves stretched pixels or a gap. The underlay is a separate Base Body image with flat fill under the limbs, carried by its own mesh beneath the main skin. It shows only where the main skin moves away, and at rest it is completely hidden.

**Format** (inside `skin.json`):
```
"underlay": {
  "image": "base_body_underlay.png",  // relative to views/<view>/, W×H, owned by Base Body
  "layer"?: 219,                       // default: just below the lowest main-skin group (min group layer − 0.5)
  // either its own mesh ...
  "vertices"?: [[x,y],...], "triangles"?: [[i,j,k],...], "weights"?: [[[boneIndex,w],...],...],   // bones = the main skin's bones, ≤4 per vertex, sum 1
  // ... or, with none of the three, it reuses the main mesh (vertices, triangles, weights)
  "uvs"?: [[u,v],...]                  // image pixel coordinates per vertex (own mesh or main mesh); default = the rest position
}
```
- It's skinned with the same bones and the same LBS as the main mesh, drawn as WebGL textured triangles of the underlay image, and composited at `layer` before the main skin groups. The "Skin underlay" checkbox in the preview toggles it.
- To reveal fill when a limb swings out, the fill must stay with the body behind the limb. So weight underlay triangles to the bone the fill belongs to (e.g. torso fill under the arm → `torso`, thigh fill under the pelvis → `thigh_*`). An underlay that reuses the main mesh topology moves exactly like the main skin and can't show anything new except where the main mesh itself tears. That form only suits custom-UV patches.
- **Rest rule.** Take every pixel the underlay would draw at rest (all parameters 0; pixel centres inside a triangle, sampling alpha > 0). Each must lie under a main-skin pixel with alpha 255 whose triangle group layer is above the underlay layer. If any footprint pixel touches a transparent pixel, a main-skin pixel with alpha < 255, or a main pixel from a group at or below the underlay, the underlay is rejected. The renderer shows a warning and doesn't draw it; `rest_check.py` and `check_underlay.py` report the rejection. With this rule, rest stays 0 px whatever the underlay contains.
  - The renderer checks this on the GPU output itself: the underlay drawn at rest with NEAREST, against the alpha of the main groups above it.
  - `rest_check.py` and `check_underlay.py` use a conservative CPU rasteriser: pixel centres on edges count as inside, and custom UVs count a pixel if any of its 4 surrounding texels has alpha > 0.
  - Both report the footprint size and the violation counts. On the test fixture they agree exactly (27,799 px valid; the negative fixture has a 316,342 px footprint with 6,584 partial-alpha violations).
- The underlay never covers her outline at rest. When posed, anything it shows is Base Body's own painted fill.

**Base Body how-to.**
1. Paint the fill in a W×H PNG: only where the skin is fully opaque at rest and hidden behind something that can move away (e.g. the torso under the upper arms, the thigh tops under the pelvis). Leave a margin of at least 1 px inside her outline, because pixels under alpha < 255 edge pixels are rejected.
2. Build a mesh over the fill with each cell weighted to its owner bone. `python3 rig/skin_tools/make_underlay.py <view>` does this from your cut parts' hidden fill (`addedHiddenPixels`) as a starting point. It writes `rig/skin_tools/drafts/<view>_underlay.png` and `<view>_skin_ul.json` (the skin plus the underlay) and never touches `views/`.
3. Validate: `python3 rig/skin_tools/check_underlay.py <view> [--skin=draft:<view>_skin_ul.json]`. Exit 0 means valid, 1 rejected, 2 none. It writes a map `rig/skin_tools/drafts/<view>_underlay_check.png` (green = valid footprint, red = violations).
4. Check rest and motion: `python3 rig/rest_check.py --skin=draft:<view>_skin_ul.json` must give `total: 0` and `underlay.ok: true`. Then use `rig/index.html?view=<view>&skin=draft:<view>_skin_ul.json` and the "Joint test" button (skin vs skin+underlay).
5. Ship: copy the image into `views/<view>/` and add the `underlay` block (with `image` relative to `views/<view>/`) to `views/<view>/body/skin.json`.

## 10. Layers panel (v1.6, preview only)
The right side of `rig/index.html` has a Layers panel. It's a viewing tool, not part of the format.
- **Source of truth:** `rig.json` (and `skin.json`) stay the only source of truth for parts, layers and order. The panel never writes to them or to anything under `views/`.
- **Tree:** view > system (hair_back, body, hands, eyes, mouth, hair_front) > group > part. Rows are listed in the real draw order of the current frame (first drawn / back at the top), and each shows its `layer` and draw index `#n`. The tree updates live while she animates.
- **Rows per owner:**
  - Base Body: one row per skin layer-group pass (labelled with its main bones), plus the underlay row (200, or 219 in profiles). Cut-part views show one row per part with its live angle.
  - Base Hands: one group row per hand, showing all curls and the wrist. Each segment row shows its current frame (`fK/2` and file name) and curl.
  - Base Hair: one group row per strand (chain root), with its chained pieces inside. Each piece shows its live sway angle against its clamp `swayWeight × maxSwayDeg` (the authored `maxSwayDeg` is shown too), plus the accumulated chain angle for tips.
  - Base Mouth: a group row with the current shape (k/9), MouthOpen and MouthForm. During a crossfade it shows both the outgoing shape (opacity 1, underneath) and the incoming shape (opacity a, on top).
  - Base Eyes: one group per eye, with the lid frame (k of 0..n−1), EyeOpen and EyeBallX/Y. Back view: no eye or mouth rows, because none are loaded.
- **Row controls:** show/hide and solo on every row. Hovering a row dims every other part to 25% alpha. Nothing is ever drawn over her; there are no outlines or shapes on the character canvas.
- **Hair erase mask:** an optional toggle shows `hair/<view>_hair_erase_mask.png` as a semi-transparent HTML `<img>` over the canvas. It's requested only when the toggle is on.
- **Pause and step:** Pause freezes the animation and the renderer clock. Step advances by a fixed dt (1/60 s by default; also 1/120 s, 1/30 s, 10, 5, 1 and 70 ms), so the 70 ms mouth hold, crossfades and finger/lid frame switches can be inspected. The panel shows `anim t` and how long the current mouth shape has been held.
- **Preview reorder:** drag a part row to try a different order. The result is stored only in this browser's `localStorage` (key `shadowveil.layers.previewOverride.v1.<view>`). While it's set, a red "PREVIEW ORDER OVERRIDE ACTIVE" badge is shown; **Reset order** clears it. To make an order real, the owner changes `layer` in their `rig.json`.
- **Isolation:** panel state (hide, solo, hover dim, reorder override, pause) applies only to the on-screen preview frame. The page's Rest check, the Motion quality test, the joint test and `rest_check.py` always render with defaults (everything visible, no override), so the panel can't change their results. It defaults to everything visible.

## 11. Reserved outfit / wear layer bands (v1.7, documentation only)
These bands are reserved for a future outfit auto-skinner. Nothing uses them yet.
- Each band sits inside its owner's existing band (section 5), so no code change is needed. `rest_check.py` and the renderer's band check accept a part in a reserved band as an ordinary layer of that owner, exactly as today. Nothing new is rejected.
- The dev guard doesn't look at layers at all; it still only blocks shape, path, text and pixel-write calls.
- "Reserved" means only this: owners don't put base-model parts here, and outfit parts go only here.

| Band | Owner | Use | Rule / test |
|---|---|---|---|
| 110–199 | Base Hair | back-worn cloth: capes, hood backs | Above back hair (100) and the front-view bun (101) and its ornament (102), below the body. Test with the hair at full sway: nothing hidden behind her neck may show. |
| strand root + 1 | Base Hair | a clip on a strand | The strand's **root** layer + 1 (confirmed by Base Hair, v1.7.1). On a chained strand the clip rides the root piece, not the tip. Strands are not always 3 apart (e.g. apose 607/608, right 601/602 and 604/605), and a chained tip sits at root − 1, so tip + 1 is the root itself. Root + 1 is free in every view today. |
| 102 | Base Hair | bun ornament, front views (apose, tpose; bun at 101) | Not used in back, where the bun is at 650 (see 690–699). |
| 260–299 | Base Body | body cloth, including wrist cuffs | Cuffs draw under the palm (300 / 320). Front views: explicit layers inside 260–299. Profiles: near and centre cloth = its skin triangle's layer + 40 (260–291); far cloth uses 207–209 and far-hand wear 216–218 (see the resolved items below). |
| 340–379 | Base Hands | 340–355 right glove, 360–375 left glove; 376–379 rings and bracelets | Each glove segment = its hand segment layer + 40, keeping the palm, pinky, ring, middle, index, thumb order. If a segment's layer changes with curl (`layerCurled`, or a per-frame `layer`), the glove follows it + 40. Gloves need their own drawn f0–f2 frames per segment, pinned to the same pivots and switching in step with the finger frames. A long sleeve that covers the back of the hand also uses + 40. |
| 450–499 | Base Eyes | face wear: glasses, visors, eye masks | Lids and gaze must show through a lens; a mask may hide them on purpose. |
| 510–519 | Base Mouth | lip wear | One part per mouth shape; it switches and crossfades with the mouth (section 5 crossfade rule). |
| 550–599 | Base Mouth | masks, veils | Fixed to the head, never lip-synced. |
| 660–689 | Base Hair | hats, hood fronts | Above the bun (650 in the side and back views). Each needs a hair mask that hides the covered hair parts and turns off their sway. |
| 690–699 | Base Hair | bun ornaments, side and back views | |

**Resolved in v1.7.1** (the five v1.7 open items, settled by the owners):
1. **Hair clips** (Base Hair): at the strand's **root** layer + 1. A clip on a chained strand rides the root piece, not the tip.
2. and 3. **Profile cloth** (Base Body and Base Hands). The profile skin has no far-limb triangles; the far limbs are declared but never drawn.

   | Profile layers | Use |
   |---|---|
   | 200–206 | far limbs, declared, never drawn |
   | 207 / 208 / 209 | (a) far body cloth: leg / sleeve / cuff, under the far palm |
   | 210–215 | far hand |
   | 216 | (b) far glove; it follows the far hand's visibility, so it's hidden whenever the far hand is |
   | 217–218 | (b) far rings and bracelets |
   | 219 | skin underlay |
   | 220–251 | all skin (near arm 250–251) |
   | 260–291 | (c) near and centre cloth = its skin triangle's layer + 40 |
   | 300 / 320 | near palm (right view R_palm 300, left view L_palm 320) |

   Far cloth tops out at 218 and near cloth starts at 260, so a far sleeve can never draw over near skin. Near cuffs (forearm skin 250 + 40 = 290) stay under the near palm.
4. **Front views** (Base Body): cloth uses explicit layers inside 260–299. The +40 rule is profile-only (front skin spans 201–250).
5. **Back view** (Base Hair): uses the side-view hair rules, hats 660–689 and bun ornaments 690–699 (its bun is at 650).

Also noted: every body `rig.json` declares `"layerBand": [200, 299]`. That's a declaration, not a part layer, and it already contains 260–299; no change is needed.

**v1.7.1 read-only check of the profile claims** (`views/left` and `views/right` `body/skin.json`, `body/rig.json`, `hands/rig.json`):
- Confirmed:
  - Skin triangles use only 220, 222, 239, 240, 241, 242, 246, 250 and 251, and none are dominated by a far-limb bone.
  - The underlay is at 219.
  - The far limbs are at 200–206 with `file: null` and `hidden: true` (toes 200, foot 201, shin 202, thigh 203, forearm 205, upper arm 206).
  - The far hand is at 210–215, likewise with no files and `hidden: true`.
  - Skin + 40 gives 260–291.
- Discrepancies (none of them breaks the rules above; the owners may want to tidy the metadata):
  - The body `rig.json` `profile` block says `"farLayers": [201, 209]`. The far limbs actually declared are 200–206 (toes at 200 is outside that range), and 207–209 are now the far body cloth slots.
  - The same block says `"reservedForFarHand": [210, 219]`, but 219 is the skin underlay's layer. Far-hand parts and wear use 210–218.
  - "Near cuffs at 290–291": a cuff over the forearm skin (250) lands at 290. 291 is upper-arm skin (251) + 40, i.e. an upper-arm sleeve.
  - "Under the near palm at 300" holds in the right view. In the left view the near palm is L_palm at 320. Both are above 291.
  - In the right view, 74 torso-pass (220) triangles are dominated by `upperArm_R` (near arm). Cloth over them lands at 260 with the torso cloth, still near cloth.
  - "The far glove follows the far hand's visibility" is a package rule, not current renderer behaviour. The renderer has no visibility flag. The far hand is not drawn today only because its parts have no file, so an outfit loader must implement this rule.

### 11.1 Outfit package (planned)
- **Folder:** each outfit is one folder per view, holding its parts, a manifest and its own rest image (her wearing it, at rest).
- **Manifest:** gives each part's band (above) and how it moves:
  - skin weights copied from the nearest body skin point;
  - curl frames (gloves);
  - a hair mask (hats and hoods);
  - riding on a strand (clips);
  - per-mouth-shape (lip wear).
- **The rig loads packages** and is never edited per outfit. `rig.json` files stay the base model's.
- **Checks:**
  - Her undressed rest must still match `base.png` exactly (0 px, section 1).
  - Each outfit needs its own exact-match rest check against its rest image.
  - Each outfit must pass the ±25° joint test (section 8) with no tears and no skin poking through the cloth.

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
