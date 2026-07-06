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

- **`nessie/`** — Blender-built magnet set (head, two humps, tail). **Read `nessie/README_nessie.md` first** — it has the "fridge = waterline" design concept and the magnet placement spec. The 2026-04-19 autonomous phased-loop run drifted badly and was reverted; see `nessie/FINDINGS_2026-04-19_autonomous_session.md` for what not to repeat. Frozen per-phase snapshots live under `nessie/frozen/`.
- **`maxs_dagger/`** — Per-extruder colorized 3MF. `colorize.py` + `multi_object_3mf.py` produce the painted output; `align/` and `preview/` hold alignment overlays and render previews.
- **`planner_stencil/`** — `planner_stencil.py` builds `stencil.stl` (squares for checkboxes, droplet cutouts). `droplet_analysis.png` and `stencil_topdown.png` are reference images. `planner_stencil_wide.py` builds `stencil_wide.stl` for a 7.8mm-line notebook (1.2× scale: 7.2mm squares, 84mm wide, 9 squares). **Stencil plate thickness preference: 2.0mm** — Eric found 1.0mm too thin (confirmed 2026-05-24).
- **`roborock/`** — `mini_roborock_q8.py` builds the miniature; `_colored.3mf` is the painted export.

## Conventions

- **Build scripts** are Python (`build123d` preferred; `numpy-stl` is fine for stacked/overlapping primitives per `SKILL.md`).
- **Colorization** for Bambu: per-extruder multi-object 3MFs. See `reference_bambu_*` auto-memories and `maxs_dagger/multi_object_3mf.py` for the pattern. The `paint_color` bitstream only renders in Bambu's Color Painting tool, not Prepare view.
- **Self-review** renders in `stl_viewer.html` before presenting to the user.
- **Phased loops** (like nessie) freeze intermediate STLs into a `frozen/` subfolder at each 95% phase gate.

## What NOT to optimize

These come up repeatedly and are not worth iteration cycles:

- **Build-plate orientation in the output 3MF.** The user can re-lay the model flat in Bambu Studio in <10 seconds. Optimize the canonical/analysis frame for *your* reasoning (typically: human-head convention with +Z up, neck cut at z=0), not for which face sits on the build plate.
- **Filament hex codes / palette aesthetics.** Bambu's UI shows numbered slots with a color dropdown — slot N is slot N regardless of what hex you write. Use a sensible default (e.g., `["#2E7D4E" green, "#0A0A0A" black]` for nessie body+eyes) and move on. The user picks actual filament at print time.
- **Sub-nozzle feature resolution** for parts with longest axis ≥ ~50mm. At those scales, eye recesses and similar features print fine on a 0.4mm nozzle. Don't gate on printability checks.

## Mesh / orientation rules

- **PCA-based orient routines** (e.g., `slice_and_drill.pca_orient`) align to the principal axis but don't pick semantic up/forward. Always verify after orient by inspecting bounds or vertex distribution along each axis. For pieces where "up" matters (head with face/spikes vs neck cut), the agent may need a post-orient flip step. Don't edit shared orient functions — write a piece-specific canonicalization that runs after.
- **Rodin AI output meshes** typically arrive at 500k+ vertices / 1M+ faces with high local triangulation noise. Single-pass curvature, vertex normal divergence, and connected-component flood-fill all give noisy/unusable signals at this resolution. Reach for multi-scale curvature, image-space approaches (render → detect features in 2D → unproject to faces), or geodesic distance with dihedral-angle stops.
- **Coloring an existing feature ≠ replacing it with a primitive.** When the user asks to color a recess/bump/etc., do mesh-region selection on the existing triangles. Substituting sphere/cap primitives at the location is a different request and looks visibly wrong.

## Visual workflow rule

For any task that produces a visual output the user will grade by eye (color regions, feature placement, geometry shape):

1. **Build the render-grade harness FIRST.** Before any algorithm work, set up Blender headless renders at the user's reference angles and a way to compare against ground-truth images. If you can't see whether the result matches, iteration is blind.
2. **Don't ship until your render matches the reference.** The user's review cycle is "look in Bambu, take photo." If your render looks wrong, shipping won't fix it.
3. **One filter / change at a time**, render, grade, iterate. Stacking filters before validating each one makes debugging exponentially harder.
4. **Strategy pivots are decisions, not progress.** Tweaking parameters within an approach is autonomous iteration; switching from approach A to B is a decision — surface it and ask before pivoting.
