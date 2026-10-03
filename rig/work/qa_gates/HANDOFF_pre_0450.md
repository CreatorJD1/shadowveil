# Shadowveil: master handoff (Oct 3, 2026, ~4:00 AM PT)

For any coding agent picking this up (Codex, Freebuff, or anyone else). Everything here comes from the five bot handoffs, `STATUS.md` / `status/status.json`, `CODER_HANDOFF.md`, `rig/poser/HOOKS.md` and the rig files as they were when this was pushed. Where something wasn't checked, this file says so.

## Top 5 next steps
1. **Get the user's OK, or a no, on the staged items** (section 5). Nothing staged is live. Don't flip anything live without the user's OK, and use one OK-list line per item.
2. **Fix the profile weight bleed** (left 9 / right 21 elbow vertices over the torso, plus the forearm/hip isolation failures) using a candidate skin under `rig/work/weight_bleed_fix/`. Never write `skin.json` directly, and the gates must pass with rest at 0 px. Note: `rig/work/weight_bleed_fix/` did **not** exist on disk at push time, so it isn't in this commit (see section 7).
3. **Fix the handorder wrist rows.** Draw the palm over the forearm, clipped to the hand erase mask, on the left rows y852–853 (53 px) and right rows y856–857 (24 px). Staged work is in `rig/work/handorder/wristrows/`.
4. **Finish Body's visible-defect fixes** in `body_tools/work/diag_body_fix/` (it was still running, so it's not in this push), and the `?palsnap=1` palette snap (`rig/work/palsnap/`).
5. **Before anything goes live, run the checks in section 8:** `rig/qa_gates.py`, rest identity at 0 px in all 5 views (with and without flags), and the md5 of the served `rig/index.html`.

---

## 1. What the project is
Shadowveil is a 2D character rig built from the artist's own drawn art of her. There are five base views (`apose`, `tpose`, `left`, `right`, `back`), each in `views/<view>/` with a `base.png` (the truth) and per-system parts (body, eyes, mouth, hands, hair). The live renderer `rig/index.html` and the unified poser `rig/poser.html` drive her with bones, skin weights (`skin.json` + underlay) and swapped/blended shapes (eye lid frames, mouth shapes, finger frames, hair springs).

**Run it locally**
```
cd shadowveil            # repo root
python3 -m http.server 8765 --bind 127.0.0.1
```
- http://127.0.0.1:8765/app/ is the master app (dashboard, tabs, Body > Rig controls, Clean room reference, pose driver).
- http://127.0.0.1:8765/rig/ is the live rig (`?view=apose|tpose|left|right|back`, `&quality=linear`, plus staged flags).
- http://127.0.0.1:8765/rig/poser.html is the unified poser (staged). It drives `rig/index.html` in a same-origin iframe.
- http://127.0.0.1:8765/status/ is the status dashboard (redirects into `/app/#status`).

