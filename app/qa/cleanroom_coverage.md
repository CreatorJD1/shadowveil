# Clean room coverage (media file -> where it is used in the app)

Media files (png/jpg/mp4): 2409; used: 2409 (100.0%). All files incl. json/html/md/zip: 2735, all listed in the gallery.

Where: gallery:<group> = app/cleanroom/gallery.html?g=<group> (#reference tab "Clean room media gallery"); cleanroom-page = patched app/cleanroom/index.html; driver = app/driver (poses.json); registry = app/registry.json media entry.

| group | files | also in Clean room page | also in driver |
|---|---|---|---|
| Turnaround | 64 | 9 | 8 |
| Eyes | 288 | 10 | 5 |
| Hands | 24 | 2 | 10 |
| Mouth / talk | 57 | 12 | 15 |
| Hair | 35 | 8 | 8 |
| Videos (loops / actions) | 38 | 38 | 0 |
| Hires stills | 173 | 172 | 0 |
| Sheets | 92 | 40 | 0 |
| Frames | 171 | 0 | 0 |
| Layer cuts | 638 | 38 | 0 |
| Rig parts | 14 | 14 | 0 |
| Imagine images | 442 | 0 | 0 |
| Imagine videos | 61 | 0 | 0 |
| Artifacts QA | 314 | 0 | 0 |
| Data & pages | 324 | 2 | 0 |

Driver uses:

- reference/grok_build/public/clean-room/layers/rotation/turn-000.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-045.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-090.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-135.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-180.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-225.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-270.png (gallery:turnaround + driver + registry)
- reference/grok_build/public/clean-room/layers/rotation/turn-315.png (gallery:turnaround + driver + registry)
- reference/grok_build/artifacts/turn/fix/eyes-000.jpg (gallery:eyes + driver)
- reference/grok_build/artifacts/turn/fix/eyes-045.jpg (gallery:eyes + driver)
- reference/grok_build/artifacts/turn/fix/eyes-090.jpg (gallery:eyes + driver)
- reference/grok_build/artifacts/turn/fix/eyes-270.jpg (gallery:eyes + driver)
- reference/grok_build/artifacts/turn/fix/eyes-315.jpg (gallery:eyes + driver)
- reference/grok_build/artifacts/turn/hands-000.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/hands-045.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/hands-180.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/hands-315.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-000L.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-000R.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-045L.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-045R.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-315L.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/lock/hand-315R.jpg (gallery:hands + driver)
- reference/grok_build/artifacts/turn/qa/ask-0.4.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/ask-1.8.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/ask-3.2.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/ask-5.0.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/laugh-0.4.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/laugh-1.8.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/laugh-3.2.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/laugh-5.0.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/speak-0.4.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/speak-1.8.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/speak-3.2.jpg (gallery:mouth + driver)
- reference/grok_build/artifacts/turn/qa/speak-5.0.jpg (gallery:mouth + driver)
- reference/grok_build/public/clean-room/videos/talk-ask.mp4 (gallery:mouth + cleanroom-page + driver + registry)
- reference/grok_build/public/clean-room/videos/talk-laugh.mp4 (gallery:mouth + cleanroom-page + driver + registry)
- reference/grok_build/public/clean-room/videos/talk-speak.mp4 (gallery:mouth + cleanroom-page + driver + registry)
- reference/grok_build/public/clean-room/layers/hair/hair-000.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-045.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-090.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-135.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-180.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-225.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-270.png (gallery:hair + cleanroom-page + driver)
- reference/grok_build/public/clean-room/layers/hair/hair-315.png (gallery:hair + cleanroom-page + driver)

Full per-file list: app/qa/cleanroom_coverage.csv