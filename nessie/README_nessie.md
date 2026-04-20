# Nessie Fridge Magnets — Design Concept

## The core metaphor: *Nessie is swimming out of your fridge*

The fridge surface IS the waterline. Every piece represents a **segment of a sea serpent currently above the water** — with the parts that would be underwater hidden behind the fridge.

## Aesthetic target: cartoon abstraction

This is a stylized cartoon Nessie, **not** an anatomically realistic sea serpent.
- **Uniform body thickness** along the spine (like a cartoon snake, not a tapered worm).
- **Bold simple silhouettes** — charm comes from shape contrast *between* pieces (tall head, fat humps, tall tail), not from girth variation *within* a piece.
- Smooth clean curves over anatomical detail.

This aesthetic was validated with the user after an earlier realism-direction iteration failed. Resist the urge to add "realistic" variation.

## Piece breakdown

| Piece | Role | Silhouette | Current size (mm) |
|---|---|---|---|
| **Head & neck** | Periscope rising from water, leans forward | Tall arch, head/neck distinction; forward-lean | 43.7 L × 16.0 D × 50.0 H |
| **Hump 1** | Front body segment above water | Fat round arch | 42.1 × 16.0 × 26.0 |
| **Hump 2** | Rear body segment | Smaller fat arch | 36.4 × 16.0 × 24.0 |
| **Tail** | Rising stem above water, leans back | Tall arch with backward lean | 46.2 × 16.0 × 42.0 |

Body tube is uniformly 16mm in diameter across all pieces.

## Architecture

Geometry lives in a single bezier curve in Blender:
- 9 control points (uniform radius = 1.0 with `bevel_depth = 8mm` giving 16mm tube diameter)
- Control points oscillate above/below z=0 (the waterline)
- Cut at z=0 to isolate above-water chunks into 4 magnet pieces
- Head and tail get a Z-dependent horizontal shear for directional lean (flat bottom at z=0 preserved)

Export pipeline: Blender → 4 STLs → `trimesh` → `ColoredModel` → Bambu-trusted 3MF.

## Print details

- **Orientation:** print flat back down (z=0 face on build plate); dome self-supports.
- **Magnets:** 6mm Ø × 3mm H disc magnets → Ø6.4mm × 3.2mm recess (added at end of design, after final sizing).
- **Units:** millimeters throughout (1 Blender unit = 1mm).
- **Colors:** single slot (green #2E7D4E) for MVP body. Phase 2 adds slot 2 (black eye).
- **Layer height:** 0.16mm for smooth dome curves.

## Phase roadmap

### Phase 1 — MVP body ✓ (done)
Uniform-radius cartoon serpent, sliced into 4 pieces, head/tail lean, single-color.

### Phase 2 — Features (next)
- Tail taper (narrow stem where fluke attaches)
- Dorsal spines on humps (5-7 triangular blades per hump)
- Head crown (5-7 horn spikes radiating from top of head)
- Eye (second slot, grouped with head body)
- Tail fluke (V-splay at top)

### Final pass
- Magnet recesses (Ø6.4 × 3.2mm)
- Scale confirmation before print

## Why this document exists

Earlier design iterations drifted toward over-organic, anatomically realistic shapes that the user rated as ~50% match. The lesson: anchor on "cartoon abstraction," accept that uniform simple shapes beat accurate-but-busy ones. This README locks in that aesthetic so future iterations don't re-drift.
