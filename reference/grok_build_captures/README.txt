Captures of CreatorJD1/shale-sky-wave-timber (commit 1dc06ca "Export from Grok"), run locally.
Dev server: http://127.0.0.1:8842/  (vite dev, auth off via .grok/app-env.json VITE_AUTH_ENABLED=false; log /tmp/grok_build_dev.log)
App = "Clean room": a static HTML player (public/clean-room/index.html, iframed by the only TanStack route "/").
  Animate mode: 39 pre-rendered mp4 clips (public/clean-room/videos, 24fps h264, no audio, 6.04s / 10.04s long),
    blue-screen chroma-keyed live onto a <canvas> each frame. Tabs: Loops 17, Actions 21, Talk 1.
  Stills mode: 10 tabs / 234 image entries (Base 5, Hair 8, Loops 24, Extreme 27, Playful 4, Move 31, Ground 25, Face 33, Idle 46, Older 31).
Not procedural. src/components/puppet/* (bone rig w/ joint ranges) exists but is NOT routed.
Files:
  page_root.png, page_cleanroom.png  - initial load
  stills/<clip>_t{0.5,mid,end}s.png  - keyed stage at 3 times per clip (117 PNGs)
  clips/<clip>.webm                  - screen recording of each clip playing keyed (39 webm, 600x1000)
  tabs/stills_<Tab>.png              - Stills tabs (viewport)
  asset_inventory.tsv                - every image/video/json in the repo with bytes + dims/duration
  capture_log.json                   - per-clip stage size + console/network log
