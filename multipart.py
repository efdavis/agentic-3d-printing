"""
ColoredModel — thin facade over multi_object_3mf.write_multi_object_3mf.

The generator scripts in this project (nessie_magnets.py, mini_roborock_q8.py,
future ones) already know which triangles belong to which semantic part.
Instead of rendering the model then colorizing from images, use this facade
to label parts at generation time and emit a Bambu-trusted multi-object 3MF
with per-object AMS-slot assignments.

Usage:
    from multipart import ColoredModel
    m = ColoredModel(palette=["#2E2E2E","#B5B5B5","#1F7A4C","#8B4513"])
    m.add("head",    head_mesh,    slot=1)
    m.add("body",    body_mesh,    slot=2)
    m.add("magnets", magnet_mesh,  slot=3)
    m.write("nessie.3mf")

Each part must be a trimesh.Trimesh (or anything with .vertices / .faces
ndarrays). Slots are 1-based (match Bambu Studio AMS UI).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing multi_object_3mf from maxs_dagger/ without installing anything
_HERE = Path(__file__).resolve().parent
_MAXS_DAGGER = _HERE / "maxs_dagger"
if str(_MAXS_DAGGER) not in sys.path:
    sys.path.insert(0, str(_MAXS_DAGGER))

import numpy as np  # noqa: E402
from multi_object_3mf import write_multi_object_3mf  # noqa: E402


DEFAULT_TEMPLATE_DIR = _MAXS_DAGGER / "templates"


class ColoredModel:
    """Accumulate named parts + slot assignments, then write a colored 3MF.

    Two granularities of color:
      - Per-object (base case): `add(name, mesh, slot=N)` — entire mesh is slot N.
      - Per-triangle (painted regions): `add(name, mesh, slot=N, paint={slot: face_indices})`
        — the part's base color is slot N, but specific triangles get painted
        with a different slot via Bambu's paint_color bitstream. Useful for
        adding small accents ("black eye on a green head") without splitting
        the mesh into separate objects.
    """

    def __init__(self, palette: list[str], template_dir: str | Path | None = None):
        """
        palette: list of hex color strings ("#RRGGBB") — one per AMS slot used.
                 Must have at least max(slot) entries.
        template_dir: overrides default template location (for tests).
        """
        if not palette:
            raise ValueError("palette must have at least one color")
        self.palette = [_normalize_hex(c) for c in palette]
        self.template_dir = Path(template_dir) if template_dir else DEFAULT_TEMPLATE_DIR
        self._parts: dict[str, object] = {}
        self._slots: dict[str, int] = {}
        self._paint: dict[str, np.ndarray] = {}
        self._group: dict[str, str] = {}

    def add(self, name: str, mesh, slot: int,
            paint: "dict[int, object] | None" = None,
            group: "str | None" = None) -> "ColoredModel":
        """Register a named part.

        slot: 1-based AMS slot for the part's base color.
        paint: optional dict mapping {slot_N: face_indices} for per-triangle
               painted accents. NOTE: paint_color only renders in Bambu's
               Color Painting tool, not the default Prepare view — prefer
               splitting into separate parts + group= for visible-on-load
               colors.
        group: optional group name. Parts with the same `group` bundle
               together in Bambu as a single draggable object (useful when
               e.g. a head's body + eye should move as one unit even though
               they're separate parts with different slots). Default
               (None) = each part is its own group.

        Example — 4 Nessie pieces, head has body + eye that move together:
            (m.add("head_body", head_mesh, slot=1, group="head")
              .add("head_eye", eye_mesh,  slot=2, group="head")
              .add("hump1",    hump1_mesh, slot=1)
              .add("tail",     tail_mesh,  slot=1))
        """
        if name in self._parts:
            raise ValueError(f"part {name!r} already added")
        if slot < 1 or slot > len(self.palette):
            raise ValueError(
                f"slot {slot} out of range; palette has {len(self.palette)} colors "
                f"(slots 1..{len(self.palette)})"
            )
        if not hasattr(mesh, "vertices") or not hasattr(mesh, "faces"):
            raise TypeError(
                f"part {name!r}: expected trimesh.Trimesh-like object with "
                f".vertices and .faces"
            )

        nfaces = len(np.asarray(mesh.faces))
        face_slots = np.full(nfaces, slot, dtype=np.int32)
        if paint:
            for paint_slot, indices in paint.items():
                if paint_slot < 1 or paint_slot > len(self.palette):
                    raise ValueError(
                        f"paint slot {paint_slot} out of range "
                        f"(1..{len(self.palette)})"
                    )
                if isinstance(indices, slice):
                    face_slots[indices] = paint_slot
                else:
                    idx = np.asarray(list(indices), dtype=np.int64)
                    if idx.size:
                        if idx.min() < 0 or idx.max() >= nfaces:
                            raise ValueError(
                                f"paint[{paint_slot}] indices out of range "
                                f"[0, {nfaces})"
                            )
                        face_slots[idx] = paint_slot

        self._parts[name] = mesh
        self._slots[name] = slot
        if paint:
            self._paint[name] = face_slots
        if group is not None:
            self._group[name] = group
        return self

    def write(self, out_path: str | Path) -> None:
        """Emit the 3MF. Raises if no parts have been added."""
        if not self._parts:
            raise RuntimeError("no parts added; call .add() first")
        write_multi_object_3mf(
            out_path=out_path,
            parts=self._parts,
            slot_map=self._slots,
            palette_hex=self.palette,
            template_dir=self.template_dir,
            paint_map=self._paint or None,
            group_map=self._group or None,
        )

    def __repr__(self) -> str:
        parts_desc = ", ".join(
            f"{n}(slot={self._slots[n]})" for n in self._parts
        )
        return f"ColoredModel(palette={self.palette}, parts=[{parts_desc}])"


def _normalize_hex(c: str) -> str:
    """Accept '#RRGGBB' or 'RRGGBB', return '#RRGGBB' uppercase."""
    s = c.strip().lstrip("#")
    if len(s) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in s):
        raise ValueError(f"invalid hex color: {c!r}")
    return "#" + s.upper()
