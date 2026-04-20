# Nessie — Phased Ralph-Wiggum-Loop Plan

**Last updated:** 2026-04-19

This document replaces the free-form iteration approach with a structured phase-by-phase loop. The core idea: each phase has a **narrow visual target**, the /loop skill auto-iterates **against the blueprint image** until the naive-observer 95% gate is cleared, then the phase is frozen and we move on.

## Why this workflow

Prior iteration drifted off the reference. I'd view the blueprint once, build an internal description, then iterate against that description — so my "95%" was measured against my memory of the blueprint, not the pixels. The user's feedback (logged in memory as `feedback_compare_to_reference_every_iteration.md`): **re-open the reference image at the start of every iteration**.

A structured phased loop enforces this:
- One phase = one narrow visual target (e.g. "head crown spikes match blueprint density/size")
- Every loop cycle: re-read the reference → screenshot the current viewer → compare at the pixel level → identify the single biggest gap → make the targeted change → rescreenshot
- Don't advance until the narrow metric clears ~95% (judged against the reference each time, not remembered)
- User checks in at phase boundaries, not mid-iteration

## Reference images per phase

**Body / head / humps:** `nessieblueprint.png` (the main technical spec image)

**Tail:** user is providing a **separate tail blueprint**. Save it at `nessietailblueprint.png` or similar. **Ignore the tail as drawn in `nessieblueprint.png`** — it is explicitly superseded. The main blueprint's tail shape is not the target.

## Phase structure

Each phase has:
- **Narrow metric** — what is being matched, explicitly excluding features from other phases
- **What to ignore** — features the phase is NOT responsible for (to avoid scope drift)
- **Exit criterion** — concrete description of "95%"

### Phase 1 — Head shape (no features yet)
- **Narrow metric:** cranium proportions, snout projection, neck taper, forward lean. Does the head silhouette match the blueprint head-module outline?
- **Ignore:** crown spikes, eye, nostril (all future phases)
- **Exit criterion:** silhouette of the head matches blueprint head-module silhouette at 95%+ when mentally stripped of crown/eye. Specifically: egg-shape cranium, clearly distinct snout bump, neck narrower than cranium, slight forward lean.

### Phase 2 — Head crown
- **Narrow metric:** count, size, position, and orientation of crown spikes compared to blueprint head module.
- **Ignore:** eye, nostril.
- **Exit criterion:** crown spike pattern reads 95% like the blueprint's radiating-spike crown. Spikes should be proportional (not tiny antennae) and spread around the upper hemisphere, not just along a top-center line.

### Phase 3 — Eye + nostril
- **Narrow metric:** eye size, position, color differentiation (slot 2 black). Nostril visible on snout.
- **Ignore:** anything else.
- **Exit criterion:** eye reads as a prominent kawaii feature at the right position (side of cranium, above the snout). Nostril visible as an indent on the snout tip.

### Phase 4 — Hump1 shape
- **Narrow metric:** hump arch proportions (width, height, thickness) vs blueprint body module 1.
- **Ignore:** dorsal scales.
- **Exit criterion:** hump1 silhouette matches blueprint body-module-1 silhouette at 95% when scales are mentally stripped.

### Phase 5 — Hump1 scales
- **Narrow metric:** scale shape (chunky triangles, not needles), count, base width vs height ratio, curvature-alignment (fanning outward, not all vertical), back-sweep.
- **Ignore:** shape of the hump itself (frozen from Phase 4).
- **Exit criterion:** scale pattern on top of hump1 matches blueprint body-module-1 scale pattern at 95%.

### Phase 6 — Hump2 shape
Same as Phase 4 but for hump2 (smaller, scaled proportions).

### Phase 7 — Hump2 scales
Same as Phase 5 but for hump2 (applying any learnings from Phase 5).

### Phase 8 — Tail shape
- **Reference:** USER'S SEPARATE TAIL BLUEPRINT (not the tail in `nessieblueprint.png`).
- **Narrow metric:** tail stem proportions, taper, and overall silhouette per the user's blueprint.
- **Ignore:** the fluke geometry (Phase 9).
- **Exit criterion:** tail stem matches user's blueprint at 95%.

### Phase 9 — Tail fluke
- **Reference:** USER'S SEPARATE TAIL BLUEPRINT.
- **Narrow metric:** fluke shape (V-splay, lobe count, lobe angle) per user's blueprint.
- **Ignore:** stem (frozen from Phase 8).
- **Exit criterion:** fluke matches user's blueprint at 95%.

### Phase 10 — Finalization
- Magnet recesses (Ø6.4 × 3.2mm for 6×3mm magnets, subtracted from flat back).
- Final uniform scale pass (if needed).
- Mounting-orientation decision (the open question: does the piece go on the fridge with the flat Z=0 back pressed to it, or do we pivot so the X-Z silhouette faces the viewer?).
- Final 3MF generation + Bambu trust verify.

