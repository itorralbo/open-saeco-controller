#!/usr/bin/env python3
"""Trace the owner's logo bitmap into a silkscreen outline.

Reads hardware/controller/silkscreen/bicho.png (black shape on white or
transparent) and writes bicho-outline.json next to it: one outer ring and its
holes, in millimetres, scaled to LOGO_WIDTH_MM and with the origin at the
top-left of the shape. silkscreen_controller_pcb.py places it on the board.

Needs Pillow, NumPy, scikit-image and Shapely (outside KiCad's Python):
    python3 -m pip install pillow numpy scikit-image shapely
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from skimage import measure

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'hardware/controller/silkscreen/bicho.png'
TARGET = ROOT / 'hardware/controller/silkscreen/bicho-outline.json'
LOGO_WIDTH_MM = 20.0
SIMPLIFY_PX = 1.5


def main():
    image = Image.open(SOURCE).convert('RGBA')
    rgba = np.asarray(image).astype(float) / 255.0
    darkness = (1.0 - rgba[..., :3].mean(axis=2)) * rgba[..., 3]
    mask = np.pad(darkness > 0.5, 2).astype(float)
    rings = [Polygon(np.fliplr(c)) for c in measure.find_contours(mask, 0.5)]
    rings = [r for r in rings if r.area > 100]
    rings.sort(key=lambda r: r.area, reverse=True)
    outer = rings[0]
    holes = [r for r in rings[1:] if outer.contains(r)]
    shape = Polygon(outer.exterior.coords, [h.exterior.coords for h in holes])
    shape = shape.simplify(SIMPLIFY_PX, preserve_topology=True)
    x0, y0, x1, _ = shape.bounds
    scale = LOGO_WIDTH_MM / (x1 - x0)

    def ring(coords):
        return [[round((x - x0) * scale, 3), round((y - y0) * scale, 3)] for x, y in coords]

    data = {
        'source': SOURCE.name,
        'width_mm': LOGO_WIDTH_MM,
        'height_mm': round((shape.bounds[3] - y0) * scale, 3),
        'outer': ring(shape.exterior.coords),
        'holes': [ring(h.coords) for h in shape.interiors],
    }
    TARGET.write_text(json.dumps(data, indent=1) + '\n')
    print(f"{TARGET.name}: {len(data['outer'])} points, {len(data['holes'])} hole(s), "
          f"{LOGO_WIDTH_MM} x {data['height_mm']} mm")


if __name__ == '__main__':
    main()
