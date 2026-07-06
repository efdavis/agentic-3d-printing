# CAD Patterns Reference

Copy-paste-ready code patterns for common 3D printing operations. Organized by task — each section shows how to accomplish the same thing across supported tools.

---

## 1. Basic Primitives

### build123d

```python
from build123d import *

box = Box(60, 40, 10)                    # centered at origin
cyl = Cylinder(radius=5, height=20)      # centered, along Z
sph = Sphere(radius=10)
cone = Cone(bottom_radius=10, top_radius=0, height=20)
```

### CadQuery

```python
import cadquery as cq

box = cq.Workplane("XY").box(60, 40, 10)
cyl = cq.Workplane("XY").cylinder(20, 5)
sph = cq.Workplane("XY").sphere(10)
```

### numpy-stl

```python
from stl import mesh
import numpy as np

# Box from 12 triangles (6 faces x 2 triangles each)
def make_box(lx, ly, lz):
    vertices = np.array([
        [0,0,0],[lx,0,0],[lx,ly,0],[0,ly,0],
        [0,0,lz],[lx,0,lz],[lx,ly,lz],[0,ly,lz]
    ])
    faces = np.array([
        [0,3,1],[1,3,2],  # bottom
        [0,4,7],[0,7,3],  # left
        [4,5,6],[4,6,7],  # top
        [5,1,2],[5,2,6],  # right
        [2,3,6],[3,7,6],  # back
        [0,1,5],[0,5,4],  # front
    ])
    box = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            box.vectors[i][j] = vertices[f[j],:]
    return box
```

---

## 2. Boolean Operations

### build123d (algebra mode)

```python
from build123d import *

# Difference (cut)
result = Box(60, 40, 10) - Pos(0, 0, 0) * Cylinder(5, 10)

# Union (join)
result = Box(60, 40, 10) + Pos(0, 0, 15) * Box(20, 20, 10)

# Intersection
result = Box(60, 40, 10) & Cylinder(25, 10)
```

### build123d (builder mode)

```python
from build123d import *

with BuildPart() as part:
    Box(60, 40, 10)
    with Locations((0, 0, 0)):
        Cylinder(5, 10, mode=Mode.SUBTRACT)
result = part.part
```

### CadQuery

```python
import cadquery as cq

# Box with a hole
result = (
    cq.Workplane("XY")
    .box(60, 40, 10)
    .faces(">Z")
    .workplane()
    .hole(10)  # diameter, not radius
)

# Union
box1 = cq.Workplane("XY").box(60, 40, 10)
box2 = cq.Workplane("XY").transformed(offset=(0, 0, 15)).box(20, 20, 10)
result = box1.union(box2)

# Cut
result = box1.cut(box2)
```

### numpy-stl

**Cannot do boolean operations.** Use build123d or CadQuery instead. If forced to use numpy-stl, you must manually construct the final geometry without any cuts or unions.

---

## 3. Fillets and Chamfers

### build123d

```python
from build123d import *

with BuildPart() as part:
    Box(60, 40, 10)
    fillet(part.edges().filter_by(Axis.Z), radius=2)    # round vertical edges
    chamfer(part.edges().filter_by(Axis.Z), length=1)   # bevel vertical edges
result = part.part
```

### CadQuery

```python
import cadquery as cq

# Fillet all edges
result = cq.Workplane("XY").box(60, 40, 10).edges().fillet(2)

# Fillet only top edges
result = cq.Workplane("XY").box(60, 40, 10).edges("|Z").fillet(2)

# Chamfer
result = cq.Workplane("XY").box(60, 40, 10).edges().chamfer(1)
```

### numpy-stl

**Cannot do fillets or chamfers.** These require modifying edge topology, which raw triangle meshes don't support well. Use a CAD kernel.

---

## 4. Shell / Hollow (Thin-Walled Enclosures)

### build123d

```python
from build123d import *

with BuildPart() as part:
    Box(60, 40, 30)
    # Remove top face, hollow to 2mm wall thickness
    shell(part.faces().sort_by(Axis.Z)[-1:], thickness=-2)
result = part.part
```

### CadQuery

```python
import cadquery as cq

# Shell: remove top face, 2mm walls
result = (
    cq.Workplane("XY")
    .box(60, 40, 30)
    .faces(">Z")
    .shell(-2)
)
```

