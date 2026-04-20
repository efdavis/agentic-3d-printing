---
name: 3d-printing
description: 'Generate print-ready 3D models as STL files from natural-language descriptions. Use this skill whenever the user wants to create a 3D-printable part — stencils, templates, nameplates, cookie cutters, organizers, enclosures, stands, mounts, tokens, keychains, brackets, adapters, or any physical object. Also trigger when the user says "3D print", "STL", "make me a part", "design a case", "parametric model", "mesh generation", or describes physical dimensions and mounting features. This skill prioritizes watertight, manifold geometry that slicers accept without repair, using proper CAD kernels over raw mesh construction.'
---

# 3D Printing Skill

You are helping the user design 3D-printable parts as Python scripts that output STL files. The default mode is **functional parts** — the user is making something to actually print. Optimize for printability, dimensional accuracy, and parametric flexibility over visual complexity.

The most important principle: **use a real CAD kernel when you need boolean operations.** If the design requires cutting, intersecting, or filleting, use build123d or CadQuery. However, for models built from layered/overlapping primitives (cylinders, domes, grooves stacked on top of each other), numpy-stl works well — slicers auto-repair overlapping geometry without issues. Match the tool to the task, not the other way around.

## Tool Selection

Before writing any code, check what's available:

```python
for lib in ['build123d', 'cadquery', 'stl', 'solid2']:
    try:
        __import__(lib if lib != 'stl' else 'stl')
        print(f"  {lib}: available")
    except ImportError:
        print(f"  {lib}: not installed")
```

If nothing is installed, help the user install the recommended tool before proceeding.

### Primary: build123d (recommended)

The most Pythonic CAD library. Algebra mode for simple objects, builder mode for complex multi-step designs.

```bash
pip install build123d
```

Why it's preferred:
- Clean API: `result = Box(60, 40, 10) - Pos(0, 0, 0) * Cylinder(5, 10)`
- Always watertight (OpenCascade kernel)
- Fillets, chamfers, lofts, sweeps, shells built in
- Export: `export_stl(part, "output.stl")`

### Alternative: CadQuery

More established, larger community, more tutorials and Stack Overflow answers.

```bash
pip install cadquery
```

- Fluent API: `cq.Workplane("XY").box(60, 40, 10).faces(">Z").hole(10)`
- Same OpenCascade kernel, same watertight guarantees
- Export: `cq.exporters.export(result, "output.stl")`

### Practical default: numpy-stl

Often the most practical choice — easy to install, no C++ dependencies, and surprisingly capable when you use the **overlapping geometry** approach (layer primitives on top of each other; slicers auto-repair the overlaps).

```bash
pip install numpy-stl
```

- Good for: layered/additive models (stack cylinders, domes, grooves), miniatures, decorative objects, flat geometry, simple extrusions
- Bad for: boolean operations (cutting one shape from another), fillets, precision mechanical parts
- The "mesh not closed" warning is cosmetic — slicers handle it fine
- See `references/cad-patterns.md` for proven numpy-stl primitives: domes, groove rings, arc lips, chamfer rings, rounded rectangles

### Alternative: SolidPython2 + OpenSCAD

Best when the user already has OpenSCAD installed and prefers CSG-style thinking.

```bash
pip install solidpython2
brew install openscad  # macOS
```

- Python generates `.scad` files; OpenSCAD renders to STL
- Strong for parametric designs with lots of repeated boolean operations
- Requires OpenSCAD as a separate install

### macOS / Apple Silicon Notes

`build123d` and `cadquery` depend on `cadquery-ocp` which may not have a PyPI wheel for ARM64. If `pip install` fails:
- Try `conda install -c conda-forge cadquery` (conda has better Apple Silicon support)
- Or install the OCP wheel manually from the CadQuery GitHub releases matching your Python version
- As a last resort, fall back to numpy-stl or SolidPython2

## The Workflow

Five phases. Do them in order.

### Phase 1: Requirements Gathering

Physical objects have tight constraints. Don't guess — ask upfront:

1. **What is the object?** Functional description, not just shape name.
2. **Critical dimensions?** Length, width, height, wall thickness, hole diameters. If it needs to fit something (a device, a shelf, a journal), get exact measurements.
3. **Tolerances and fit?** Parts that mate need clearance defined:
   - **Press fit:** hole undersized by 0.1–0.2mm (parts stay together by friction)
   - **Clearance fit:** hole oversized by 0.2–0.4mm (parts slide freely)
   - **Sliding fit:** hole oversized by 0.1–0.2mm (snug but movable)