Staged flags in `rig/index.html` (default output is unchanged when they're off): `?hairless=1`, `?headgroup=1` (with hair/bun sub-offsets), `?handorder=1` (needs `hairless=1`), `?armsub=1`, `?mouthfix=1`, `?partmesh=1`, `?handangles=off`, `?ss2rest=1`. The `?palsnap=1` flag is **not** in `rig/index.html` yet. It only exists in the staged copy `rig/work/palsnap/index.palsnap.html` (patcher: `apply_palsnap.py`).

## 2. Hard rules (must not break)
- **Her authored art only.** Only regenerate inside tight approved masks, with no anatomy drift from the master character sheet.
- **Never draw circles, ellipses, strokes or shapes over her eyes or mouth.** (The renderer has a dev guard that throws on any shape draw.)
- **Never mirror her.** She has a mark under one eye. Her **right eye is amber** (EyeR, layers 400–403) and her **left is green** (EyeL, 410–413). One-sided shapes are never mirrored, not even behind a flag.
- **Rest pose = 0 px difference** from her art in every view, with flags on and off.
- **Line art within about 1 px** of rest width, with no breaks. The 1 px mark is preserved.
- **No chroma/key blue `#0000FF`** and no colour leaks while rotating. Parts are keyed on `#0000FF` and use flat colour from her palette only.
- **No weight bleed** between unrelated bones.
- **Hands and feet keep their scale** vs her head and forearm in every view (more than 1 px off fails). Her five base views are the scale truth, and the master sheet is reference only (this scale rule itself is on the OK list).
- **Never use `clean-room/layers/rotation/turn-*.png`** (generated stills with wrong feet, knees and head).
- **Edit safely:** copy into scratch, run `node --check` on the extracted script, and swap atomically. The default output must stay byte-identical (the bots check 30/30 frame hashes).
- **Everything stays staged until the user OKs it.**
- Coder work never writes to `views/` or any owner `rig.json`. Don't touch port 8765 (main) or 8766 (auth gate) from test scripts.

## 3. Decisions in force
- **Hair preset A** (spring 4.0 Hz, damping ζ 0.8, sway cap 1.0) is the default.
- **The anger face uses the Clean room art** (`reference/grok_build/public/puppet/emotions/anger.png`), as drawn.
- **The head group is the single correction path** (Body head + eyes/brows/mouth + hair, pivot 681.5,318; `rig/partmesh/staged/headgroup.json`, `?headgroup=1`).
- **The mouth uses only two controls:** MouthOpen (0..1) and MouthForm (−1..1).
- **One-sided shapes are never mirrored.**
- **Turning plan:** 8 angles at 45° steps, bending toward shared bones and switching at the midpoint. *The diagonal work is PAUSED* (section 6).
- **The smooth-mesh rebuild was DROPPED by the user.** Only fix the visible defects on the existing pieces and setup.

## 4. Current status per area
**Body** ([body_tools/work/HANDOFF_BODY.md](body_tools/work/HANDOFF_BODY.md)). Everything is staged. The diagonal pieces in `diag_body/{045,315}` (rest 0 px, 0 holes at ±25°) were rejected for unnatural bends. `diag_body_fix/` is fixing those exact defects (waist step, hip dent, jagged shoulders/elbows, head-neck gap, 045 neck key at alpha 0) and **isn't in this push**. The crotch `ulnb` candidate is recommended. The hairless live patch (`hairless_division_staged/<view>/live_patch_paired_hairfront/`) must go live with Hair's hair_front. The `handorder_wrist_trim` and `weight_bleed` attempts were rejected. Spot-1 (right armpit/hip) still opens ~650 px under combined shoulder+hip bends and needs a skin.json weights fix from the Coder. The line-tone snap (1,046 px) is staged in `linetone_snap/`.

**Eyes** ([eyes/HANDOFF_EYES.md](eyes/HANDOFF_EYES.md)). Live in apose/tpose/left/right with rest 0 px (left-profile gaze fix in). Staged: the lash fix, closed-frame crease choice, side-glance white tone, 45°/315° diagonal eyes with the far-eye blue fix (`eyes/staged/diagonals/`), and diagonal iris limits v4. 135°/225° have no eye parts because no eye is visible in her frames (`eyes/qa/diag_135_225/`). Open: a pale line above the iris and specks in the right profile (small), and the eye mesh lid for FORMAT v0.2 (not started). Expressions are parked.

**Mouth** ([mouth/HANDOFF_MOUTH.md](mouth/HANDOFF_MOUTH.md)). Live in all 5 views via MouthOpen/MouthForm, and passes qa_gates (0 off-palette, 0 chroma). Staged: the tone snap (`mouth/staged/tone_fix/`) and the Coder's `?mouthfix=1` (removes doubled/flickering outlines; flag-off output byte-identical). Diagonals, mesh_bend/mesh_split and benchmarks are parked. Open: the talk driver loses M.

**Hair** ([hair/HANDOFF_HAIR.md](hair/HANDOFF_HAIR.md)). Live in all 5 views with preset A and the T-pose wisp underfill. Staged: tone_fix, hairfront_holes, lineart_fix, the A-pose ear strands plus merged strand_04, speck_fix (needs a choice), the ear/eye-corner ink paired with Body, and the T-pose eye-corner 181 px. Diagonals v4 are kept but paused.

**Hands** ([hands/HANDOFF_HANDS.md](hands/HANDOFF_HANDS.md)). The apose/tpose finger fixes are live. Staged and passing (rest 0, 0 #0000FF, 0 off-palette): F5 line-art (v2 ring width), the F7/F10/F11 wrist flaps (one OK item together with `?handorder=1`), F8 diagonals and F12 diagonal wrist flaps (paused). Open: the A-pose fist is flat and lumpy, T-pose ring/pinky hide behind the index, profile thumbs only rotate, claw and wrapped-thumb fist are unreachable, the generated turned hands are ~+33 px long on the far side, and F6 is parked.

**Rig / Poser (Coder)** ([CODER_HANDOFF.md](CODER_HANDOFF.md), [rig/poser/HOOKS.md](rig/poser/HOOKS.md), [rig/work/qa_gates/README.md](rig/work/qa_gates/README.md)). `rig/index.html` is md5 `562c32a7…` at push time. All new paths are behind flags, and the default renders 30/30 identical. `rig/poser.html` is the unified poser plus keyframe timeline. It works today with no rig change by reading the rig's globals, and HOOKS.md proposes additive patches H1–H5 (RigAPI, RigHair, RigClock, `?embed=1`, postMessage), none of them applied. `rig/qa_gates.py` (G1 weights, G2 leak, G3 scale) is read-only. Staged work is under `rig/work/` (diag_rig, irislimits, palsnap, handorder, hgsubhair, headgroup, armsub, crotch_weights, mouthfix, hairless, partmesh_pilot, qa_gates). **Another worker was editing `rig/` during this push.** The files were committed as they were, so some may be mid-work. For example, `rig/poser/pixdet.json`, `rig/poser/tools/dbg.js` and `rig/poser/tools/pixdet.js` disappeared while the file list was being built, and new `rig/_ps_test.html` / `rig/_wr_test.html` scratch pages appeared (not pushed). Check `git status` and re-diff before trusting anything under `rig/`.

## 5. Staged items waiting for the user's OK
(From the dashboard OK list: `STATUS.md` "Waiting on your OK" and "Blockers & open issues". Each one is a separate OK.)
- **Eyes: diagonal far-eye blue fix.** 167 px removed, 0 chroma. 62 px of faint navy are kept because they're in the turn frame (`eyes/staged/diagonals/`).
- **Body + Hair ear patch pair (one OK line, both go live together or neither does).** Body's masked hairless live patch (left/right/back, `body_tools/work/hairless_division_staged/<view>/live_patch_paired_hairfront/`) plus Hair's new hair_front (`hair/staged/ear_strands/<view>/…/hair_front.png`). Together, rest is 0/0/0 px. Either one alone is 378–640 px off.
- **Body crotch notch: ulnb** (`--crotch 0`, no `--bgk`). Rest is 0. It reduces the wide-stance notch (apose 778→366, tpose 1033→731) but doesn't fully close it, and adds a few new dark-edge px (78/18). Sheet: `body_tools/work/crotch_candidates/sheet_crotch_before_after.png`. Skin: `rig/work/crotch_weights/apose_skin_ulnb.json`.
- **The poser:** `rig/poser.html` as the main driver, replacing `app/driver/simple.html`. Rest matches index.html exactly, scrubbing matches playback, and there are 0 console errors. Diagonal angles are view-only for now.
- **Iris limits v4** (`?irislimits=diag`, `rig/work/irislimits/diag_irislimits_v4.json`) for 045/315. Wider sideways reach (315 near EyeR −2/+4, 045 near EyeL −3/+2), eyes linked, 0 leaks, rest 0 px. **Trade-off:** up-left/up-right and 045 down-right glances go straight up (0 sideways; up to 2 px today). Eyes' verification: `eyes/qa/irislimits_diag/v4/sheet_v4.png`.
- **Hair:** tone fix (`hair/staged/tone_fix/`), hair_front 2 px hole fills (`hair/staged/hairfront_holes/`), line-art fixes (`hair/staged/lineart_fix/`), and the ear fixes (A-pose ear_strands + merged strand_04, T-pose eye-corner 181 px, and the paired item above). The speck fix needs a choice: a chroma exception for base.png copies, or Body keeps the specks.
- **Mouth:** the tone snap (`mouth/staged/tone_fix/`) and the doubled-outline fix `?mouthfix=1` (suggested as the default).
- Also on the list: the Eyes lash fix, closed-frame crease, 2 px/column diagonal lid rule and side-glance white tones; Hands F5 line-art and the A-pose wrist flaps (F7), plus F10/F11 together with `?handorder=1`; Body round-2 right-view underlay, hairless bases, A-pose neck extension, T-pose eye-corner/ear fill, and the line-tone snap; the scale rule (base views are the truth); Coder `?handangles=off` (generated turned hands off by default), `?ss2rest=1` (exact rest at default quality), wiring the driver to the head group, and the Mouth lip-bend extras.

## 6. Paused / dropped work
- **The 4 diagonal angles (45/135/225/315) are PAUSED.** The user said "I just want to fix her model". Staged diagonal work from every bot is kept for reference.
- **Body's 45/315 diagonal sheets were rejected** for stair-steps and dents at the waist, hips, shoulders and elbows, and the neck gap. Body is fixing exactly those visible defects in `body_tools/work/diag_body_fix/`, which **isn't in this push** (still running; it comes in a later push).
- **The smooth mesh** (`body_tools/work/natural_bend_proto/`, not pushed) **and the knuckle mesh were dropped.**
- **Hair v4 diagonals** (`hair/staged/diagonals_v4/`) have one-sided sway caps (`sway_caps.json`) that need `degAtPlus1`/`degAtMinus1` support for hair in `rig/index.html`. That's not done. Without it, 045 `strand_03`/`strand_03_tip` and 315 `strand_06` can swing over the eye or mouth.
- **Benchmarks** (`reference/benchmarks/`, `rig/benchmarks/PLAN.md`), **outfit work** (`reference/outfit/`, `body_tools/work/outfit_staged/`) **and Massfront are parked.**

## 7. Open issues and how to address them
1. **Profile weight bleed.** Left 9 and right 21 vertices at the elbow over the torso, plus forearm/hip isolation failures (G1 in `rig/qa_gates.py`). *Fix:* build a candidate skin under `rig/work/weight_bleed_fix/` and check it with `python3 rig/qa_gates.py --gate weights,leak --part body --view left --skin <candidate>` (and the same for right). Rest must be 0 px with no visible shape change. **Never write `skin.json` directly.** Body's `--zero-cross-limb` attempt was rejected because vertices moved up to 31 px and 48 holes opened (`rig/tools/REJECTED_visible_change`, `body_tools/work/weight_bleed/`). *Note:* `rig/work/weight_bleed_fix/` and `rig/work/bend_check/` did not exist on disk when this was pushed. Whoever owns them should commit them in a later push.
2. **Handorder wrist rows.** Left: 53 px at y852–853. Right: 24 px at y856–857. *Fix:* draw the palm over the forearm on those rows only, clipped to `hands/<view>_hand_erase_mask.png`. Don't trim the body skin (Body's trim was rejected). Staged work: `rig/work/handorder/wristrows/` (`apply_wristrows.py`, `index.wr.html`, `ho_check_wr.json`).
3. **`?palsnap=1` palette snap is in progress.** It's in `rig/work/palsnap/` (`apply_palsnap.py` is an idempotent patcher and `index.palsnap.html` is the staged copy). Each posed item's non-exact texels snap to that item's own source tones, and rest frames are never touched. *To finish:* run `ps_check.js` with `cases_full.json`, confirm the default is byte-identical (`default_same_ab.js`), and check that 1–2 px hair tips don't vanish at full sway. The mouth palette must include teeth #efe4da, tongue #9c5a4a and profile interior #3f2319. Then rerun qa_gates for hair and mouth. The render output in `palsnap/out/` wasn't pushed.
4. **hgSub hair/bun offsets.** Keep them at (0,0) in left, right and back while the posed bodies still have baked-in hair. Re-tune from `hair/qa/turn_handoff/subofs_v2/` once they don't (`rig/work/hgsubhair/`).
5. **NeckTwist doesn't actually turn the head.** It only reprojects neck skin. *Fix:* a real head turn has to switch between her drawn angles (the 8-angle plan, which is paused), not warp the neck.
6. **Wrist rotation, twist and split finger curl** show as "in progress" (disabled) in the Body > Rig controls panel (`app/rigctl.js`). They switch on automatically once the rig's `P` exposes WristRot / PalmTwist / per-joint twist / split-curl params. Rotation means switching between authored hand angles (squash ≤15%, forearm follows at 50%).
7. **The Mouth talk driver drops M.** M shows in 4 of 240 frames instead of 22, because the M press lands on the rest/M tie. *Fix (rig side):* push MouthForm to about −0.6 for M presses, and use posed frames during handoffs.
8. **The 150 Mouth render PNGs question.** Last push, `.gitignore` (`*/renders/`) silently dropped 150 Mouth PNGs. Mouth's handoff says the real shapes are in `mouth/staged/{diagonals,diagonals_snap}/{045,315}/renders/`. This push force-adds every file in `mouth/push_manifest.txt`. Someone should still confirm with Mouth that those PNGs are real shapes and not scratch.
9. **Local main is behind origin.** Local `main` is 6d5b239 and origin/main is 3515d57 (Eyes PR #1 merge). The work tree has uncommitted changes. Don't `reset --hard`. Fast-forward main only after the PR is merged, with a clean or stashed work tree.
10. Also open (from STATUS.md): joint gaps from flat limbs (the main quality gap); the default `quality=ss2` display at rest differs from base.png by 149k–235k px (the Rest check uses the non-ss2 path; `?ss2rest=1` is staged); the generated turned hands in `rig/hand_angles/` break "authored art only" (needs a decision); qa_gates known bugs (the `045` key skips `45_*.png`, and staged lookup can't find flat layouts); the Body spot-1 armpit/hip ~650 px; the Hands fist and thumb issues (see Hands' handoff); and the Hair renderer smoothing (bilinear adds off-palette px).

## 8. Checks to run before anything goes live
- **md5 first:** the served `rig/index.html` must match the file on disk (`rig/work/md5gate.sh`). Render on a per-bot port, never on 8765/8766.
- **`rig/qa_gates.py`** (read-only; usage in `rig/work/qa_gates/README.md`):
  ```
  PYTHONDONTWRITEBYTECODE=1 python3 rig/qa_gates.py --gate weights,leak,scale|all --part body|eyes|mouth|hands|hair[/glob] \
     --view apose,tpose,left,right,back [--staged-dir DIR] [--skin cand.json] [--hair-dir/--mouth-dir/--eyes-dir/--hands-dir/--body-dir DIR] \
     [--no-diagonals] [--no-mesh] [--tol 2] [--json out.json]
  ```
  - G1 **weights**: bleed vs dominant bone (fails), plus a bone isolation test (an unrelated vertex moving more than 0.5 px fails).
  - G2 **leak / colour sweep**: off-palette (more than `--tol` from any of her tones for that part/view), chroma, soft edges (info only), and the mesh_outside_mask pose sweep.
  - G3 **scale**: hand and foot length vs head and forearm. More than 1 px drift fails, and the base views are the truth.
  - **The required chroma rules:** exact `#0000FF` always fails. Her own blue-ish colours are allowlisted only from 1 px-eroded silhouette art pixels. Frame-edge fringe is counted separately. *Caveat:* the `qa_gates.py` pushed here still uses the older heuristic (`blue > max(r,g)+60 and blue > 120`), and its `--help` has no bend-check flag. The exact/eroded/fringe rule and a bend check were in progress with the other rig worker, so confirm they've landed before relying on them.
- **Rest identity:** 0 px vs `base.png` in all 5 views at `quality=linear`, with no flag and with each staged flag (e.g. `?hairless=1`, `&headgroup=1`). Use `python3 rig/rest_check.py`, the rig's Rest check, or each bot's rest_check scripts. The default output must stay byte-identical (30/30 frame hashes).
- **Bot-side checks:** `python3 eyes/qa/qa_gates/check_diag_chroma_fix.py` (Eyes diagonal rest), `hands/qa/gates/gates_extra.py` (Hands), the Hair colour sweep (`hair/qa/colour_sweep/`) for 0 over the eyes/mouth across full sway, and the Body pose extremes at ±25° on every joint (0 holes, outline within 1 px). Every fix needs a before/after sheet.
- **Dashboard (`status/update.py`)** only edits `status/status.json` and `STATUS.md`:
  ```
  python3 status/update.py add progress|built|blockers|next 'text' [done|wip|todo|blocked|decision]
  python3 status/update.py move 'item text' STATE [--stay]
  python3 status/update.py owner Body 'latest item'
  python3 status/update.py register <section> reports|pages|media <path> '<label>'
  python3 status/update.py scan        # rescan media + registry
  python3 status/update.py check       # HTTP-check every path (default http://127.0.0.1:8765/)
  ```

## 9. Repo / push notes
- Repo: https://github.com/CreatorJD1/shadowveil. On the box, the git dir is `/workspace/.shadowveil-git` and the work tree is `/workspace/shadowveil` (use `git --git-dir=/workspace/.shadowveil-git --work-tree=/workspace/shadowveil`).
- Branches: `main` on origin is 3515d57 (merged Eyes PR #1). `staged/combined-2026-10-03` = a803a02 (the first combined push) plus this commit (the full project push + this handoff). **Draft PR #2:** https://github.com/CreatorJD1/shadowveil/pull/2. Everything in it is staged and awaiting the user's OK. `eyes/progress-2026-10-03` is the old Eyes branch (merged).
- Where each bot's files live (each one's exact push list is its `push_manifest.txt`):
  - Body: `body_tools/` (`body_tools/work/push_manifest.txt`)
  - Eyes: `eyes/` (`eyes/push_manifest.txt`)
  - Hands: `hands/` (`hands/push_manifest.txt`)
  - Hair: `hair/` (`hair/push_manifest.txt`)
  - Mouth: `mouth/` (`mouth/push_manifest.txt`)
  - Coder: `rig/`, `app/`, `status/`
  - Live art: `views/<view>/`. Reference: `reference/` (the benchmarks/outfit updates weren't pushed because they're parked).
- Port map (127.0.0.1):

  | Port | Use |
  |---|---|
  | **8765** | Main server (`python3 -m http.server 8765` in the repo root). Don't use it for tests. |
  | **8766** | Password auth gate (`remote/authproxy.py`) for the Cloudflare quick tunnel. Don't touch it. `remote/` is never pushed. |
  | 8770–8774 | Body |
  | 8775 | Hands F7 check |
  | 8780–8784 | Hair |
  | 8785–8789 | Mouth |
  | 8790/8791 | Box egress tunnel (not ours) |
  | 8792–8796 | Coder test servers (handorder 8792, hgsub 8794, others ad hoc) |

- Not pushed on purpose: `remote/` (tunnel and password files), backups, `__pycache__`, the `vis.npy` files (over 50 MB), render scratch (`rig/previews/wrist`, `rig/previews/idle`, `rig/previews/actions` renders, `rig/work/*/renders|out|tmp`, `.rgba` dumps in `rig/work/mouthfix`, most partmesh_pilot PNGs), large regenerable JSON (candidate skins, render dumps over 1 MB), `rig/index.*.html` working copies and `_*_test.html` pages, `body_tools/work/natural_bend_proto/` (dropped) and `diag_body_fix/` (still running), and the parked `reference/outfit` and `reference/benchmarks` updates. The full exclude list with reasons is `rig/work/push_prep/list2.json`.
