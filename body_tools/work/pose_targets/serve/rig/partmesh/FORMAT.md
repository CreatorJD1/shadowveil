# Part mesh format: partmesh v0.2 (2026-10-02 PT)

**Status.** The renderer is built behind `?partmesh=1` in `rig/index.html`. It is off by default, and the live default is
byte-identical to 6d5b239: 30/30 FR hashes match over 5 views × 6 poses (`rig/work/partmesh_pilot/default_same.json`).
It reads `rig/partmesh/staged/manifest.json` and the files listed there. Nothing is read from `views/`, and nothing here
writes to `views/` or any `rig.json`.

Two pilots are staged. Hair passes. Hands passes the v0.2 pass mark except the new floating-speck check (5.3); see 5. `rig/work/partmesh_pilot/` holds the numbers and contact sheets:
- `apose_hair_strand_03.json`: strand_03 and strand_03_tip
- `tpose_hands_R_Middle.json`: R_Middle1/2/3

v0.2 replaces the v0.1 draft. **Section 2 is the shape the renderer actually reads today.** Owners can author against it now.
Section 3 lists fields that are specified but not yet read by the renderer. They stay rejected-safe: an unknown field is ignored,
never guessed. G1–G14 refer to the Eyes notes (`eyes/staged/partmesh_notes.md`); G13 is settled by this file.

## 1. Model
A **part** is one named, controllable thing: a strand, a finger segment, a lip, a lid. It keeps the same `id` and the same
controls at every angle and in every pose. Each (pose, angle) slot gives it one or more **drawings**. A drawing is an authored
PNG on that slot's canvas, never edited, with its own pivot and mesh. Every per-part rule uses one override chain:

`flap field` → `drawing field` → `angles[<deg>] field` → `part field` → renderer default

The first defined value wins.

**Deform model (built).** It is the angle blend, `"deform": "angle"`.
- A part sits between its root joint (parent → part) and its tip joint (part → child).
- The rig still computes the rigid matrices M_parent, M_part and M_child exactly as it does today, including swaps and pivots.
- Each mesh vertex x carries two weights: `w` is its share of the root joint and `u` its share of the tip joint.
- Each vertex is posed as `M_parent · D_root(w) · D_tip(u) · x`.
  - `D(t) = T(t·d) · rotAt(c, t·a)` is the fraction t of the relative joint transform.
  - For the root joint the relative transform is `inv(M_parent)·M_part`. For the tip joint it is `inv(M_part)·M_child`.
  - `a` is the angle, `c` the joint centre and `d` the residual offset.
- With w=1 and u=0 the vertex is exactly rigid, the same as today.
- Both sides of a joint use the same centre, axis and blend. The parent's distal end and the child's root therefore deform the
  same way where they overlap, with no seam and no gap.

**Rest rule (enforced in code).** When both relative transforms are the identity, the renderer skips the mesh and draws the
drawing through the unmeshed `drawM` path. The result is byte-identical. Measured with the flag on: rest is 0 px in all
5 views, and live FR is 0 px against base.png.

## 2. Files the renderer reads now (v0.1 and v0.2 contracts accepted)

### 2.1 Manifest: `rig/partmesh/staged/manifest.json`
```jsonc
{ "contract": "partmesh v0.2",
  "files": [ { "file": "tpose_hands_R_Middle.json", "view": "tpose", "system": "hands", "parts": ["R_Middle1","R_Middle2","R_Middle3"] } ] }
```
A file is loaded only for its `view`. That one field is the pose/angle slot, so it settles G11: a T-pose is its own file with
`"view": "tpose"`.