4. **Mounting method?** Screws, snap-fit, friction, magnets, adhesive?
5. **Printer type and material?** FDM (PLA, PETG, ABS, TPU) vs resin. Affects minimum wall thickness and detail level.
6. **Nozzle diameter and layer height?** Defaults to 0.4mm nozzle, 0.2mm layers if unspecified.
7. **Print orientation preference?** How will it sit on the build plate?
8. **Reference photos?** If making a replica or miniature, ask for photos of the real object. A single reference photo completely changes the quality of the output — without one, you're guessing at proportions and features.

If the user gives a vague description ("make me a phone stand"), ask these questions. Do not guess dimensions for functional parts.

#### For Replicas and Miniatures

When making a miniature or replica of a real object, add these steps:

1. **Analyze reference photos** — identify every distinct visual feature: seam lines, lips, turrets, vents, buttons, color-change boundaries. List them before coding.
2. **Determine scale-appropriate detail** — not everything visible in the photo will print at the target scale:
   - **> 80mm**: Most surface features printable (text, fine grooves, small holes)
   - **40–80mm**: Simplify text to embossed dots, grooves ≥ 0.5mm, skip features < 0.3mm
   - **< 40mm**: Major shapes only — turrets, lips, body zones. Fine detail won't resolve on FDM.
3. **Map features to construction primitives** — each visible feature becomes a cylinder, dome, groove ring, arc lip, or indentation. Plan the build order (bottom-up).

### Phase 2: Design Decisions

Before writing code, state the design approach:

- **Which CAD tool** will be used and why
- **Construction strategy:** what is the base shape, what features get added/subtracted
- **Print orientation:** how it sits on the build plate, where overhangs occur
- **Parametric variables** to expose (so the user can easily adjust dimensions)
- **Potential issues:** overhangs needing support, thin walls, bridging spans

This is the "think before you code" step. Get the user's buy-in on the approach before generating geometry.

### Phase 3: Generate the Script

Write a self-contained Python script that:

1. **Defines all dimensions as named variables at the top** — grouped with comments
2. **Constructs the geometry** using the selected CAD library
3. **Exports to STL**
4. **Prints a summary:** bounding box dimensions, estimated volume, output filename

Read `references/cad-patterns.md` for code patterns specific to the selected tool.

**Code conventions:**
- All dimensions in **millimeters** (universal standard for 3D printing STL)
- Named variables for every dimension — no magic numbers in geometry construction
- Comments explaining each major construction step
- The script should be runnable with `python generate_part.py` and produce an STL file
- Include a matplotlib or text-based preview if useful for verification

### Phase 4: Printability Review

After generating the script, review the design against printing constraints:

| Check | FDM Rule | Resin Rule |
|-------|----------|------------|
| Wall thickness | >= 2x nozzle diameter (typically 0.8mm) | >= 0.3mm |
| Smallest feature | >= 0.5mm | >= 0.2mm |
| Unsupported overhang | <= 45 degrees from vertical | <= 45 degrees |
| Bridge span | <= 20mm without support | N/A |
| Clearance for mating parts | 0.2–0.4mm per side | 0.1–0.2mm per side |
| Hollow models | N/A | Need drain holes >= 2mm |

**Also check:**
- **Elephant's foot:** first layer squishes ~0.1–0.2mm. Add a small chamfer on bottom edges if precision matters.
- **Screw holes:** self-tapping screws in PLA need pilot holes sized to the screw's minor diameter minus 0.1–0.2mm.
- **Snap-fit clips:** PLA is brittle — keep deflection under 2% of beam length. PETG and TPU are more forgiving.

Flag any violations and suggest fixes before the user prints.

### Phase 5: Output and Iteration

Run the script, confirm the STL was generated, and report:

- Output file path
- Bounding box dimensions (sanity check against intended size)
- Estimated volume in cm^3 (sanity check material usage)
- Number of triangles in the mesh
- Whether the mesh is manifold/watertight (if using a CAD kernel, it will be)

Generate a matplotlib preview with dimensions annotated if the object is non-trivial.

**Expect iteration.** The first version is rarely final. The feedback loop is:

