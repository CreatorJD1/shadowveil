# Crotch candidates in the browser rig (Base Body, STAGED, Sat Oct 3 2026 PT)
Renders: headless chrome, rig/index.html md5 562c32a7, scratch COPY tree /workspace/scratch_basebody/tree (no symlinks), port 8773, ?skin=cand_skin_<x>.json. Raw frames: /workspace/scratch_basebody/out_t2/.
apose candidates = Coder's rig/work/crotch_weights/apose_skin_{ulnb,cb24}.json (my rebuild of apose ulnb is byte-identical in underlay px + mesh).
tpose/back built here with copies of Coder's scripts: ulnb = live skin + build_underlay_bb.py --depth 34 --margin 6 --crotch 0 (no --bgk); cb24 = build_skin_crotch_bb.py --crotch-blend 24 --crotch-seg (body_specs cut) + live underlay. *_cbref.json = no-flag rebuild, identical to live.
Metrics: crotch_metrics.json (holes = px opaque in her rest art that show background posed; box = cut x+-41, y cut0-18..cut1+25; "above apex" = notch).
Sheet: sheet_crotch_before_after.png (approved_turnaround crop | live | ulnb | cb24; magenta notch hole, cyan new dark px vs live).
