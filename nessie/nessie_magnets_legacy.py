"""
Loch Ness Monster Fridge Magnet Set — STL Generator v2
======================================================
4 separate ROUNDED 3D pieces that pop out from the fridge:
  1. Head & Neck — rounded head blob, thinner neck ridge
  2. Hump 1 — large rounded body hump
  3. Hump 2 — smaller rounded hump
  4. Tail — rounded body tapering to flukes

Each piece:
  - Flat back face (z=0) sits against fridge with magnet recesses
  - Rounded dome surface pops outward from fridge
  - Height at any point = f(distance from edge) — natural 3D roundness
"""

import numpy as np
import math
from stl import mesh
from scipy.spatial import Delaunay
from scipy.ndimage import distance_transform_edt
from scipy.interpolate import RegularGridInterpolator
from matplotlib.path import Path
import matplotlib.pyplot as plt
import os

# === Config ===
MAGNET_DIA = 10.4        # Recess diameter (0.4mm tolerance for 10mm magnet)
MAGNET_DEPTH = 3.2       # Recess depth (0.2mm for glue)
MAGNET_R = MAGNET_DIA / 2
MAGNET_PTS = 36
BEZIER_PTS = 60          # Smooth curves
MIN_WALL = 2.5           # Minimum dome height at edges (mm)
GRID_RES = 0.3           # Height field resolution (mm)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# === Mesh Assembly ===
class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []

    def add_tri(self, v0, v1, v2):
        offset = len(self.verts)
        self.verts.extend([v0, v1, v2])
        self.faces.append([offset, offset+1, offset+2])

    def add_quad(self, p0, p1, p2, p3):
        self.add_tri(p0, p1, p2)
        self.add_tri(p0, p2, p3)

    def build_stl(self, filename):
        verts = np.array(self.verts)
        faces = np.array(self.faces)
        m = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                m.vectors[i][j] = verts[f[j]]
        m.save(filename)
        size = m.max_ - m.min_
        print(f"  Saved: {os.path.basename(filename)}")
        print(f"  Size: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm")
        print(f"  Triangles: {len(faces)}")
        return m


# === Bézier ===
def bezier(P0, P1, P2, P3, n=BEZIER_PTS):
    pts = []
    for i in range(n + 1):
        t = i / n
        p = ((1-t)**3 * np.array(P0) + 3*(1-t)**2*t * np.array(P1)
             + 3*(1-t)*t**2 * np.array(P2) + t**3 * np.array(P3))
        pts.append(p.tolist())
    return pts


def chain(*segments):
    all_pts = []
    for i, seg in enumerate(segments):
        pts = bezier(*seg)
        if i > 0:
            pts = pts[1:]
        all_pts.extend(pts)
    return all_pts


def close_outline(pts):
    if len(pts) > 1 and np.allclose(pts[0], pts[-1], atol=0.1):
        return pts[:-1]
    return pts


# === Magnet Recess ===
def magnet_circle(cx, cy):
    return [[cx + MAGNET_R * math.cos(2*math.pi*i/MAGNET_PTS),
             cy + MAGNET_R * math.sin(2*math.pi*i/MAGNET_PTS)]
            for i in range(MAGNET_PTS)]


# === Height Field ===
def compute_height_field(outline_2d, max_height):
    """
    Compute dome height at each grid point using distance transform.
    Points at the edge get MIN_WALL height, center gets max_height.
    """
    xs = [p[0] for p in outline_2d]
    ys = [p[1] for p in outline_2d]
    pad = GRID_RES * 4
    x_min, x_max = min(xs) - pad, max(xs) + pad
    y_min, y_max = min(ys) - pad, max(ys) + pad

    grid_x = np.arange(x_min, x_max + GRID_RES, GRID_RES)
    grid_y = np.arange(y_min, y_max + GRID_RES, GRID_RES)
    ny, nx = len(grid_y), len(grid_x)

    # Rasterize outline to mask
    outline_path = Path(outline_2d)
    gx, gy = np.meshgrid(grid_x, grid_y)
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    mask = outline_path.contains_points(pts).reshape(ny, nx)

    # Distance transform: distance from each True pixel to nearest False
    dist = distance_transform_edt(mask).astype(float) * GRID_RES
    max_dist = max(dist.max(), 0.01)
    d_norm = np.clip(dist / max_dist, 0, 1)

    # Rounded dome profile — matches the blueprint's smooth-dome look for
    # the body modules (Phase 1 redo). Smoothstep easing across the full
    # distance field, no plateau. Cross-section resembles a half-ellipse
    # rather than a flat-topped plateau.
    #
    # Shape:         ___
    #              /     \         <- smooth rounded dome
    #            /         \
    #         _/             \_
    profile = d_norm * d_norm * (3.0 - 2.0 * d_norm)  # smoothstep
    height = np.where(mask, MIN_WALL + (max_height - MIN_WALL) * profile, 0)

    return grid_x, grid_y, height, mask


