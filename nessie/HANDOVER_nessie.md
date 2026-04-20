# Nessie Magnets — Session Handover

**Last updated:** 2026-04-19 (Phase 2 features landed: spines, head reshape, crown, eye, fluke)

Use this to bootstrap a fresh Claude Code session without losing context.

## Core concept — read this first

Nessie is **swimming out of the fridge**. The fridge surface is the waterline. Every piece represents part of her body above water; parts underwater are hidden behind the fridge. See `README_nessie.md` for the full framing.

**Aesthetic is cartoon abstraction, not anatomical realism.** Uniform body thickness (like a cartoon snake, not a tapered worm). Bold simple silhouettes. The charm is in shape contrast between pieces, not in girth variation within a piece. See memory `feedback_cartoon_abstraction.md`.

## Current architecture (post-Blender migration)

**Geometry → STL → 3MF handoff:**
1. Blender (driven by `mcp__blender__execute_blender_code`) builds a single bezier curve with uniform radius bevel (16mm diameter cartoon tube).
2. Curve is converted to mesh, cut at z=0 (waterline) via boolean, separated by loose parts into 4 pieces, sorted along X into head/hump1/hump2/tail.
3. Head and tail get a Z-dependent horizontal shear for directional lean (head forward, tail back). Flat bottom at z=0 is preserved.
4. Each piece exports as STL via `bpy.ops.wm.stl_export` with `global_scale=1.0` (Bambu convention: 1 Blender unit = 1mm).
5. `nessie_blender.py` loads the 4 STLs with trimesh and feeds them into `ColoredModel` (from `multipart.py`), which emits the Bambu-trusted multi-object 3MF via `maxs_dagger/multi_object_3mf.py`.

**Why this split:** Blender handles organic geometry well; the existing 3MF writer is already proven for Bambu trust (all 5 thumbnails, fresh `project_settings.config`, etc.). Don't use Blender's built-in 3MF exporter — it fails the Bambu trust check.

## Where the work lives

| File | Purpose |
|---|---|
| `nessie_blender.py` | Orchestrator. Loads STLs (exported from Blender) → `ColoredModel` → Bambu 3MF. |
| `nessie_magnets_legacy.py` | Retired numpy/scipy generator. Kept for reference (magnet recess dimensions, silhouette intentions). Do NOT regenerate from this. |
| `multipart.py` | `ColoredModel` facade — used by `nessie_blender.py`. |
| `maxs_dagger/multi_object_3mf.py` | Low-level 3MF writer (Bambu-trusted). |
| `stl_viewer.html` | Three.js viewer — supports STL and 3MF with per-object color + palette legend. |
| `nessieblueprint.png` | Reference blueprint. Compare body-curve match against this. |

**Persistent memory to read before starting:**
- `~/.claude/projects/-Users-EricDavis/memory/project_3d_printing_setup.md`
- `~/.claude/projects/-Users-EricDavis/memory/reference_bambu_paint_color_encoding.md`
- `~/.claude/projects/-Users-EricDavis/memory/reference_bambu_3mf_trust_requirements.md`
- `~/.claude/projects/-Users-EricDavis/memory/feedback_cartoon_abstraction.md` — target cartoon, not realism
- `~/.claude/projects/-Users-EricDavis/memory/feedback_phase_gate_95.md` — don't advance phases at 80%
- `~/.claude/projects/-Users-EricDavis/memory/feedback_grade_visible_output.md` — naive-observer grading

## What's DONE

### Phase 1 — MVP body
- Bezier serpent spine in Blender, uniform 16mm-diameter tube, waterline oscillation
- 4 pieces: head, hump1, hump2, tail, sliced at waterline
- Head leans forward (quadratic shear), tail leans back (linear shear)

### Phase 2a — Dorsal spines
- hump1: 5 triangular blade sails along top ridge (base 4.5mm, max height 7mm, back-swept 15°)
- hump2: 4 smaller blades (base 4.0mm, max height 6mm, proportional scaling)
- Implementation: `bmesh` triangular-prism blades, boolean UNION (FAST solver) into hump meshes

### Phase 2b — Head reshape
- Head rebuilt from composite primitives, NOT the bezier slice:
  - Tapered neck (cone, radius 7→4.5mm, depth 32mm)
  - Throat blend (ellipsoid 6.5×7×4.5mm at neck-cranium junction)
  - Cranium (ellipsoid 9.5×9×8.5mm)
  - Snout (ellipsoid 6×6×5mm projecting −X)
- All UNION'd (FAST solver) then quadratic forward-lean shear, clipped at z=0