1. Generate STL and matplotlib preview
2. **Self-review with the Three.js viewer** — use the local `stl_viewer.html` to inspect the model in 3D with proper lighting before showing the user. Launch it via the `3d-printing-viewer` server in `.claude/launch.json` and navigate to `/stl_viewer.html?file=<filename>.stl`. Use `window.setView(elevation, azimuth)` to check multiple angles. This catches issues the flat matplotlib preview misses.
3. Fix any obvious issues found in self-review
4. Present to the user with screenshots from the 3D viewer
5. User provides feedback ("the bumper needs more lip", "the turret looks too small")
6. Adjust parameters or add features, re-run
7. Repeat until the user is satisfied

**Self-review checklist (what to look for in the 3D viewer):**
- Do features look proportional from all angles, not just top-down?
- Are grooves/seams deep enough to be visible with real lighting?
- Does the silhouette match the reference photo?
- Are there any unexpected gaps or z-fighting artifacts?
- Does it look like the real thing, or just a cylinder with bumps?

**numpy-stl "mesh not closed" warning:** This appears when using overlapping geometry (layering primitives). It's harmless — slicers auto-repair overlapping meshes without issues. Don't waste time trying to make overlapping geometry watertight; it's not worth the complexity.

## Printing Constraints Quick Reference

### FDM Minimums
- Wall between features: >= 0.4mm (single nozzle width)
- Plate/base thickness: >= 0.8mm (2 layers at 0.4mm layer height)
- Smallest printable feature: >= 0.5mm
- Clearance for mating parts: 0.2–0.4mm per side
- Overhang without support: <= 45 degrees
- Bridge span without support: <= 20mm

### Resin Minimums
- Wall thickness: >= 0.3mm
- Smallest feature: >= 0.2mm
- Hollow models need drain holes: >= 2mm diameter
- Supported surfaces need >= 0.5mm thickness

### Tolerance Guide
| Fit Type | Hole Adjustment | Use Case |
|----------|----------------|----------|
| Press fit | -0.1 to -0.2mm | Pins, bearings, parts that shouldn't move |
| Clearance fit | +0.2 to +0.4mm | Lids, caps, parts that slide on/off |
| Sliding fit | +0.1 to +0.2mm | Drawers, telescoping parts |
| Threaded insert | Per manufacturer spec | Heat-set inserts in PLA/PETG |

## Multi-Color Printing (Bambu Lab AMS)

Two paths, pick the one that matches your input:

| Path | Input | Tool | GUI clicks |
|---|---|---|---|
| **A (primary)** — multi-object 3MF with per-object extruder | Python generator that already knows parts | `multipart.ColoredModel` | 0 |
| **B (fallback)** — per-triangle paint_color 3MF | Opaque STL + reference images | `maxs_dagger/colorize.py` | 0 |

### Path A — `ColoredModel` facade (recommended)

For Python-generated models where the code already knows semantic parts (head vs body vs accent). Each named part becomes a separate `<object>` in the 3MF assigned to an AMS slot. No per-triangle painting, no reference-image pipeline, no slicer click-through.

```python
import trimesh
from multipart import ColoredModel

m = ColoredModel(palette=["#E8E8E8", "#2E2E2E", "#C8326B"])
m.add("body",    body_mesh,    slot=1)   # light gray main body
m.add("turret",  turret_mesh,  slot=2)   # black accent
m.add("details", details_mesh, slot=3)   # pink buttons / vents
m.write("output.3mf")
```

Each mesh must be a `trimesh.Trimesh` (or anything with `.vertices` / `.faces` ndarrays). See `nessie_magnets.py` and `mini_roborock_q8.py` for working examples.

The emitted 3MF passes Bambu Studio's `is_bbl_3mf` trust check — the bundled `project_settings.config` (including the 4-color palette) is honored, and the file opens with all AMS slots visible and no "not from Bambu Lab" dialog.

### Path B — image-reference colorization (`colorize.py`)

Use this when you have an input STL and reference art showing how it should be colored (e.g., a miniature with a painted concept). At `/Users/EricDavis/Projects/3D-printing/maxs_dagger/colorize.py`. It raycasts reference images onto mesh faces, snaps pixels to a palette in CIE-Lab, votes across views, and writes per-triangle `paint_color` attributes using the bit-packed `CONST_FILAMENTS` subdivision bitstream.