## How to run the loop

At the start of a phase, kick off:

```
/loop <run until user stops>
Re-open the reference image (nessieblueprint.png for phases 1-7, user's tail blueprint for phases 8-9).
Re-screenshot the current Blender viewport (mcp__blender__get_viewport_screenshot) at an angle that shows the narrow-metric feature clearly.
Compare pixel-for-pixel. Identify the SINGLE biggest visual gap on the narrow metric.
Make ONE targeted change in Blender via mcp__blender__execute_blender_code.
Re-screenshot. Self-grade honestly against the reference (naive-observer test, not an internal description).
If the narrow metric is ≥95% AND it's been at least 2 iterations since the user last confirmed, STOP the loop and notify the user for phase-boundary check-in.
Otherwise, continue iterating.
```

The /loop plugin self-paces if no interval is given. One tick = one iteration.

## Critical principles to encode in every loop cycle

(These are in my memory files — listed here so they're explicit in the handoff.)

1. **`feedback_compare_to_reference_every_iteration.md`** — the reference image is re-opened with the Read tool at the start of every iteration. Don't iterate off internal descriptions.
2. **`feedback_phase_gate_95.md`** — 95% on the **narrow metric**, not on the overall Nessie match. If hump1 scales are at 70%, keep looping; don't advance to hump2 yet.
3. **`feedback_grade_visible_output.md`** — naive-observer test. Pipeline/infrastructure work counts zero toward visual match.
4. **`feedback_cartoon_abstraction.md`** — target is cartoon stylization, not anatomical realism. If the iteration drifts toward "realistic worm," stop.
5. **`feedback_iterate_autonomously.md`** — don't ping the user between iterations for progress checks. Only pause at phase boundaries or for genuine taste-call ambiguity.

## Architecture / tooling (unchanged)

- Blender is the geometry engine, driven by `mcp__blender__execute_blender_code` + `mcp__blender__get_viewport_screenshot`.
- STL export from Blender → `nessie_blender.py` loads them with trimesh → `ColoredModel` emits Bambu-trusted 3MF.
- `stl_viewer.html` served via preview MCP (`3d-printing-viewer` launch config) for final confirmation.
- 2-slot palette: green `#2E7D4E` body, black `#0A0A0A` eye. Head body + eyes share `group="head"`.

## Current state (before loop kickoff)

- Phase 1 head shape: ~85% (egg-shaped cranium + snout + tapered neck, slight forward lean)
- Phase 2 head crown: ~80% (9 big + 7 smaller spikes, radiating pattern)
- Phase 3 eye + nostril: ~90% (two black slot-2 eyes, two nostril indents)
- Phase 4 hump1 shape: ~95% (fat rounded arch)
- Phase 5 hump1 scales: ~85% (chunky curvature-aligned triangles, 6 count)
- Phase 6 hump2 shape: ~95%
- Phase 7 hump2 scales: ~85% (5 scales, proportional to hump1)
- Phase 8 tail shape: pending user blueprint
- Phase 9 tail fluke: pending user blueprint
- Phase 10 finalization: pending

Recommended order: resume Phase 2 (crown) loop first since it's the lowest %, then Phase 5+7 for scales, then get tail blueprint and do Phases 8-9, then finalize.

## Concerns with this workflow

Logging these honestly so you can adjust if needed:

1. **Self-grading is unreliable.** I have consistently over-called my own matches (graded 94% when user saw 50% on the "realistic worm" body, graded 85% on scales when user felt they had no width). The 95% gate works only if my grading is actually calibrated. Mitigation: the naive-observer test helps, but you may want to check in at phase boundaries even if I say "95%."

2. **Phase-scope creep.** When a Blender operation rebuilds a piece (e.g. to change head shape), it wipes sibling work. Mitigation: before running any major rebuild, export the STL for the piece being rebuilt so we have a recoverable snapshot. Freeze a phase by exporting its STL to `frozen/phase-N-<piece>.stl`.

3. **Loop may spin on a plateau.** If the metric is stuck at 85% and every change makes it worse, the loop shouldn't burn forever. Mitigation: if 3 consecutive iterations all move the metric backward or sideways, stop and ask the user.

4. **"95%" needs operational definition per phase.** The exit criteria above are my attempt; user should edit these in this doc if they disagree with the bar.

## Your turn

Review the phase breakdown and narrow metrics above. If the phases are right, kick off `/loop` on Phase 2 (or whichever phase you want first) with the prompt template in the "How to run" section. If you want to tweak the exit criteria or split/merge phases, edit this doc first.
