# Hand scale audit vs her drawings / master sheet — 2026-10-03 (PT)

Read-only audit. Nothing in rig/, views/ or any live file was touched; outputs only in hands/qa/scale_audit/. Renders only through my own server on 127.0.0.1:8778/8779 (8775 was already taken by another process, so I did not use it), with md5(served rig/index.html) == md5(disk) checked before every render (work/rend_*/md5.txt). **Gate: |Δ| ≤ 1 px** (view px, body 1642 px tall) on every measured landmark.

## Verdict summary

| group | case | verdict | worst Δ px | likely cause |
|---|---|---|---|---|
| view rest (rig vs her base.png) | apose_L | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | apose_R | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | tpose_L | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | tpose_R | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | back_L | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | back_R | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | left_L | PASS | 0.0 | rig at rest = her pixels |
| view rest (rig vs her base.png) | right_R | PASS | 0.0 | rig at rest = her pixels |
| wrist flap | apose_L f7_wrist_apose_over | PASS | 0.0 | flap outside her hand |
| wrist flap | apose_L f7_wrist_apose_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | apose_R f7_wrist_apose_over | PASS | 0.0 | flap outside her hand |
| wrist flap | apose_R f7_wrist_apose_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | tpose_L f10_wrist_tpose_over | PASS | 0.0 | flap outside her hand |
| wrist flap | tpose_L f10_wrist_tpose_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | tpose_L real_rig_00892ccb_hairless_handorder | PASS | 0.0 | real rig render; hand under forearm |
| wrist flap | tpose_R f10_wrist_tpose_over | PASS | 0.0 | flap outside her hand |
| wrist flap | tpose_R f10_wrist_tpose_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | tpose_R real_rig_00892ccb_hairless_handorder | PASS | 0.0 | real rig render; hand under forearm |
| wrist flap | back_L f11_wrist_profile_back_over | PASS | 0.0 | flap outside her hand |
| wrist flap | back_L f11_wrist_profile_back_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | back_L real_rig_00892ccb_hairless_handorder | PASS | 0.0 | real rig render; hand under forearm |
| wrist flap | back_R f11_wrist_profile_back_over | PASS | 0.0 | flap outside her hand |
| wrist flap | back_R f11_wrist_profile_back_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | back_R real_rig_00892ccb_hairless_handorder | PASS | 0.0 | real rig render; hand under forearm |
| wrist flap | left_L f11_wrist_profile_back_over | FAIL | 2.57 | flap drawn OVER the forearm (live default order) adds an edge that moves the wrist landmark proximally |
| wrist flap | left_L f11_wrist_profile_back_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | left_L real_rig_00892ccb_hairless_handorder | PASS | 0.5 | real rig render; hand under forearm |
| wrist flap | right_R f11_wrist_profile_back_over | FAIL | 9.71 | flap drawn OVER the forearm (live default order) adds an edge that moves the wrist landmark proximally |
| wrist flap | right_R f11_wrist_profile_back_underFA | PASS | 0.0 | hand under forearm (staged README order) |
| wrist flap | right_R real_rig_00892ccb_hairless_handorder | PASS | 0.0 | real rig render; hand under forearm |
| turn angle (live rig vs her turn frame) | 0_L | FAIL | 3.25 | frame-vs-drawing calibration: rig = her apose drawing exactly; her turn video is ~1.8% larger |
| turn angle (live rig vs her turn frame) | 0_R | FAIL | 2.27 | frame-vs-drawing calibration: rig = her apose drawing exactly; her turn video is ~1.8% larger |
| turn angle (live rig vs her turn frame) | 45_L | FAIL | 9.0 | near-side generated sprite: length ok, palm/finger split and palm width wrong (palm −3, finger +4.9, width −9) |
| turn angle (live rig vs her turn frame) | 45_R | FAIL | 32.51 | far-side sprite is a full-length hand scaled by fitHand (≈1.64×), so the foreshortening is lost |
| turn angle (live rig vs her turn frame) | 90_L | NO GROUND TRUTH | — | her hand hidden in the turn frame; no ground truth |
| turn angle (live rig vs her turn frame) | 90_R | NO GROUND TRUTH | — | her hand hidden in the turn frame; no ground truth |
| turn angle (live rig vs her turn frame) | 135_L | FAIL | 4.5 | length ok; wrist chord −4.5; knuckle not found on the sprite |
| turn angle (live rig vs her turn frame) | 135_R | FAIL | 32.72 | far-side sprite: full length instead of foreshortened |
| turn angle (live rig vs her turn frame) | 180_L | FAIL | 16.94 | back-view donor scaled down to ~138 by fitHand (non-axial branch) |
| turn angle (live rig vs her turn frame) | 180_R | FAIL | 13.68 | back-view donor scaled down to ~138 by fitHand (non-axial branch) |
| turn angle (live rig vs her turn frame) | 225_L | FAIL | 33.43 | far-side sprite: full length instead of foreshortened |
| turn angle (live rig vs her turn frame) | 225_R | FAIL | 6.5 | near-side sprite ~6 px short, narrower wrist |
| turn angle (live rig vs her turn frame) | 270_L | NO GROUND TRUTH | — | her hand hidden in the turn frame; no ground truth |
| turn angle (live rig vs her turn frame) | 270_R | NO GROUND TRUTH | — | her hand hidden in the turn frame; no ground truth |
| turn angle (live rig vs her turn frame) | 315_L | FAIL | 54.94 | far-side sprite: full length instead of foreshortened |
| turn angle (live rig vs her turn frame) | 315_R | FAIL | 8.79 | length ok; palm +8.3 / finger −8.8 split wrong |
| staged F8 diagonal vs her frame | 45_L | PASS | 0.51 | within gate |
| staged F8 diagonal vs her frame | 45_R | PASS | 0.83 | within gate |
| staged F8 diagonal vs her frame | 135_L | FAIL | 2.02 | L ≤0.83; palm/finger split or palm width 1.2–2.0 px (knuckle-web landmark noise ±1.5 px; silhouette p95 offset ≤1.4 px) |
| staged F8 diagonal vs her frame | 135_R | PASS | 1.0 | within gate |
| staged F8 diagonal vs her frame | 225_L | FAIL | 1.5 | L ≤0.83; palm/finger split or palm width 1.2–2.0 px (knuckle-web landmark noise ±1.5 px; silhouette p95 offset ≤1.4 px) |
| staged F8 diagonal vs her frame | 225_R | FAIL | 1.5 | L ≤0.83; palm/finger split or palm width 1.2–2.0 px (knuckle-web landmark noise ±1.5 px; silhouette p95 offset ≤1.4 px) |
| staged F8 diagonal vs her frame | 315_L | FAIL | 1.5 | L ≤0.83; palm/finger split or palm width 1.2–2.0 px (knuckle-web landmark noise ±1.5 px; silhouette p95 offset ≤1.4 px) |
| staged F8 diagonal vs her frame | 315_R | PASS | 0.5 | within gate |
| master sheet | front_R->apose_R | FAIL | 20.63 | her own view drawing differs from the sheet by the same 20.63 px: sheet hands are relaxed/curled and low-res (269 KB JPEG) |
| master sheet | front_L->apose_L | FAIL | 22.34 | her own view drawing differs from the sheet by the same 22.34 px: sheet hands are relaxed/curled and low-res (269 KB JPEG) |
| master sheet | back_L->back_L | FAIL | 17.13 | her own view drawing differs from the sheet by the same 17.13 px: sheet hands are relaxed/curled and low-res (269 KB JPEG) |
| master sheet | back_R->back_R | FAIL | 17.6 | her own view drawing differs from the sheet by the same 17.6 px: sheet hands are relaxed/curled and low-res (269 KB JPEG) |
| master sheet | prof_L->left_L | FAIL | 10.7 | her own view drawing differs from the sheet by the same 10.7 px: sheet hands are relaxed/curled and low-res (269 KB JPEG) |
| staged F5 curl f1 (vs live f1) | tpose/L_Ring1_f1.png | PASS | 0.0 |  |
| staged F5 curl f1 (vs live f1) | tpose/R_Ring1_f1.png | PASS | 0.0 |  |
| staged F5 curl f1 (vs live f1) | back/L_Index1_f1.png | PASS | 0.0 |  |
| staged F5 curl f1 (vs live f1) | back/L_Middle1_f1.png | PASS | 0.36 |  |
| staged F5 curl f1 (vs live f1) | back/L_Pinky1_f1.png | PASS | 0.0 |  |
| staged F5 curl f1 (vs live f1) | back/L_Ring1_f1.png | FAIL | 1.34 | segment widened (Ring1 her rest 14.0/13.1 → 16.65) |
| staged F5 curl f1 (vs live f1) | back/R_Middle1_f1.png | PASS | 0.0 |  |
| staged F5 curl f1 (vs live f1) | back/R_Ring1_f1.png | FAIL | 2.24 | segment widened (Ring1 her rest 14.0/13.1 → 16.65) |

