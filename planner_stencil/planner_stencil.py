"""
Planner Stencil Generator
- Top row: square cutouts with rounded corners (for drawing checkboxes)
- Bottom row: water droplet cutouts
- Wide side padding for comfortable grip
"""

from stl import mesh
import numpy as np
import math

# === Stencil Parameters ===

# Square cutouts (top row)
SQUARE_SIZE = 6.0          # mm, inner dimension of each square
NUM_SQUARES = 11           # 7 original + 4 new
SQUARE_CORNER_R = 1.0      # mm, rounded corner radius on squares
SQUARE_GAP = 0.5           # mm, gap between adjacent squares

# Droplet cutouts (bottom row)
NUM_DROPLETS = 5           # same as original
DROPLET_CIRCLE_R = 2.41    # mm, radius of circular part
DROPLET_TIP_Y = 2.9        # mm, tip height above droplet reference center
DROPLET_CIRCLE_CY = -0.671 # mm, circle center Y offset from droplet reference
DROPLET_CX_OFFSET = 0.2    # mm, slight X offset of circle center
DROPLET_HEIGHT = 7.2        # mm, total height of droplet cutout (bottom circle to tip)

# Layout
SIDE_PADDING = 7.0         # mm, left/right padding for grip (was ~2.5mm)
TB_PADDING = 2.5           # mm, top/bottom padding
ROW_GAP = 3.0              # mm, vertical gap between square row and droplet row
THICKNESS = 1.0            # mm

# Resolution
CORNER_SEGMENTS = 8        # segments per rounded corner arc
CIRCLE_SEGMENTS = 48       # segments for droplet circle

# === Derived dimensions ===
content_width = NUM_SQUARES * SQUARE_SIZE + (NUM_SQUARES - 1) * SQUARE_GAP
total_width = content_width + 2 * SIDE_PADDING
total_height = 2 * TB_PADDING + SQUARE_SIZE + ROW_GAP + DROPLET_HEIGHT
# = 2*2.5 + 6 + 3 + 7.2 = 21.2mm... but original was 20mm

# Let's match original height: TB_PADDING=2.0 bottom, ROW_GAP=2.8
# Original: droplets Y=[2, 9.2] (7.2mm), squares Y=[11.5, 17.5] (6mm), total=20
# Bottom padding = 2.0, gap between rows = 11.5 - 9.2 = 2.3, top padding = 20 - 17.5 = 2.5
BOTTOM_PADDING = 2.0
TOP_PADDING = 2.5
ROW_GAP = 2.3

total_height = BOTTOM_PADDING + DROPLET_HEIGHT + ROW_GAP + SQUARE_SIZE + TOP_PADDING
# = 2 + 7.2 + 2.3 + 6 + 2.5 = 20mm

# Y positions
drop_y_bot = BOTTOM_PADDING                                    # 2.0
drop_y_top = drop_y_bot + DROPLET_HEIGHT                      # 9.2
sq_y_bot = drop_y_top + ROW_GAP                               # 11.5
sq_y_top = sq_y_bot + SQUARE_SIZE                              # 17.5


def rounded_rect_points(x0, y0, x1, y1, r, n_seg=8):
    """Generate CCW points for a rounded rectangle outline."""
    pts = []
    corners = [
        (x0 + r, y0 + r, math.pi, 1.5 * math.pi),
        (x1 - r, y0 + r, 1.5 * math.pi, 2 * math.pi),
        (x1 - r, y1 - r, 0, 0.5 * math.pi),
        (x0 + r, y1 - r, 0.5 * math.pi, math.pi),
    ]
    for cx, cy, a_start, a_end in corners:
        for i in range(n_seg + 1):
            a = a_start + (a_end - a_start) * i / n_seg
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return pts


