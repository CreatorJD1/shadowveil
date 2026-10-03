# AGENTS.md (for Codex, Freebuff and other coding agents)

Read **[HANDOFF.md](HANDOFF.md)** first. It's the master handoff: what the project is, the hard rules, decisions, status per area, the staged OK list, open issues with fixes, the checks, and the repo/port notes.

The short version:
- Shadowveil is a 2D rig of the artist's own drawn character. Run `python3 -m http.server 8765 --bind 127.0.0.1` in the repo root, then open `/app/`, `/rig/`, `/rig/poser.html` or `/status/`.
- Use her authored art only. Never mirror her (right eye amber, left eye green, one-sided mark). Never draw shapes over her eyes or mouth. Rest must be 0 px vs `views/<view>/base.png`. Use no `#0000FF`, and allow no weight bleed.
- Everything new is staged behind a flag or in a staged folder until the user OKs it. The default output must stay byte-identical.
- Run `python3 rig/qa_gates.py` and the rest check before proposing anything. Never write `skin.json`, `views/` or owner `rig.json` files directly.
- Per-area handoffs: `body_tools/work/HANDOFF_BODY.md`, `eyes/HANDOFF_EYES.md`, `mouth/HANDOFF_MOUTH.md`, `hair/HANDOFF_HAIR.md`, `hands/HANDOFF_HANDS.md`, `CODER_HANDOFF.md`, `rig/poser/HOOKS.md`.