# === Build Rounded Piece ===
def build_rounded_piece(outline_2d, magnet_centers, max_height, name="piece",
                        eye=None, extras=None):
    """
    Build a rounded 3D piece:
    - Flat back at z=0 (against fridge) with magnet recesses
    - Smooth dome surface popping outward (z > 0)
    - Perimeter walls connecting dome to back face
    - Optionally: an eye bump on top of the dome (for Nessie head)

    `eye` = None or (cx, cy) tuple. If provided, adds a small hemisphere on
    top of the dome at that XY location. Returns (size, mb, eye_face_range)
    where eye_face_range is (start, end) face indices of eye triangles, or
    None if no eye.
    """
    mb = MeshBuilder()
    outline_path = Path(outline_2d)

    # --- Height field ---
    grid_x, grid_y, height_field, hmask = compute_height_field(outline_2d, max_height)
    interp = RegularGridInterpolator(
        (grid_y, grid_x), height_field,
        method='linear', bounds_error=False, fill_value=MIN_WALL
    )

    # --- Sample boundary points (dense, on the outline) ---
    boundary_pts = []
    n_outline = len(outline_2d)
    for i in range(n_outline):
        j = (i + 1) % n_outline
        p0, p1 = np.array(outline_2d[i]), np.array(outline_2d[j])
        seg_len = np.linalg.norm(p1 - p0)
        n_seg = max(2, int(seg_len / 0.5))
        for k in range(n_seg):
            boundary_pts.append((p0 + k / n_seg * (p1 - p0)).tolist())
    n_bnd = len(boundary_pts)

    # --- Sample interior points (fine grid with jitter for smooth dome) ---
    interior_pts = []
    all_x = [p[0] for p in outline_2d]
    all_y = [p[1] for p in outline_2d]
    rng = np.random.RandomState(42)  # Deterministic jitter
    grid_step = 0.5  # Finer grid for smoother dome
    jitter = grid_step * 0.25  # Small random offset to break regularity
    for gx in np.arange(min(all_x) + 0.3, max(all_x), grid_step):
        for gy in np.arange(min(all_y) + 0.3, max(all_y), grid_step):
            jx = gx + rng.uniform(-jitter, jitter)
            jy = gy + rng.uniform(-jitter, jitter)
            if outline_path.contains_point([jx, jy]):
                interior_pts.append([jx, jy])

    all_pts = boundary_pts + interior_pts
    pts_arr = np.array(all_pts)

    # --- Compute dome heights ---
    # Query height field for each point
    heights = np.array([
        max(float(interp([[p[1], p[0]]]).item()), MIN_WALL)
        for p in all_pts
    ])
    # Boundary points get a smooth blend: mostly MIN_WALL but with slight
    # natural variation to avoid a hard ridge at the dome base
    for i in range(n_bnd):
        interp_h = heights[i]
        # Blend 70% MIN_WALL, 30% interpolated for gentle transition
        heights[i] = MIN_WALL * 0.7 + interp_h * 0.3

    # --- 1. Dome surface (Delaunay triangulation with varying z) ---
    tri = Delaunay(pts_arr)
    for simplex in tri.simplices:
        p0, p1, p2 = pts_arr[simplex]
        centroid = (p0 + p1 + p2) / 3.0
        if not outline_path.contains_point(centroid):
            continue
        h0, h1, h2 = heights[simplex[0]], heights[simplex[1]], heights[simplex[2]]
        v0 = [p0[0], p0[1], h0]
        v1 = [p1[0], p1[1], h1]
        v2 = [p2[0], p2[1], h2]
        # Ensure outward normal (z-component positive)
        edge1 = np.array(v1) - np.array(v0)
        edge2 = np.array(v2) - np.array(v0)
        normal = np.cross(edge1, edge2)
        if normal[2] < 0:
            v1, v2 = v2, v1
        mb.add_tri(v0, v1, v2)

    # --- 2. Perimeter walls (z=0 to dome edge height, following outline) ---
    for i in range(n_outline):
        j = (i + 1) % n_outline
        x0, y0 = outline_2d[i]
        x1, y1 = outline_2d[j]
        h0 = max(float(interp([[y0, x0]]).item()), MIN_WALL)
        h1 = max(float(interp([[y1, x1]]).item()), MIN_WALL)
        # Match the boundary blend formula
        h0 = MIN_WALL * 0.7 + h0 * 0.3
        h1 = MIN_WALL * 0.7 + h1 * 0.3
        mb.add_quad(
            [x0, y0, 0], [x1, y1, 0],
            [x1, y1, h1], [x0, y0, h0],
        )

    # --- 3. Back face (z=0) with magnet holes ---
    magnet_holes = [magnet_circle(cx, cy) for cx, cy in magnet_centers]
    _build_back_face(mb, outline_2d, magnet_holes, 0.0)

    # --- 4. Magnet recesses (from z=0 into the piece toward z=MAGNET_DEPTH) ---
    for hole in magnet_holes:
        nh = len(hole)
        cx = sum(p[0] for p in hole) / nh
        cy = sum(p[1] for p in hole) / nh
        for i in range(nh):
            j = (i + 1) % nh
            # Cylinder walls
            mb.add_quad(
                [hole[i][0], hole[i][1], 0],
                [hole[j][0], hole[j][1], 0],
                [hole[j][0], hole[j][1], MAGNET_DEPTH],
                [hole[i][0], hole[i][1], MAGNET_DEPTH],
            )
            # Floor
            mb.add_tri(
                [cx, cy, MAGNET_DEPTH],
                [hole[j][0], hole[j][1], MAGNET_DEPTH],
                [hole[i][0], hole[i][1], MAGNET_DEPTH],
            )

    # --- 5. Optional eye bump — built into a SEPARATE MeshBuilder so it can
    # be emitted as its own <object> in the 3MF with its own AMS slot.
    # Bambu's Prepare view only renders per-object color, not paint_color.
    eye_mb = None
    if eye is not None:
        eye_cx, eye_cy = eye
        # Sample the dome height at the eye position so the bump sits ON the dome
        base_z = max(float(interp([[eye_cy, eye_cx]]).item()), MIN_WALL)
        eye_mb = MeshBuilder()
        add_eye_bump(eye_mb, eye_cx, eye_cy, base_z)
        print(f"  eye bump: {len(eye_mb.faces)} triangles at "
              f"({eye_cx}, {eye_cy}, {base_z:.1f}mm)")

    # --- 6. Extras callback (e.g. dorsal spines on humps, head crown) ---
    # Runs on the SAME mesh builder as the body so spikes render in the
    # same AMS slot (green body color) without an extra draggable part.
    if extras is not None:
        faces_before = len(mb.faces)
        extras(mb, interp)
        print(f"  extras: +{len(mb.faces) - faces_before} triangles")

    filepath = os.path.join(OUTPUT_DIR, f"{name}.stl")
    size = mb.build_stl(filepath)
    return size, mb, eye_mb


