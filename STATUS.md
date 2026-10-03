# Shadowveil — character rig & live driver status

Last updated: Sat Oct 3 2026, 4:59 AM PT

Overall: ~45% — roughly 40–50% to a quality live driver (rough estimate)

Legend: [x] done  [~] in progress  [ ] to do  [!] blocked  [?] needs USER DECISION

Dashboard: http://127.0.0.1:8765/app/#status (master app; /status/ redirects there). Data: status/status.json, app/registry.json

## Waiting on your OK

- [?] **USER DECISION** Eyes: lash fix go live? Lids now on her exact tones (eyes/staged/, Eyes HANDOFF.md)
- [?] **USER DECISION** Eyes: closed-frame crease, stay or hide? (eyes/staged/, Eyes HANDOFF.md)
- [?] **USER DECISION** Eyes: diagonals lid rule 2 px/column? (eyes/staged/diagonals/)
- [?] **USER DECISION** Eyes: side-glance white tones, 214 px (eyes/staged/white_tone/sheet.png)
- [?] **USER DECISION** Hair: staged hair set go live: speck fix, ear strands, merged strand_04, six line-art fixes, four diagonal angles (hair/staged/, hair/HANDOFF.md)
- [?] **USER DECISION** Hair: hair_back fill tone fix (hair/staged/tone_fix/, tone_fix_log.json)
- [?] **USER DECISION** Hair: hair_front 2 px hole fills (hair/staged/hairfront_holes/)
- [?] **USER DECISION** Hands: F5 line-art fixes (hands/staged/f5_lineart/README.md)
- [?] **USER DECISION** Hands: A-pose wrist flaps, ~520 px/wrist new colour (hands/staged/f7_wrist_apose/README.md, palette fixed to her tones)
- [?] **USER DECISION** Mouth: lip bend extras (skin pad, interior notch fill, upper-lip flap), once the format loads them (mouth/staged/mesh_bend/REPORT.md)
- [?] **USER DECISION** Mouth: talk-shape tone snap (mouth/staged/tone_fix/)
- [?] **USER DECISION** Body: right-view round-2 underlay, reviewed safe by Coder (body_tools/work/round2_staged/README.md)
- [?] **USER DECISION** Body: hairless bases go live; needs the hand_mask cut baked into base_body_skin (body_tools/work/hairless_division_staged/<view>/live_patch_staged/; test rig/?hairless=1; palette fix: fill (186,129,86), palms match)
- [?] **USER DECISION** Coder: turn off generated turned-hand sprites by default (?handangles=off; rig/index.html HAND_ANGLES_GENERATED)
- [?] **USER DECISION** Coder: exact rest at default quality, ss2rest or linear as default (?ss2rest=1; rig/index.html SS2_EXACT_REST)
- [?] **USER DECISION** Coder: make simple.html the main driver and cut the 8 extra sliders (app/driver/simple.html)
- [?] **USER DECISION** Coder: wire the driver to the head group, RigHeadGroup.applyHandoff at handoffs (rig/partmesh/staged/headgroup.json, FORMAT.md 3.6)
- [?] **USER DECISION** Coder: mouth switch fix: hard cut, no flicker, rest wins ties (?mouthfix=1; rig/index.html MOUTHFIX)

## Built & working

