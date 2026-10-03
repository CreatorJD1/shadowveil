# Eyes → partmesh v0.1: mapping notes and gaps (2026-10-02 PT, Eyes, notes only, nothing wired)

Source: `rig/partmesh/FORMAT.md` (draft v0.1), read-only. I also looked at `rig/partmesh/staged/` (hair and hands pilots) and the
`?partmesh=1` loader in `rig/index.html` (lines ~395-409). Nothing in `rig/` or `views/` was changed.

## 1. How the eye parts map
One file per owner (`"owner": "Eyes"`), with angles `0 apose, 90 left, 270 right` (+ `45`, `315` when the diagonals are accepted; `180` back = hidden).
Each eye is its own set of parts, so every rule can be set per eye:

| current part (views/<v>/eyes/rig.json) | partmesh part id | layer | how |
|---|---|---|---|
| `EyeR_white` | `EyeR_white` | 400 | 1 drawing per angle, no mesh (rest path) |
| `EyeR_iris` | `EyeR_iris` | 401 | `clip: {to: "EyeR_white"}`, `limits` per angle (gaze), pivot = iris centre |
| `EyeR_lid_0..7` (frame swap) | `EyeR_lid_upper` | 402 | **A (today's art):** 8 drawings + `swap: {param: "EyeROpen", buckets: [1, 6/7, …, 0], drawing: [0..7]}`. **B (mesh):** 1 drawing (`lid_0`) with a spine along the upper-lid edge, bent by `EyeROpen` |
| `EyeR_lash` | `EyeR_lash` | 403 | `bind: {spineOf: "EyeR_lid_upper", offset: [0, 0]}` (with B); a static drawing with A |
| (EyeL same) | `EyeL_*` | 410-413 | same |

At rest the lid is `lid_0` (her exact drawing) and the mesh is the identity. That satisfies the rest rule. The eye rest is 0 px today.

## 2. Coverage of the four requirements
| requirement | covered? | where | notes |
|---|---|---|---|
| Iris clipped to the white | **Yes** | `clip: {to: "EyeR_white"}` | Same as today's offscreen `source-atop`. Per-eye ids keep R and L separate. |
| Per-angle gaze limits | **Mostly** | `part.angles[deg].limits` (k), `sign: -1` for the left profile | Only `EyeBallX {dxPlus, dxMinus, sign}` is spelled out. Gaps G1–G3 below. |
| A single bent upper lid, with the lash sharing its bend line | **Partly** | `bind.spineOf` (l): the lash uses the lid's deformed spine and weights | The bind half is covered. The lid bend is not: controls are rotations from a root. Gaps G4–G7. |
| Per-angle hiding of each eye | **Yes, part by part** | `angles[deg].visible: false`, or a missing angle (i) | Each eye has 4 parts, so hiding one eye means 4 overrides. Gaps G8–G9. |

## 3. Gaps for the Coder
- **G1 Y limits.** Define `EyeBallY {dyPlus, dyMinus}` next to X. Today's views use `dxAtXminus1/dxAtXplus1/dyAtYminus1/dyAtYplus1`, and the diagonals use the same values per eye.
- **G2 Units and rounding.** Say whether limits are in canvas px, and give the rounding rule. Today: `dx = round(X*(plus if X>0 else -minus))`, with round = `floor(x+0.5)`. The diagonal limits are in turn-frame px (×1.54468 = view px). See G10.
- **G3 Limits between angles.** Nothing says how `limits` behave at in-between dial positions (snap at t=0.5 like the art? interpolate?). Suggest: snap with the drawing.
- **G4 Lid control type.** `controls` are rotations (`maxDeg`, `falloff` along a root-first chain). Closing a lid is a downward sweep of the lid edge with **both corners pinned** (largest at the middle, 0 at the corners). The format needs a non-rotational control, for example `{"param": "EyeROpen", "spineAt0": [[x,y]...]}`, where the spine points are interpolated by `1-Open` and the end points stay fixed. It should also allow a pinned tail joint, not just a pinned root.
- **G5 Skin above the moving lid.** A mesh only moves her pixels. Something has to fill the skin left above the band: a stretchable flat-skin flap from crease to band edge (`weightsFrom: parent`), or a flat skin fill. Our current frames do this with flat skin sampled from her skin ring, and the crease is never covered.
- **G6 Hiding the eye under the lid.** The white and iris must be cut off below the bent lid edge. `clip: {gap: ["EyeR_lid_upper", "EyeR_lid_lower"]}` (the mouth's gap clip) would do it if the eye also gets a static `EyeR_lid_lower` part with a spine along the lower line. Please confirm gap-clip is allowed for Eyes and that it works with clip-to-white (two clips on one part: the white uses the gap, the iris clips to the white).
- **G7 Line width and sampling.** The lid band is 3–6 px of hard, binary-alpha pixels. To meet the eye pass mark (≤1 px width, no breaks, no kinks) the bend has to be a vertical shear with nearest-pixel sampling. Bilinear sampling of a rotated or stretched strip would soften and thin it. The spec should state the sampling mode for deformed drawings (rest is byte-identical either way). The staged eye fix uses per-column integer shifts with slope ≤1 (≤2 on the 13–24 px diagonal eyes).
- **G8 Group hide.** There is no group or parent visibility inheritance, so hiding an eye means setting `visible:false` on 4 parts per angle. Suggest that a hidden `parent` (e.g. `EyeR_white`) hides its children, or a `group` field.
- **G9 Partial hiding (far eye at 45/135/225/315).** The far eye may need to be cut by the cheek or nose line. `clip` only intersects (`to`) or uses a lip `gap`. Add an inverse clip (`{"outside": "<part id>"}`) or an authored per-angle mask image. (The staged diagonals keep the far eye whole, as asked.)
- **G10 Diagonal canvas.** FORMAT requires full-canvas images of the per-angle canvas (1365x1739) and checks rest against `base.png`. The 45/315 eye parts are in **turn-frame px (768x1168)**, and placing them needs `view_fit` (scale 1.54468, dx/dy from `body_tools/work/apose_turn/diagonals/diagonals.json`). There is also no `views/<45|315>/base.png`. Options: (a) a per-angle `fit: {scale, dx, dy}` field, with rest checked against the frame (that is how `eyes/staged/diagonals/` passes: 0 px); or (b) resample the parts into view space. Option (b) is no longer her exact pixels, and nearest-neighbour at ×1.54 gives uneven pixel doubling.
- **G11 T-pose has no angle slot.** `angles` maps deg → view, but `tpose` is a second pose at 0°. Eyes ship tpose art. FORMAT needs a pose key (e.g. one file per pose, which the pilots already do with `"view": "tpose"`).
- **G12 Swap semantics.** If the lid stays a frame swap (option A), define how a param value picks a bucket (nearest? floor?). Eyes need `frame = round((1-Open)*7)`.
- **G13 Draft vs pilot drift.** The staged pilots (`staged/*.json`) use a different shape from FORMAT.md: one file per view with `view`/`system`, a top-level `joints`, `deform: "angle"`, `drawings` as a keyed dict with `sha256` and explicit meshes. Also, FORMAT says the renderer is "not built", but `rig/index.html` already has a `?partmesh=1` loader (v1.9, off by default). Please settle which schema the Eyes should author against before we write a file.
- **G14 Spine point count across angles.** Point counts must match across angles or the part snaps. Eyes would use a 5-point lid spine at every angle (corner, ¼, middle, ¾, corner). That is fine, but the diagonal eyes are only 13–24 px wide, so the points are 3–6 px apart.

## 4. Suggested order (when the Coder is ready)
1. Settle the schema (G13) and the diagonal canvas question (G10).
2. Option A first: per-eye parts, a swap for the lid frames, `clip.to` for the iris, and per-angle `limits`. This keeps today's look exactly.
3. Option B (bent lid + `bind` lash) only after G4–G7 exist. Its pass mark is the same as the staged lash fix (≤1 px width, 0 breaks, 0 kinks, crease never covered).