def _build_back_face(mb, outline, holes, z):
    """Triangulate the back face (z=0) with magnet holes using Delaunay."""
    boundary_pts = []
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        p0, p1 = np.array(outline[i]), np.array(outline[j])
        dist = np.linalg.norm(p1 - p0)
        n_seg = max(2, int(dist / 0.6))
        for k in range(n_seg):
            boundary_pts.append((p0 + k / n_seg * (p1 - p0)).tolist())

    for hole in holes:
        nh = len(hole)
        for i in range(nh):
            j = (i + 1) % nh
            p0, p1 = np.array(hole[i]), np.array(hole[j])
            dist = np.linalg.norm(p1 - p0)
            n_seg = max(2, int(dist / 0.4))
            for k in range(n_seg + 1):
                boundary_pts.append((p0 + k / n_seg * (p1 - p0)).tolist())

    all_x = [p[0] for p in outline]
    all_y = [p[1] for p in outline]
    outline_path = Path(outline)
    hole_paths = [Path(h) for h in holes]

    for gx in np.arange(min(all_x) + 0.4, max(all_x), 0.8):
        for gy in np.arange(min(all_y) + 0.4, max(all_y), 0.8):
            if outline_path.contains_point([gx, gy]):
                if not any(hp.contains_point([gx, gy]) for hp in hole_paths):
                    boundary_pts.append([gx, gy])

    pts_2d = np.array(boundary_pts)
    tri = Delaunay(pts_2d)
    for simplex in tri.simplices:
        p0, p1, p2 = pts_2d[simplex]
        centroid = (p0 + p1 + p2) / 3.0
        if not outline_path.contains_point(centroid):
            continue
        if any(hp.contains_point(centroid) for hp in hole_paths):
            continue
        mb.add_tri(
            [p0[0], p0[1], z],
            [p2[0], p2[1], z],
            [p1[0], p1[1], z],
        )