## Discrepancies with the brief
- **"61 MB master sheet e843956d…":** e843956d-1e25-414e-8793-341da4274435.jpg is a 269 KB 1792×1008 JPEG (the only file with that name on the box). The 61 MB file is freebuff/…/Shadowveil_Interactive_Master_Sheet.html (380 embedded images), which does not contain e843956d. I used the JPEG, loading only per-hand crops (Image.crop on the lazily opened file); I never decoded it into a full array.
- **"Live rig is now 0ce6fecc":** on disk rig/index.html is **00892ccb…** (modified 02:01 PT). Compared with 0ce6fecc it only adds the staged `?hairless=1&handorder=1` path (F10/F11 palms served from hands/staged, hands drawn under the forearm); default behaviour is unchanged. The default-path renders (views, turns) were made at 0ce6fecc. The F10/F11 real-rig renders were made at 00892ccb. Both md5s were verified as served == disk.

## Method
- **Wrist:** the flare onset on the chord-width profile perpendicular to the forearm (forearm axis = Base Body forearm pivot → wristPivot). The scan goes distally from the running minimum. The wrist is the first point where the smoothed width rises ≥6 px over 8 px and ≥12 px over 16 px. Profile views use the area enclosed by her dark outline because the hand lies on her own skin.
- **Tip:** the hand pixel radially farthest from the wrist centre (the middle finger). L = |tip − wrist|.
- **Knuckle:** the base of the middle finger, at the mean of the two inter-finger webs. palm_len = wrist→knuckle; finger_len = L − palm_len. palm_w = silhouette chord at 85 % of palm_len. wrist_w = the wrist chord.
- **Hers:** views/<v>/base.png for rest views. reference/apose_turn/frames (Lanczos-upsampled to the 1642-px view scale) for angles. Master sheet crops scaled by per-figure body height.
- **Rig:** live renders. Staged palms are also composited over base_body.png. F8 parts are placed into her frame with Body's view_fit, using the same diag_check wrist cut and the same key rule.
- **Uncertainty:** views ±1 px, frames ±1.5–3 px (soft video edges, knuckle webs), sheet ±3 px plus curl (L is a lower bound).
- **Calibration note:** at 0° the rig is pixel-identical to her apose drawing, yet it differs from her turn frame f001 by −3.2/−2.3 px. So the turn-frame ground truth itself carries about 2 % scale offset relative to her drawings.