### 2.2 Part-mesh file: one per (owner/system, view)
```jsonc
{
  "contract": "partmesh v0.2",            // "partmesh v0.1" is also accepted (the pilots); anything else is rejected and logged
  "owner": "Hands",                       // Body | Eyes | Mouth | Hands | Hair | Coder (pilot)
  "view": "tpose",                        // apose | tpose | left | right | back (45/135/225/315: see 3.6)
  "system": "hands",                      // must match the rig system key: body | eyes | mouth | hands | hair
  "status": "staged ...", "generator": "rig/partmesh/tools/build_pilot.py step=2",
  "deform": "angle",                      // only model built
  "joints": {                             // one per meshed part = its ROOT joint (parent -> part)
    "R_Middle2": { "parent": "R_Middle1",
                   "centre": [84.4, 401.6],   // canvas px (view canvas), = the part's base pivot in rig.json
                   "axis": [-0.99, 0.11],     // unit vector root -> tip (builder: pivot -> drawing centroid)
                   "blend": 4.0,              // half-width of the bend zone along `axis`, px. 0 = rigid joint
                   "blendOffset": 0.0 }       // shift of the zone centre along `axis`, px (+ = toward the tip). Default 0
  },
  "parts": [ {
    "id": "R_Middle2",                    // = the part id in views/<view>/<system>/rig.json (hair ids without the "hair:" prefix)
    "parent": "R_Middle1", "child": "R_Middle3",   // child = next meshed part (its joint is this part's tip joint) or null
    "layer": 308,                         // informational; the draw order still comes from rig.json / z.json
    "joint": "R_Middle2", "childJoint": "R_Middle3",
    "drawings": {                         // keyed by the rig's drawing key
      "part": { ... },                    //   "part" = the rig.json `file`
      "f0":   { ... }, "f4": { ... }      //   "f<i>" = rig.json frames[i] (the swap the rig already picks)
    }
  } ]
}
```

### 2.3 Drawing
```jsonc
{ "image": "views/tpose/hands/R_Middle1_f2.png",   // read-only, must be the same PNG the rig draws for this key
  "sha256": "0123abcd...",                         // first 16 hex of sha256(image); a mismatch means the mesh is stale (see 2.5)
  "pivot": [114.31, 398.46],                       // root joint centre FOR THIS DRAWING (per-frame pivots, Hands)
  "spine": [[x,y],[x,y],[x,y]],                    // informational for now: zone start, pivot, tip-joint centre
  "mesh": { "vertices": [[x,y],...],               // canvas px; the builder uses a 2 px grid over the dilated alpha
            "triangles": [[i,j,k],...],
            "weights": [[w,u],...] } }             // one pair per vertex, each in [0,1]
```
**Units and rounding (G2).** Everything is in canvas px of that view, as floats. Nothing is rounded. Vertices are positioned in
float. Raster output is the GL path with linear sampling, or nearest when `quality=nearest` (see 3.4 for per-part sampling).

**Builder weights.** `w = smoothstep((s - blendOffset + blend) / (2·blend))`, where `s = (x - pivot)·axis`, and blend 0 gives
w = 1. The tip weight u is computed the same way from the child's joint. Owners can supply any weights in [0,1]. The renderer
only reads the numbers.

**Per-drawing weight patch (v0.2, builder side, optional).** A drawing may carry
`"weightPatch": [{"box": [x0,y0,x1,y1], "w": 1, "feather": 2}]` (canvas px, inclusive box). The builder pulls the root weight w
of every vertex in the box to `w`, feathered over `feather` px by smoothstep. The field is informational for the renderer, which
still only reads `mesh.weights`. Use: ink drawn behind the pivot inside the bend zone (root caps, crease ends) that must ride its
own segment as it does in the rigid rig. Builder flag: `--wpatch=<part>/<key>:x0,y0,x1,y1:w[:feather]`.
- Hands F9 (tpose R_Middle, 00:30 PT): patches on R_Middle1 f1/f2/f3 (121,402–403), R_Middle1 f4 (= R_Middle1_f2.png, 119,403–406)
  and R_Middle2 f1/f2/f3 (84–91,395–401), each w=1 feather 2, on her untouched PNGs (sha256 unchanged). This clears the floating
  specks: 0 stray ink in all 10 poses, 0 breaks, max |dw| 0.62, 0 px outside the middle reach. Rest and the rigid default are
  unchanged.