# =============================================================================
# NESSIE SILHOUETTES (define footprint on fridge)
# =============================================================================

def head_outline():
    """
    Loch Ness monster head & neck — hook-forward posture matching blueprint.

    Blueprint cues (re-examined Phase 1 redo):
      - The head does NOT sit above a vertical neck. Instead the neck rises
        and then the HEAD BULB CURLS FORWARD to the right, giving the whole
        piece a hook / question-mark silhouette (classic seahorse posture).
      - Wide base on the fridge for magnet contact + visual anchor.
      - Big round chubby cheek/face on the head bulb with the eye on the
        forward-facing portion.
      - Snout tucked just below the forehead at the front of the bulb.

    Reference frame: x = left-right across fridge, y = up from build plate.
    Head bulb protrudes to +x (right).
    """
    # Base: wide anchor at y=0
    outline = [[-14, 0], [14, 0]]

    # Right (front) of neck — rises upward with a subtle forward lean
    right_neck = chain(
        ([14, 0],   [13, 4],   [10, 9],   [7, 15]),     # base flare → throat
        ([7, 15],   [5, 20],   [4.5, 26], [5, 31]),     # throat midline
    )

    # --- Forward hook: head bulb protrudes to the right ---
    # Chin curves forward from the throat
    chin = chain(
        ([5, 31],   [7, 32],   [12, 32],  [17, 34]),    # chin / under-jaw forward
        ([17, 34],  [21, 35],  [23, 37],  [23, 40]),    # jowl out to snout
    )

    # Snout tip — forward-facing rounded snout
    snout = chain(
        ([23, 40],  [23.5, 42], [23, 44], [21, 45]),    # snout tip rolls up
    )

    # Forehead → top of skull (this is where the crown of spikes will go
    # in Phase 2)
    top = chain(
        ([21, 45],  [18, 46],   [13, 47], [8, 47]),     # brow → forehead
        ([8, 47],   [3, 47],    [-1, 46], [-4, 44]),    # crown → back of skull
    )

    # Back of skull curling down to nape, connecting to back of neck
    back = chain(
        ([-4, 44],  [-5, 40],   [-5, 36], [-5, 32]),    # nape descent
    )

    # Left (back) of neck — mirror of right neck, descending to base
    left_neck = chain(
        ([-5, 32],  [-6, 25],   [-7, 17], [-9, 10]),    # back-of-neck curve
        ([-9, 10],  [-11, 6],   [-13, 3], [-14, 0]),    # back base flare
    )

    outline.extend(right_neck[1:])
    outline.extend(chin[1:])
    outline.extend(snout[1:])
    outline.extend(top[1:])
    outline.extend(back[1:])
    outline.extend(left_neck[1:])
    return close_outline(outline)


# === Eye bump geometry ===
# Parameters for the eye feature on the head. The eye is a small raised
# hemisphere sitting on top of the main head dome — clearly visible as a
# separate bump in print, and its triangles are tagged with a face-index
# range so the 3MF writer can paint them with a different AMS slot.
EYE_POS = (15, 41)       # (x, y) — on the forward-hook head bulb (redo Phase 1)
EYE_RADIUS = 3.0         # outer radius of the eye bump (mm)
EYE_RISE = 1.4           # how much the eye protrudes above the dome surface (mm)
EYE_RINGS = 5            # latitude rings for the eye hemisphere
EYE_SEGMENTS = 24        # longitude segments for the eye hemisphere