## 1. Views at rest — her base.png vs rig render
| case | metric | hers | rig | Δ px | Δ ratio % | verdict |
|---|---|---|---|---|---|---|
| apose_L | L | 148.6 | 148.6 | 0.0 | 0.0 | PASS |
|  | palm_len | 80.4 | 80.4 | 0.0 | 0.0 | PASS |
|  | finger_len | 68.1 | 68.1 | 0.0 | 0.0 | PASS |
|  | palm_w | 62.0 | 62.0 | 0.0 | 0.0 | PASS |
|  | wrist_w | 40.0 | 40.0 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| apose_R | L | 148.8 | 148.8 | 0.0 | 0.0 | PASS |
|  | palm_len | 80.4 | 80.4 | 0.0 | 0.0 | PASS |
|  | finger_len | 68.4 | 68.4 | 0.0 | 0.0 | PASS |
|  | palm_w | 60.5 | 60.5 | 0.0 | 0.0 | PASS |
|  | wrist_w | 40.5 | 40.5 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| tpose_L | L | 127.5 | 127.5 | 0.0 | 0.0 | PASS |
|  | palm_len | — | — | — | — | n/m |
|  | finger_len | — | — | — | — | n/m |
|  | palm_w | — | — | — | — | n/m |
|  | wrist_w | 32.0 | 32.0 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| tpose_R | L | 128.5 | 128.5 | 0.0 | 0.0 | PASS |
|  | palm_len | — | — | — | — | n/m |
|  | finger_len | — | — | — | — | n/m |
|  | palm_w | — | — | — | — | n/m |
|  | wrist_w | 32.0 | 32.0 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| back_L | L | 148.6 | 148.6 | 0.0 | 0.0 | PASS |
|  | palm_len | 79.4 | 79.4 | 0.0 | 0.0 | PASS |
|  | finger_len | 69.1 | 69.1 | 0.0 | 0.0 | PASS |
|  | palm_w | 61.0 | 61.0 | 0.0 | 0.0 | PASS |
|  | wrist_w | 38.5 | 38.5 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| back_R | L | 146.8 | 146.8 | 0.0 | 0.0 | PASS |
|  | palm_len | 77.8 | 77.8 | 0.0 | 0.0 | PASS |
|  | finger_len | 69.0 | 69.0 | 0.0 | 0.0 | PASS |
|  | palm_w | 60.5 | 60.5 | 0.0 | 0.0 | PASS |
|  | wrist_w | 40.5 | 40.5 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| left_L | L | 144.5 | 144.5 | 0.0 | 0.0 | PASS |
|  | palm_len | 76.9 | 76.9 | 0.0 | 0.0 | PASS |
|  | finger_len | 67.6 | 67.6 | 0.0 | 0.0 | PASS |
|  | palm_w | 68.5 | 68.5 | 0.0 | 0.0 | PASS |
|  | wrist_w | 44.5 | 44.5 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |
| right_R | L | 149.0 | 149.0 | 0.0 | 0.0 | PASS |
|  | palm_len | 77.8 | 77.8 | 0.0 | 0.0 | PASS |
|  | finger_len | 71.2 | 71.2 | 0.0 | 0.0 | PASS |
|  | palm_w | 70.0 | 70.0 | 0.0 | 0.0 | PASS |
|  | wrist_w | 44.0 | 44.0 | 0.0 | 0.0 | PASS |
| | **overall** | | | max 0.0 | | **PASS** |