### numpy-stl

Manual approach: create outer box and inner box, then construct the six outer faces and six inner faces (with reversed normals), plus the rim faces connecting inner to outer at the open top. Very tedious and error-prone — use a CAD kernel.

---

## 5. Holes

### build123d

```python
from build123d import *

with BuildPart() as part:
    Box(60, 40, 10)
    # Through hole
    with Locations((10, 0, 0)):
        Cylinder(3, 10, mode=Mode.SUBTRACT)
    # Counterbore hole
    with Locations((-10, 0, 0)):
        CounterBoreHole(radius=2, counter_bore_radius=4, counter_bore_depth=3, depth=10)
    # Countersink hole
    with Locations((0, 10, 0)):
        CounterSinkHole(radius=2, counter_sink_radius=4, depth=10)
result = part.part
```

### CadQuery

```python
import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(60, 40, 10)
    .faces(">Z")
    .workplane()
    # Simple through hole (diameter)
    .hole(6)
)

# Counterbore
result = (
    cq.Workplane("XY")
    .box(60, 40, 10)
    .faces(">Z")
    .workplane()
    .cboreHole(diameter=4, cboreDiameter=8, cboreDepth=3)
)

# Countersink
result = (
    cq.Workplane("XY")
    .box(60, 40, 10)
    .faces(">Z")
    .workplane()
    .cskHole(diameter=4, cskDiameter=8, cskAngle=82)
)
```

---

## 6. Extrude from 2D Sketch

### build123d

```python
from build123d import *

# L-shaped bracket from sketch
with BuildPart() as part:
    with BuildSketch() as sk:
        with BuildLine() as ln:
            Polyline([(0,0), (30,0), (30,5), (5,5), (5,20), (0,20)], close=True)
        make_face()
    extrude(amount=10)
result = part.part
```

### CadQuery

```python
import cadquery as cq

# L-shaped bracket from sketch
result = (
    cq.Workplane("XY")
    .polyline([(0,0), (30,0), (30,5), (5,5), (5,20), (0,20)])
    .close()
    .extrude(10)
)
```

### numpy-stl (simple extrusion only)

```python
def extrude_polygon(points_2d, z0, z1):
    """Extrude a closed 2D polygon into a solid prism.
    points_2d: list of [x,y] in CCW order.
    Only works for convex polygons or simple shapes where fan triangulation is valid.
    """
    all_triangles = []
    n = len(points_2d)

    # Walls
    for i in range(n):
        j = (i + 1) % n
        p0, p1 = points_2d[i], points_2d[j]
        # Two triangles per wall quad
        all_triangles.append([
            [p0[0], p0[1], z0], [p1[0], p1[1], z0], [p1[0], p1[1], z1]
        ])
        all_triangles.append([
            [p0[0], p0[1], z0], [p1[0], p1[1], z1], [p0[0], p0[1], z1]
        ])

    # Bottom face (fan, reversed winding for downward normal)
    for i in range(1, n - 1):
        all_triangles.append([
            [points_2d[0][0], points_2d[0][1], z0],
            [points_2d[i+1][0], points_2d[i+1][1], z0],
            [points_2d[i][0], points_2d[i][1], z0]
        ])

    # Top face (fan, normal winding for upward normal)
    for i in range(1, n - 1):
        all_triangles.append([
            [points_2d[0][0], points_2d[0][1], z1],
            [points_2d[i][0], points_2d[i][1], z1],
            [points_2d[i+1][0], points_2d[i+1][1], z1]
        ])

    m = mesh.Mesh(np.zeros(len(all_triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_triangles):
        for j in range(3):
            m.vectors[i][j] = tri[j]
    return m
```

---

## 7. Arrays and Patterns

### build123d

```python
from build123d import *

with BuildPart() as part:
    Box(100, 50, 5)
    # Grid of holes
    with GridLocations(x_spacing=15, y_spacing=15, x_count=5, y_count=3):
        Cylinder(3, 5, mode=Mode.SUBTRACT)
    # Circular pattern of posts
    with PolarLocations(radius=20, count=6):
        Cylinder(2, 10)
result = part.part
```

### CadQuery