def droplet_points(cx, cy_ref, n_circle=48):
    """Generate CCW points for a water droplet shape.
    cx: center X of droplet
    cy_ref: reference Y (bottom of droplet = cy_ref, tip at cy_ref + DROPLET_HEIGHT)

    Shape: circle at bottom with tangent lines meeting at a pointed tip above.
    """
    # Circle center in absolute coords
    circle_cx = cx + DROPLET_CX_OFFSET
    circle_cy = cy_ref + DROPLET_CIRCLE_R - DROPLET_CIRCLE_CY - (DROPLET_CIRCLE_R + DROPLET_CIRCLE_CY)
    # Recalculate: bottom of circle = cy_ref
    # circle center = cy_ref + DROPLET_CIRCLE_R + offset
    # From original: bottom of droplet at Y=2.0, circle center at Y=4.929
    # So circle_cy = cy_ref + (4.929 - 2.0) = cy_ref + 2.929
    circle_cy = cy_ref + (DROPLET_CIRCLE_R - DROPLET_CIRCLE_CY)
    # = cy_ref + 2.41 + 0.671 = cy_ref + 3.081...
    # But original circle center was at Y=4.929, bottom at 2.0, so offset = 2.929
    # DROPLET_CIRCLE_R = 2.41, bottom of circle = center - radius = 4.929 - 2.41 = 2.519
    # But droplet bottom is at Y=2.0... so the circle doesn't extend all the way down
    # The tangent lines from the tip to the circle define the bottom

    # Let me use the absolute geometry directly:
    # Original droplet: absolute center ref ≈ (5.0, 5.6) [midpoint of bounding box]
    # But the shape is defined by: circle at (5.0, 4.929) r=2.41, tip at (5.0, 8.5)
    # Bounding box bottom: Y=2.0, top: Y=9.2 (but tip is at 8.5, hmm)
    # Wait, the tip was at (0.200, 2.900) relative to (4.8, 5.6) = absolute (5.0, 8.5)
    # And the circle bottom = 4.929 - 2.41 = 2.519

    # The droplet outline from the original had points down to y=-3.112 relative
    # = absolute 5.6 - 3.112 = 2.488... close to circle bottom 2.519

    # So the shape is: full circle + tangent lines to tip
    # Let me recompute using cleaner parameters

    # Circle center (absolute)
    ccx = cx + DROPLET_CX_OFFSET  # slight X offset
    ccy = cy_ref + 2.929          # from original: center at 2.0 + 2.929 = 4.929

    # Tip position (absolute)
    tip_x = cx + DROPLET_CX_OFFSET
    tip_y = cy_ref + DROPLET_HEIGHT  # 2.0 + 7.2 = 9.2

    # Find tangent angle from tip to circle
    # Distance from tip to circle center
    d = tip_y - ccy  # = 9.2 - 4.929 = 4.271
    # Tangent angle: sin(alpha) = R/d
    alpha = math.asin(DROPLET_CIRCLE_R / d)

    # The circle arc goes from (270° + alpha) around the bottom to (270° - alpha)
    # (measuring from circle center, 0° = right, 90° = up)
    # Actually: tangent point angle from center = 90° ± alpha (towards tip which is above)
    # The tangent touches the circle at angle (90° + alpha) on the left side
    # and (90° - alpha) on the right side

    # Going CCW: start from right tangent point, go around the bottom, to left tangent point
    # Right tangent: angle = 90° - alpha (from positive X axis)
    # Left tangent: angle = 90° + alpha
    # We go CCW: from right tangent, down around bottom, to left tangent
    # = from (90° - alpha) going clockwise (decreasing angle) through 0°, -90°, -180° to (90° + alpha)
    # In CCW terms: from (90° + alpha) through 180°, 270°, 360° to (360° + 90° - alpha)

    start_angle = math.pi / 2 + alpha       # left tangent point
    end_angle = 2 * math.pi + math.pi / 2 - alpha  # right tangent point (going CCW all the way around bottom)

    pts = []
    # Tip point
    pts.append([tip_x, tip_y])

    # Left tangent line: from tip to left tangent point on circle
    # (the tangent point is automatically connected)

    # Circle arc from left tangent around bottom to right tangent (CCW)
    for i in range(n_circle + 1):
        a = start_angle + (end_angle - start_angle) * i / n_circle
        px = ccx + DROPLET_CIRCLE_R * math.cos(a)
        py = ccy + DROPLET_CIRCLE_R * math.sin(a)
        pts.append([px, py])

    # Right tangent line back to tip (automatically connected by closing the shape)
    return pts


def build_walls(outline_pts, z0, z1):
    """Build wall triangles for a cutout defined by outline points."""
    triangles = []
    n = len(outline_pts)
    for i in range(n):
        j = (i + 1) % n
        p0, p1 = outline_pts[i], outline_pts[j]
        triangles.append([
            [p0[0], p0[1], z0],
            [p1[0], p1[1], z0],
            [p1[0], p1[1], z1],
        ])
        triangles.append([
            [p0[0], p0[1], z0],
            [p1[0], p1[1], z1],
            [p0[0], p0[1], z1],
        ])
    return triangles


