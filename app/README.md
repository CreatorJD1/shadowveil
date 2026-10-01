# Shadowveil master app — notes for the bots

URL: http://127.0.0.1:8765/app/   (served by `python3 -m http.server 8765` from /workspace/shadowveil)
Old URL http://127.0.0.1:8765/status/ redirects to /app/#status.

The app is plain HTML/CSS/JS (app/index.html) with no CDN dependencies. It only reads files:
- `status/status.json`: progress bar, status cards, owners, latest outputs, live-rig config, rendered-clip list
- `app/registry.json`: per-bot sections (tool pages, reports, media) plus the HTML inventory

It wraps your pages in iframes and never edits them. Keep working in your own folders as usual.
Don't point the app at rig/views or rig.json, and don't edit other owners' files through it.

## Routes (hash deep links)
`#status`, `#preview`, `#body`, `#eyes`, `#mouth`, `#hands`, `#hair`, `#coder`, `#reference`, `#inventory`.
The Live Preview route also takes params, e.g. `#preview?view=left&clip=breathe&src=1&hair=A`
(src 0 = rig/index.html, 1 = rig/index.v18-wip.html).
`#status` reloads every 60 s. The other routes refresh their data every 60 s without resetting embedded tools.

## Register a new tool page, report or media file
All paths are relative to /workspace/shadowveil. The file must exist.

    python3 status/update.py register <section> <kind> <path> '<label>' ['<note>']
    #   section: body | eyes | mouth | hands | hair | coder | reference
    #   kind:    pages (html, shown as an iframe tab) | reports (md/txt/log/json, shown as text) | media (png/gif/mp4)
    python3 status/update.py register hands pages hands/live/index.html 'Hands live preview' 'curl + poses'

You can also edit `app/registry.json` by hand. Each entry looks like
`{"label": "...", "path": "...", "note": "...", "minw": 1200, "heavy": false}`.
- `minw` renders the page at that CSS width and scales it down to fit (use it for wide tool UIs).
- `heavy: true` makes the page load only on click (for pages over about 2 MB).

## Auto-discovery
    python3 status/update.py scan

This walks each section's `scan_dirs` and does the following:
- Auto-registers new `.html`, `.mp4` and `.md` files, `SUMMARY*`/`REPORT*` `.txt/.log/.json` files, and top-level `.png` files. They get `"auto": true`.
- Skips paths that contain `backup`, `old_`, `proto_tree`, `__pycache__`, `/frames/`, `(copy` or `/tmp/`.
- Drops auto entries whose file is gone and hides any missing entry (`exists: false`).
- Rebuilds the HTML inventory.
- Rescans `status.json` `video_sources` (rendered clip gallery): rig/previews/idle/*_idle*.mp4, idle_all.mp4, keys/*.mp4, idle/v2/**, and actions/v1/**. To add a new render folder, add a `{glob, group, version}` entry there.

## Status updates (one command each; every one stamps "last updated" in PT and rewrites STATUS.md)
    python3 status/update.py touch
    python3 status/update.py move 'foot plant' done      # done|wip|todo|blocked|decision (substring match)
    python3 status/update.py add progress 'New item text'
    python3 status/update.py owner Hair 'Preset A clamps in; keys delivered' 'keys ready'
    python3 status/update.py progress 55
    python3 status/update.py check                        # HTTP 200 check of every path the app links

## Rig URL params (for the Coder)
rig/index.html accepts only `?view=` (plus `?skin=` and `#check`). index.v18-wip.html adds `auto`, `footplant`, `hair`, `mouthfade` and `quality`.
The clip tabs need `?clip=<idle|breathe|weight_shift|arm_settle|jump|anger|run|showcase>` and `?autoplay=1`.
Until those exist, the clip tabs filter the rendered-clip gallery.

## Build status line
Each tab shows a one-line build status (top right of the nav), read from `status.json` `build_lines`:

    python3 status/update.py build hands "Build: back-view lean fixed"

Live Preview shows a **pose driver ↗** link automatically once `app/driver/index.html` exists.

## Current posing and live hand updates

The master preview includes collapsible controls, zoom and pan, whole-body joint nodes, wrist twist, per-finger controls and articulated rotating hand variants. New hand artwork and its calibration metadata live in `rig/hand_angles/`; reproducible atlas inputs and Python generators live in `tools/`. To regenerate the reconstructed hands, install NumPy, Pillow and SciPy, then run `python tools/install-hd-hands.py`. This changes the reconstructed assets only. The reference extraction generator is retained separately.

The Clean Room reference is linked at `reference/grok_build` as a Git submodule. After cloning, run `git submodule update --init --recursive` to fetch the reference assets. Serve the repository root with `python -m http.server 8765` and open `http://localhost:8765/app/`. Serve Clean Room's `public` directory when opening its native `/clean-room/` page.
