# F11: wrist flaps for left, right and back (staged)

Status: **PASS** in the real rig, using a scratch copy of the renderer for draw order.
- Rest 0 px, gestures (Fist/Point/Peace) 0 px, and 0 holes / 0 breaks in every wrist case, for all three views.
- One extra tear pixel in back R run−0.12.

## Files
- `<view>/{L,R}_palm.png`: the flaps. Left and right have one hand each; back has both.
- Also per view: `flap_log.json`, `rig_check.json`, `rig_check_sheet.png` (rows: rig control / F11 r20 / alt r20d5), and the scratch sim JSONs.
- `<view>/alt_r20d5_linestrip/`: depth-5 alternative, mostly line colour.
- Tools: `make_flap_v.py` and `wrist_sim_v.py` (F7/F10 tools per view), `hb_render_f11.mjs` (render harness), `rigc.py` (metrics), `exposure.json`, `scratch_rig_patch_vs_db5cf270.diff`.

## Method (same as F7/F10, radius 20, line 2)
**Wrist lines** (Body's `hairless_division_staged/<view>/wrist_line_*.json`, which match the brief):

| view | line | pivot |
|---|---|---|
| left | (703,850.7)–(656,852.2) | (678,852) |
| right | (705,855.3)–(676,856.3) | (676,857) |
| back L | (323.9,744.1)–(293.5,715.4) | (308,730) |
| back R | (1069.5,715.4)–(1039.1,744.1) | (1055,730) |

**Flap rules:**
- Flap px sit on the forearm side of the line, within 20 px of the pivot.
- They lie only under Body's forearm piece where it is alpha 255 (`flap_not_under_opaque_forearm` = 0), so they are hidden at rest.
- They are transparent in her live palm (0 of her opaque px changed) and outside `hands/<view>_hand_erase_mask.png` (0 changed).

**Colours:**
- Skin is Body's tone per view: left (185,122,78), right (183,120,76), back (183,122,77). All three exist in that view's base.png.
- The line uses a substitute colour. **(13,11,29) does not exist in any of the three base.png files**, so I used the nearest colour that does: left (12,10,28), right (11,11,28), back (12,12,31).
- Every new opaque colour was checked against that view's base.png.

**Flap size** (flap px / line px):

| view | flap | line |
|---|---|---|
| left L | 532 | 141 |
| right R | 532 | 141 |
| back L | 505 | 139 |
| back R | 533 | 146 |

## Real-rig check (2026-10-03 01:04–01:11 PT)
**Why a scratch copy of the renderer.** Live rig/index.html (md5 db5cf270… at the time) with `?hairless=1` draws hands above everything in these views:
- left/right: hands 320+, above forearm 250;
- back: hands 300+, above forearm 220.

So I rendered with a **scratch copy** in `/workspace/scratch/f11rig/rig/`, served by the harness on port 8778 with `--rigroot`. The served md5 matched disk on every render.
- It changes hairlessOrder: hands 300–335 move to **243–248.25** in left/right (above thigh 242, under forearm 250) and to **210–219** in back (under forearms 220, above thighs 205).
- `?f11dir=` maps the view's palms.
- rig/ was not edited. **Coder needs the equivalent order and palm mapping live.**
- Live rig/index.html has since changed to 0ce6fecc…; the copy was taken from db5cf270.

**Control:** the same scratch rig with her live palms.

**Results** (cases: rest, wrist ±1, anger, jump −0.2/+0.2969, run ±0.12, Fist/Point/Peace):

| view | rest vs ctrl | gestures | holes / breaks | worse than ctrl | max abs dw |
|---|---|---|---|---|---|
| left | 0 px | 0 px | 0 / 0 | none | 0.16 |
| right | 0 px | 0 px | 0 / 0 | none | 0.27 |
| back | 0 px | 0 px | 0 / 0 | tears 2→3 on R run−0.12 | 0.02 |

**Thigh** (`exposure.json`; px changed by more than 8/255, outside the forearm and over the thigh):
- At rest: 0 in all views.
- At bend: left 3 (+1) / 53 (−1); right 1 / 24. This is the flap filling the wrist gap as the hand bends away; it is above the thigh by design.
- Back: 0 over the thighs.

**Alt r20d5:** no case worse than the control, and smaller exposure (left 2/13, right 0/13). Most of it is line colour (back is line only).

**Scratch sim:**
- Profiles: live is already 0/0/0, and r20 stays 0.
- Back: tears 20–33 → 0–5 and breaks 18–21 → 0–2, but +2 holes on L bend−1.
- The real rig does not show those holes.
