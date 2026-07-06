"""Windowsill trough planter for California Giant zinnia seedlings — reeded style.

Coordinate convention:
  X = length, along the sill (centered on 0)
  Y = depth: window edge at y=0 (stays VERTICAL), room edge flares +Y
  Z = height, base at z=0, prints base-down

Styling: WIDE REEDS — raised rounded vertical columns baked into the loft
profile so they follow the wall taper. Reeds are raised (additive) so they
never thin the 3mm wall, hide FDM layer lines, and print support-free.

Sharp end flare (25mm/side, ~10.9 deg) per the requested tweak; window side
stays vertical so it sits flush against the sash (no reeds or rim poke toward
the window).
"""
import math
from build123d import (
    Align, Axis, Box, Circle, Cylinder, Plane, Pos, Rectangle,
    chamfer, export_stl, loft,
)

# ---------------------------------------------------------------------------
# Planter parameters (mm)
# ---------------------------------------------------------------------------
BASE_LEN   = 190.0   # X, along sill (sized so reeded top fits the P1S bed)
BASE_WID   = 100.0   # Y, window->room
HEIGHT     = 130.0
ROOM_FLARE = 20.0    # room side juts outward this much at top; window side vertical
END_FLARE  = 25.0    # each X end flares outward this much at top (sharper)
WALL       = 3.0
FLOOR      = 4.0

# Reeds (raised rounded columns)
REED_R       = 5.0   # column radius -> protrudes ~5mm from the wall
REED_N_LONG  = 9     # reeds per long face (window / room)
REED_N_SHORT = 5     # reeds per end face

# Drainage
HOLE_DIA  = 8.0
HOLE_COLS = 5
HOLE_ROWS = 2

BOTTOM_CHAM = 0.6    # fights elephant's foot

# Catch tray
TRAY_CLEAR  = 4.0
TRAY_WALL   = 3.0
TRAY_HEIGHT = 20.0
TRAY_FLOOR  = 3.0

EPS = 0.01


def rect_dims(z, inset=0.0):
    t = z / HEIGHT
    x_half = (BASE_LEN + 2 * END_FLARE * t) / 2
    x_min, x_max = -x_half + inset, x_half - inset
    y_min, y_max = 0.0 + inset, (BASE_WID + ROOM_FLARE * t) - inset
    return x_min, x_max, y_min, y_max


def reed_centers(xmin, xmax, ymin, ymax):
    pts = []
    for i in range(REED_N_LONG):
        f = (i + 0.5) / REED_N_LONG
        x = xmin + f * (xmax - xmin)
        pts.append((x, ymin))   # window face
        pts.append((x, ymax))   # room face
    for i in range(REED_N_SHORT):
        f = (i + 0.5) / REED_N_SHORT
        y = ymin + f * (ymax - ymin)
        pts.append((xmin, y))   # left end
        pts.append((xmax, y))   # right end
    return pts


def reeded_profile(z):
    xmin, xmax, ymin, ymax = rect_dims(z)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    sk = Pos(cx, cy) * Rectangle(xmax - xmin, ymax - ymin)
    for px, py in reed_centers(xmin, xmax, ymin, ymax):
        sk = sk + Pos(px, py) * Circle(REED_R)
    return Plane.XY.offset(z) * sk


def plain_profile(z, inset=0.0):
    xmin, xmax, ymin, ymax = rect_dims(z, inset)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    return Plane.XY.offset(z) * Pos(cx, cy) * Rectangle(xmax - xmin, ymax - ymin)


# ---------------------------------------------------------------------------
# Reeded outer shell minus plain inner cavity
# ---------------------------------------------------------------------------
shell = loft([reeded_profile(0), reeded_profile(HEIGHT)])
cavity = loft([plain_profile(FLOOR, inset=WALL), plain_profile(HEIGHT + EPS, inset=WALL)])
planter = shell - cavity

# ---------------------------------------------------------------------------
# Drainage holes through the floor
# ---------------------------------------------------------------------------
x_step = (BASE_LEN - 2 * WALL - HOLE_DIA) / (HOLE_COLS - 1)
y_step = (BASE_WID - 2 * WALL - HOLE_DIA) / (HOLE_ROWS - 1)
x_start = -(HOLE_COLS - 1) * x_step / 2
y_start = BASE_WID / 2 - (HOLE_ROWS - 1) * y_step / 2
for c in range(HOLE_COLS):
    for r in range(HOLE_ROWS):
        x = x_start + c * x_step
        y = y_start + r * y_step
        planter -= Pos(x, y, -EPS) * Cylinder(
            HOLE_DIA / 2, FLOOR + 2 * EPS,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

# Note: no model-level bottom chamfer on the reeded body — the reed arcs meet
# the floor in tangent edges OCCT can't chamfer cleanly. Enable "elephant foot
# compensation" in the slicer instead (Bambu Studio: ~0.15mm).

# ---------------------------------------------------------------------------
# Catch tray
# ---------------------------------------------------------------------------
TRAY_X = BASE_LEN + 2 * TRAY_CLEAR + 2 * TRAY_WALL
TRAY_Y = BASE_WID + 2 * TRAY_CLEAR + 2 * TRAY_WALL
tray = Box(TRAY_X, TRAY_Y, TRAY_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
tray -= Pos(0, 0, TRAY_FLOOR) * Box(
    TRAY_X - 2 * TRAY_WALL, TRAY_Y - 2 * TRAY_WALL, TRAY_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN))
tray = chamfer(tray.edges().group_by(Axis.Z)[0], BOTTOM_CHAM)

# ---------------------------------------------------------------------------
# Export + summary
# ---------------------------------------------------------------------------
export_stl(planter, "zinnia_planter.stl")
export_stl(tray, "zinnia_tray.stl")

pbb, tbb = planter.bounding_box(), tray.bounding_box()
print("=== Planter (reeded) ===")
print(f"  bbox: {pbb.size.X:.1f} x {pbb.size.Y:.1f} x {pbb.size.Z:.1f} mm")
print(f"  volume: {planter.volume / 1000:.1f} cm^3")
print(f"  end flare:  {math.degrees(math.atan(END_FLARE / HEIGHT)):.1f} deg")
print(f"  room flare: {math.degrees(math.atan(ROOM_FLARE / HEIGHT)):.1f} deg")
print(f"=== Tray === bbox {tbb.size.X:.1f} x {tbb.size.Y:.1f} x {tbb.size.Z:.1f} mm")
fits = pbb.size.X <= 256 and pbb.size.Y <= 256
print(f"Bed fit (P1S 256x256): widest {pbb.size.X:.0f} x {pbb.size.Y:.0f} mm -> {'OK' if fits else 'TOO BIG'}")