```python
import cadquery as cq

# Grid of holes
result = (
    cq.Workplane("XY")
    .box(100, 50, 5)
    .faces(">Z")
    .workplane()
    .rarray(15, 15, 5, 3)  # xSpacing, ySpacing, xCount, yCount
    .hole(6)
)

# Circular pattern
result = (
    cq.Workplane("XY")
    .box(50, 50, 5)
    .faces(">Z")
    .workplane()
    .polarArray(radius=20, startAngle=0, angle=360, count=6)
    .hole(4)
)
```

---

## 8. Text and Labels

### build123d

```python
from build123d import *

with BuildPart() as part:
    Box(60, 20, 3)
    # Embossed text (raised)
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]) as sk:
        Text("HELLO", font_size=10, align=(Align.CENTER, Align.CENTER))
    extrude(amount=1)
result = part.part

# Debossed text (cut in)
with BuildPart() as part:
    Box(60, 20, 3)
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]) as sk:
        Text("HELLO", font_size=10, align=(Align.CENTER, Align.CENTER))
    extrude(amount=-1, mode=Mode.SUBTRACT)
result = part.part
```

### CadQuery

```python
import cadquery as cq

# Embossed text
result = (
    cq.Workplane("XY")
    .box(60, 20, 3)
    .faces(">Z")
    .workplane()
    .text("HELLO", fontsize=10, distance=1)  # distance > 0 = emboss
)

# Debossed text
result = (
    cq.Workplane("XY")
    .box(60, 20, 3)
    .faces(">Z")
    .workplane()
    .text("HELLO", fontsize=10, distance=-1, cut=True)
)
```

### numpy-stl

Text requires converting font outlines to polygons, then extruding each glyph. This is extremely complex to do manually. Use a CAD kernel.

---

## 9. Screw Bosses and Mounting

### build123d

```python
from build123d import *

# Screw boss: cylindrical post with a pilot hole for self-tapping screw
BOSS_OD = 8       # outer diameter
BOSS_HEIGHT = 10
PILOT_HOLE = 2.2  # for M3 self-tapping screw

with BuildPart() as part:
    # Base plate
    Box(50, 50, 3)
    # Screw bosses at corners
    with Locations((18, 18, 0), (-18, 18, 0), (-18, -18, 0), (18, -18, 0)):
        Cylinder(BOSS_OD / 2, BOSS_HEIGHT)
        Cylinder(PILOT_HOLE / 2, BOSS_HEIGHT, mode=Mode.SUBTRACT)
result = part.part
```

### CadQuery

```python
import cadquery as cq

BOSS_OD = 8
BOSS_HEIGHT = 10
PILOT_HOLE = 2.2

result = (
    cq.Workplane("XY")
    .box(50, 50, 3)
    .faces(">Z")
    .workplane()
    .pushPoints([(18, 18), (-18, 18), (-18, -18), (18, -18)])
    .circle(BOSS_OD / 2)
    .extrude(BOSS_HEIGHT)
    .faces(">Z")
    .workplane()
    .pushPoints([(18, 18), (-18, 18), (-18, -18), (18, -18)])
    .hole(PILOT_HOLE)
)
```

### Common Screw Pilot Hole Sizes (self-tapping in PLA)

| Screw | Pilot Hole Diameter |
|-------|-------------------|
| M2    | 1.5mm |
| M2.5  | 1.8mm |
| M3    | 2.2mm |
| M4    | 3.0mm |

---

## 10. Snap-Fit Features

### Cantilever Snap Clip (build123d)

```python
from build123d import *

# Simple cantilever clip on one face of a box
CLIP_LENGTH = 8
CLIP_WIDTH = 4
CLIP_THICKNESS = 1.2
HOOK_DEPTH = 0.8
HOOK_HEIGHT = 1.5

with BuildPart() as clip:
    # Beam
    with BuildSketch(Plane.XZ) as sk:
        Rectangle(CLIP_THICKNESS, CLIP_LENGTH)
    extrude(amount=CLIP_WIDTH)
    # Hook at the end
    with BuildSketch(Plane.XZ.offset(0)) as sk2:
        with Locations((CLIP_THICKNESS / 2 + HOOK_DEPTH / 2, CLIP_LENGTH / 2 - HOOK_HEIGHT / 2)):
            Rectangle(HOOK_DEPTH, HOOK_HEIGHT)
    extrude(amount=CLIP_WIDTH)
result = clip.part
```