def build_outer_walls(w, h, z0, z1):
    """Build wall triangles for the outer rectangle edges."""
    triangles = []
    corners = [[0, 0], [w, 0], [w, h], [0, h]]
    for i in range(4):
        j = (i + 1) % 4
        p0, p1 = corners[i], corners[j]
        triangles.append([
            [p0[0], p0[1], z0],
            [p0[0], p0[1], z1],
            [p1[0], p1[1], z1],
        ])
        triangles.append([
            [p0[0], p0[1], z0],
            [p1[0], p1[1], z1],
            [p1[0], p1[1], z0],
        ])
    return triangles


def triangulate_face_with_holes(outer_pts, hole_outlines, z, flip=False):
    """Triangulate a face with holes using Delaunay + hole filtering."""
    from scipy.spatial import Delaunay
    from matplotlib.path import Path

    all_pts = list(outer_pts)
    hole_paths = []
    for hole in hole_outlines:
        hole_paths.append(Path(hole))
        all_pts.extend(hole)

    pts_2d = np.array(all_pts)
    tri = Delaunay(pts_2d)

    outer_path = Path(outer_pts)
    triangles = []
    for simplex in tri.simplices:
        centroid = pts_2d[simplex].mean(axis=0)
        if not outer_path.contains_point(centroid):
            continue
        inside_hole = any(hp.contains_point(centroid) for hp in hole_paths)
        if inside_hole:
            continue
        p0, p1, p2 = pts_2d[simplex[0]], pts_2d[simplex[1]], pts_2d[simplex[2]]
        if flip:
            triangles.append([[p0[0], p0[1], z], [p2[0], p2[1], z], [p1[0], p1[1], z]])
        else:
            triangles.append([[p0[0], p0[1], z], [p1[0], p1[1], z], [p2[0], p2[1], z]])
    return triangles


# === Build the stencil ===
all_triangles = []
all_hole_outlines = []

# --- Square cutouts (top row) ---
for i in range(NUM_SQUARES):
    x0 = SIDE_PADDING + i * (SQUARE_SIZE + SQUARE_GAP)
    x1 = x0 + SQUARE_SIZE
    outline = rounded_rect_points(x0, sq_y_bot, x1, sq_y_top,
                                   SQUARE_CORNER_R, CORNER_SEGMENTS)
    all_triangles.extend(build_walls(outline, 0, THICKNESS))
    all_hole_outlines.append(outline)

# --- Droplet cutouts (bottom row) ---
# Space droplets evenly across the content width
droplet_spacing = content_width / NUM_DROPLETS
for i in range(NUM_DROPLETS):
    cx = SIDE_PADDING + droplet_spacing * (i + 0.5) - DROPLET_CX_OFFSET
    outline = droplet_points(cx, drop_y_bot, CIRCLE_SEGMENTS)
    all_triangles.extend(build_walls(outline, 0, THICKNESS))
    all_hole_outlines.append(outline)

# --- Outer walls ---
all_triangles.extend(build_outer_walls(total_width, total_height, 0, THICKNESS))

# --- Top and bottom faces ---
# Generate outer boundary points with enough density
outer_pts = []
n_w = max(40, int(total_width))
n_h = max(20, int(total_height))
for x in np.linspace(0, total_width, n_w):
    outer_pts.append([x, 0])
for y in np.linspace(0, total_height, n_h):
    outer_pts.append([total_width, y])
for x in np.linspace(total_width, 0, n_w):
    outer_pts.append([x, total_height])
for y in np.linspace(total_height, 0, n_h):
    outer_pts.append([0, y])

# Top face
all_triangles.extend(triangulate_face_with_holes(outer_pts, all_hole_outlines,
                                                  THICKNESS, flip=False))
# Bottom face
all_triangles.extend(triangulate_face_with_holes(outer_pts, all_hole_outlines,
                                                  0, flip=True))

# === Create mesh ===
stencil = mesh.Mesh(np.zeros(len(all_triangles), dtype=mesh.Mesh.dtype))
for i, tri in enumerate(all_triangles):
    for j in range(3):
        stencil.vectors[i][j] = tri[j]

# === Export ===
output_file = "stencil.stl"
stencil.save(output_file)

# === Summary ===
print(f"Planner Stencil Generated: {output_file}")
print(f"  Dimensions: {total_width:.1f} x {total_height:.1f} x {THICKNESS:.1f} mm")
print(f"  Square cutouts: {NUM_SQUARES} (each {SQUARE_SIZE:.1f} x {SQUARE_SIZE:.1f} mm)")
print(f"  Droplet cutouts: {NUM_DROPLETS}")
print(f"  Side padding: {SIDE_PADDING:.1f} mm (for grip)")
print(f"  Content width: {content_width:.1f} mm")
print(f"  Triangles: {len(all_triangles)}")
