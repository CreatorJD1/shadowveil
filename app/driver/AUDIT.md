# Live driver simplification audit (2026-10-02 PT)

Scope: `app/driver/index.html` (+ `driver.js`), `app/rigctl.js` (Rig controls tab in `app/index.html#body`),
`app/pose-editor.js`, `app/workspace.js`, the rig control panel in `rig/index.html` (`groups[...]` / `groupBox`, settings,
Layers panel, the inline pose toolbar), and the Live Preview bars in `app/index.html` that pick view, clip, hair and auto for the rig.
This was a read-only audit. `rig/index.html` was not edited; another worker changed it during the audit (md5 6ddf13f9… at 20:35 PT, e7246ffe… at 21:15 PT).

Tags: **DUP** = the same parameter or setting is controlled in more than one place · **DEAD** = does nothing, is stale, or is never loaded ·
**TEST** = test, QA or debug only · **KEEP** = goes into the simplified driver (`simple.html`).
Counts are interactive elements measured in headless Chrome at view `apose`.

## Counts

| Surface | Controls before |
|---|---|
| `app/driver/index.html` (Clean room turn player) | 20 (16 inputs + 4 clickable QA thumbnails) |
| `rigctl.js` Rig controls panel (loads `rig/index.v18-wip.html` first) | 95 (78 live sliders, 4 disabled "in progress" rows, 5 dial labels, ◀ ▶, Reset, 4 hand presets, hair preset) |
| `rig/index.html` `#ui` panel | 109 (18 settings + 86 param sliders + 4 hand presets + Replay clip) |
| `rig/index.html` inline pose toolbar (same code as `app/pose-editor.js`) | 12, plus about 40 draggable joint handles |
| `rig/index.html` Layers panel | 7 static, plus about 154 per-layer row toggles |
| `app/index.html` Live Preview bars + `#workspace-tools` | 39 (37, plus the hair and auto selects that only show for the v1.8 WIP source) |
| `app/pose-editor.js`, `app/workspace.js` | 0. No page loads them (see DEAD below). |
| **Total** | **282 static controls**, plus about 194 dynamic ones (layer rows and joint handles) |
| **`app/driver/simple.html`** | **76**: 43 in the main sections + 33 under the collapsed Advanced group (2 of those are disabled because they have no param) |

## 1. `app/driver/index.html` + `driver.js` (Clean room authored-turn player)