def add_eye_bump(mb, eye_cx, eye_cy, base_z, radius=EYE_RADIUS, rise=EYE_RISE,
                 n_rings=EYE_RINGS, n_seg=EYE_SEGMENTS):
    """Append a small spherical-cap dome (eye bump) to MeshBuilder `mb`.

    Returns (face_start, face_end) — the face-index range that was added.
    The caller uses this range to tag which triangles get painted differently
    in the multi-color 3MF writer.

    The bump sits ON the main head dome, overlapping it slightly (slicers
    auto-repair the union). rise = how much the TOP of the eye protrudes
    above the main dome's height at that point.
    """
    face_start = len(mb.faces)

    # Sphere ring vertices — spherical-cap parametrization.
    # phi = angle from vertical axis (0 = top, pi/2 = equator at base)
    # We stop a bit before pi/2 so the base slightly overlaps the head dome
    # underneath, ensuring a clean printable join.
    phi_max = math.pi * 0.48  # go ~86° from top (leaves slight overlap flare)

    rings = []
    for ri in range(n_rings + 1):
        phi = phi_max * (ri / n_rings)
        z = base_z + rise * math.cos(phi)
        r = radius * math.sin(phi)
        ring = []
        for si in range(n_seg):
            theta = 2 * math.pi * si / n_seg
            x = eye_cx + r * math.cos(theta)
            y = eye_cy + r * math.sin(theta)
            ring.append([x, y, z])
        rings.append(ring)

    # Triangulate between adjacent rings (outward normals up/away from center)
    for ri in range(n_rings):
        upper = rings[ri]       # closer to top
        lower = rings[ri + 1]   # farther out / lower
        for si in range(n_seg):
            sj = (si + 1) % n_seg
            mb.add_quad(lower[si], lower[sj], upper[sj], upper[si])

    # Seal the very top (cap apex). ring 0 is a tiny ring at the top.
    # For a true apex, ri=0 gives r=0 so all points are coincident — skip cap.
    # Our ring 0 has phi=0 so r=0 — it's degenerate but fine (zero-area tris).

    face_end = len(mb.faces)
    return face_start, face_end


# === Dorsal spike (sail blade) geometry ===
# A pyramid with a thin rectangular base sitting on (and embedded in) the
# dome surface, and a single apex above. Apex leans in -ridge_dir for a
# "swimming forward" back-swept look.
def add_dorsal_spine(mb, cx, cy, base_z, ridge_dir=(1.0, 0.0),
                     length=3.0, thickness=0.9, height=5.0, sweep=1.0,
                     embed=0.6):
    """Add a dorsal spike to MeshBuilder `mb`.

    (cx, cy)    = XY position of spike base center on the dome.
    base_z      = z height of the dome at that point (the spike base is
                  dropped by `embed` mm below this so it overlaps the dome
                  for a clean manifold join).
    ridge_dir   = unit direction of the blade's long (length) axis.
                  Thickness axis is perpendicular to this.
    length      = base extent along ridge_dir.
    thickness   = base extent perpendicular to ridge_dir.
    height      = apex height above base_z.
    sweep       = how far the apex leans in -ridge_dir (tail-ward).
    embed       = how far below base_z the base quad is buried.
    """
    dx, dy = ridge_dir
    mag = max(math.sqrt(dx * dx + dy * dy), 1e-6)
    dx, dy = dx / mag, dy / mag
    # Perpendicular (90° CCW rotation of ridge direction)
    px, py = -dy, dx
    hl = length / 2
    ht = thickness / 2
    bz = base_z - embed

    def pt(sl, st, z):
        return [cx + sl * dx + st * px, cy + sl * dy + st * py, z]

    b0 = pt(-hl, -ht, bz)   # back-left
    b1 = pt(hl, -ht, bz)    # front-left
    b2 = pt(hl, ht, bz)     # front-right
    b3 = pt(-hl, ht, bz)    # back-right
    apex = [cx - sweep * dx, cy - sweep * dy, base_z + height]

    # Four side faces (outward-facing). Order: CCW viewed from outside.
    mb.add_tri(b0, b1, apex)
    mb.add_tri(b1, b2, apex)
    mb.add_tri(b2, b3, apex)
    mb.add_tri(b3, b0, apex)
    # Base quad facing down — embedded in the dome, but still include for
    # manifoldness in case a slicer inspects pre-union.
    mb.add_tri(b0, b2, b1)
    mb.add_tri(b0, b3, b2)


