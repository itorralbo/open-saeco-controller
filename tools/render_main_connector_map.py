#!/usr/bin/env python3
"""Render the accepted main-board outline and connector placement as SVG."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'hardware/controller'
SOURCE = json.loads((BASE / 'mechanical-source.json').read_text())
OUT = BASE / 'validation/main-connector-map.svg'
S = 5
W = SOURCE['outline_mm']['width']
H = SOURCE['outline_mm']['height']


def rect(cx, cy, w, h, cls, label):
    x, y = (cx-w/2)*S, (cy-h/2)*S
    return (f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w*S:.1f}" '
            f'height="{h*S:.1f}" rx="3"/><text x="{cx*S:.1f}" y="{cy*S:.1f}" '
            f'class="label">{html.escape(label)}</text>')


parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 {W*S+60:.1f} {H*S+85:.1f}">
<style>
.board{{fill:#e7f2e7;stroke:#184d2c;stroke-width:2}} .hole{{fill:white;stroke:#184d2c;stroke-width:2}}
.active{{fill:#ffca6a;stroke:#874c00;stroke-width:1.5}} .reserved{{fill:#ffd9d9;stroke:#9d2525;stroke-width:1.5;stroke-dasharray:5 3}}
.label{{font:8px sans-serif;text-anchor:middle;dominant-baseline:middle;fill:#17202a}}
.note{{font:9px sans-serif;fill:#17202a}}
</style>
<rect class="board" x="0" y="0" width="{W*S:.1f}" height="{H*S:.1f}"/>''']

for hole in SOURCE['mounting_holes']:
    parts.append(f'<circle class="hole" cx="{hole["x"]*S:.1f}" cy="{hole["y"]*S:.1f}" r="{hole["diameter"]*S/2:.1f}"/>')
    parts.append(f'<text class="label" x="{hole["x"]*S+16:.1f}" y="{hole["y"]*S:.1f}">{hole["reference"]}</text>')

# Envelopes approximate the photographed housing, not copper pads.
active_sizes = {'JP21': (29, 11), 'JP16': (12.5, 23.5), 'JP14': (12.5, 8.5),
                'JP3': (16, 12.5), 'JP22': (9, 8.7), 'JP13': (8.5, 12.5), 'JP5': (11, 12.5)}
for item in SOURCE['connector_placements']:
    x, y = item['footprint_origin_mm']
    w, h = active_sizes[item['original_reference']]
    if item['rotation_deg'] in (90, 270) and item['original_reference'] not in ('JP21', 'JP16', 'JP14'):
        w, h = h, w
    # Hand-tuned body centers from KiCad footprint bounds at the stored rotation.
    offsets = {'JP21': (8.9, -0.8), 'JP16': (3.45, -8.75), 'JP14': (3.45, -1.25),
               'JP3': (5.0, 3.45), 'JP22': (2.0, 2.45), 'JP13': (1.25, 3.45), 'JP5': (2.5, 3.45)}
    dx, dy = offsets[item['original_reference']]
    parts.append(rect(x+dx, y+dy, w, h, 'active', f'{item["original_reference"]} / {item["new_reference"]}'))

for item in SOURCE['reserved_original_connector_envelopes']:
    parts.append(rect(*item['center_mm'], *item['size_mm'], 'reserved', item['original_reference']))

parts.append(f'<text class="note" x="0" y="{H*S+24:.1f}">Naranja: conector implementado y alineado. Rojo discontinuo: envolvente original reservada. Incertidumbre fotográfica ±{SOURCE["connector_position_uncertainty_mm"]:.1f} mm.</text>')
parts.append('</svg>\n')
OUT.write_text('\n'.join(parts))
print(OUT)
