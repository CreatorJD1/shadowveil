# Reference blink/gaze timing — grok_build clean-room clips (read-only reference)

Source: `reference/grok_build/public/clean-room/videos/*.mp4` (39 clips, 24 fps, 145 frames; idle-long/walk 241).
Frames were streamed with OpenCV. Nothing was painted from the clips, and nothing under `views/` was touched.
Frame = 41.7 ms.

## Blinks (12 events in 10 clips; 11 had measurable partial frames)
| phase | median | range |
|---|---|---|
| close (last open → first fully shut) | 42 ms (1 f) | 0–125 ms |
| closed hold | 250 ms (6 f) | 125–375 ms |
| open (first partial → fully open) | 125 ms (3 f) | 0–250 ms |
| total | 333 ms (8 f) | 125–625 ms |

- The shape is asymmetric: a near-instant snap shut, a long hold, then a slower reopen.
- Several blinks are hard cuts, with 0 partial frames (hip #1, strap).
- The hold is long compared with real blinks. It is probably a stylistic feature of the generated video.
- Measured blinks:
  - idle 9–24
  - hip 18–23 and 90–98
  - glare 42–48
  - kick 65–72
  - clasp 12–20
  - strap 105–108
  - tongue 3–14
  - side 7–19 and 67–81
  - look 110–122
  - sway 75–83
- Full table: `per_clip_events.csv`.

## Intervals
- Only 3 clips have 2 blinks: hip 73 f = 3.0 s, sway 63 f = 2.6 s, side 60 f = 2.5 s.
- Clips with a single blink only give lower bounds. idle has no second blink for ≥5.0 s after the first.
- Estimated range: roughly 2.5 s to more than 5 s.

## Sync and winks
- Both eyes close within 0–1 frames of each other in every verified blink. Glare's L eye holds 1 frame longer.
- No winks were confirmed:
  - smirk: a head tilt and squint moved one eye out of the crop.
  - getup: a false positive from shading.
  - point: happens during a head turn and could not be verified.

## Long and expressive closures (not blinks)
- idle-long 45–164 (5.0 s)
- talk 45–98 (2.2 s)
- sad 15–86
- nod 9–77, eyes shut through the head bow
- worry 21–46
- angry 29–50 (squeeze)
- cheeks 42–53 (squeeze)
- yawn 9–56 and 86–144
- smirk 66–78: happy "^^" arcs
- sway 12–29 (0.75 s hold): borderline between a long blink and a closure

## Gaze
- **Idle and talk:** there are no discrete glances. The irises drift slowly, about ±0.1 of eye width (1–2 px), and move with the idle head sway.
- **idle-long:** after the eyes reopen, the drift is about +0.05–0.08. No saccade-and-hold glances appear.
- **"Glance every 9 s":** untestable. Clips are 6–10 s, and the only 10 s front clip has its eyes shut for 5 s.
- **look (head turns):**
  - The eyes jump about 0.4 eye width toward the target.
  - They hold there for the whole head hold, about 1 s (frames ~21–44).
  - On the return, eyes and head recentre together, with no lead.
- **Eye lead on turns:**
  - Turn 1 (viewer-left): the iris shifts at about frame 8. The head accelerates at 9–12. Lead is about 2–4 f (80–170 ms).
  - Turn 2 (viewer-right): the iris shifts at about 66–68. The head starts at 70–72. Lead is about 4–6 f (170–250 ms).
  - A blink happens at the reversal of the second turn (113–118).
- **Nod:** the eyes close at about frames 8–12, in step with (0–2 f ahead of) the start of the bow at ~10. They stay shut through the bow and reopen as the head comes back up (~77).

## Lid shape
- In a blink, only the upper lid moves. It comes down to a closed lash line that sags downward.
- The lower lid rises only in squints and squeezes (glare, kick, tongue, angry).
- Happy closures use upward "^^" arcs.
- The iris does not visibly move during blinks.

## Caveats
- The videos are generated and hold frames. Unique face frames can be as low as 37/145 (clasp), so the effective frame rate is often below 24 fps and 0-frame partials may be artifacts.
- The eyes are tiny (about 20 px wide), and the iris mask is noisy.
- Tracking and gaze metrics are unreliable during head turns. Look/nod timings come from visual reads of the strips.
- Eyes are not visible in: back, kneel, run, sit, stumble.
- Tracking is unusable in: brace, dodge, squat, jump.
- The clips.json rates (the blink sprite at 8 fps with holds [4,1], i.e. open 500 ms / shut 125 ms; talk at 9 fps) describe sprite loops, not these videos. The video blinks hold shut for about 250 ms, twice the 125 ms sprite value.

## Files
- `per_clip_events.csv`
- Contact sheets: `blink_idle.png`, `blink_hip.png`, `blink_glare_kick.png`, `blink_side.png`, `look_turn.png`, `idle-long_close.png`
- Scripts: `analyze.py`, `events.py`, `gaze.py`, `evstrip.py`
- Raw data: `raw/`
