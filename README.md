# Agentic 3D Printing

Design print-ready 3D models by *describing them in plain language* to Claude Code, and get back parametric Python scripts that export clean, watertight STLs a slicer will accept without repair.

This repo is the working setup behind that: a reusable Claude Code **skill** that encodes the whole workflow, a **CAD pattern cookbook** to copy from, a browser-based **STL self-review viewer**, and a handful of **worked examples** (a windowsill planter, planner stencils, a Loch Ness magnet set).

The core idea: you don't open CAD software. You tell Claude what you want and the constraints it has to satisfy ("a windowsill trough planter, 190mm along the sill, window side vertical so it sits flush, 3mm walls, drainage holes"), and it writes a `build123d` script that produces the STL. You iterate in natural language until it's right, then slice and print.

---

## How the process works

The full method lives in [`SKILL.md`](SKILL.md). In short, every part goes through five phases:

1. **Requirements** — purpose, critical dimensions (mm), tolerances/fit, mounting method, printer + material, orientation. For replicas/miniatures: reference photos first. Claude asks these before guessing.
2. **Design decisions** — pick the CAD tool and *why*, state the construction strategy (base shape → what's added/subtracted), call out overhangs and thin walls, decide which dimensions become parameters. Think before coding.
3. **Generate the script** — a self-contained Python file with **all dimensions as named variables at the top**, geometry built with a real CAD kernel, `export_stl(...)`, and a printed summary (bbox, volume, filename).
4. **Printability review** — check against FDM/resin rules: wall ≥ 2× nozzle, features ≥ 0.5mm, overhangs ≤ 45°, bridges ≤ 20mm, clearances 0.2–0.4mm, elephant's-foot chamfers. Flag violations *before* printing.
5. **Output + iterate** — run it, **self-review in the Three.js viewer** ([`stl_viewer.html`](stl_viewer.html)) at multiple angles, fix what looks wrong, show the user, adjust parameters, repeat.

**Tool choice matters.** Use a real CAD kernel (`build123d`, OpenCascade under the hood) whenever you need booleans, fillets, or lofts — it's watertight by construction. For models built from *layered/overlapping primitives* (domes, groove rings, stacked cylinders), `numpy-stl` is simpler and slicers auto-repair the overlaps. Match the tool to the task; don't force one.

---

## Using the skill in Claude Code

Your friend uses Claude Code, so the highest-leverage share is the skill itself — installing it means "describe a part, get a printable STL" works out of the box.

**Option A — install as a local plugin** (cleanest; the skill auto-triggers on 3D-print requests):

```
~/.claude/plugins/local/3d-printing/
├── .claude-plugin/plugin.json
└── skills/3d-printing/SKILL.md   ← copy of this repo's SKILL.md
```

`plugin.json` is minimal:

```json
{
  "name": "3d-printing",
  "description": "Generate print-ready 3D models as STL files from natural-language descriptions. Supports build123d, CadQuery, numpy-stl, and SolidPython2.",
  "author": { "name": "Eric Davis" }
}
```

**Option B — drop the skill in directly.** Copy `SKILL.md` to `~/.claude/skills/3d-printing/SKILL.md`. Same effect, no plugin wrapper.

Either way, the skill triggers on prompts like *"3D print…", "make me an STL", "design a case/bracket/stand"*, or any description with physical dimensions. It reads [`references/cad-patterns.md`](references/cad-patterns.md) for code patterns as it builds.

---

## What's in here

| File / folder | What it is |
|---|---|
| [`SKILL.md`](SKILL.md) | The full workflow — tool selection, 5-phase process, printability constraints, Bambu multi-color. The reusable engine. |
| [`references/cad-patterns.md`](references/cad-patterns.md) | Copy-paste CAD cookbook: primitives, booleans, fillets, shells, holes, arrays, text, screw bosses, snap-fits, proven `numpy-stl` overlapping-geometry recipes, and the fluting/reeding-a-tapered-vessel pattern. |
| [`CLAUDE.md`](CLAUDE.md) | Project conventions + hard-won *"what NOT to optimize"* rules (skip build-plate orientation fuss, filament hex codes, sub-nozzle detail on large parts). |
| [`stl_viewer.html`](stl_viewer.html) | Three.js STL viewer for self-review — proper lighting catches what a flat matplotlib preview misses. |
| [`multipart.py`](multipart.py) | Helper for assembling multi-part 3MFs. |

### Prerequisites

- Python 3, plus one CAD library — `pip install build123d` (recommended) or `cadquery` or `numpy-stl`.
- A slicer (this setup targets a Bambu P1S / Bambu Studio, but any works).
- Claude Code, to drive it.

---

## Worked examples

Each folder is self-contained — build script(s), STL/3MF outputs, reference images, and handoff notes together.

| Folder | What it demonstrates |
|---|---|
| `windowsill_planter/` | A flared, **reeded** trough planter built by lofting a 2D profile with rounded columns baked in so they follow the wall taper. Includes drainage holes, a catch tray, and a style-variant comparison (plain / grooves / ribs / reeds / faceted). Good first read for the `build123d` loft technique. |
| `planner_stencil/` | Flat functional parts — checkbox squares + droplet cutouts, with a wide variant. Shows text/cutout patterns and the 2.0mm plate-thickness lesson. |
| `nessie/` | A Blender-built magnet set assembled from AI-generated (Rodin) mesh pieces, with a phased-loop build process. Also documents a failed autonomous run — see `FINDINGS_*.md` for what *not* to repeat. |

---

## The short version

Describe the part and its constraints → Claude picks the right kernel and writes a parametric script → it self-reviews the STL in the viewer → you iterate in plain language → slice and print. The skill and the pattern cookbook are what make it repeatable.