Head height (chin − crown): apose 230, tpose 226, left 222, right 225 px. L/head and L/forearm are identical for rig and hers in every view (Δ ratio 0); see scale.json.

## 2. Wrist flaps F7 / F10 / F11
- `_over` = staged palm drawn over the forearm. `_underFA` = forearm drawn on top (README order).
- `real_rig_00892ccb_hairless_handorder` = actual render of the current rig with `?hairless=1&handorder=1`.
- px_changed_in_her_hand is 0–8 everywhere.

- apose_L f7_wrist_apose_over: **PASS**, L 148.6→148.6 (0.0), palm_len 80.4→80.4 (0.0), finger_len 68.1→68.1 (0.0), palm_w 62.0→62.0 (0.0), wrist_w 40.0→40.0 (0.0)
- apose_L f7_wrist_apose_underFA: **PASS**, L 148.6→148.6 (0.0), palm_len 80.4→80.4 (0.0), finger_len 68.1→68.1 (0.0), palm_w 62.0→62.0 (0.0), wrist_w 40.0→40.0 (0.0)
- apose_R f7_wrist_apose_over: **PASS**, L 148.8→148.8 (0.0), palm_len 80.4→80.4 (0.0), finger_len 68.4→68.4 (0.0), palm_w 60.5→60.5 (0.0), wrist_w 40.5→40.5 (0.0)
- apose_R f7_wrist_apose_underFA: **PASS**, L 148.8→148.8 (0.0), palm_len 80.4→80.4 (0.0), finger_len 68.4→68.4 (0.0), palm_w 60.5→60.5 (0.0), wrist_w 40.5→40.5 (0.0)
- tpose_L f10_wrist_tpose_over: **PASS**, L 127.5→127.5 (0.0), wrist_w 32.0→32.0 (0.0)
- tpose_L f10_wrist_tpose_underFA: **PASS**, L 127.5→127.5 (0.0), wrist_w 32.0→32.0 (0.0)
- tpose_L real_rig_00892ccb_hairless_handorder: **PASS**, L 127.5→127.5 (0.0), wrist_w 32.0→32.0 (0.0)
- tpose_R f10_wrist_tpose_over: **PASS**, L 128.5→128.5 (0.0), wrist_w 32.0→32.0 (0.0)
- tpose_R f10_wrist_tpose_underFA: **PASS**, L 128.5→128.5 (0.0), wrist_w 32.0→32.0 (0.0)
- tpose_R real_rig_00892ccb_hairless_handorder: **PASS**, L 128.5→128.5 (0.0), wrist_w 32.0→32.0 (0.0)
- back_L f11_wrist_profile_back_over: **PASS**, L 148.6→148.6 (0.0), palm_len 79.4→79.4 (0.0), finger_len 69.1→69.1 (0.0), palm_w 61.0→61.0 (0.0), wrist_w 38.5→38.5 (0.0)
- back_L f11_wrist_profile_back_underFA: **PASS**, L 148.6→148.6 (0.0), palm_len 79.4→79.4 (0.0), finger_len 69.1→69.1 (0.0), palm_w 61.0→61.0 (0.0), wrist_w 38.5→38.5 (0.0)
- back_L real_rig_00892ccb_hairless_handorder: **PASS**, L 148.6→148.6 (0.0), palm_len 79.4→79.4 (0.0), finger_len 69.1→69.1 (0.0), palm_w 61.0→61.0 (0.0), wrist_w 38.5→38.5 (0.0)
- back_R f11_wrist_profile_back_over: **PASS**, L 146.8→146.8 (0.0), palm_len 77.8→77.8 (0.0), finger_len 69.0→69.0 (0.0), palm_w 60.5→60.5 (0.0), wrist_w 40.5→40.5 (0.0)
- back_R f11_wrist_profile_back_underFA: **PASS**, L 146.8→146.8 (0.0), palm_len 77.8→77.8 (0.0), finger_len 69.0→69.0 (0.0), palm_w 60.5→60.5 (0.0), wrist_w 40.5→40.5 (0.0)
- back_R real_rig_00892ccb_hairless_handorder: **PASS**, L 146.8→146.8 (0.0), palm_len 77.8→77.8 (0.0), finger_len 69.0→69.0 (0.0), palm_w 60.5→60.5 (0.0), wrist_w 40.5→40.5 (0.0)
- left_L f11_wrist_profile_back_over: **FAIL**, L 144.5→147.0 (2.52), palm_len 76.9→79.5 (2.57), finger_len 67.6→67.5 (-0.05), palm_w 68.5→68.5 (0.0), wrist_w 44.5→42.5 (-2.0)
- left_L f11_wrist_profile_back_underFA: **PASS**, L 144.5→144.5 (0.0), palm_len 76.9→76.9 (0.0), finger_len 67.6→67.6 (0.0), palm_w 68.5→68.5 (0.0), wrist_w 44.5→44.5 (0.0)
- left_L real_rig_00892ccb_hairless_handorder: **PASS**, L 144.5→145.0 (0.5), palm_len 76.9→77.4 (0.46), finger_len 67.6→67.6 (0.04), palm_w 68.5→68.5 (0.0), wrist_w 44.5→44.5 (0.0)
- right_R f11_wrist_profile_back_over: **FAIL**, L 149.0→158.4 (9.46), palm_len 77.8→87.5 (9.71), finger_len 71.2→70.9 (-0.24), palm_w 70.0→70.0 (0.0), wrist_w 44.0→42.5 (-1.5)
- right_R f11_wrist_profile_back_underFA: **PASS**, L 149.0→149.0 (0.0), palm_len 77.8→77.8 (0.0), finger_len 71.2→71.2 (0.0), palm_w 70.0→70.0 (0.0), wrist_w 44.0→44.0 (0.0)
- right_R real_rig_00892ccb_hairless_handorder: **PASS**, L 149.0→149.0 (0.0), palm_len 77.8→77.8 (0.0), finger_len 71.2→71.2 (0.0), palm_w 70.0→70.0 (0.0), wrist_w 44.0→44.0 (0.0)

