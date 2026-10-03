# rig/qa_gates.py: QA gates (read-only)

Coder, Sat Oct 3 2026, PT. The script only reads files. It writes nothing except the `--json` you pass it.

    PYTHONDONTWRITEBYTECODE=1 python3 rig/qa_gates.py [--gate weights,leak,scale|all] [--part SYS[/glob]] \
        [--view apose,tpose,left,right,back] [--staged-dir DIR ...] [--skin candidate.json] \
        [--tol 2] [--no-diagonals] [--no-mesh] [--json out.json]

Exit code: 0 if every selected gate passes, 1 if any fails. A one-line summary per gate goes to stdout, and the full detail goes to `--json`.

## Running it on your own parts
| bot | command |
|---|---|
| Eyes | `python3 rig/qa_gates.py --gate leak --part eyes --staged-dir eyes/work/lashfix/staged` |
| Mouth | `python3 rig/qa_gates.py --gate leak --part mouth --staged-dir mouth/staged/tone_fix` (add `--part mouth/anger` to check one shape) |
| Hair | `python3 rig/qa_gates.py --gate leak --part hair --staged-dir hair/staged/tone_fix` |
| Hands | `python3 rig/qa_gates.py --gate leak,scale --part hands` |
| Body | `python3 rig/qa_gates.py --gate weights,leak,scale --part body --view apose --skin path/to/candidate_skin.json` |

How the flags work:
- `--part` takes a system name (`body`, `eyes`, `mouth`, `hands`, `hair`), optionally followed by `/` and a filename glob, for example `hair/bun*` or `eyes/EyeL_lid_*`.
- `--staged-dir` can be repeated. It is looked up as `<dir>/<view>/<system>/<file>`, then `<dir>/views/<view>/<system>/<file>`, then `<dir>/<view>/<file>` (the eyes layout). If you leave it out, the script uses all three tone-fix dirs.
- A file with no staged fix is reported as live in the staged column.

## Per-part dir overrides
- `--hair-dir`, `--mouth-dir`, `--eyes-dir`, `--hands-dir` and `--body-dir` point one system at another folder, so staged sets run without making a copy.
- For each view the script looks for, in order:
  1. `DIR` with `{view}` replaced by the view name
  2. `DIR/<view>/<sys>`
  3. `DIR/views/<view>/<sys>`
  4. `DIR/<view>`
  5. `DIR` itself, if it holds a rig.json or PNGs
- If none of those exist, it falls back to `views/<view>/<sys>`.
- Diagonal angles can be passed to `--view` along with an override, for example:
  `python3 rig/qa_gates.py --gate leak --part hair --hair-dir hair/staged/diagonals_v2 --view 045,135,225,315 --no-mesh`
  The palette is then all 5 base.png, her live hair in all 5 views, and her turn frame.
- Result for that run (03:48 PT): 34 files, 0 off-palette, 0 chroma, 0 soft edge.

## G1 `weights`: weight bleed (body `skin.json` plus its `underlay`)
- **bleed_vs_dominant_bone:** any weight above 0.001 on a bone that is not the vertex's dominant bone, its parent, its child, or its sibling. **Fails.**
- **bleed_vs_texel_owner:** the same test, but the owner is the top-layer body part mask under the vertex (the way build_skin assigns owners). This is reported for information; profile overlaps show up here.
- **isolation:** each posable bone is rotated on its own to its ±1 angle (the same `bodyAngle` / `rotAt` / chain / LBS maths as `rig/index.html`).
  - Any vertex of an *unrelated* part (not self, descendant, parent or sibling) that moves more than 0.5 px **fails**.
  - Parent and sibling seam motion is listed as info.

