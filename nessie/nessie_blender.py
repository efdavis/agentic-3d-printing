"""
Nessie Fridge Magnets — Blender-sourced edition.

Geometry pipeline:
  1. Blender (driven by mcp__blender__execute_blender_code) builds a uniform-radius
     bezier-tube serpent, cuts it at the waterline (z=0), separates into 4 loose
     pieces, leans head forward and tail back via Z-shear, exports 4 STLs here.
  2. This script loads those 4 STLs with trimesh and feeds them into ColoredModel
     to emit a Bambu-trusted multi-object 3MF (same proven export pipeline as the
     legacy numpy generator used).

Run after (re)exporting STLs from Blender:
    maxs_dagger/.venv/bin/python nessie_blender.py
"""

from pathlib import Path

import trimesh

from multipart import ColoredModel

HERE = Path(__file__).resolve().parent

PIECES = ["head", "hump1", "hump2", "tail"]

PALETTE = ["#2E7D4E", "#0A0A0A"]  # green body, black eye


def main() -> None:
    m = ColoredModel(palette=PALETTE)

    head_mesh = trimesh.load(HERE / "nessie_head.stl", force="mesh")
    m.add("head_body", head_mesh, slot=1, group="head")
    print(f"  head_body: {len(head_mesh.vertices):>6} verts, {len(head_mesh.faces):>6} faces")

    for side in ("R", "L"):
        eye_mesh = trimesh.load(HERE / f"nessie_head_eye_{side}.stl", force="mesh")
        m.add(f"head_eye_{side}", eye_mesh, slot=2, group="head")
        print(f"  head_eye_{side}: {len(eye_mesh.vertices):>6} verts, {len(eye_mesh.faces):>6} faces")

    for piece in ("hump1", "hump2", "tail"):
        mesh = trimesh.load(HERE / f"nessie_{piece}.stl", force="mesh")
        m.add(piece, mesh, slot=1)
        print(f"  {piece:>9}: {len(mesh.vertices):>6} verts, {len(mesh.faces):>6} faces")

    out = HERE / "nessie_magnets_colored.3mf"
    m.write(out)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