## 3. Turn angles — live rig (WristTwist = deg/180, apose view) vs her turn frames
| case | metric | hers | rig | Δ px | Δ ratio % | verdict |
|---|---|---|---|---|---|---|
| 0_L (f001 vs apose (native)) | L | 151.8 | 148.6 | -3.25 | -2.14 | FAIL |
|  | palm_len | 81.7 | 80.4 | -1.24 | -1.51 | FAIL |
|  | finger_len | 70.1 | 68.1 | -2.01 | -2.87 | FAIL |
|  | palm_w | 64.0 | 62.0 | -2.0 | -3.12 | FAIL |
|  | wrist_w | 40.5 | 40.0 | -0.5 | -1.23 | PASS |
| | **overall** | | | max 3.25 | | **FAIL** |
| 0_R (f001 vs apose (native)) | L | 151.0 | 148.8 | -2.27 | -1.5 | FAIL |
|  | palm_len | 81.4 | 80.4 | -1.09 | -1.33 | FAIL |
|  | finger_len | 69.6 | 68.4 | -1.18 | -1.7 | FAIL |
|  | palm_w | 61.0 | 60.5 | -0.5 | -0.82 | PASS |
|  | wrist_w | 41.0 | 40.5 | -0.5 | -1.22 | PASS |
| | **overall** | | | max 2.27 | | **FAIL** |
| 45_L (f035 vs 45_L) | L | 151.2 | 153.1 | 1.86 | 1.23 | FAIL |
|  | palm_len | 80.1 | 77.1 | -3.04 | -3.79 | FAIL |
|  | finger_len | 71.1 | 76.0 | 4.9 | 6.89 | FAIL |
|  | palm_w | 60.0 | 51.0 | -9.0 | -15.0 | FAIL |
|  | wrist_w | 39.0 | 39.5 | 0.5 | 1.28 | PASS |
| | **overall** | | | max 9.0 | | **FAIL** |
| 45_R (f033 vs 45_R) | L | 122.0 | 154.5 | 32.51 | 26.65 | FAIL |
|  | palm_len | 63.0 | — | — | — | n/m |
|  | finger_len | 59.0 | — | — | — | n/m |
|  | palm_w | 46.5 | — | — | — | n/m |
|  | wrist_w | 39.5 | 40.0 | 0.5 | 1.27 | PASS |
| | **overall** | | | max 32.51 | | **FAIL** |
| 90_L | — | — | 143.2 | — | — | NO GROUND TRUTH (her hand hidden behind body/hip in the turn frame(s) f057; rig sprite: left (authored view donor)) |
| 90_R | — | — | 152.1 | — | — | NO GROUND TRUTH (her hand hidden behind body/hip in the turn frame(s) f057; rig sprite: 135_R (no -90 donor; nearest-angle tie)) |
| 135_L (f087 vs 135_L) | L | 157.4 | 156.9 | -0.57 | -0.36 | PASS |
|  | palm_len | 72.3 | — | — | — | n/m |
|  | finger_len | 85.1 | — | — | — | n/m |
|  | palm_w | 57.5 | — | — | — | n/m |
|  | wrist_w | 43.0 | 38.5 | -4.5 | -10.47 | FAIL |
| | **overall** | | | max 4.5 | | **FAIL** |
| 135_R (f087 vs 135_R) | L | 119.4 | 152.1 | 32.72 | 27.4 | FAIL |
|  | palm_len | 63.1 | — | — | — | n/m |
|  | finger_len | 56.3 | — | — | — | n/m |
|  | palm_w | 49.0 | — | — | — | n/m |
|  | wrist_w | 33.0 | 38.0 | 5.0 | 15.15 | FAIL |
| | **overall** | | | max 32.72 | | **FAIL** |
| 180_L (f109 vs back (authored view donor)) | L | 155.9 | 138.9 | -16.94 | -10.87 | FAIL |
|  | palm_len | 81.6 | 73.3 | -8.34 | -10.21 | FAIL |
|  | finger_len | 74.2 | 65.6 | -8.61 | -11.59 | FAIL |
|  | palm_w | 62.5 | 57.0 | -5.5 | -8.8 | FAIL |
|  | wrist_w | 43.0 | 39.0 | -4.0 | -9.3 | FAIL |
| | **overall** | | | max 16.94 | | **FAIL** |
| 180_R (f109 vs back (authored view donor)) | L | 151.4 | 137.7 | -13.68 | -9.03 | FAIL |
|  | palm_len | 79.8 | 73.0 | -6.83 | -8.56 | FAIL |
|  | finger_len | 71.6 | 64.8 | -6.84 | -9.56 | FAIL |
|  | palm_w | 67.5 | 57.0 | -10.5 | -15.56 | FAIL |
|  | wrist_w | 42.5 | 39.5 | -3.0 | -7.06 | FAIL |
| | **overall** | | | max 13.68 | | **FAIL** |
| 225_L (f131 vs 225_L) | L | 123.9 | 157.3 | 33.43 | 26.99 | FAIL |
|  | palm_len | 64.5 | 88.5 | 24.0 | 37.24 | FAIL |
|  | finger_len | 59.4 | 68.8 | 9.42 | 15.86 | FAIL |
|  | palm_w | 53.5 | 46.0 | -7.5 | -14.02 | FAIL |
|  | wrist_w | 34.5 | 39.5 | 5.0 | 14.49 | FAIL |
| | **overall** | | | max 33.43 | | **FAIL** |
| 225_R (f131 vs 225_R) | L | 158.4 | 152.5 | -5.97 | -3.77 | FAIL |
|  | palm_len | 77.8 | — | — | — | n/m |
|  | finger_len | 80.7 | — | — | — | n/m |
|  | palm_w | 63.0 | — | — | — | n/m |
|  | wrist_w | 44.5 | 38.0 | -6.5 | -14.61 | FAIL |
| | **overall** | | | max 6.5 | | **FAIL** |
| 270_L | — | — | 157.3 | — | — | NO GROUND TRUTH (her hand hidden behind body/hip in the turn frame(s) f164; rig sprite: 225_L (no -90 donor; nearest-angle tie)) |
| 270_R | — | — | 148.7 | — | — | NO GROUND TRUTH (her hand hidden behind body/hip in the turn frame(s) f164; rig sprite: right (authored view donor)) |
| 315_L (f189 vs 315_L) | L | 121.9 | 156.4 | 34.45 | 28.26 | FAIL |
|  | palm_len | 64.4 | 119.4 | 54.94 | 85.3 | FAIL |
|  | finger_len | 57.5 | 37.0 | -20.49 | -35.64 | FAIL |
|  | palm_w | 45.5 | 28.0 | -17.5 | -38.46 | FAIL |
|  | wrist_w | 35.0 | 39.0 | 4.0 | 11.43 | FAIL |
| | **overall** | | | max 54.94 | | **FAIL** |
| 315_R (f191 vs 315_R) | L | 154.0 | 153.4 | -0.51 | -0.33 | PASS |
|  | palm_len | 80.4 | 88.7 | 8.28 | 10.3 | FAIL |
|  | finger_len | 73.6 | 64.8 | -8.79 | -11.95 | FAIL |
|  | palm_w | 59.5 | 57.5 | -2.0 | -3.36 | FAIL |
|  | wrist_w | 39.0 | 35.5 | -3.5 | -8.97 | FAIL |
| | **overall** | | | max 8.79 | | **FAIL** |