## G2 `leak`: chroma, off-palette, soft edges and colour outside the mask
- **Palette, per part:** a tone counts as hers if it appears anywhere in her authored source art for that part and view:
  - the view's `base.png`;
  - her own live part files for that system in that view (every PNG the system's `rig.json` references), for example the live apose hand parts that carry (13,11,29);
  - the extra sources listed below.
  - Only tones found in none of her art are off-palette.
  - Because her live files are part of the palette, **live** counts are 0 for those files by construction. The meaningful numbers are **staged** (new tones a staged fix introduces), the diagonals, and the body skin textures, which `build_skin_texture` rebuilds.
  - All mouth shapes also use `reference/test_sheet_expressions.jpg` (mouth interior, teeth, tongue).
  - `mouth/anger*` also uses the Clean room anger art `reference/grok_build/public/puppet/emotions/anger.png`.
  - Diagonals use all 5 `base.png` files, her live files of that system in all 5 views, and her turn frame for that angle (045=f033, 135=f087, 225=f131, 315=f191).
  - Her own drawn colours are never flagged.
- **What is counted:**
  - `off_palette`: opaque px (α=255) whose RGB is more than `--tol` (default 2) from every palette colour.
  - `chroma`: px with α>0 and blue > max(r,g)+60 and blue > 120 (key spill).
  - `soft_edge`: px with 0<α<255. This is counted separately and **does not** fail the gate.
- **Three file sets:**
  - `live`: `views/<view>/<system>/*.png` plus the body skin texture.
  - `staged`: the same files with the staged tone fixes swapped in.
  - `diagonals`: `hair/staged/diagonals/<ang>/hair/*.png`, `mouth/staged/diagonals/<ang>/renders/*.png`, and the hand diagonals in `rig/hand_angles/<ang>_<side>.png`.
  - The gate verdict uses `staged`.
- **mesh_outside_mask** (body skin, posed):
  - Poses: rest, every param at ±1 alone, all +1, and all −1.
  - Each opaque vertex's LBS position must stay within 1 px of the hull of the positions its own texel-owner part's related bones would give it. Anything further is colour drawn outside its own part's mask.
  - Rigid parts (eyes, mouth, hair, hands) are drawn with drawImage under one matrix, so they cannot leak outside their mask by construction. For them, only the file-level checks apply.
- `nearest` renders only sample texels, so file-level colours are what reach the screen. `linear` adds blended edge px; those count as soft edges, not as off-palette.

## G3 `scale`: hand and foot proportions
- **Truth:** her five base views are the scale truth. Their ratios vs apose are listed as info only (`info_drift_gt_tol`) and never fail.
- **Measured** (and can fail): the turn-angle hand sprites `rig/hand_angles/<ang>_<side>.json`. The value is `physicalLength` (wrist→tip, frame px) × that frame's frame→view scale from `body_tools/work/apose_turn/turn_measure.json`. It is compared with the apose palm + middle finger (wrist pivot → Middle1 → Middle2 → Middle3 tip).
- **Flag:** drift above 1 px.
- **Base-view measures:**
  - palm: wrist (palm pivot) to Middle1 pivot.
  - finger: the Middle chain plus the tip.
  - foot: foot mask extent.
  - Each is divided by head height and by forearm length (elbow → `wristPivot`).
- **Limits:**
  - The sprites' `physicalLength` may be defined differently from the apose chain. All 8 come out at 144.7 view px vs 156.6, so check the definition before reading −12 px as real drift.
  - Generated diagonal body/turn frames other than hands are not covered yet.

## Added Oct 3, 2026 (~04:30–04:45 PT)
- **G2 chroma rule v2 (default)** `--chroma-rule v2|old`:
  - Exact `#0000FF` always fails (`chroma_v2.key_exact`).
  - A bluish px (old test: b > max(r,g)+60 and b > 120) is hers only if its RGB is in the allowlist. The allowlist is built from her palette-source art with the silhouette eroded 1 px, where key = alpha 0, exact key, or bluish connected to the border.
  - A non-allowlisted px that exactly equals `views/<view>/base.png` at the same position counts as `frame_match_rest` (at rest), or as `frame_fringe` when posed. Neither one fails.
  - `--chroma-rule old` restores the old bluish heuristic for comparison. Every file reports both `chroma_old_rule` and `chroma_v2{...}`.
  - On the live rig (all 5 views) both rules give identical totals: live 0, staged 0, diagonals 1 (`hair/staged/diagonals/315/hair/strand_04.png`). See `out/leak_live_chroma_{old,v2}.json`.
- **`--owner texel|layer`** (G1 isolation): the owner is the top-layer texel (default), or the part of the vertex's own triangle layer(s).
- **`--bend-check`** (or `--gate bend` to run it alone): runs `rig/work/bend_check/bend_check.py`. It measures waist side-step, hip crease dent/notch, shoulder/elbow outline spikes and the head-neck gap:
  - on Body's `diag_body` vs `diag_body_fix` (`--bend-angles 045,315`);
  - on the live rig renders (`--bend-live apose`). `--bend-render PORT` re-renders them with `render_live.js` against a server you already run on PORT.
  - It is informational and never changes PASS. Output goes to `rig/work/bend_check/`.
- **Per-system dir overrides** `--hair-dir/--mouth-dir/--eyes-dir/--hands-dir/--body-dir DIR`.