```bash
./.venv/bin/python colorize.py \
    --stl input.stl \
    --palette "#1A1A1A,#B5B5B5,#D4A57A,#3D1F2B" \
    --view "front:front_ref.png:-y" \
    --view "back:back_ref.png:+y" \
    --scale 50 --decimate 80000 \
    --out colored.3mf
```

Quality of the output depends heavily on the reference images. Multi-view coverage matters — front + back only yields ~8% direct face coverage, the rest BFS-filled from neighbors.

### Verifying a 3MF without opening Bambu

Three checks, increasing expense. Run `maxs_dagger/verify_3mf.py`:

```bash
./.venv/bin/python maxs_dagger/verify_3mf.py output.3mf --expect-slots 3
./.venv/bin/python maxs_dagger/verify_3mf.py output.3mf --verify-gcode   # slow: slices via BambuStudio CLI
```

Or open the STL/3MF viewer in the browser — it renders per-object colors and per-triangle `paint_color`:

```
http://localhost:8123/stl_viewer.html?file=output.3mf
```

(Server is launched via `.claude/launch.json`; Playwright MCP can screenshot for automated visual verification.)

### Legacy path — split STLs (still works, but requires manual assignment)

The older workflow of exporting one STL per color and assigning each to an AMS slot by clicking in Bambu Studio still works. Prefer Path A (`ColoredModel`) — it emits a single pre-configured 3MF and skips the manual assignment step entirely.

### Color Zone Strategies

| Strategy | When to Use | Example |
|----------|------------|---------|
| **Body zones** | Large areas of different colors | White body + black bumper |
| **Accent features** | Small details in a contrasting color | Silver buttons on a black panel |
| **Top surface art** | Logos or patterns on a flat top | Colored logo on a white lid |
| **Functional markings** | Labels, indicators, scales | Red warning text on a gray enclosure |

### Tips

- **Z-aligned boundaries work best.** Color changes happen at layer boundaries, so horizontal splits (different Z heights) produce clean transitions. Vertical color boundaries within the same layer require purge towers and add print time.
- **Overlap color zones by 0.1–0.2mm** at boundaries to prevent gaps from thermal contraction or slight misalignment.
- **Keep color count ≤ 4** for AMS (4-slot AMS) or ≤ 16 for AMS Hub setups. Fewer colors = fewer filament changes = faster prints.
- **Purge tower cost:** Each filament change wastes ~1–3g of material in the purge tower. A 2-color print with 50 layer changes adds ~100g of waste. Design color boundaries to minimize the number of changes per layer.
- **Test with 2 colors first** before attempting complex multi-color designs. Get the workflow down before adding complexity.

## What NOT to Do

- **Don't use numpy-stl for boolean operations.** It cannot cut one shape from another. If the design requires subtraction or intersection, use build123d or CadQuery. But numpy-stl is fine for additive/overlapping geometry — slicers handle the overlaps.
- **Don't hardcode dimensions.** Every measurement goes in a named variable at the top of the script. The user will iterate, and parametric variables make that painless.
- **Don't ignore print orientation.** A part that looks correct in CAD may be unprintable in certain orientations. State the intended orientation.
- **Don't assume the user has any CAD tool installed.** Check first, install if needed.
- **Don't skip reference photo analysis for replicas.** Without a reference, you'll guess proportions wrong. One photo is worth a thousand parameters.
- **Don't model details that won't print at the target scale.** At 50mm, features under 0.3mm vanish on FDM. Match detail to scale.
- **Don't treat output as one-shot.** The first version is a starting point. Design for iteration: parametric variables, clear section comments, modular construction so features can be tweaked independently.
- **Don't over-engineer simple parts.** A phone stand doesn't need FEA. Match complexity to the task.

## Output Checklist

Before presenting the final output to the user, verify:

- [ ] All dimensions are parameterized as named variables at the top of the script
- [ ] The script runs without errors and produces an STL file
- [ ] The STL is watertight (no non-manifold edges, no open faces)
- [ ] Bounding box matches the user's intended dimensions
- [ ] Wall thickness meets the minimum for the user's printer type
- [ ] Overhangs > 45 degrees are flagged or have support noted
- [ ] Print orientation is stated
- [ ] Tolerance adjustments are applied for mating features
- [ ] The script includes comments explaining each construction step
- [ ] Units are millimeters throughout
- [ ] A preview image or dimension summary is provided for visual verification
- [ ] Self-reviewed in the Three.js viewer (`stl_viewer.html`) from at least 2 angles before presenting to user