Rotation relative to the forearm (deg, rig − hers): 0_L 0.1, 0_R -0.4, 45_L -0.4, 45_R 7.1, 135_L 8.0, 135_R -1.9, 180_L 1.2, 180_R 1.7, 225_L -2.4, 225_R -5.5, 315_L -4.2, 315_R 6.7

## 4. Staged F8 diagonals (hands/staged/f8_diagonals) vs her frames
| case | metric | hers | rig | Δ px | Δ ratio % | verdict |
|---|---|---|---|---|---|---|
| 45_L | L | 147.3 | 147.6 | 0.28 | 0.19 | PASS |
|  | palm_len | 76.2 | 76.8 | 0.51 | 0.67 | PASS |
|  | finger_len | 71.0 | 70.8 | -0.23 | -0.32 | PASS |
|  | palm_w | 59.0 | 58.5 | -0.5 | -0.85 | PASS |
| | **overall** | | | max 0.51 | | **PASS** |
| 45_R | L | 115.1 | 115.9 | 0.83 | 0.72 | PASS |
|  | palm_len | 56.9 | 57.6 | 0.76 | 1.34 | PASS |
|  | finger_len | 58.2 | 58.3 | 0.07 | 0.11 | PASS |
|  | palm_w | 44.5 | 44.0 | -0.5 | -1.12 | PASS |
| | **overall** | | | max 0.83 | | **PASS** |
| 135_L | L | 154.2 | 155.0 | 0.83 | 0.54 | PASS |
|  | palm_len | 70.9 | 72.9 | 2.02 | 2.85 | FAIL |
|  | finger_len | 83.3 | 82.2 | -1.18 | -1.42 | FAIL |
|  | palm_w | 55.5 | 54.0 | -1.5 | -2.7 | FAIL |
| | **overall** | | | max 2.02 | | **FAIL** |
| 135_R | L | 100.4 | 100.4 | 0.0 | 0.0 | PASS |
|  | palm_len | 45.4 | 46.4 | 1.0 | 2.2 | PASS |
|  | finger_len | 55.0 | 54.0 | -1.0 | -1.82 | PASS |
|  | palm_w | 46.5 | 47.5 | 1.0 | 2.15 | PASS |
| | **overall** | | | max 1.0 | | **PASS** |
| 225_L | L | 109.5 | 109.5 | 0.0 | 0.0 | PASS |
|  | palm_len | 51.2 | 51.7 | 0.5 | 0.98 | PASS |
|  | finger_len | 58.3 | 57.8 | -0.5 | -0.86 | PASS |
|  | palm_w | 48.0 | 49.5 | 1.5 | 3.12 | FAIL |
| | **overall** | | | max 1.5 | | **FAIL** |
| 225_R | L | 157.0 | 157.0 | 0.0 | 0.0 | PASS |
|  | palm_len | 78.7 | 78.9 | 0.25 | 0.32 | PASS |
|  | finger_len | 78.3 | 78.1 | -0.25 | -0.32 | PASS |
|  | palm_w | 61.0 | 62.5 | 1.5 | 2.46 | FAIL |
| | **overall** | | | max 1.5 | | **FAIL** |
| 315_L | L | 113.6 | 114.2 | 0.53 | 0.47 | PASS |
|  | palm_len | 57.0 | 58.3 | 1.24 | 2.17 | FAIL |
|  | finger_len | 56.6 | 55.9 | -0.71 | -1.25 | PASS |
|  | palm_w | 44.0 | 45.5 | 1.5 | 3.41 | FAIL |
| | **overall** | | | max 1.5 | | **FAIL** |
| 315_R | L | 145.9 | 145.9 | 0.01 | 0.01 | PASS |
|  | palm_len | 75.0 | 75.0 | 0.01 | 0.02 | PASS |
|  | finger_len | 70.9 | 70.9 | 0.0 | 0.0 | PASS |
|  | palm_w | 59.5 | 59.0 | -0.5 | -0.84 | PASS |
| | **overall** | | | max 0.5 | | **PASS** |

