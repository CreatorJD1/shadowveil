# Shadowveil — character rig & live driver status

Last updated: Wed Sep 30 2026, 5:10 AM PT

Overall: ~45% — roughly 40–50% to a quality live driver (rough estimate)

Legend: [x] done  [~] in progress  [ ] to do  [!] blocked  [?] needs USER DECISION

Dashboard: http://127.0.0.1:8765/app/#status (master app; /status/ redirects there). Data: status/status.json, app/registry.json

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

- **Body** (skin fix WIP): Profile skin/underlay fix for the armpit hole and hip slit; jump/run/anger action JSON + stress checks (body_tools/actions)
- **Eyes** (See eyes/HANDOFF.md; lash fix and turn offsets unfinished): Stopped, handoff written
- **Mouth** (keys ready): Handoff written (mouth/HANDOFF.md)
- **Hands** (fixes live): Stopped. Handoff in hands/HANDOFF.md; live verified, rest 0 in all views.
- **Hair** (wisp fix WIP): Tpose wisp fill live; speck move and line-art check in progress
- **Coder** (v1.8 WIP): Hand rotation (WristRot + palm twist), wrist leak fix, twist axes on all joints, weighted skinning; life idle + action clips

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

- [idle v1] rig/previews/idle/apose_idle.mp4 (Sep 30 1:51 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/back_idle.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/left_idle.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/right_idle.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/tpose_idle.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/apose_idle_hair_middle.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/apose_idle_hair_stiff.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [idle v1] rig/previews/idle/idle_all.mp4 (Sep 30 1:52 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_all5.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_apose.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_back.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_left.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_right.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_arm_settle_tpose.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_all5.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_apose.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_back.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_left.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_right.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_breathe_tpose.mp4 (Sep 30 2:07 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_keys_all.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_all5.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_apose.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_back.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_left.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_right.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [keys v1] rig/previews/idle/keys/idle_weight_shift_tpose.mp4 (Sep 30 2:08 AM PT, 8.0 s)
- [idle v2] rig/previews/idle/v2/life/apose_life_after.mp4 (Sep 30 4:19 AM PT, 8.0 s)
- [idle v2] rig/previews/idle/v2/life/apose_life_before_after.mp4 (Sep 30 4:18 AM PT, 8.0 s)

## Live rig

rig/index.html accepts only ?view=<apose|tpose|left|right|back> (plus ?skin= and #check). It has no clip or autoplay param, so clip tabs fall back to the rendered clip and Play/Auto must be clicked inside the rig. index.v18-wip.html adds ?auto=idle|talk, ?footplant=xy|y|off, ?hair=default|A|B, ?mouthfade=35|0, ?quality= but still no clip/autoplay. Needed for full tabs: ?clip=<idle|breathe|weight_shift|arm_settle|jump|anger|run|showcase> and ?autoplay=1 (tick Auto/Play on load).
