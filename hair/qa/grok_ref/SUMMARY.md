# Shadowveil hair vs Clean-room reference (a63fd8e), read-only analysis, 2026-09-30 ~01:30 PT
Outputs: compare_sheet.png, motion_<clip>.png (11 clips), mask_debug_<clip>.png, motion_metrics.json, subframe_lags.json,
scripts: make_compare_sheet.py, hair_motion.py (per-frame tracking, streamed), analyze_motion.py, subframe_lag.py.
Sources: public/clean-room/videos/*.mp4 (24 fps, 768x1168, the originals). The captures/clips/*.webm are 25 fps screen recordings of the same mp4s, so they were not re-measured.
Result: the reference hair is effectively rigid with the head (lag under 1 frame, about 42 ms). It shows no free oscillation and no overshoot.
Settle time can't be measured because no clip has a clean stop-and-rest event.
Proposed spring targets (NOT applied): see the final report.