### Phase 2c — Head crown + eye + nostril
- Crown: 8 conical spikes radiating from upper hemisphere of cranium (length 7-11mm, base radius 2.1-3.0mm)
- Nostrils: two 0.9mm sphere DIFFERENCE indents on +Y and −Y sides of snout tip
- Eye: SEPARATE black mesh (slot 2 #0A0A0A), radius 3.2mm sphere on +Y side of cranium at (−11, 7.5, 40). Grouped with head body via `group="head"` so they drag together in Bambu

### Phase 2d — Tail taper + fluke
- Taper: Y-only linear scale, 1.0 at z=0 → 0.5 at z_max (narrows tube at top)
- V-fluke: two triangular-prism blades at tail top, splaying forward-up (−X) and backward-up (+X) at ~34° from vertical, length 12mm

### Export pipeline
- 5 STLs exported from Blender (4 body pieces + 1 eye mesh)
- `nessie_blender.py` loads all 5, builds `ColoredModel(palette=["#2E7D4E","#0A0A0A"])`, head body + eye bundled via `group="head"`
- 3MF trust check passing, 2-slot palette confirmed

## What's NEXT (deferred to end of design)

- **Magnet recesses.** 6×3mm disc magnets → Ø6.4mm × 3.2mm deep recess in each piece's flat back (z=0 face). Add as boolean DIFFERENCE cylinder in Blender. Wait until final piece dimensions are locked.
- **Final scale pass.** User may want uniform scaling (1.0×, 1.2×, etc.) before print — apply in Blender with a whole-object scale + transform_apply before STL export.
- **Mounting orientation question.** Open architectural question: pieces are currently designed with the silhouette visible in the X-Z plane, flat back at z=0. For a fridge magnet, this means the "flat back at z=0 against fridge, dome toward viewer" orientation shows the TOP-DOWN view of the body (elliptical blobs), not the side-profile we've been designing. May need to rotate pieces 90° before final export, or redesign the flat-back as a Y-face. Worth discussing before print.

## Workflow for a new session

1. Verify Blender MCP connected: call `mcp__blender__get_scene_info`.
2. If resuming geometry work, first re-establish the spine in Blender (spine definition lives in chat history; consider saving to a `.blend` file if reuse matters).
3. Iterate on geometry with `mcp__blender__execute_blender_code` + `mcp__blender__get_viewport_screenshot` until user approves the narrow-metric 95% gate.
4. Export STLs from Blender.
5. Run `maxs_dagger/.venv/bin/python nessie_blender.py` to regenerate the 3MF.
6. Verify: `maxs_dagger/.venv/bin/python maxs_dagger/verify_3mf.py nessie_magnets_colored.3mf --expect-slots N`.
7. Screenshot via `stl_viewer.html` + Playwright/Preview MCP.

## Critical gotchas (earned the hard way)

1. **Cartoon, not realism.** Uniform body thickness is the aesthetic — don't taper at waterline crossings to simulate "realistic neck." That was the v4→v5 lesson; user saw v4 as 50% match even though I graded it 94%.
2. **Phase-gate at 95% on the narrow metric.** Don't advance at 80%. Compounding drift across phases is how you end up at 8% overall match.
3. **Grade by what the user sees.** Pipeline/infrastructure work gets zero credit toward visual match %.
4. **`paint_color` does NOT render in Bambu Prepare view.** Use separate objects with per-object `extruder` (ColoredModel's `slot=N`) for visible-on-load colors.
5. **3MF trust requires the full template file set.** Don't hand-roll; always use `ColoredModel`.
6. **Blender's built-in 3MF exporter is not Bambu-trusted.** STL-from-Blender → `ColoredModel` is the required path.
7. **Units.** Set `scene.unit_settings.scale_length = 0.001` for mm display. Export with `global_scale=1.0`. Coords preserved 1:1.
8. **Boolean order.** Apply subsurf BEFORE waterline-cut, or the flat bottom gets rounded.
9. **Blender session persists.** `execute_blender_code` runs in a live Blender instance. Clear prior `nessie_*` objects at the start of scripts so re-runs are idempotent.
10. **Use FAST solver for boolean UNION on composite heads.** EXACT solver failed on multi-primitive unions (consumed the base mesh, left only the cutter). FAST is less precise but reliable for our geometry.
11. **Do NOT re-apply the shear when re-importing a piece from STL.** The exported STL has the shear already baked in. Re-shearing gives a doubled lean that distorts the piece.
12. **Exporting a SEPARATE eye mesh** (rather than union'ing into head body) is required for multi-slot colored-on-load rendering in Bambu. ColoredModel's `group="head"` keeps body + eye draggable as one.

## Quick commands

```bash
cd /Users/EricDavis/Projects/3d-printing
# Rebuild 3MF from currently-exported STLs (does NOT re-run Blender):
maxs_dagger/.venv/bin/python nessie_blender.py
# Verify Bambu trust:
maxs_dagger/.venv/bin/python maxs_dagger/verify_3mf.py nessie_magnets_colored.3mf --expect-slots 1
# View (use preview MCP, server name "3d-printing-viewer"):
#   -> http://localhost:<port>/stl_viewer.html?file=nessie_magnets_colored.3mf
```

## Current state checklist

- [x] Bambu 3MF trust: all files present, opens without "not from Bambu Lab" dialog
- [x] Cartoon aesthetic: uniform body thickness, bold simple silhouettes
- [x] Head leans forward, tail leans back
- [x] Flat backs coplanar at z=0
- [x] 4 pieces drag independently; head body + eye bundled via `group="head"`
- [x] Phase 2a: dorsal blade spines on hump1 + hump2
- [x] Phase 2b: head reshape (cranium + snout + tapered neck)
- [x] Phase 2c: head crown, eye (slot 2 black), nostrils
- [x] Phase 2d: tail taper + V-fluke
- [ ] Magnet recesses (deferred to end)
- [ ] Final scale confirmation (deferred to end)
- [ ] Mounting orientation decision (open question)
