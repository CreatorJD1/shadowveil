# (A) Crotch notch: inner-thigh weight blend (proposal; candidates only, nothing in views/ or body_tools/ changed)

Coder, Sat Oct 3 2026, PT. Apose only. The cut from body_specs.json is [681,838]–[681,875].

## Cause
`build_skin` blends weights only across parent/child seams. thigh_L and thigh_R are siblings, so the vertices on the crotch cut are split: each side follows only its own thigh. When she bends one hip, or both hips the opposite way, the texels at the inner thigh slide off. The live underlay leaves the gap empty, because `--bgk 8` keeps underlay fill away from the background between her legs and `--crotch 40` drops the thigh fill near the midline.

## Spec: `--crotch-blend R` (patch in `build_skin_crotch.py`, a copy of body_tools/build_skin.py)
- Thigh-owned px within R of the crotch cut (extended `--crotch-below 40` px under the apex) fade their thigh weight to the pelvis, their shared parent. The fade is a smoothstep, with `--crotch-floor` (default 1) at the cut itself. The weight moved goes to the pelvis, so the partition of unity is kept.
- `--crotch-seg x0,y0,x1,y1` overrides the cut.
- `generator.crotchBlend` records the parameters.
- The copy refuses to write outside `rig/work/crotch_weights/`.
- **Check:** `apose_skin_ref.json` (copy with no new flag, the recorded generator cmd) is identical to live (vertices, triangles, weights).

## Underlay variant (`build_underlay_copy.py`, a copy that writes its PNG here and not to views/)
`ulnb` = `--crotch 0`, no `--bgk`. The pelvis flat fill then also sits behind the inner thighs at the crotch.

## Results (`notch.py` → `notch_apose.json`, `notch_apose.png`)
- Method: posed mesh (skin + underlay) rasterized in Python.
- Each cell is: holes in the crotch box x640–722, y820–900 / of those, holes above the rest apex y875. Holes are px opaque at rest that show background when posed.
- Rest is 0 / 0 for every candidate.

| pose | live | cb24 (weights) | ulnb (underlay) | cb24ulnb (both) |
|---|---|---|---|---|
| HipL −1 | 1105 / 430 | 815 / 292 | 841 / 183 | 671 / 165 |
| HipR +1 | 1203 / 468 | 811 / 315 | 992 / 257 | 682 / 186 |
| Hips +1 | 402 / 194 | 396 / 256 | 289 / 81 | 268 / 128 |
| Hips −1 | 322 / 177 | 417 / 246 | 167 / 22 | 275 / 119 |
| HipL −1, HipR +1 | 2216 / 806 | 1616 / 597 | 1770 / 377 | 1343 / 341 |
| HipL +1, HipR −1 | 3 / 3 | 0 / 0 | 3 / 3 | 0 / 0 |

- cb12 and cb18f06 (smaller R / floor 0.6) change nothing that matters.
- **cb24 has a side effect:** the stretched inner-thigh texels leave a dotted dark edge under the panty when the legs separate. See row 2 of the sheet.
- **ulnb** fills the notch top with her flat panty/skin underlay colour and gives the cleanest look. Hips −1 goes 177 → 22.

## Gates (`../../qa_gates.py --skin`, apose)
- **G1:** bleed 0 and isolation clean for cb24, ulnb and cb24ulnb, the same as live.
- **G2 mesh_outside_mask** (all±1): live 198/194, cb24 112/108, ulnb 198/194, cb24ulnb 112/108.
- **Recommendation:** ulnb (underlay `--crotch 0` without `--bgk`). Add cb24 only if Base Body accepts the dotted edge.
- Rest equality in the real rig still has to be checked by Base Body. The underlay sits under alpha-255 skin with a 6 px margin, but this was not rendered in the browser here.