Silhouette check (F8 alpha vs her keyed frame, distal of the cut): IoU 45_L 0.966, 45_R 0.959, 135_L 0.969, 135_R 0.973, 225_L 0.973, 225_R 0.961, 315_L 0.946, 315_R 0.951. Boundary p95 offset is ≤1.4 px for all; max 2–6 px at isolated spots.

## 5. Master sheet e843956d (L only; sheet hands are relaxed, so palm and finger are not measurable)
| sheet hand → view | sheet L | rig L | Δ px | Δ % | verdict | her view drawing − sheet |
|---|---|---|---|---|---|---|
| front_R->apose_R | 128.1 | 148.8 | 20.63 | 16.1 | FAIL | 20.63 |
| front_L->apose_L | 126.2 | 148.6 | 22.34 | 17.7 | FAIL | 22.34 |
| back_L->back_L | 131.4 | 148.6 | 17.13 | 13.03 | FAIL | 17.13 |
| back_R->back_R | 129.2 | 146.8 | 17.6 | 13.62 | FAIL | 17.6 |
| prof_L->left_L | 133.8 | 144.5 | 10.7 | 8.0 | FAIL | 10.7 |

Scale sanity: sheet bun→chin is 274.2 vs apose 275 (Δ −0.8), and profile 269.4 vs left 267. The sheet-to-view scaling is therefore right, and the hand gap comes from the sheet's relaxed or curled hands. The 3/4 figure hand touches the thigh, so it was excluded.

## 6. Staged F5 curl line-art (f1 frames, only shown when curled)
- tpose/L_Ring1_f1.png: reach Δ 0.0, median segment width Δ 0.0 → PASS
- tpose/R_Ring1_f1.png: reach Δ 0.0, median segment width Δ 0.0 → PASS
- back/L_Index1_f1.png: reach Δ 0.0, median segment width Δ 0.0 → PASS
- back/L_Middle1_f1.png: reach Δ 0.0, median segment width Δ 0.36 → PASS
- back/L_Pinky1_f1.png: reach Δ 0.0, median segment width Δ 0.0 → PASS
- back/L_Ring1_f1.png: reach Δ 0.0, median segment width Δ 1.34 → FAIL
- back/R_Middle1_f1.png: reach Δ 0.0, median segment width Δ 0.0 → PASS
- back/R_Ring1_f1.png: reach Δ 0.0, median segment width Δ 2.24 → FAIL

## Files
- REPORT.md (this file) and scale.json (all numbers).
- scale_sheet.png: 39 side-by-side crops with landmark marks.
- tools/: measurement code. work/: renders, md5 logs and raw results.
