# Hair handoff (Base Hair), 2026-10-03

Plain-English status of every hair item, for whoever picks this up next. The detailed log is in `hair/HANDOFF.md`.
Nothing below is live unless it says so. Everything new waits on the user's OK, one line per item.

## Rules the hair follows
- Hair is cut from her own art. Never redraw her, never mirror her, and use flat colour with no shadows.
- Chroma is `#0000FF` on 1365x1739 canvases.
- **Rest must match her `base.png` at 0 px.**
- **Hair never covers the eyes or the mouth**, at rest or at any sway.
- Each hair colour must come from her own art for that part and view. The gates are 0 off-palette, 0 chroma and 0 colour outside the part's mask.
- Line art stays within about 1 px of its rest width.
- Hair rides only the head group and its own spring bones, with no weight bleed onto the body.
- The white line at her widow's peak is her design, so keep it (apose 53 px, tpose 42 px).
- Layers: hair_back 100; bun 101 front-facing and 650 at the sides and back; hair_front 600 (static); strands 601-619. The bodysuit collar sits above hair_back and below the bun and strands.
- Springs: preset A (4.0 Hz, damping 0.8) is the live default, with sway capped at 1.0.
- Hair test servers use ports 8780-8784. Never touch 8765 (the main server) or 8766 (the password gate).

## Live now
- The main 5 views (apose, tpose, left, right, back) with spring preset A.
- The T-pose wisp underfill in `views/tpose/hair/hair_back.png`.

## Staged, waiting on the user's OK (main model)
| Item | Where | What it fixes |
|---|---|---|
| tone_fix | `hair/staged/tone_fix/` | Off-palette px in live hair_back (apose, back, right, tpose) |
| hairfront_holes | `hair/staged/hairfront_holes/` | Small holes in hair_front (apose, right) |
| lineart_fix | `hair/staged/lineart_fix/` | Strand line breaks at joints during sway |
| A-pose ear_strands + merged strand_04 | `hair/staged/ear_strands/apose/`, `hair/staged/merged/` | Ear and strand pieces in A-pose |
| speck_fix | `hair/staged/speck_fix/` | Erase-mask specks. Needs a choice: a chroma exception for base.png copies, or Body keeps the specks |
| Ear/eye-corner ink, PAIRED with Body | `hair/staged/ear_strands/{left,right,back}/` + Body's `hairless_division_staged/<view>/live_patch_paired_hairfront/` | **One OK line. Both go live together or neither does** (each alone is 400-640 px off at rest) |
| T-pose eye-corner 181 px | `hair/staged/ear_strands/tpose/` | Rest is 0 with Body's restored copies |

## Paused by the user (diagonals 45/135/225/315)
The user stopped all diagonal work on 2026-10-03 to focus on the main model. The latest version is kept in case it resumes.
- **Latest: `hair/staged/diagonals_v4/`**. It covers all of her hair at every angle, has 0 hair over the eye openings and mouth across the full sway range, and its frame_scale cuts match her turn frames at 0 px. qa_gates is 0/0/0. v1-v3 are kept for reference.
- Open issue 1: the one-sided sway caps (`sway_caps.json`) need `degAtPlus1`/`degAtMinus1` support for hair in `rig/index.html`, which is the Coder's change. Without it, 045 `strand_03`/`strand_03_tip` and 315 `strand_06` can swing over the eye or mouth.
- Open issue 2: Body's diagonal heads have no skull under the hair, so sway opens holes of up to 241 px. There's a provisional underfill mask in `diagonals_v4/<ang>/for_base_body/`. Body's diagonal pieces were rejected, so redo the mask against whatever head is chosen.
- Open issue 3: 135/225 hair isn't parented to `head` yet.

## Other open issues and how to fix them
1. **Sub-offsets in left/right/back:** keep hgSub hair and bun at (0,0) while the posed bodies still have baked-in hair. Re-tune from `hair/qa/turn_handoff/subofs_v2/` once they don't.
2. **Renderer smoothing:** bilinear scaling adds off-palette and half-alpha px at sway poses (`hair/qa/colour_sweep/SUMMARY.md`). The Coder plans a post-render palette snap behind a flag. When testing it, check that 1-2 px strand tips don't vanish at full sway, and use each view's own palette.
3. **qa_gates:** the Coder is adding `--hair-dir`. Until then, use the pointed copies in `hair/qa/qa_gates_runs/`.
4. **Parked by the user:** the benchmark expression sheet (`reference/benchmarks/`) and the gold bun band from `reference/outfit/`.

## Checks before anything hair goes live
- Rest diff against `base.png` is 0 px in every view, including `?hairless=1` with Body's paired patch.
- The colour sweep has 0 off-palette, 0 chroma and 0 outside the mask.
- Hair over the eyes and mouth is 0 across the full sway sweep.
- No mirrored parts, and the widow's peak is intact.
- The md5 of the served `rig/index.html` matches the repo file before any render.

## Push
`hair/push_manifest.txt` lists every hair file to push. It excludes backups, work frames and scratch renders.
