"""Generate styled variants of the planter for visual comparison.

Each variant reuses the same flared trough body; only the wall surface /
profile treatment changes. Flutes are baked into the 2D loft profile so the
walls stay straight and the taper is followed automatically.
"""
import numpy as np
from build123d import (
    Align, Axis, Box, Circle, Plane, Polygon, Pos, Rectangle,
    export_stl, extrude, loft,
)

# --- shared body params (match build_planter.py) ---
BASE_LEN, BASE_WID, HEIGHT = 200.0, 100.0, 130.0
ROOM_FLARE, END_FLARE = 20.0, 25.0
WALL, FLOOR = 3.0, 4.0
EPS = 0.01


def rect_dims(z):
    t = z / HEIGHT
    x_half = (BASE_LEN + 2 * END_FLARE * t) / 2
    return -x_half, x_half, 0.0, BASE_WID + ROOM_FLARE * t


def edge_points(xmin, xmax, ymin, ymax, n_long, n_short):
    """Centers for flutes along all 4 edges (evenly spaced, off the corners)."""
    pts = []
    for i in range(n_long):
        f = (i + 0.5) / n_long
        x = xmin + f * (xmax - xmin)
        pts.append((x, ymin))   # window edge
        pts.append((x, ymax))   # room edge
    for i in range(n_short):
        f = (i + 0.5) / n_short
        y = ymin + f * (ymax - ymin)
        pts.append((xmin, y))   # left end
        pts.append((xmax, y))   # right end
    return pts


def body_profile(z, mode):
    xmin, xmax, ymin, ymax = rect_dims(z)
    w, d = xmax - xmin, ymax - ymin
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2

    if mode == "faceted":
        c = 20.0 * (1 if z == 0 else (BASE_LEN + 2 * END_FLARE) / BASE_LEN)
        c = 20.0  # constant chamfer; corners stay parallel up the loft
        pts = [
            (xmin + c, ymin), (xmax - c, ymin),
            (xmax, ymin + c), (xmax, ymax - c),
            (xmax - c, ymax), (xmin + c, ymax),
            (xmin, ymax - c), (xmin, ymin + c),
        ]
        sk = Polygon(*pts, align=None)
        return Plane.XY.offset(z) * sk

    sk = Pos(cx, cy) * Rectangle(w, d)
    if mode == "plain":
        return Plane.XY.offset(z) * sk

    if mode == "grooves":
        r, n_long, n_short, sign = 2.1, 24, 11, -1
    elif mode == "ribs":
        r, n_long, n_short, sign = 2.3, 24, 11, +1
    elif mode == "reeds":
        r, n_long, n_short, sign = 5.0, 10, 5, +1
    else:
        return Plane.XY.offset(z) * sk

    for (px, py) in edge_points(xmin, xmax, ymin, ymax, n_long, n_short):
        c = Pos(px, py) * Circle(r)
        sk = sk + c if sign > 0 else sk - c
    return Plane.XY.offset(z) * sk


def cavity_solid():
    base = body_profile_plain(FLOOR, inset=WALL)
    top = body_profile_plain(HEIGHT + EPS, inset=WALL)
    return loft([base, top])


def body_profile_plain(z, inset=0.0):
    xmin, xmax, ymin, ymax = rect_dims(z)
    xmin += inset; xmax -= inset; ymin += inset; ymax -= inset
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    return Plane.XY.offset(z) * Pos(cx, cy) * Rectangle(xmax - xmin, ymax - ymin)


def top_rim():
    """Flat overhanging flange around the mouth."""
    xmin, xmax, ymin, ymax = rect_dims(HEIGHT)
    over = 4.0
    outer = Pos((xmin + xmax) / 2, (ymin + ymax) / 2) * Rectangle(
        (xmax - xmin) + 2 * over, (ymax - ymin) + 2 * over)
    # inner opening = cavity mouth
    ix0, ix1, iy0, iy1 = rect_dims(HEIGHT)
    ix0 += WALL; ix1 -= WALL; iy0 += WALL; iy1 -= WALL
    inner = Pos((ix0 + ix1) / 2, (iy0 + iy1) / 2) * Rectangle(ix1 - ix0, iy1 - iy0)
    ring = (Plane.XY.offset(HEIGHT) * outer) - (Plane.XY.offset(HEIGHT) * inner)
    return extrude(ring, -6.0)


def build(mode, rim=False):
    shell = loft([body_profile(0, mode), body_profile(HEIGHT, mode)])
    part = shell - cavity_solid()
    if rim:
        part = part + top_rim()
    return part


VARIANTS = [
    ("plain",   "Plain (current)",   False, "plain"),
    ("grooves", "Recessed grooves",  False, "grooves"),
    ("ribs",    "Raised ribs",       False, "ribs"),
    ("reeds",   "Wide reeds",        False, "reeds"),
    ("faceted", "Faceted",           False, "faceted"),
    ("rim",     "Grooves + top rim", True,  "grooves"),
]

for key, label, rim, mode in VARIANTS:
    try:
        part = build(mode, rim=rim)
        export_stl(part, f"variant_{key}.stl")
        bb = part.bounding_box()
        print(f"OK  {label:22s} bbox {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f}")
    except Exception as e:
        print(f"ERR {label:22s} -> {type(e).__name__}: {e}")
