# Shadowveil base model: runtime contract (v1.5.1)

## Changelog
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
| `Hand{L,R}{Thumb,Index,Middle,Ring,Pinky}{1,2,3}` | 0 to 1 curl | 0 | Base Hands |
| `Hand{L,R}ThumbSpread` | -1 across the palm to 1 out | 0 | Base Hands |
| `Hand{L,R}Spread` | 0 together to 1 fanned (index, ring, pinky) | 0 | Base Hands |
| `HairSwayX` | -1 to 1 | 0 | runtime motion input, shaped by Base Hair |
| `HairSwayY` | -1 to 1 | 0 | runtime motion input, shaped by Base Hair |
| `BodyLean` | -1 to 1 | 0 | Base Body (placeholder, v1.2) |
| `Shoulder{L,R}`, `Elbow{L,R}`, `Hip{L,R}`, `Knee{L,R}`, `Ankle{L,R}` | -1 to 1 | 0 | Base Body (placeholder, v1.2) |
| `Toe{L,R}` | -1 to 1 (about −30° to +20° through the part's own limits) | 0 | Base Body (v1.3) |
| `Wrist{L,R}` | -1 to 1 (±25° about the forearm `wristPivot`; override with hands `wristMaxDeg` or palm `maxWristDeg`, `wristDegAtPlus1`/`wristDegAtMinus1`) | 0 | Base Hands / Base Body (v1.4) |

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
- **Hold:** a shown shape stays up at least 70 ms before the next switch, whatever the input, and the 60 ms crossfade finishes inside that hold. So a shape never flickers. `rest` at (0, 0) must match the drawn mouth exactly. Each shape covers the drawn mouth fully so no part of the old mouth shows around it.

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
  - A segment's curl is its finger's `Hand{L,R}<Finger>` value, which drives all 3 joints in the preview.
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

**Crossfade rule (v1.3, applies everywhere).** Any crossfade anywhere draws the outgoing image at full opacity, then the incoming image on top at the rising opacity. The outgoing image is dropped only once the incoming one reaches 1. Two images are never both at partial opacity, so nothing underneath ever shows through mid-fade: her base lips, or `base_body.png`, which is erased under the hands and hair. This covers mouth shapes, including swaps involving `rest`.

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
- **Blinks:** random intervals of 2–6 s. Each blink closes fast (75 ms, ease-in), holds 35 ms and opens more slowly (170 ms, ease-out). About 18% become a double blink.
- **Gaze:** saccades of 30–90 ms with eased moves, holds of 0.5–2.7 s between, occasional small corrective saccades and returns to centre.
- **Talk:** phrases of 3–10 syllables, each 130–270 ms, eased open→close with a random peak and a random form. There are short gaps inside a phrase and pauses of 0.35–1.45 s between phrases. Shape switching follows the 70 ms hold.
- **Body idle** (only with jointed body parts): slow breathing (4.6 s period) on `BodyLean`, the shoulders and the elbows. Every 7–14 s there's a weight shift, eased over 1.6 s, on the hips and knees (knees counter the hips so the shins stay near vertical), with a slight toe lift on the unloaded side.
- **Hair:** hierarchical damped springs, as in section 4 (Hair).
- **Motion quality test** (the "Motion quality" button): runs 4 s of simulated auto mode twice, with a fixed seed, fixed 60 Hz steps and rendering at 15 fps.
  - **Face-only pass:** reports every frame with a guard violation or a missing part image. It also reports every pixel where composite alpha drops below rest alpha inside the hand mask, hair mask or rest silhouette.
  - **Full pass:** reports guard violations and missing parts only.
  - **Both passes:** report blink count, mouth switches and the minimum shape hold. Anything under 70 ms is flagged as FLICKER.
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