**Design rules for snap-fits in PLA:**
- Beam deflection should be < 2% of beam length
- Minimum beam thickness: 1.0mm
- Include a 45-degree lead-in ramp on the hook for easy insertion
- PETG and TPU tolerate more flex — increase deflection to 3–4%

---

## STL Export

### build123d

```python
from build123d import export_stl
export_stl(result, "output.stl")

# Get bounding box
bb = result.bounding_box()
print(f"Size: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"Volume: {result.volume / 1000:.1f} cm^3")
```

### CadQuery

```python
import cadquery as cq
cq.exporters.export(result, "output.stl")

# Get bounding box
bb = result.val().BoundingBox()
print(f"Size: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
```

### numpy-stl

```python
m.save("output.stl")

# Get bounding box
print(f"Size: {m.max_ - m.min_} mm")
```

---

## 11. Proven numpy-stl Primitives (Overlapping Geometry Approach)

These patterns were developed and tested for building detailed models by layering primitives on top of each other. Slicers auto-repair the overlaps. Use the shared `all_verts`/`all_faces` + `add_mesh()` assembly pattern from section 6.

### Spherical Cap Dome

```python
def add_dome(cx, cy, z_base, radius, rise, n_radial=96, n_rings=12):
    """Spherical cap on top of a cylinder. Connects at (radius, z_base),
    rises to (cx, cy, z_base + rise) at center."""
    if rise <= 0:
        add_disc(cx, cy, z_base, radius, normal_up=True)
        return
    R = (radius ** 2 + rise ** 2) / (2 * rise)  # sphere radius from chord + sagitta
    sphere_cz = z_base + rise - R
    rings = []
    for ring_i in range(n_rings + 1):
        t = ring_i / n_rings
        max_angle = math.asin(min(1.0, radius / R))
        angle = t * max_angle
        r = R * math.sin(angle)
        z = sphere_cz + R * math.cos(angle)
        ring_pts = circle_pts(cx, cy, r, n_radial)
        rings.append((ring_pts, z))
    # Top cap
    center = [cx, cy, rings[0][1]]
    for i in range(n_radial):
        j = (i + 1) % n_radial
        v = np.array([center, [rings[0][0][i][0], rings[0][0][i][1], rings[0][1]],
                      [rings[0][0][j][0], rings[0][0][j][1], rings[0][1]]])
        add_mesh(v, [[0, 1, 2]])
    # Ring bands
    for ri in range(len(rings) - 1):
        pu, zu = rings[ri]
        pl, zl = rings[ri + 1]
        for i in range(n_radial):
            j = (i + 1) % n_radial
            v = np.array([[pu[i][0],pu[i][1],zu],[pl[i][0],pl[i][1],zl],
                          [pl[j][0],pl[j][1],zl],[pu[j][0],pu[j][1],zu]])
            add_mesh(v, [[0, 1, 2], [0, 2, 3]])
```

Use for: body tops, turret caps, any gentle curved surface. The `rise` parameter controls curvature — larger rise = more pronounced dome.

### Groove Ring (Surface Detail)

```python
def add_groove_ring(cx, cy, z_mid, radius, depth, height, start_deg, end_deg, n=96):
    """Cut a groove into a cylindrical wall over an angular range.
    Creates a recessed band — use for seam lines, ring bands, vent slots."""
    half_h = height / 2
    z0, z1 = z_mid - half_h, z_mid + half_h
    r_inner = radius - depth
    start_rad, end_rad = math.radians(start_deg), math.radians(end_deg)
    arc = end_rad - start_rad
    n_arc = max(8, int(n * abs(arc) / (2 * math.pi)))
    for i in range(n_arc):
        a0 = start_rad + arc * i / n_arc
        a1 = start_rad + arc * (i + 1) / n_arc
        ox0, oy0 = cx + radius * math.cos(a0), cy + radius * math.sin(a0)
        ox1, oy1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
        ix0, iy0 = cx + r_inner * math.cos(a0), cy + r_inner * math.sin(a0)
        ix1, iy1 = cx + r_inner * math.cos(a1), cy + r_inner * math.sin(a1)
        # Top lip, bottom lip, inner wall
        for (pts, ff) in [
            ([[ox0,oy0,z1],[ox1,oy1,z1],[ix1,iy1,z1],[ix0,iy0,z1]], [[0,2,1],[0,3,2]]),
            ([[ox0,oy0,z0],[ox1,oy1,z0],[ix1,iy1,z0],[ix0,iy0,z0]], [[0,1,2],[0,2,3]]),
            ([[ix0,iy0,z0],[ix1,iy1,z0],[ix1,iy1,z1],[ix0,iy0,z1]], [[0,1,2],[0,2,3]])]:
            add_mesh(np.array(pts), ff)
```

