# Nessie — Resume Handoff (post-permissions-setup)

**Last updated:** 2026-04-19
**Context:** Eric restarted the session with "accept all" permissions so Ralph loops can run without prompt interruptions. This doc captures exactly where we stopped and what to do next.

---

## TL;DR — kick off with this

```
/ralph-wiggum:ralph-loop "<Phase 4 prompt below>" --max-iterations 30 --completion-promise "PHASE_4_READY_FOR_REVIEW"
```

The loop will re-open `nessieblueprint.png` every iteration, screenshot Blender, compare, tweak one thing, repeat. It exits on its own when the narrow metric hits 95%.

---

## What's already done in this round

- **Plan written:** `/Users/EricDavis/.claude/plans/execute-users-ericdavis-projects-3d-prin-indexed-peacock.md`
- **Execution order agreed** (user call): **shapes first, details after.** Humps → tail → head (hardest, saved for after warmup) → scales/fluke/crown/eye → finalize.
- **Max 30 iterations per phase**, `/learnings` at each phase boundary, re-verify hump shapes (don't rubber-stamp).
- **Frozen dir created:** `/Users/EricDavis/Projects/3d-printing/frozen/` for per-phase STL snapshots.
- **Phase 4 iteration 1 applied:**
  - Snapshot exported: `frozen/phase-4-hump1.stl`
  - Hump1 scaled Y × 1.5 (thickness 16 → 24; W:T ratio 1:3.25 → 1:2.17).
  - Transform applied/baked, STL re-exported as `nessie_hump1.stl`.
  - Side silhouette unchanged (52.2 W × 34.9 H, ratio 1.5:1 matches blueprint body-module-1).
  - Self-grade: **~95%** on the narrow metric (arch proportions).
  - **Needs:** 2 more no-change iterations to satisfy calibration window before declaring ready.

## User-observed issues to address later

- **Triangles (scales) aren't perfect yet** — noted while viewing top view. These are Phase 5's territory, not Phase 4. The scales may have been scaled with the hump (since they're part of the same mesh), so their Y-dimension got stretched too. Phase 5 will need to rebuild/re-shape them anyway, so don't fight this now.

## Phase queue (in execution order)

| # | Phase | State | Narrow metric |
|---|-------|-------|---------------|
| 1 | Phase 4 — Hump1 shape | **IN PROGRESS** (~95%, needs 2 no-change iters) | Arch proportions (W, H, thickness) vs body module 1 |
| 2 | Phase 6 — Hump2 shape | Pending | Same as Phase 4 for hump2 |
| 3 | Phase 8 — Tail shape | Pending (blueprint ready: `nessietailblueprint.png`) | Tail stem silhouette per user's separate blueprint |
| 4 | Phase 1 — Head shape | Pending (hardest) | Cranium, snout, neck taper, forward lean |
| 5 | Phase 5 — Hump1 scales | Pending (user flagged triangles imperfect) | Chunky triangle scales, count, base-width ratio |
| 6 | Phase 7 — Hump2 scales | Pending | Same pattern as Phase 5 |
| 7 | Phase 9 — Tail fluke | Pending | Fluke V-splay per tail blueprint |
| 8 | Phase 2 — Head crown | Pending (~80%) | Radiating spike pattern |
| 9 | Phase 3 — Eye + nostril | Pending (~90%) | Kawaii eye, nostril indent |
| 10 | Phase 10 — Finalization | Pending | Magnets (Ø6.4×3.2mm), final scale, orientation, Bambu-trusted 3MF |

## Ralph prompt template (fill per phase)

```
PHASE {N} — {metric name}

Reference image: /Users/EricDavis/Projects/3d-printing/{nessieblueprint.png OR nessietailblueprint.png}
Current STL: /Users/EricDavis/Projects/3d-printing/{nessie_<piece>.stl}
Snapshot target: /Users/EricDavis/Projects/3d-printing/frozen/phase-{N}-<piece>.stl

Narrow metric: {phase-specific}
Ignore: {phase-specific}
Exit criterion: {phase-specific 95% description}

Relevant memory: feedback_compare_to_reference_every_iteration, feedback_phase_gate_95, feedback_grade_visible_output, feedback_cartoon_abstraction, feedback_iterate_autonomously, reference_blender_composite_gotchas.

Every iteration:
1. Read the reference image with the Read tool (not from memory).
2. mcp__blender__get_viewport_screenshot at an angle showing the narrow-metric feature clearly.
3. Pixel-compare. Identify the SINGLE biggest gap on the narrow metric.
4. If a structural rebuild is needed, FIRST export current piece to frozen/phase-{N}-<piece>.stl.
5. Make ONE targeted change via mcp__blender__execute_blender_code.
6. Re-screenshot. Grade honestly (naive-observer test).
7. If 3 consecutive iterations move backward/sideways, output <promise>PHASE_{N}_PLATEAU</promise>.
8. When narrow metric ≥95% AND 2+ iterations since last major change, output <promise>PHASE_{N}_READY_FOR_REVIEW</promise>.

Rules: cartoon abstraction; don't touch ignore-list features; don't output the promise unless genuinely ≥95%.
```

### Phase 4 prompt (use this first)

```
PHASE 4 — Hump1 shape re-verification.

Reference image: /Users/EricDavis/Projects/3d-printing/nessieblueprint.png
Current STL: /Users/EricDavis/Projects/3d-printing/nessie_hump1.stl
Snapshot (already taken): /Users/EricDavis/Projects/3d-printing/frozen/phase-4-hump1.stl

Current state: prior iteration scaled Y × 1.5. Thickness 24, W:T 1:2.17. Self-grade ~95%. NEED 2 no-change iterations to declare ready.

Narrow metric: hump arch proportions (W, H, thickness) vs blueprint body module 1 — fat rounded arch.
Ignore: scales (Phase 5), head, hump2, tail.
Exit criterion: silhouette matches body-module-1 silhouette at 95% (scales mentally stripped).

Every iteration: [standard loop steps from the template above]

Do NOT touch scales — they are Phase 5's problem. User has noted triangles aren't perfect; those belong to Phase 5, not this phase.

Output <promise>PHASE_4_READY_FOR_REVIEW</promise> when silhouette is stable at 95% across 2 iterations.
```

## Between-phase workflow

1. Ralph exits (promise fires or max-iters hit).
2. User visually reviews Blender viewport and/or STL viewer (`stl_viewer.html` via `3d-printing-viewer` MCP).
3. If accepted: copy `frozen/phase-{N}-<piece>.stl` → `nessie_<piece>.stl` if needed (already done live for Phase 4); run `/learnings` to capture durable lessons; kick off next phase.
4. If rejected: re-run `/ralph-wiggum:ralph-loop` for the same phase with added guidance in the prompt.

## Key files & tools

- `HANDOFF_PHASED_LOOP.md` — original phased-loop spec with narrow metrics per phase (read for Phase 2/5/7/8/9/10 prompts).
- `nessieblueprint.png` — main blueprint (phases 1-7).
- `nessietailblueprint.png` — separate tail blueprint (phases 8-9).
- `nessie_blender.py` — STL-to-3MF assembly; run after all phases: `maxs_dagger/.venv/bin/python nessie_blender.py`.
- `stl_viewer.html` — Three.js viewer for STL review.
- Blender MCP tools: `mcp__blender__execute_blender_code`, `mcp__blender__get_viewport_screenshot`, `mcp__blender__get_scene_info`, `mcp__blender__get_object_info`.
- `/ralph-wiggum:ralph-loop` — kick off; `/ralph-wiggum:cancel-ralph` — bail.

## Blender scene state (currently open)

All 4 pieces loaded: `nessie_head`, `nessie_head_eye_L/R`, `nessie_hump1` (just modified), `nessie_hump2`, `nessie_tail`. Camera + light present. Ensure Blender is still running before resuming — if not, reload STLs with the same names.

## Verification after Phase 10

- `maxs_dagger/.venv/bin/python nessie_blender.py` → regenerates `nessie_magnets_colored.3mf`.
- Load the 3MF in Bambu Studio — must open without segfault, show green body + black eyes.
- Confirm magnet recesses (Ø6.4 × 3.2mm) on each flat back.
- Visual sanity: `stl_viewer.html` served via `3d-printing-viewer` preview MCP.
