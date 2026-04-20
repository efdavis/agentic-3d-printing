# 3D Printing Projects

Working directory for designing print-ready parts. Each named model lives in its own subfolder; shared tooling and the skill definition live at the root.

## Layout

```
3d-printing/
├── SKILL.md              # The 3D-printing skill itself (Claude Code skill definition)
├── CLAUDE.md             # This file
├── stl_viewer.html       # Three.js viewer — open in browser, drop an STL on it
├── multipart.py          # Shared helper for assembling multi-part 3MFs
├── references/           # Reusable CAD patterns / snippets
│
├── nessie/               # Loch Ness monster magnet set (phased-loop project)
├── maxs_dagger/          # Max's dagger — colorized 3MF with per-extruder parts
├── planner_stencil/      # Planner page stencil (squares + droplets)
└── roborock/             # Miniature Roborock Q8
```

## Per-project folders

Each project folder is self-contained: Python build scripts, STL outputs, colorized 3MFs, reference/blueprint images, and any handoff notes all live together. New projects get their own folder — don't leave build artifacts loose at the root.

- **`nessie/`** — Blender-built magnet set (head, two humps, tail). Phased Ralph-Wiggum loop against `nessieblueprint.png`; frozen intermediate STLs under `nessie/frozen/`. See `HANDOFF_NESSIE_COMPLETE.md` for current state.
- **`maxs_dagger/`** — Per-extruder colorized 3MF. `colorize.py` + `multi_object_3mf.py` produce the painted output; `align/` and `preview/` hold alignment overlays and render previews.
- **`planner_stencil/`** — `planner_stencil.py` builds `stencil.stl` (squares for checkboxes, droplet cutouts). `droplet_analysis.png` and `stencil_topdown.png` are reference images.
- **`roborock/`** — `mini_roborock_q8.py` builds the miniature; `_colored.3mf` is the painted export.

## Conventions

- **Build scripts** are Python (`build123d` preferred; `numpy-stl` is fine for stacked/overlapping primitives per `SKILL.md`).
- **Colorization** for Bambu: per-extruder multi-object 3MFs. See `reference_bambu_*` auto-memories and `maxs_dagger/multi_object_3mf.py` for the pattern. The `paint_color` bitstream only renders in Bambu's Color Painting tool, not Prepare view.
- **Self-review** renders in `stl_viewer.html` before presenting to the user.
- **Phased loops** (like nessie) freeze intermediate STLs into a `frozen/` subfolder at each 95% phase gate.