Use for: seam lines between body sections, chrome ring bands on turrets, vent grille slots (repeat with small height and spacing), decorative grooves.

### Arc Lip (Bumper / Bezel Protrusion)

```python
def add_arc_lip(cx, cy, body_radius, lip_depth, z_bot, z_top, arc_start_deg, arc_end_deg, n=96):
    """A protruding lip around part of a cylinder — like a robot vacuum bumper.
    Extends outward from body_radius by lip_depth over the given arc."""
    r_lip = body_radius + lip_depth
    arc_span = arc_end_deg - arc_start_deg
    n_arc = max(16, int(n * arc_span / 360))
    for i in range(n_arc):
        a0 = math.radians(arc_start_deg + arc_span * i / n_arc)
        a1 = math.radians(arc_start_deg + arc_span * (i + 1) / n_arc)
        ix0, iy0 = body_radius * math.cos(a0), body_radius * math.sin(a0)
        ix1, iy1 = body_radius * math.cos(a1), body_radius * math.sin(a1)
        ox0, oy0 = r_lip * math.cos(a0), r_lip * math.sin(a0)
        ox1, oy1 = r_lip * math.cos(a1), r_lip * math.sin(a1)
        # Outer face
        v = np.array([[ox0,oy0,z_bot],[ox1,oy1,z_bot],[ox1,oy1,z_top],[ox0,oy0,z_top]])
        add_mesh(v, [[0,1,2],[0,2,3]])
        # Top face
        v = np.array([[ix0,iy0,z_top],[ix1,iy1,z_top],[ox1,oy1,z_top],[ox0,oy0,z_top]])
        add_mesh(v, [[0,1,2],[0,2,3]])
        # Bottom face
        v = np.array([[ix0,iy0,z_bot],[ix1,iy1,z_bot],[ox1,oy1,z_bot],[ox0,oy0,z_bot]])
        add_mesh(v, [[0,2,1],[0,3,2]])
    # End caps (vertical walls at arc terminations)
    for a_deg, winding in [(arc_start_deg, [[0,1,2],[0,2,3]]), (arc_end_deg, [[0,2,1],[0,3,2]])]:
        a = math.radians(a_deg)
        ix, iy = body_radius * math.cos(a), body_radius * math.sin(a)
        ox, oy = r_lip * math.cos(a), r_lip * math.sin(a)
        v = np.array([[ix,iy,z_bot],[ox,oy,z_bot],[ox,oy,z_top],[ix,iy,z_top]])
        add_mesh(v, winding)
```

Use for: bumpers, bezels, protruding rims, any feature that extends outward from a cylindrical body over part of its circumference.

### Bottom Chamfer Ring

```python
def add_bottom_chamfer(cx, cy, outer_radius, chamfer_size, n=96):
    """45-degree chamfer on the bottom edge. Prevents elephant's foot,
    gives a cleaner first layer. Bottom face is at z=0, chamfer ends at z=chamfer_size."""
    pts_outer = circle_pts(cx, cy, outer_radius, n)
    pts_inner = circle_pts(cx, cy, outer_radius - chamfer_size, n)
    # Bottom disc (smaller radius)
    add_disc(cx, cy, 0, outer_radius - chamfer_size, normal_up=False, n=n)
    # Angled chamfer surface
    for i in range(n):
        j = (i + 1) % n
        v = np.array([
            [pts_inner[i][0], pts_inner[i][1], 0],
            [pts_inner[j][0], pts_inner[j][1], 0],
            [pts_outer[j][0], pts_outer[j][1], chamfer_size],
            [pts_outer[i][0], pts_outer[i][1], chamfer_size]])
        add_mesh(v, [[0,1,2],[0,2,3]])
```