- [x] Rest is 0 px against her drawing in all 5 views (apose, tpose, left, right, back)
- [x] Only her authored PNG parts are rendered; dev guard throws on any shape draw
- [x] Layers panel live (eye white + iris rows; single-part hair strands as plain rows)
- [x] Hair angle readout live during Play
- [x] Eyes blink, gaze and switch lid frames (left-profile gaze reversal fixed, user-approved)
- [x] Mouth switches all 9 drawn shapes via MouthOpen / MouthForm
- [x] Fingers: 3 joints each + Fist / Point / Peace poses (T-pose half-curl bend fixed by Hands)
- [x] Hair spring sway on 37 parts
- [x] Runtime contract v1.7.1 (layer order, outfit bands, param names)
- [x] Three-quarter reference frames agreed: f033 (45°) and f191 (315°)
- [x] Idle test v1 run — findings:
    - [!] Auto idle is lifeless (body under 1°)
    - [!] Mouth flickers (47 changes in 8 s)
    - [!] Head flickers sharp/soft
    - [!] Keyed clips: right-view forearm opens 420 px of holes at arm_settle f169
    - [!] Keyed clips: knees kink ~33°, feet lift 14 px
    - [!] Hair at 1.1 Hz / ζ 0.3 pins at its limits; tips overrun (worst +6.1°)
- [x] Clean room page embed: images and videos fixed in #reference (patched copies app/cleanroom/index.html + static.html via app/cleanroom/build.py; 0 broken imgs/videos in headless check, tunnel OK; turnaround strip + talk clips added to Media)
    - [x] Reference media path fix: 0 broken of 52 images and 49 videos (local and tunnel)