### 2.4 Wiring today
- **hair:** `pmDraw` is used for any hair part with an entry. The parent and child world matrices come from the hair chain,
  head included.
- **hands:** the drawing key is `f<frameIndex>` or `part`. The parent is `M[p.parent]` and the child is `M[child]`.
- **body / eyes / mouth:** no hook yet. They are next, once their files exist (see 4).

### 2.5 Validation (built: reject and log in `R.warn`; the part falls back to its normal rigid/swap render)
These checks are built:
- wrong `contract`
- `weights.length != vertices.length`
- a missing drawing key, or an empty image. These draw rigidly.

Specified and to be built next:
- an `sha256` mismatch
- a triangle flipped at rest
- a negative-determinant mesh (no mirroring, ever)
- a weight outside [0,1]
- a `view` with no base.png
- a failed rest rule

## 3. Specified, not yet read by the renderer (author these now; unknown fields are ignored until built)

### 3.1 Requirements (a)–(l)
| | requirement | field |
|---|---|---|
| a | draw order per part, inside the owner band (eyes 400-403 EyeR, 410-413 EyeL). **Any order inside a chain is allowed, including child under parent** (a finger segment under the segment it hangs from, a strand tip under its strand). Draw order and the parent/child bone chain are independent. Per angle via `angles[deg].layer`, per drawing via `drawings.<key>.layer`, so a curled frame can flip the order. | `layer` (abs) or `{"under"/"over": id}`, e.g. R_Middle2 `{"under":"R_Middle1"}` |
| b | Mouth upper-lip flap tucked under the lower lip | flap `layer: {"under":"lower_lip"}` |
| c | visibility gated by a param | `visibleWhen: {"param":"MouthOpen","op":">","value":0}` |
| d | per-drawing pivots and swaps (curled Middle1 moves its pivot) | `drawings.f<i>.pivot` (**built**) and swap (3.3) |
| e | Hands flap under the parent segment | flap `layer: {"under":"<parent segment id>"}` |
| f | per-angle z (hair bun 101 front-facing vs 650) | `angles[deg].layer` |
| g | spring state keyed by part id and joint index; it persists across angle switches and swaps, and hidden parts keep integrating | `physics` (preset A default) |
| h | Hair root flap under the fringe; tip flap under the parent strand | flaps |
| i | per-angle visibility | `angles[deg].visible:false`, or a missing angle |
| j | clips: to a part, a dynamic gap, outside (inverse) | `clip` (3.2) |
| k | per-angle limits | `angles[deg].limits` (3.5) |
| l | bind to another part's spine (lash on the lid edge) | `bind: {"spineOf": id, "offset": [dx,dy]}` |

### 3.2 Clips (j, G6, G9)
- `clip: {"to": "<part id>"}`: intersect with the target's deformed alpha. This is the iris in the white.
- `clip: {"gap": ["<upper id>", "<lower id>"]}`: the dynamic region between the two parts' deformed inner edges (their spines).
  - Mouth: the interior gap clip, so the interior can't poke out (today it does, up to 5 px at half open).
  - Eyes: white/iris under a bent lid, with a static `EyeR_lid_lower` spine. Eyes may use it (G6).
- `clip: {"outside": "<part id>"}`: inverse clip. Use it for the far eye cut by the cheek/nose at 45/135/225/315 (G9), or
  give an authored per-angle mask `{"mask": "path.png"}`.
- **Two clips on one part (G6).** `clip` may be an array, and the clips are intersected in order. Example: the white uses
  `[{"gap":[…]}]` and the iris uses `[{"to":"EyeR_white"}]`. That clips the iris through the white, which is itself gap-clipped.

### 3.3 Swaps (d, G12)
`swap: {"param": "EyeROpen", "map": "round", "expr": "(1-v)*7", "drawing": [0..7]}`. The bucket index is
`floor(expr + 0.5)`, clamped to the list. That gives Eyes their `frame = round((1-Open)*7)`. Hands keep the rig's own frame
pick, and the file only supplies meshes per `f<i>`. A swap is a hard switch with no crossfade. Spring state is never reset.