def hump1_outline():
    """Front hump — rounded dome, taller proportions than original.

    The reference's peaked "dragon back" look comes from dorsal spikes
    (phase 2), NOT from a peaked silhouette. Underlying shape stays a
    smooth rounded dome."""
    outline = [[-14, 0], [14, 0]]
    right = chain(([14, 0], [14, 3], [13, 8], [10, 13]))
    top = chain(([10, 13], [7, 18],  [3, 22],  [0, 22]),    # rounded dome top
                ([0, 22],  [-3, 22], [-7, 18], [-10, 13]))
    left = chain(([-10, 13], [-13, 8], [-14, 3], [-14, 0]))
    outline.extend(right[1:])
    outline.extend(top[1:])
    outline.extend(left[1:])
    return close_outline(outline)


def hump2_outline():
    """Rear hump — smaller rounded dome. Dorsal spikes come in phase 2."""
    outline = [[-11, 0], [11, 0]]
    right = chain(([11, 0], [11, 2], [10, 6], [8, 10]))
    top = chain(([8, 10], [6, 14],  [2, 17], [0, 17]),
                ([0, 17], [-2, 17], [-6, 14], [-8, 10]))
    left = chain(([-8, 10], [-10, 6], [-11, 2], [-11, 0]))
    outline.extend(right[1:])
    outline.extend(top[1:])
    outline.extend(left[1:])
    return close_outline(outline)


def tail_outline():
    """Tail — narrow stem curving up to a symmetric V-fluked fin.

    Silhouette reads like a whale-tail viewed from the side:
      - wide base (magnet fits comfortably)
      - narrow stem rising
      - two flukes fanning outward at the top with a V-notch between them
    """
    outline = [[-8, 0], [8, 0]]
    # Right side of stem: wide base → narrow neck rising
    right_stem = chain(([8, 0], [7, 3], [6, 8], [5, 14]),
                       ([5, 14], [4, 20], [4, 26], [6, 30]))
    # Right fluke: fanning outward + up, then curling back toward the valley
    right_fluke = chain(([6, 30], [10, 32], [14, 34], [16, 38]),
                        ([16, 38], [14, 40], [10, 39], [7, 37]))
    # V-notch valley between the two flukes (the dip in the middle of the tail)
    valley = chain(([7, 37],  [5, 35],  [2, 33],  [0, 33]),
                   ([0, 33],  [-2, 33], [-5, 35], [-7, 37]))
    # Left fluke: mirror of right
    left_fluke = chain(([-7, 37], [-10, 39], [-14, 40], [-16, 38]),
                       ([-16, 38], [-14, 34], [-10, 32], [-6, 30]))
    # Left side of stem: descending back to base
    left_stem = chain(([-6, 30], [-4, 26], [-4, 20], [-5, 14]),
                      ([-5, 14], [-6, 8],  [-7, 3],  [-8, 0]))
    outline.extend(right_stem[1:])
    outline.extend(right_fluke[1:])
    outline.extend(valley[1:])
    outline.extend(left_fluke[1:])
    outline.extend(left_stem[1:])
    return close_outline(outline)


# =============================================================================
# PREVIEW
# =============================================================================