| Control | What it does | Tag |
|---|---|---|
| Auto ▶ | autoplays the turn tour (rest → turn → hold → drift) | DUP of angle control: the tour is another way to change angle. Cut. |
| Target buttons f001, f033, f062, f087, f109, f132, f160, f191 (8) | turn to an authored frame | DUP: angle. Merged into the View dial. |
| "rest" select (f001/f062/f109/f160) | picks the handoff frame to rest on | DUP: angle. Merged into the View dial. |
| idle sway checkbox | ±3 px x-offset of the whole frame | TEST (fakes motion by shifting the image; not a rig param). Cut. Use Motion → Idle instead. |
| blue despill checkbox | colour clean-up of the turn stills | TEST. Cut. |
| speed select (0.5–2) | turn tour speed | TEST. Cut. |
| Talk ▶ + talk clip select (speak/ask/laugh) | plays Clean room talk videos, front rest only | DUP: mouth (video, not params). Replaced by Mouth → Auto-talk (the rig's talk driver). |
| QA thumbnails (4) | seek the talk video to 0.4/1.8/3.2/5.0 s | TEST. Cut. |
| Turn dial (range f001–f232) | scrubs the authored turn | DUP: angle. Merged into the View dial (authored views only). |
| Timeline `#tl` (markers, beauty-mark ticks) | `cursor:pointer` but no click handler | DEAD as a control (display only). Cut. |
| Phase chips (rest/turn/hold/drift/talk/manual) | status display | TEST. Cut. |
| Rules text | notes | TEST. Cut. |

`index.html` is still there for the Clean room turn. `simple.html` covers only the live rig.

## 2. `app/rigctl.js` (Rig controls tab, `app/index.html#body`)

| Control | Tag |
|---|---|
| View dial (5 labels) + ◀ ▶ | DUP: angle (rig `#view`, Live Preview view tabs, driver turn dial). **KEEP** as the only angle control. Note: its angles (right = 90°, left = 270°) are the reverse of `poses.json` (f062 90° = left, f160 270° = right). `simple.html` uses the `poses.json` angles. |
| Reset to rest | DUP of rig `#rest` (it clicks it). KEEP: one Reset. |
| Open / Fist / Point / Peace | DUP of the rig's Hand presets. Unlike the rig's version, this one does not zero the per-joint offsets (Hand*1..3). Merged into one Hand pose dropdown. |
| Hand L / Hand R finger curl (7 + 7 sliders) | DUP of rig groups `Hand L/R (curl…)` |
| Wrist rotation L/R: WristL, WristR, PalmTwistL, PalmTwistR | DUP. PalmTwist is linked to WristTwist inside rig `set()`, so it is one param shown twice. |
| "in progress" WristRotL / WristRotR rows | **DEAD**: stale. `WristL`/`WristR` already exist, but the PENDING regex looks for `WristRot*`. |
| Twist group (13 sliders) | DUP of rig Twist group |
| Split finger curl (30 sliders Hand*1..3) | DUP of rig "individual joints" groups |
| "in progress" Claw L / Claw R rows | **DEAD**: no param in `rig/index.html` (only in `index.v19-next.html`) |
| Head (2), Body joints (13), Root (2) | DUP of rig groups |
| Hair spring preset select | DUP of rig `#hairpreset` (and the Live Preview `hair` select) |
| "Other params" group | **DEAD**: always empty |
| Collapsible headings (10) | KEEP the idea; `simple.html` uses `<details>` |
| `fit()` minw | **DEAD** code: `Math.min(1, w / w)` is always 1, so `minw` is ignored |

## 3. `rig/index.html` control panel (`#ui`)

| Control | Tag |
|---|---|
| `#view` select | DUP: angle. Hidden in `simple.html` (the dial reloads `?view=`). |
| `#zoom` select (Full/Head/Hands) | TEST. Cut. |
| Body mode (auto/cut/skin), Skin underlay, Posed filtering, Edge seal, Mouth switch (fade ms) | TEST: renderer settings. Cut. |
| Reset to rest | KEEP (single Reset; `simple.html` calls it) |
| Rest check, Motion quality, Joint test | TEST. Cut. |
| Show original base.png | TEST. Cut. |
| Auto (blink, gaze, sway, idle) checkbox | DUP: also the pose-toolbar Play motion, the workspace Play motion, `SVPlayback`, and `?autoplay`. Split into Motion (idle) plus separate Auto-blink, Auto-talk and Physics switches. |
| Life slider (0..1) | Merged: Motion → Idle (procedural) runs at the rig default of 1.0 |
| Auto style select (idle/talk) | DUP of the Live Preview `auto` select. Merged into Motion (idle) and Auto-talk. |
| Foot plant select | TEST. Used implicitly (default `xy`) by the Weight shift mapping. |
| Hair spring select | KEEP (as Hair → Spring preset, default A). DUP with rigctl and the Live Preview hair select. |
| Auto hand angles checkbox | TEST / leave at the rig default (on). Cut from the simple UI. |
| Eyes: EyeLOpen, EyeROpen, EyeBallX, EyeBallY | KEEP (Left lid, Right lid, Blink, gaze pad) |
| Mouth: MouthOpen, MouthForm | KEEP |
| Hair: HairSwayX, HairSwayY | Advanced → Other (manual, only while Physics is off). Physics + Sway amount replace them. |
| Hand L/R curl groups: Thumb, Index, Middle, Ring, Pinky, Spread, ThumbSpread, Wrist (8 + 8) | KEEP as Curl (4 fingers), Thumb, Spread, Wrist bend. Per-finger and ThumbSpread go to Advanced. |
| Hand L/R individual joints (15 + 15, Hand*1..3) | DUP-ish (offsets on top of the per-finger curl, also in rigctl). Cut from the simple UI; Reset still zeroes them. |
| Body joints (13) | KEEP Lean, Shoulder, Elbow, Hip, Knee L/R. Ankle and Toe go to Advanced → Other. |
| Root (2) | Advanced |
| Head (2) | KEEP (Head tilt, Head nod) |
| Twist (15, incl. PalmTwistL/R) | Advanced (twist axes + WristTwist). PalmTwist is cut as a DUP of WristTwist (linked in `set()`). |
| Hand presets (4 buttons) | DUP. Merged into the Hand pose dropdown. |
| Clip status + Replay clip | KEEP (as the status line and ↻ next to Motion) |

### Inline pose toolbar (`rig/index.html`; identical code in `app/pose-editor.js`)
| Control | Tag |
|---|---|
| Play motion | DUP (rig Auto, workspace Play motion) |
| Controls / Layers toggles | DUP (workspace "Hide rig controls" / "Hide layers") |
| Nodes, joint drag handles | DUP: a second way to set every body and hand param. Hidden in `simple.html`. |
| Twist handles | DUP (the workspace bar has the same button) |
| Left hand / Right hand focus, Pan, −, Zoom, +, Fit | TEST: viewport tools. Cut. |

### Layers panel (preview only)
| Control | Tag |
|---|---|
| hide, Pause, Step, step size, Reset order, Clear hide/solo, hair mask overlay, per-layer show/solo/expand rows | TEST (documented as preview-only). Cut. |

## 4. `app/index.html` Live Preview bars and workspace bar

| Control | Tag |
|---|---|
| rig source tabs (Live rig / v1.8 WIP / Pose driver) | TEST: chooses which page to embed |
| view tabs (all + 5 views) | DUP: angle |
| hair select, auto select (WIP only, set through the URL) | DUP: rig `#hairpreset` / `#autostyle` |
| clip tabs: all, idle, breathe, weight shift, arm settle, jump, anger, run, showcase, keys | KEEP as the single Motion dropdown. `keys` and `showcase` load the same `body_showcase.json` (DUP), so only showcase is kept. `all` becomes Off. |
| renders group tabs | TEST: video gallery filter |
| workspace bar: Play motion, Hide videos / preview controls / reports / sliders / notes, Focus pose, Show all, Hide rig controls, Hide layers, Twist handles | Layout only. Play motion, Hide rig controls, Hide layers and Twist handles DUP the pose toolbar. |
| open rig ↗ / pose driver ↗ links | KEEP (navigation) |

## 5. Dead files
- `app/pose-editor.js` (67 lines): no page loads it. The live copy is inlined in `rig/index.html` (lines ~1075–1142), and the file copy is stale: it lacks the `max-width:1100px` hideLayers line.
- `app/workspace.js` (17 lines): no page loads it. The live copy is inlined in `app/index.html`.

## 6. Decisions carried into `simple.html`
- **Angle:** the View dial is the only control (`?view=` reload; authored views only; manual pose is carried across views).
- **Motion:** one dropdown: Off, Idle (procedural Life), breathe, weight shift, arm settle, Body showcase, jump, anger, run (`?clip=&autoplay=1`). ↻ replays the clip.
- **Expression:** Neutral (0,0), Smile (0,1), Anger (0.25,−1). Anger is the mouth grid point of `mouth_anger`/`anger.png`, the art the anger clip already keys. It is disabled where the view has no anger mouth (left, right) or no face (back).
- **Weight shift:** no single param exists, so it is a UI-only mapping. It uses the rig's `idleLegStance` (hips + knees + ankles, legs solved to the rest ankle positions) plus `footPlantApply` (Root X/Y). At 0 it writes the exact rest values.
- **Auto-blink:** uses the rig's `BLINK` timing on both lids (scales the manual lid values). **Auto-talk:** uses the rig's `stepTalk` with the talk-shape filter. **Physics:** uses the rig's `stepHair` springs. **Sway amount:** scales every strand's drive. **Spring preset:** A by default.
- **Disabled because there is no param:** Per-strand angles and Bun offset. Controls the rig disables per view (e.g. far-hand fingers in profile) are greyed out.
- **Reset to rest:** turns off Motion and the auto switches, then calls the rig's own Reset. Verified: every param is at its default, the on-screen frame is identical to a fresh rest load, and the rig's Rest check passes (0 px).