### 3.4 Sampling per part (G7)
`sampling: "linear" | "nearest" | "shear-nearest" | "area"`.
- `nearest`: hard binary-alpha bands (lids, lashes) keep their width.
- `shear-nearest`: per-column integer vertical shift, with slope ≤1 (≤2 on eyes 13–24 px wide). This is the staged eye fix
  and is used for G4 lids.
- `area`: box/mip filtering on minification, for parts drawn at scale < 1, such as diagonals and fits (bilinear drops 1 px
  lines; Mouth, 3.8).
- The default is the view's quality setting. Rest is byte-identical in every mode.

### 3.5 Limits (k, G1–G3)
```jsonc
"limits": { "EyeBallX": {"dxPlus": 6, "dxMinus": 5, "sign": 1}, "EyeBallY": {"dyPlus": 3, "dyMinus": 4} }
```
- Units are canvas px of that slot, or turn-frame px when the slot has a `fit` (3.6). The renderer applies `fit.scale` once.
- Value: `dx = floor(X·(X>0 ? dxPlus : -dxMinus)·sign + 0.5)`, and the same for Y.
- At in-between dial positions, limits **snap at the midpoint together with the drawing** (t<0.5 uses angle a, otherwise b).
  They are not interpolated.

### 3.6 Turn: 8 angles, the per-angle fit, and the head group
- Angles are 0 apose, 45, 90 left, 135, 180 back, 225, 270 right, 315. One file per authored slot. The diagonals use
  `"view": "45"` and so on once art is accepted.
- In-between dial positions: pivot and spine points interpolate linearly by `t=(deg-a)/(b-a)`. The art is a hard switch at
  t=0.5 (drawing(a) below, drawing(b) at or above), with no crossfade.
- **Spine point count (G14).** The count must match across angles, otherwise the part snaps at the midpoint. Eyes use 5 lid
  points at every angle: corner, ¼, middle, ¾, corner. That is fine even when the points end up 3–6 px apart on the 13–24 px
  diagonal eyes.
- **Per-angle fit (G10).** `fit: {"scale": 1.54468, "dx": …, "dy": …}` on the file, or on `angles[deg]`. It is for art authored
  in turn-frame px (768×1168), such as the 45/315 eye parts, placed with `body_tools/work/apose_turn/diagonals/diagonals.json`.
  The rest check for a fitted slot runs against the frame at frame scale (0 px, the same as `eyes/staged/diagonals/`). Art is
  never resampled into view space.