Use for: any model's bottom edge. Chamfer of 0.5–0.8mm eliminates elephant's foot artifacts on FDM prints.

### Flared Base (Turret/Post Transition)

```python
def add_flared_base(cx, cy, z_base, inner_radius, outer_radius, flare_height, n=96):
    """Angled transition from wider base to narrower cylinder above.
    Adds visual weight and structural strength at the base of turrets/posts."""
    pts_outer = circle_pts(cx, cy, outer_radius, n)
    pts_inner = circle_pts(cx, cy, inner_radius, n)
    add_disc(cx, cy, z_base, outer_radius, normal_up=False, n=n)
    for i in range(n):
        j = (i + 1) % n
        v = np.array([
            [pts_outer[i][0], pts_outer[i][1], z_base],
            [pts_outer[j][0], pts_outer[j][1], z_base],
            [pts_inner[j][0], pts_inner[j][1], z_base + flare_height],
            [pts_inner[i][0], pts_inner[i][1], z_base + flare_height]])
        add_mesh(v, [[0,1,2],[0,2,3]])
```

Use for: base of LiDAR turrets, mounting posts, any cylinder that should look like it grows out of a surface rather than sitting on top of it.

---

## build123d: Fluting / Reeding a Tapered Vessel (planters, vases, cups)

Bake the flutes into the **2D loft profile**, not as 3D boolean cuts on the
finished wall. The flutes then follow the wall taper automatically, the walls
stay straight (ruled between matching profiles), and it's one cheap loft instead
of dozens of slow 3D booleans on a slanted surface.

```python
from build123d import Plane, Pos, Rectangle, Circle, loft

def fluted_profile(z, dims_fn, r, n_long, n_short, raised=True):
    """dims_fn(z) -> (xmin, xmax, ymin, ymax) of the plain rect at height z."""
    xmin, xmax, ymin, ymax = dims_fn(z)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    sk = Pos(cx, cy) * Rectangle(xmax - xmin, ymax - ymin)
    pts = []
    for i in range(n_long):          # window + room faces
        x = xmin + (i + 0.5) / n_long * (xmax - xmin)
        pts += [(x, ymin), (x, ymax)]
    for i in range(n_short):         # end faces
        y = ymin + (i + 0.5) / n_short * (ymax - ymin)
        pts += [(xmin, y), (xmax, y)]
    for px, py in pts:               # circle centered ON the edge = half-round
        c = Pos(px, py) * Circle(r)
        sk = sk + c if raised else sk - c
    return Plane.XY.offset(z) * sk

shell = loft([fluted_profile(0, dims, ...), fluted_profile(H, dims, ...)])
```

- **Circle centered exactly on the edge** → a clean half-round column (raised reed)
  or scallop (recessed groove). `raised=True` adds material; `False` subtracts.
- **Reeds vs grooves:** raised reeds (r≈5, ~9–10 per long face) read boldest and
  hide FDM layer lines; recessed grooves (r≈2, ~24 per long face) are subtle/refined.
  **Keep recessed depth < wall thickness** or you breach the cavity — raised reeds
  have no such limit, so they're the safer bold choice.
- **Cavity stays plain:** loft an un-fluted inset profile for the interior and
  subtract. Constant wall thickness, flutes live only on the outside.
- **Same flute count + fractional positions at base and top** → ruled loft keeps
  walls straight. Spacing differs between base/top (different edge lengths); that's
  fine, just avoid overlap at the *narrower* base (check dia < base spacing).

**Gotcha — chamfer fails on fluted bottoms.** `chamfer(part.edges().group_by(Axis.Z)[0], ...)`
throws `BRep_API: command not done` when reed arcs meet the floor in tangent edges.
Don't model the elephant's-foot chamfer on a fluted body — use the slicer's
elephant-foot compensation (Bambu Studio ~0.15mm) instead. Plain-walled bodies
chamfer fine.

**Grading the finish:** matplotlib's flat per-face shading makes flutes look like
noise. Render in Blender headless (EEVEE Next) with a **raking side light** (low,
~80° tilt, off to one side) so the columns cast shadow lines — that's the only way
to judge flute depth/density by eye before printing. Use `shade_auto_smooth(~30°)`
so flat box faces stay flat while the half-round reeds smooth out.