- [x] DECIDED: hair preset A (spring 4.0 Hz, ζ 0.8) is the default
- [x] DECIDED: the anger face uses the Clean room art (authored images only)
- [x] Hands: apose + tpose hand rig.json fixes live (rest 0 px)
- [x] Remote access: public link via the Cloudflare quick tunnel through the password gate (temporary address)
- [x] Pose driver (Clean room): app/driver/ — in-between crossfade of the turnaround stills with idle>turn>hold>drift>idle, scrub, targets, eye/hand stills composited where aligned, hair skin-fill hide, front-only talk clips; beauty-mark audit holds out turn-045/090/315 (app/qa/beauty_marks/REPORT.md)
- [x] Body tab: Rig controls panel (app/rigctl.js) embeds the v1.8 WIP rig and drives it via set()+draw(). Live: finger curl L/R, WristL/R, HeadTilt/Nod, body joints, root, hair preset, and a view dial with ◀ ▶ (reloads ?view=). WristRot, twist and split-curl params show as in progress and switch on automatically when the rig's P adds them
- [x] Post-6d5b239 regression check (Oct 2): rig Rest check PASS 0 px in apose/tpose/left/right/back; live canvas at Reset-to-rest is 0 px with quality=linear in all 5 views; 8 hand_angles load in all views with 0 console errors (rig/work/qa_post6d5b239/)
- [x] Anger clips regenerated with rig/tools/merge_clips.py (byte-identical to the live anger.json / anger_stress.json, no old M keys); load OK in 5 views; anger shown at t>=0.3 s in apose/tpose; auto-talk never picks anger (rest 0 px after clip)
- [x] Hairless rest check (Oct 2, 10:54 PM PT): ?hairless=1 = 0 px in apose/tpose/left/right/back at linear (Body's speck-cleared base_body/base_body_skin copies, Body apose order with hands under forearms + Hands F7 palms, Hair's full staged set; eyes/mouth live). Default (no flag) still 0 px in all 5. Test: http://127.0.0.1:8765/rig/?view=apose&hairless=1&quality=linear (swap view=)
- [x] Part mesh format v0.2 written (rig/partmesh/FORMAT.md): matches the schema the renderer reads behind ?partmesh=1; requirements (a)-(l) incl. child-under-parent order, 8-angle turn, Eyes G1-G14, Mouth's mesh-bend needs (OH/EE stay swaps), head-group rule. Ready for Hair and Hands; Mouth/Eyes/Body need clip/flap/lid/sampling fields built next
- [x] Part mesh pilot, hair (apose strand_03 + tip): PASS at iteration 1 (width p95 0.43 px, 0 breaks, 0 new holes, browser vs Python mirror within 2 ink px); rest 0 px in all 5 views with ?partmesh=1; flag-off default byte-identical (30/30 frame hashes)
- [x] Full project push + master HANDOFF.md (commit e0df3a1, PR #2)

## In progress — v1.8

- [~] v1.8 (root motion, foot plant, consistent resampling, internal-edge alpha fix) + core fixes
    - [~] Root motion + foot plant
    - [~] Sharp/soft flicker fix
    - [~] Calm idle mouth + 125 ms talk timing (no EE, no smile)
    - [~] Livelier idle body
    - [~] Eyes' blink timing
    - [~] Per-tip hair clamps
    - [~] Hair presets: default / A (4.0 Hz, ζ 0.8, now the default) / B (2.0 Hz, ζ 0.6)
    - [~] Hair reacts to vertical motion
    - [~] HeadTilt / HeadNod with eyes, mouth and hair parented to the head
    - [~] Runtime contract v1.8
    - [~] Consistent resampling (ss2 posed filtering on every frame)
    - [~] Internal-edge alpha fix (edge seal between parts)
- [~] Owner keys for v1.8
    - [x] Eyes keys ready
    - [x] Mouth keys ready
    - [x] Hands keys ready
    - [~] Body keys pending
    - [~] Hair keys pending
- [~] Action clips + showcase
    - [~] Jump / run / anger action clips (clip JSON + stress variants in rig/previews/actions/v1; renders queued)
    - [ ] Full showcase in 5 views
    - [~] Audit against the Clean room clips (idle/jump/run/angry strips prepared)
- [~] Life layer (Jason's request): no breathing; natural standing arm sway, weight shift with planted feet, follow-through, face/hands micro-motion, hair reacting to motion. Pushed to the rig's joint limits. Before/alive/max renders in 5 views go to rig/previews/idle/v2/life/
    - [~] Life-layer idle clip idle_arm_sway (no breathing); Eyes + Mouth QA now run on it
- [~] Hand rotation: WristRot + palm twist via authored hand angles
- [~] Wrist joint block leak fix
- [~] Twist axis on all joints (shoulder, forearm, wrist, hip, knee, ankle, neck)
- [~] Weighted skinning (mesh test to close the flat-limb joint gaps)
- [~] Pose driver: Clean room turnaround in-between driver (idle → turn → hold → drift → idle); blends only between beauty-mark-consistent stills
- [~] Clean room art integration of ALL normal full-figure/face stills: 1,323 counted (123 turnaround + 1,200 pose; layers dropped from the count)
- [~] Beauty mark check across all 1,323 stills (canonical: two marks on her right cheek); mismatches held out of the driver and flagged for regeneration. Report: app/qa/beauty_marks/REPORT.md (pending)
- [~] Hair: tpose wisp fill (hair/qa/wisp_fix)
- [~] Body: profile skin/underlay fix for the armpit hole and hip slit
- [~] Pose driver turn verified end to end (Oct 2): reference/apose_turn f001-f232, 6 full idle>turn>hold>drift cycles, live parts only at f001/f062/f109/f160, 80 ms crossfade, 0 generated-still requests, mirror false, 0 errors. Open: visible jump at handoffs (IoU 0.92/0.88/0.81/0.86) (rig/work/qa_post6d5b239/driver_turn/)
- [~] Part mesh pilot, fingers (tpose R_Middle, blend 4/4/3, 3 rounds + 10 sweep candidates): passes width (<=0.62 px), breaks (rigid 6 -> 0 at curl 0.87), no new holes, 0 px changed outside; mesh removes the need for flaps at the Middle joints. OPEN: 1-3 px floating specks from frame f1/f2 cap/crease ink in the bend zone (art-side fix for Hands)
- [~] Head group staged behind ?headgroup=1 (Body head + eyes/brows/mouth + hair, pivot 681.5,318, single correction path; rig/partmesh/staged/headgroup.json). Handoff head offsets dx,dy: f001 apose 0,-10 · f062 left -2,+1 · f109 back +2,+11 · f160 right +5,-6. Neck seam gap 0 px at all 4 (skin stretches): stretch +10 apose, +6 right; overlap 1 left, 11 back. Driver not wired yet
- [~] Coder: head-group hair/bun sub-offsets wired behind ?headgroup=1 (rig/partmesh/staged/headgroup.json sub.hair/sub.bun, Base Hair values); left/right edge distance improves, back gets worse and the bun shows a ring + see-through gaps, so it waits on Base Hair (rig/work/hgsubhair/)
- [~] Coder: ?hairless=1 confirmed working (no regression; at rest it matches live by design). tpose hairless fails 181 px from Body's 02:01 eye-corner fill. index.html now 562c32a7 (handorder + armsub, flags only, default 30/30 identical). qa_gates.py baseline, crotch candidates, arm handoff proto, diag iris limits, hair/bun sub-offsets staged.
- [~] Coder: rig/poser.html unified poser + keyframe timeline (staged; drives live rig/index.html via iframe, no rig edits). Hooks proposed in rig/poser/HOOKS.md. Benchmark plan parked in rig/benchmarks/PLAN.md.
- [~] Follow-up merged to main: chroma rule v2, bend check, weight-bleed fix, Body diag fix + HANDOFF (PR #3, merge d8a8331)
- [x] qa_gates glob fixes: staged sweep reads each system's staged dirs; diagonals read hair v4 / mouth diag_posable / eyes / hands f8+f12 / body diag_fix; leak v2 all 0/0 (body PASS False only from mesh_outside_mask 3,762)

## Blockers & open issues

- [!] Joint gaps from flat limbs on pivots: weighted mesh skinning approved and now in progress, no clean mesh test yet (main quality gap)
- [!] Turning her needs native lossless angle stills at ~22.5° steps (no mirroring)
- [!] Joint caps (25°) and 8° lean make the run a tight jog
- [ ] Not built: split finger curl (claw)
- [ ] Not built: driver system (timeline, reference import, linked motion, lip sync)
- [!] Open: Clean room talk clips are missing layer cuts (held frame 404)
- [!] Hands: back-view lean still open
- [!] Hair erase mask proposal on hold until Body posts the profile skin/underlay fix
- [!] Permanent named Cloudflare tunnel needs a domain
- [!] Turned hands (rig/hand_angles 45/135/225/315, from 20ff7bb/6d5b239) are reconstructed art from generated atlases (tools/hand-art), palette-normalised, with no outline and a visible wrist seam: breaks 'authored art only' and line-art rules. Needs a user decision
- [!] Default live display (quality=2x supersampled) at Reset-to-rest differs from base.png by 149k-235k px in all 5 views (pre-existing since at least 9458143; the Rest check renders the non-ss2 path so it passes). Needs a decision on the default quality or an exact rest path in ss2
- [?] **USER DECISION** Body: A-pose neck extension for the head group (138 px of her skin and outline added to neck.png, hidden at rest, up to 9 px shows at the turn handoff). Staged in hairless_division_staged/apose/pieces/; sheet_headgroup_neck_before_after.png. Needs your OK because it adds her colours where she didn't draw.
- [?] **USER DECISION** Body + Hair: T-pose eye-corner and ear-strand fill. 68 + 113 px move into the static hair_front, and Body turns the pixels under them into her skin (186,129,86). Staged in hair/staged/ear_strands/tpose/. Needs your OK because it adds her colours where she didn't draw.
- [?] **USER DECISION** Body: line-tone snap on the live body files. 1,046 px of (13,11,29) become each view's nearest dark tone from her base.png. The snapped copies are in body_tools/work/linetone_snap/live/, and the live files are untouched until you OK it.
- [?] **USER DECISION** Scale rule: her five base views are the scale truth for hands and feet, and the base feet and hands stay as drawn. The low-res master sheet is a reference only, and only generated turn frames get measured against her views. Body's foot report: body_tools/work/foot_scale/. Hands' report: hands/qa/scale_audit/REPORT.md.
- [?] **USER DECISION** Hands: the F10/F11 wrist flaps and ?handorder=1 go live together as one item. If the flaps are drawn over the forearm, they fail by 2.6 px on the left and 9.7 px on the right.
- [?] **USER DECISION** Coder: the generated turned hands are +32 to +35 px too long on the far side, and the back view is shrunk 14-17 px. I recommend switching them off (?handangles=off) and using Hands' F8 diagonals. If they stay on, the 1.64x fit should apply to the near-side hands only.
- [?] **USER DECISION** Crotch notch: underlay change (--crotch 0, no --bgk) recommended over the weight blend; candidates in rig/work/crotch_weights/, need Body browser render
- [?] **USER DECISION** Coder ?irislimits=diag v4 (045/315): wider sideways reach (315 near EyeR -2/+4, 045 near EyeL -3/+2), eyes linked, 0 leaks, rest 0 px. Trade-off: up-left/up-right and 045 down-right glances go straight up (0 sideways; today up to 2 px). Eyes verified: eyes/qa/irislimits_diag/v4/sheet_v4.png
- [?] **USER DECISION** Eyes: diagonal far-eye blue fix (167 px removed, 0 chroma; 62 px faint navy kept because it's in the turn frame)
- [?] **USER DECISION** Coder: rig/poser.html (Poser unified) as the main driver, replacing simple.html. Rest matches index.html exactly, scrub = playback, 0 console errors. Diagonal angles view-only for now.
- [?] **USER DECISION** Body + Hair pair (one line, live together or not at all): Body's masked hairless live patch (left/right/back) + Hair's new hair_front (hair/staged/ear_strands/<view>/.../hair_front.png). Together rest 0/0/0 px; either alone is 378-640 px off.
- [?] **USER DECISION** Body crotch notch: ulnb skin (--crotch 0, no --bgk). Rest 0, reduces wide-stance notch (apose 778->366, tpose 1033->731) but doesn't fully close it; small new dark-edge px (78/18). Sheet: body_tools/work/crotch_candidates/sheet_crotch_before_after.png
- [?] **USER DECISION** USER DECISION: soft edges in her live textures (body 131,030 / hands 22,362 / mouth 8,655 / hair 7,385 px): exempt her own antialiasing (report-only, current) or snap alpha? qa_gates reports them as pre-existing vs new; never fail PASS (HANDOFF.md section 8)

## Next / estimate (rough)

- [ ] v1.8 + action audit — within hours
- [ ] Weighted meshes clean in 5 views — a few days
- [ ] Angle views — depends on the stills
- [ ] Driver system — about a week after that
- [ ] Todo: animation states wiring (idle / talk / turn / action state machine in the live driver)
- [ ] Todo: manual rotation control (arrow buttons + dial to switch views, no mirroring)

## Build status per tab

- status: Build: rig v1.8 WIP (life idle, hand rotation, twist axes, skinning); pose driver + Clean room integration in progress
- preview: Build: live rig = rig/index.html; v1.8 WIP = rig/index.v18-wip.html; renders: idle v1, keys v1, idle v2 life
- body: Build: stopped; see body_tools/HANDOFF.md
- eyes: Build: keys ready; idle QA now on idle_arm_sway
- mouth: Stopped. Handoff in mouth/HANDOFF.md; anger colour decision pending
- hands: Build: apose/tpose finger fixes live (rest 0 px); back lean + lineart check in progress
- hair: Stopped. Handoff: hair/HANDOFF.md. Live and verified (rest 0 px, springs A, tpose wisp fill). Unfinished: speck move (staged, waits on Body), line-art joint fixes, turn handoff offsets (first pass).
- coder: Build: v1.8 WIP: hand rotation, wrist leak fix, twist axes, weighted skinning, life idle, actions v1
- reference: Build: Clean room media fixed (0 broken / 52 img + 49 video); 1,323-still integration + beauty mark check WIP

## Owners

- **Body** (skin fix WIP): Neck cut to head-group offsets (staged)
- **Eyes** (Waiting on user: lash fix live OK, closed-frame crease, 2 px lid rule on diagonals, side-glance white tones): Staged: lash fix, 45/315 eyes, side-glance white, tpose lock trim; head-group eye fit verified within 1 px by Coder
- **Mouth** (keys ready): Handoff written (mouth/HANDOFF.md)
- **Hands** (fixes live): F12 diagonal wrist flaps 45/315 staged and passing (rest 0, gap 0 at ±25°). Merged rigs in hands/staged/f12_wrist_diag/<angle>/rig.json. Waiting on Coder ?diag=1 slot rerun. All staged, awaiting user OK.
- **Hair** (wisp fix WIP): Tpose wisp fill live; speck move and line-art check in progress
- **Coder** (v1.8 WIP): Hairless rest check 0 px in all 5 views; FORMAT v0.2; hair pilot pass; finger pilot open (specks); head group staged with handoff numbers

## Latest outputs

- Life v1.8 apose before/after: rig/previews/idle/v2/life/apose_life_before_after.mp4
- Hands idle bend REPORT: hands/work/idle_bend/REPORT.md
- Hair idle battle worst sheet: hair/qa/idle_battle/worst_sheet.png
- Hair wisp fix SUMMARY: hair/qa/wisp_fix/SUMMARY.md
- Pose driver: app/driver/index.html
- Beauty mark REPORT: app/qa/beauty_marks/REPORT.md
- All idle keys (5 views): rig/previews/idle/keys/idle_keys_all.mp4
- Idle keys contact sheet: rig/previews/idle/keys/idle_keys_contact_sheet.png
- Auto idle v1, all views: rig/previews/idle/idle_all.mp4
- Idle contact sheet: rig/previews/idle/idle_contact_sheet.png
- Idle QA summary: rig/previews/idle/qa/SUMMARY.txt
- Idle QA folder: rig/previews/idle/qa/
- Keyed clips folder: rig/previews/idle/keys/
- Idle v2 folder: rig/previews/idle/v2/
- Actions v1 folder: rig/previews/actions/v1/
- Live rig: rig/index.html
- Rig v1.8 WIP: rig/index.v18-wip.html
- Layers panel screenshot: rig/previews/layers_panel.png
- Rest diff (apose): rig/rest_diff_apose.png
- Runtime contract: runtime-contract.md
- Hands contact sheet: hands/contact_sheet.png
- Body joint zoom sheet: body_tools/joint_zoom_sheet.png
- Hair quality sheet: hair/quality_sheet.png
- Mouth review v4 (on face): mouth/review_v4_preview_on_face.png
- Eyes live preview: eyes/live/index.html
- Hair live preview: hair/live/index.html
- Clean room reference: app/cleanroom/index.html

## Rendered clips

- [idle v1] rig/previews/idle/apose_idle.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/back_idle.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/left_idle.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/right_idle.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/tpose_idle.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/apose_idle_hair_middle.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/apose_idle_hair_stiff.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [idle v1] rig/previews/idle/idle_all.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_all5.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_apose.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_back.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_left.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_right.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_tpose.mp4 (Oct 1 11:25 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_all5.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_apose.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_back.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_left.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_right.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_tpose.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_keys_all.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_all5.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_apose.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_back.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_left.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_right.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_tpose.mp4 (Oct 1 11:26 PM PT, 8.0 s)
- [idle v2] rig/previews/idle/v2/life/apose_life_after.mp4 (Oct 1 11:27 PM PT, 8.0 s)
- [idle v2] rig/previews/idle/v2/life/apose_life_before_after.mp4 (Oct 1 11:27 PM PT, 8.0 s)

## Live rig

Clip and autoplay parameters are supported by the hosted rig. Existing authored keyframes drive body clips; idle uses procedural animation. Breathe uses archived authored keys. Pose driver has its own Auto and Talk controls.