- **Head group placement per angle (single correction path).**
  - Body's head piece and all face parts (eyes, mouth, brows) plus hair form one **head group**. Per turn angle and per
    handoff frame it gets exactly one transform:
    `headGroup: {"angles": {"<deg>": {"dx": 0, "dy": 0, "rot": 0, "scale": 1}}, "pivot": [681.5, 318]}`.
    It is applied once, on top of the head bone, so the group moves locked together.
  - This is the **only** correction path for head placement. Per-part offsets for mouth, eyes or hair at handoffs must not also
    carry the head shift. Mouth's `mouth/work/turn_handoff/offsets.json` mostly measures this same head shift:
    - apose f001: dx 0, dy -9 (9 px up)
    - left f062: dx +8, dy +13
    - right f160: dx -7, dy +6

    Before use, subtract the head-group shift from these numbers. Only the remainder, the mouth's own error, may stay as a
    mouth offset. Do not double-correct.
  - Hair measured the head about 10 px high at the apose handoff and about 7 px high at the right handoff. The apose figure
    agrees with Mouth's 9 px. At the right handoff Mouth's dy is +6 (down), against Hair's "7 px high". The two disagree in
    sign there, so measure the head-group shift once from Body's head piece before anyone applies a number.
  - **Built (staged) behind `?headgroup=1`.** `rig/index.html` composes one matrix
    `T(dx,dy)·rotAt(pivot,rot)·scale(pivot)` onto the head bone in `headApply`, at rest too, but only when non-identity.
    - Everything carried by the head bone moves locked together: the skinned head, eyes, brows, mouth and all hair parts.
      The face box and bun moved by exactly (dx,dy): 0 px off.
    - API: `RigHeadGroup.set({dx,dy,rot,scale})`, `.reset()`, and `.applyHandoff(view)`, which reads
      `rig/partmesh/staged/headgroup.json`. URL params `hgdx`, `hgdy`, `hgrot` and `hgs` are also accepted.
    - The driver is not wired yet. Proposed hook: in `app/driver/driver.js` `arriveAt`, call
      `fr.contentWindow.RigHeadGroup.applyHandoff(view)` with `&headgroup=1` on the iframe URL. Ease it to 0 after the
      crossfade, so the live rest stays 0 px.
  - **Measured head offsets at the handoffs.** Method: alpha silhouette of the head region (top to y330), turn frame against
    live, maximised by IoU. Source: `rig/work/headgroup/handoff_offsets_sil.json`.

    | handoff | head dx, dy | IoU | torso dx, dy | head relative to torso |
    |---|---|---|---|---|
    | f001 apose | 0, -10 | 0.947 | 0, -9 | 0, -1 |
    | f062 left | -2, +1 | 0.884 | -2, +6 | 0, -5 |
    | f109 back | +2, +11 | 0.839 | +3, +3 | -1, +8 |
    | f160 right | +5, -6 | 0.893 | +5, +9 | 0, -15 |

    The apose and right numbers agree with Hair (about 10 px and 7 px high). Mouth's offsets minus the head group leave
    these remainders as mouth-own error: apose (0, +1), left (+10, +12), right (-12, +12). The large profile remainders mean
    Mouth's feature NCC (0.78/0.76) is not measuring the head there. Mouth should re-measure after the head group is applied,
    not apply its old numbers. The torso is also off by up to 9 px, which is a whole-figure fit issue for Body/angle_map,
    not the head group.
  - **Neck seam rule.** Whenever the head group moves, measure the neck seam at each handoff frame and report it to Body, who
    fixes it in the neck cut. Report the gap px (transparent or background between head and neck) and the overlap px (head
    over the collar or neck line), per handoff. Nothing else compensates the neck.
    Measured with the skin mesh (`rig/work/headgroup/neck_seam.json`):
    - The gap is **0 px** at all 4 handoffs, and no new enclosed holes appear anywhere (shift-aware). The skinned neck
      stretches rather than opening.
    - Apose: neck stretch +10 px.
    - Left: overlap/compression 1 px, shear -2.
    - Back: overlap/compression **11 px**, shear +2.
    - Right: stretch +6 px, shear +5.
    - With cut pieces (Body's hairless division: head and neck are separate pieces), these become a gap of the same size
      (apose 10, right 6) or an overlap (back 11, left 1) at the neck cut.
- **Per-angle visibility and z (f, i).** `angles[deg].visible` and `angles[deg].layer`. The hair bun is 101 when front-facing
  and 650 otherwise.
- **Group hide (G8).** A part with `"group": "EyeR"` is hidden whenever `groups.EyeR.visible` is false at that angle. A hidden
  `parent` also hides its children.
- Never mirror. Every angle needs its own authored drawing, and there is no flip field.

### 3.7 Per-owner requirements
- **Eyes (G4, G5).**
  - Lid spine control is non-rotational, with both corners pinned:
    `controls: [{"param": "EyeROpen", "spineAt0": [[x,y]×5], "pin": [0, 4]}]`. The spine points interpolate by `1-Open`, and
    the pinned points never move. A pinned tail joint is allowed, not just a pinned root.
  - Skin above the moving lid comes from a stretch flap from the crease to the band edge
    (`flap.weightsFrom: "parent", "stretch": true`) or a flat skin fill (`fill: {"sampleRing": "skin"}`). The crease is never
    covered.
  - The lash uses `bind.spineOf` on the lid.
  - Option A (today's 8 lid frames as a swap) needs only 3.2, 3.3 and 3.5.
- **Mouth.** z order: interior < lower lip < upper lip. The upper-lip flap goes under the lower lip. Interior and teeth have
  `visibleWhen MouthOpen>0` and a dynamic `clip.gap ["upper_lip","lower_lip"]`. The full list is in 3.8.
- **Hands.**
  - Per-drawing pivots and swaps: built (`drawings.f<i>.pivot`, rig frame pick).
  - **Hands F6 (tpose).** Each child segment draws above its parent (Middle1 307 < Middle2 308 < Middle3 309), so flaps
    hidden at rest under the child show on bend. Under 3.1(a) a child can be put under its parent (`layer: {"under": parent}`).
    The meshed alternative needs no flaps; see the pilot results.
  - Each segment's flap goes under its parent segment.
  - A frame drawing's root cap outline (the knuckle end drawn behind the pivot) must lie in the rigid part of the weights
    (w=1), or it tears into floating specks. Found in the pilot; see 5.
- **Hair.**
  - Per-angle z (bun 101/650).
  - Spring state keyed by part id; it persists across angle switches and swaps, with preset A as default.
  - Root flap under the fringe; tip flap under the parent strand.
  - The spring clamps sway to ±1. The ±1.015 overshoot of preset A is clamped in the uniform slider path.
- **Body (bend-tool candidates).**
  - The outer-hip outline steps 5–6 px at ±25°. That is a candidate for a meshed hip/thigh pair (root joint thigh←pelvis),
    using the same angle blend.
  - The neck cut absorbs head-group seams (3.6).

### 3.8 Mouth mesh bend (from `mouth/staged/mesh_bend/REPORT.md`, it16 final: PASS apose + tpose)
**Accepted plan.**
- The mesh bend covers only rest → AA (half and full), M, and smile.
- **OH and EE stay drawn swaps** (3.3). There is no pucker/round control and no teeth part.
- Rest is the identity map: 0 px.

What the format must carry for this mouth:
1. **Dense lip curves.** Each lip curve (upper outer, seam, lower outer) needs about 50 control points, one per pixel column,
   given as `spine` with `"knots": "per-column"` or as an explicit knot table `{"x": [...], "y": [...]}`. The 3–5 point limit
   in 3.6 applies only to rotational chains (hair, fingers). Dense curves are exempt, but their point count must still match
   across angles (G14).
2. **Width-preserving bands.** Per-vertex band class along a spine: `"band": "rigid" | "fill"`.
   - Outline and seam line bands are rigid and keep their pixel width.
   - The fill between them stretches, with `minFillRatio`.
   - Excess compression is spread over the neighbouring fill (`clampSpread: true`).
3. **Pixel snapping per part or band.** `snap: "none" | "y" | "xy"`. Mouth uses `"y"`, because x/y snapping folded
   72 triangles (it10). Snapping moves the line in whole-pixel steps across Open. That is accepted, and `"none"` stays available.
4. **Skin pad.** A drawable cut from `base.png` (`"image": "views/<v>/base.png", "cutMask": "<mask.png>"`). It sits under the
   lips on the vacated side, with a "pin on the vacated side" rule so skin, not background, shows where the lips leave.
5. **Flap layer under the interior.** A layer slot below `interior` (`layer: {"under": "interior"}`), with a defined overlap
   with the owner's other flaps. The extended flaps and the interior notch fill are derived parts.
6. **Interior gap clip parameters.** `clip.gap` uses the lip spines as edges, plus `tuck: 0.5`, `extend: 0.5` (px) and an
   overlap margin.
7. **Non-linear control curves.**
   - Piecewise open targets at MouthOpen 0.5 and 1.
   - Per-side corner dx/dy for smile.
   - A curl exponent: `controls[].curve: {"knots": [[0,0],[0.5,a],[1,1]], "exp": k}`.
8. **4-corner perspective per part (diagonals).** `transform: {"quad": [[x,y]×4]}` is a homography applied before the mesh,
   plus a face-silhouette clip (`clip.outside` or a mask). Mouth's staged diagonals in `mouth/staged/diagonals/` use
   homography + per-column vertical knots: IoU against her frames is **0.934 at 45°** and **0.920 at 315°**. Her far corner at
   315° is a thin point that the front corner doesn't reproduce. The fit comes from
   `body_tools/work/apose_turn/diagonals/diagonals.json` (see `fit`, 3.6).
9. **Area filtering on minification.** `sampling: "area"` (box/mip filter) for any part drawn at scale < 1, as on the
   diagonals at ×1/1.54. Bilinear drops 1 px lines. Add this to 3.4 next to linear/nearest/shear-nearest.

Known limits, accepted:
- The opening shape is only roughly matched (opening IoU 0.62 at AA_half, 0.79 at AA).
- The upper lip compresses when open, as in her art.
- The lower-lip highlight is squashed, not redrawn.

## 4. Ready for owners?
**Yes, for Hair and Hands.** They can author against section 2 today. Generate or adjust with `rig/partmesh/tools/build_pilot.py`
(`part=blend`, `part@c=offset`, `PARTMESH_OUT=dir`), or write weights directly. Submit to `rig/partmesh/staged/`. The Coder
lists the file in the manifest and runs the pass mark.

**Mouth, Eyes and Body can write files now** (Mouth: see 3.8 for the full list), but their hooks need fields from section 3 that are not built yet: clips,
flaps, the non-rotational lid control, per-part sampling, and `visibleWhen`. Until those exist the renderer ignores those
fields, and the parts draw exactly as today. The diagonals also wait on art acceptance and on `fit` (3.6).

## 5. Pass mark used for the pilots (repeat it for every new file)
1. Rest is 0 px against base.png in all 5 views with `?partmesh=1` (linear), and live FR is 0.
2. The flag-off default is byte-identical to the pre-edit rig (FR hashes, 5 views × 6 poses).
3. Line width stays within ≤1 px of rest (p95 |dw|). Breaks: no new ones (fingers: <2). No new sharp corners. No new pieces.
   No new enclosed holes. **No new floating ink specks** (dark components ≤8 px not touching a line).
4. 0 px changed outside the meshed parts' reach. Vertex displacement against rigid stays ≤2 px outside the blend zone.
5. The Python mirror (`rig/work/partmesh_pilot/pmpy.py`) agrees with the browser on ink.
6. Side-by-side contact sheets against rigid.

**Pilot results (2026-10-02 PT).**
- **Hair strand_03.** Passed at iteration 1.
- **Hands R_Middle.** Staged at blend 4/4/3 after 3 rounds (iter1, iter2, then sweeps c3–c6 and d1–d6). It passes 1, 2, 4
  and 5 and the width/break/corner/hole parts of 3. Max |dw| is 0.62, there are 0 breaks, and there are no new holes.
- **Open defect:** new floating specks of 1–3 px.
  - They sit at (121,402) at curl ≥0.20, and as faint crease-end fragments near (92,405) and (103,419).
  - Cause: the frame drawings f1/f2 have their root cap outline and knuckle creases inside the blend zone behind the pivot.
    The mesh tears them.
  - No blend or offset setting fixes both this and the 0.87 palm-seam break.
  - The fix is art-side: keep cap and crease ink out of the zone, or supply per-frame weights. Hands owners, see 3.7.
- **Does the mesh bend remove the need for flaps (tpose R_Middle, child above parent as live)?** At the Middle joints,
  **yes**. Both sides of each joint deform identically in the overlap zone, so no wedge opens and nothing hidden at rest is
  revealed. With no flaps at all:
  - New enclosed holes: 0 in every case.
  - The rigid 0.87 palm-seam break goes from 6 to 0 breaks.
  - The 1–2 px enclosed holes at curl ≥0.70 and Fist/Point are present in rigid too (identical counts), so they are not
    joint wedges.
  - What the mesh does not fix is the floating-speck defect above. That is an art issue, not a flap issue.
