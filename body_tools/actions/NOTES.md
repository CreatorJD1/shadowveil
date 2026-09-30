# Body actions: jump, run, anger (Base Body)

Generator: `python3 body_tools/actions/make_actions.py` writes `jump.json`, `run.json`, `anger.json` and `checks.json` (the validation output). It runs in about 60 s.
Schema: the same clip format as `body_tools/idle/idle_clips.json`: `{fps 30, duration, loop, interp linear, keys, viewKeys}`. Each file holds one clip at top level, not under `clips`.
- `keys` hold the apose values. `viewKeys` give full overrides for tpose, left, right and back.
- The views need their own keys: the profiles face opposite ways (left faces screen −x, right faces +x), the back view is mirrored, and each view has its own leg lengths, so legs and root are solved per view.
- Keys are sampled every frame from eased curves, so linear playback is smooth.
- Units: limbs ×25°, BodyLean ×8°, Toe −1 = toes bend up 30°, RootY in px (+ is down).
- Only files under `body_tools/actions/` were written. Nothing in views/, rig/ or other owners' folders was touched.

## Root motion: pending (v1.8 draft only)
- The live contract (v1.7.1) and `rig/index.html` have **no root parameter**.
- `RootX`/`RootY` exist only in `rig/index.v18-wip.html`, clamped to ±40 px and drawn in whole px. The v1.8 contract text exists only as the patch script `rig/previews/idle/harness/patch_contract_v18.py`.
- All three clips key `RootY` within ±40, solved per frame so the lower foot's lowest sole point sits on the rest sole line (the same rule as v1.8 foot plant). `RootX` is not keyed (0).
- Keying RootY turns off the v1.8 automatic foot plant in the harness (`render_idle.mjs` only plants when neither RootX nor RootY is keyed).
- `pendingRoot.viewKeys` in each file holds the **unclamped wanted** RootY. It differs from the keys only in the jump.
- Without root (the v1.7.1 renderer ignores RootY), the jump cannot leave the floor, and the crouch and landing make her feet float. See the foot lift section.
- Asks for Coder:
  - Wire RootY in the live renderer.
  - Raise the ±40 clamp to about ±180, or better, move the character in world space, for the jump.
  - RootX (or a world scroll) for the run.
  - v1.7.1 section 3 says "nothing else may be animated", so RootX/RootY need the v1.8 contract bump to land.

## Sign conventions used (canvas rotate, + = clockwise on screen)
- **left view** (faces −x):
  - Hip, Shoulder and Elbow: + means forward (flexion).
  - Knee: − means flexion.
  - Ankle: + means toes up.
  - BodyLean: − means forward.
- **right view** (faces +x): the mirror of left (every sign flips except Toe).
- **apose/tpose:** her L is on screen right. Abduction (limb away from the midline) is L − / R +.
- **back view:** mirrored, L + / R −.
- Front and back knees are only allowed to bend outward (knees-out, with the ankle held in place). Profile knees only bend backward (shin goes behind). Profile elbows only bend forward.
- The check covers every frame in every view (`checks.json` `kneeDirection`, `elbowDirection`): **no knee or elbow bends the wrong way.**

## Beats timeline (for Eyes, Mouth, Hands, Hair)
**Jump, 1.6 s, once:**

| t (s) | event |
|---|---|
| 0.00 | exact rest |
| 0.00–0.40 | anticipation crouch, eased: knees bend, hips flex, lean forward, arms swing back |
| 0.40 | lowest crouch. Arms fully back, lean at its peak. Heels start lifting at 0.40–0.44 |
| 0.50 | **takeoff**: legs straight, up on the balls of the feet, arms swung up and forward. Feet clear the floor at about 0.53 |
| 0.50–0.80 | rise, legs tuck |
| 0.80 | **apex**: tuck at its peak, arms up |
| 0.80–1.10 | fall, legs reach down, arms come down |
| 1.10 | **landing contact** |
| 1.20 | absorb at its lowest: knees at the limit, lean 0.75, arms down |
| 1.35 | small arm overshoot back |
| 1.60 | exact rest |