def generate_preview(pieces_data):
    """Side-view preview + height cross-section."""
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))

    # Top: footprint view (same as before)
    ax = axes[0]
    ax.set_aspect('equal')
    ax.set_title('Nessie Fridge Magnets — Footprints (view from fridge)', fontsize=13, fontweight='bold')
    colors = ['#2E8B57', '#3CB371', '#2E8B57', '#3CB371']
    x_offsets = [0, 50, 100, 140]

    for idx, (label, outline, magnets, max_h) in enumerate(pieces_data):
        xo = x_offsets[idx]
        xs = [p[0] + xo for p in outline] + [outline[0][0] + xo]
        ys = [p[1] for p in outline] + [outline[0][1]]
        ax.fill(xs, ys, color=colors[idx], alpha=0.6, edgecolor='#1a5c38', linewidth=1.5)
        for mx, my in magnets:
            circle = plt.Circle((mx + xo, my), MAGNET_R, fill=False,
                                color='red', linewidth=1.5, linestyle='--')
            ax.add_patch(circle)
        cx = np.mean([p[0] for p in outline]) + xo
        ax.text(cx, -4, f'{label}\npeak: {max_h}mm', ha='center', va='top', fontsize=8, fontweight='bold')

    ax.axhline(y=0, color='#4169E1', linewidth=2, linestyle='-', alpha=0.5)
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')
    ax.grid(True, alpha=0.2)
    ax.set_xlim(-25, 200)
    ax.set_ylim(-10, 62)

    # Bottom: cross-section showing dome height
    ax2 = axes[1]
    ax2.set_title('Side View — How Far Each Piece Pops Out From Fridge', fontsize=13, fontweight='bold')
    for idx, (label, outline, magnets, max_h) in enumerate(pieces_data):
        grid_x, grid_y, hfield, hmask = compute_height_field(outline, max_h)
        # Take the y-slice at the tallest point
        max_row = np.argmax(hfield.max(axis=1))
        profile = hfield[max_row, :]
        valid = profile > 0
        xo = x_offsets[idx]
        ax2.fill_between(grid_x[valid] + xo, 0, profile[valid],
                         color=colors[idx], alpha=0.5, edgecolor='#1a5c38', linewidth=1.5)

    ax2.set_xlabel('mm')
    ax2.set_ylabel('Pop-out height (mm)')
    ax2.axhline(y=0, color='gray', linewidth=1)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim(-25, 200)

    path = os.path.join(OUTPUT_DIR, 'nessie_preview.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"\nPreview saved: {path}")
    plt.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Loch Ness Monster Fridge Magnet Generator v2")
    print("   (Rounded 3D pieces that pop out from fridge)")
    print("=" * 50)
    print()

    # Phase 1 (silhouettes + dome profile) only. Phase 2 (dorsal spikes)
    # and Phase 3 (head crown) are gated behind matching the blueprint's
    # silhouette first — do not re-add until head curl and hump dome look
    # right.
    pieces = [
        ("Head & Neck", head_outline(),  [[0, 6], [14, 40]], "nessie_head",  16, 1, EYE_POS, None),
        ("Hump 1",      hump1_outline(), [[0, 10]],  "nessie_hump1", 14, 1, None,    None),
        ("Hump 2",      hump2_outline(), [[0, 8]],   "nessie_hump2", 12, 1, None,    None),
        ("Tail",        tail_outline(),  [[0, 4]],   "nessie_tail",  13, 1, None,    None),
    ]
    # 2-slot palette: body green + eye black. All 4 pieces share slot 1 (green);
    # only the head's eye triangles use slot 2 (black) via paint_color.
    palette = ["#2E7D4E", "#0A0A0A"]  # green body, black eye

    import trimesh
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from multipart import ColoredModel

    preview_data = []
    colored = ColoredModel(palette=palette)
    for label, outline, magnets, stl_name, max_h, slot, eye, extras in pieces:
        print(f"Building: {label} (peak height: {max_h}mm, AMS slot {slot}"
              f"{', with eye' if eye else ''}"
              f"{', with spines/crown' if extras else ''})")
        _size, mb, eye_mb = build_rounded_piece(
            outline, magnets, max_h, stl_name, eye=eye, extras=extras,
        )
        # Main body mesh -> AMS slot 1 (green)
        body_mesh = trimesh.Trimesh(
            vertices=np.array(mb.verts),
            faces=np.array(mb.faces),
            process=False,
        )
        # Group name = stl_name, so head body + head eye share the "head" group
        # (they become ONE draggable unit in Bambu's plate view), but each
        # piece is its own group (independently draggable magnets).
        colored.add(stl_name, body_mesh, slot=slot, group=stl_name)
        if eye_mb is not None:
            eye_mesh = trimesh.Trimesh(
                vertices=np.array(eye_mb.verts),
                faces=np.array(eye_mb.faces),
                process=False,
            )
            # Same group as body -> moves with it as one object.
            colored.add(f"{stl_name}_eye", eye_mesh, slot=2, group=stl_name)
        preview_data.append((label, outline, magnets, max_h))
        print()

    combined_path = os.path.join(OUTPUT_DIR, "nessie_magnets_colored.3mf")
    colored.write(combined_path)
    print(f"Combined colored 3MF: {combined_path}")

    generate_preview(preview_data)

    print()
    print("=" * 50)
    print("Done! Print recommendations:")
    print("  - Print with FLAT BACK DOWN on build plate")
    print("  - 0.16-0.2mm layer height for smooth dome")
    print("  - Supports NOT needed (dome is self-supporting)")
    print("  - Drop 10x3mm magnets into back recesses")
    print("  - Superglue in place")
    print("  - PLA or PETG, any color (green recommended!)")
    print("=" * 50)