- Eyes: look down during the crouch, blink on the landing at 1.10 (Eyes' 1.05 is fine).
- Mouth: AA_half at 0.50, OH_half at 0.80, M at 1.10 already match.
- Hair: lift at takeoff, drop at 1.10–1.20. The hair spring has no root or vertical input, so the jump itself gives the hair no lift.

**Run, 2.0 s loop, 3 strides × 0.667 s** (a step every 0.333 s):

| event | t (s) |
|---|---|
| L contact | 0.000, 0.667, 1.333 |
| R contact | 0.333, 1.000, 1.667 |
| R passing (L stance; R swing leg passes) | 0.167, 0.833, 1.500 |
| L passing (R stance; L swing leg passes) | 0.500, 1.167, 1.833 |
| L toe-off | 0.267, 0.933, 1.600 |
| R toe-off | 0.600, 1.267, 1.933 |
| short flight | just before each contact |

- Root bob: lowest at each contact, highest at each passing, one cycle every 0.333 s.
- Arms: R arm forward at L contact, L arm forward at R contact.
- Eyes: gaze bob period 0.333 s.
- Mouth: breath cycle 0.667 s from L contact.
- Hair (front roll): + at L contacts matches the stance foot in apose/tpose. See the back-view concern below.

**Anger, 3.0 s, once, ends in the held pose:**

| t (s) | event |
|---|---|
| 0.00 | exact rest |
| 0.00–0.30 | fast set-in (ease-out) with a 5% overshoot |
| 0.30 | set snap peak |
| 0.40 | settled, hold begins |
| 0.40–0.62, 1.30–1.52, 2.20–2.42 | sharp breaths: 0.9 s period, 0.22 s inhale (peaks at 0.62, 1.52, 2.42), 0.68 s exhale |
| 3.00 | still holding (no return to rest) |

- Body during the breaths: shoulders +1° out or back, elbows +1–1.5°, profile lean −0.03 on each inhale.
- Hands: close the fists during 0.10–0.35 and tighten a little on each inhale peak.
- Mouth: M at 0.30 matches.
- Eyes: narrow by 0.30.

## Clamped values (wanted → got; limits not raised)
Anything wanted beyond ±1.0 was re-authored to peak at the limit instead of being hard-clipped, so no curve has a flat top.

**Jump** (profiles unless marked):

| joint | wanted | got |
|---|---|---|
| crouch knee | ~80° | 25° (1.0) |
| crouch hip | ~50° | 14.5° (0.58, solved so the foot stays planted at the knee limit) |
| crouch lean | ~20° | 8° (body 0.85 + Hair 0.15 = 1.00, exactly at the limit) |
| arm back-swing | −50° | −25° |
| arm up-swing (takeoff/apex) | ~+150° | +25° |
| air tuck, hip / knee | 60° / 90° | 25° / 25° |
| landing absorb knee | ~70° | 25° |
| crouch drop | 20–30 px | 19.5 px (left), 21 px (right), 9–11 px (front/back, knees-out only) |
| **jump height (RootY)** | 150 px | −40 px |

- Jump height: the wanted peak is −150 to −167 px at the apex, counting the 22–32 px rise onto the toes. What you get is **−40 px**: the arc is rescaled to peak at the v1.8 limit (fitted arc 40 px front, 25 px left, 17 px right, on top of the rise onto the toes).
- Front arms-up: wanted ~+45° (Clean room goes A→T), got +25°.

**Run:**

| joint | wanted | got |
|---|---|---|
| hip reach | 40° | 25° |
| hip toe-off | −25° | −22° |
| swing knee | ~100° | 25° |
| stance knee | ~40° | 14° |
| shoulder swing | ±45° | ±25° |
| elbow | ~85° | 17–25° |
| lean | ~12° | 7.2° (0.90; + Hair 0.08 gives at most 0.98) |

- In front, tpose and back the run is a hint only: swing-leg lift by knees-out 8° hips, and a small in-plane arm pump.

**Anger:** nothing clamped. Peaks: lean 0.45 body (0.86 with Hair), shoulders 0.36 front / 0.16 profile, elbows 0.44 / 0.38, hips 0.08.

## Hair BodyLean fold (steering from the parent)
- Source: `hair/actions/hair_actions.json`, clips jump/run/anger, BodyLean only. Their `keys` go to apose/tpose/back, their `viewKeys` to left/right. No other Hair params were taken.
- Rule: `BodyLean = clamp(body + hair, −1, 1)`, sampled at 30 fps. The beats are unchanged.
- Frames that clipped: **0 in all three clips**. The jump crouch in the profiles reaches exactly ±1.00 at 0.40 s (0.85 + 0.15). Each file records this under `hairFold`.
- Refolded 03:23 PT after Hair's fix:
  - Anger now holds to 3.0 s. Left BodyLean at 3.0 = −0.8664 (body −0.448 + Hair −0.418); right = +0.8664.
  - The back-view run roll is flipped. All 48 non-zero Hair back keys are the exact negative of the front keys, and the 7 contact keys (0, 0.333 … 2.0) stay 0. Our back-view run BodyLean equals −apose at every frame.
  - Only those BodyLean channels changed (anger left/right, run back). Jump is byte-identical. Still 0 frames clip.
- Other owners' files checked for body params:
  - `eyes/showcase/eye_showcase.json`, `mouth/actions/mouth_actions.json`, `hands/actions/hand_actions.json`: **none** drive BodyLean or any body joint or Root.
  - Hands keys `WristL/R`, which the contract lists as "Base Hands / Base Body". Body doesn't key Wrist, so nothing overlaps.
  - Nothing was merged. Hands' note asks for a merge into these files. That's left to the clip player / Coder.

## Foot lift and slide (from `checks.json`; px on the 1365×1739 canvas)
The pelvis can only move by root. Knee and ankle are solved per view so each planted foot keeps its x and stays flat. On the balls of the feet, the ball of the foot is held in place instead.

| clip | no root (v1.7.1) | with RootY (v1.8 draft) | stance slip (RootX = 0) |
|---|---|---|---|
| jump | Feet float in the crouch and landing: 19–21 px in profiles, 9–11 px front/back. At toe-off the toes sink 25–32 px below the floor line in profiles | Feet on the floor within 0.5 px on the ground. Airborne up to 42–45 px | ≤ 2.6 px |
| run | The profiles float 4–44 px all the time (the legs are always shorter than rest). Front/back ≤ 0.5 px | Stance foot on the floor. Flight or swing clearance up to 23–26 px (profiles). The front/back stance foot rises 10 px at passing (the bob has no leg bend to absorb it) | **~350 px per stance** in profiles (treadmill, about 1.3k px/s): the world has to scroll that fast, or RootX has to carry it, for the foot to read planted. Front 0 |
| anger | ≤ 1.4 px | ≤ 0.5 px | Feet slide outward 20–30 px each during the 0.40 s set-in (widened stance from 2° hips) |

Idle reference values: a planted-knee hip of 6° lifts the foot about 3 px, 12° about 14 px.

Run root bob: 5.9–21.7 px in left (15.8 px peak to peak) and 3.8–22.9 px in right (19 px, a little over the 10–15 target, because the foot plant takes priority near contact). Front/back: 0 to −10 px. In the profiles her pelvis rides 4–23 px below standing height.

## Validation (`checks.json`)
- Every keyed body param is present in all 5 `rig.json` paramMaps.
- All values are in range: body ±1, RootY ±40.
- Jump and anger start at exact rest (all 0 at t=0). Jump ends at exact rest.
- Run is seamless (first frame equals last in every view).
- Legs alternate: the leading or planted leg at the contacts is L,R,L,R,L,R in all 5 views, and HipL vs HipR correlation is −0.93 (left view).
- Knee and elbow direction are correct in every frame.

## What the Clean room reference does differently (timing and ideas only; no layers copied)
The references are pre-rendered 24 fps videos and sheets, not a rig.
- **Jump** (front view):
  - No anticipation crouch. The rise starts at about 0.2 s.
  - Floaty: about 2.0 s of air (0.2–2.2 s), feet about 270 px up.
  - The knees tuck together with drawn foreshortening, which cutout parts can't do.
  - The arms rise A→T over the rise.
  - Long, deep landing settle: the head drops about 80 px at 2.5 s and recovers by about 4.4 s.
  - Ours: 1.6 s, 0.6 s of air, a real anticipation and a compact recovery, and the height is capped by the root limit.
- **Run** (profile):
  - The loop is about 0.92 s with one head bob and one foot lift per loop.
  - Frame-difference autocorrelation is worst at the half cycle (0.46 s) and best at 0.92 s, so the two halves don't match: it reads as one stride looped, not true L/R alternation (the same failure as the rejected walk sheet).
  - Its joint ranges (hip about 40°, knee 90°+, elbows about 90°) are far past our ±25°.
  - Ours: a step every 0.333 s with measured alternation.
- **Anger** (front):
  - Face-led; the body is nearly static.
  - Arms drift out a little (silhouette about 6% wider at 2.4–3.3 s).
  - Hair toss at 0.4–0.8 s, eye squeeze at about 1.2–2.1 s, no lean. `faces.json` anger has a closed mouth.
  - Ours is body-led (lean and tense arms) and leaves the face to Eyes/Mouth.

## Concerns
1. **Profiles show only one leg and one arm.** The far limbs are `hidden: true` with no files. The run truly alternates (the far leg is keyed), but on screen you see the near leg go forward, then back. It can't look like two legs until far-limb art exists.
2. **The ±25° limb limit dominates.** The run knee (25° vs ~100°) and jump tuck and crouch read stiff. The limits question should be decided on the profile run.
3. **The root is draft-only**, and ±40 px turns the jump into a hop. RootX or a world scroll is needed for the run's 350 px treadmill slip.
4. Front, tpose and back jump and run are 2D stand-ins (knees-out bends, in-plane arms). A forward swing is out of plane there.
5. (Resolved) Hair's anger release and back-view roll were fixed by Hair and refolded.

## Stress copies (render-only; for Coder's stress pass)
`stress/jump_stress.json`, `stress/run_stress.json`, `stress/anger_stress.json` and `stress/checks_stress.json` are written by the same `make_actions.py`, with the same beats and the same Hair fold.
- Each file has top-level `"stressTest": true` and a `stressNote`.
- They hold the **WANTED** angles, unclamped, in rig units. RootY is the unclamped pendingRoot, with no ±40.
- They exceed the rig limits, so the renderer's param clamp must be bypassed to see them. Never ship them.
- Left-view peaks:

  | clip | peaks |
  |---|---|
  | jump | knee 3.6 (90°), hip 2.4 (60°), shoulder 6.0 (150°), BodyLean 2.65, ankle ~1.4 |
  | run | knee 4.2 (the spline overshoots the wanted 100° to 105°), elbow 3.4 (85°), hip 1.56 (39°), shoulder 1.8 (45°), ankle 3.8 (the foot kicks up behind a folded knee), BodyLean 1.58 |

- Jump RootY: −150 px (front) to −160 px (profiles) at the apex. The unclamped 80° crouch also drops the pelvis **+173 px** in the profiles, which is what an 80° knee costs in leg length.
- Anger: nothing was clamped, so the stress copy has the same pose values as anger.json (it adds `stressTest`/`stressNote` and has no `pendingRoot` block).
- Validation: no backward knee or elbow in any frame or view, jump and anger start at exact rest, and the run loops seamlessly.
