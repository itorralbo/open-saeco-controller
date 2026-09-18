"""Render the photo-derived front-panel geometry as a 1:1 printable SVG.

Reads hardware/front-panel/mechanical-source.json and writes
hardware/front-panel/validation/mechanical-1to1.svg. Print at 100 % scale and
check the 100 mm bar before overlaying the drawing on the original PCB.
Plain Python; no KiCad required.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'hardware/front-panel'
SOURCE = json.loads((BASE/'mechanical-source.json').read_text())
OUT = BASE/'validation/mechanical-1to1.svg'
MARGIN = 10.0


def main():
    xs = [v[0] for v in SOURCE['outline_mm']['vertices']]
    ys = [v[1] for v in SOURCE['outline_mm']['vertices']]
    width, height = max(xs)+2*MARGIN, max(ys)+2*MARGIN+14
    parts = []
    add = parts.append
    points = ' '.join(f'{x:.2f},{y:.2f}' for x, y in SOURCE['outline_mm']['vertices'])
    add(f'<polygon points="{points}" fill="none" stroke="#000" stroke-width="0.15"/>')
    for hole in SOURCE['holes']:
        x, y, r = hole['x'], hole['y'], hole['diameter']/2
        add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#000" stroke-width="0.12"/>')
        add(f'<path d="M{x-1} {y}H{x+1}M{x} {y-1}V{y+1}" stroke="#000" stroke-width="0.08"/>')
        add(f'<text x="{x}" y="{y+r+2.2}" font-size="1.6" text-anchor="middle">'
            f'{hole["reference"]} Ø{hole["diameter"]} ({x}, {y})</text>')
    for pad in SOURCE['square_pads']:
        x, y, s = pad['x'], pad['y'], pad['size']
        add(f'<rect x="{x-s/2:.2f}" y="{y-s/2:.2f}" width="{s}" height="{s}" fill="none" '
            f'stroke="#060" stroke-width="0.12"/>')
        add(f'<text x="{x}" y="{y+s/2+2}" font-size="1.4" text-anchor="middle">{pad["reference"]} ({x}, {y})</text>')
    sw = SOURCE['switches']
    pitch, span = sw['leg_pitch_mm'], sw['pad_outer_span_mm']
    for pos in sw['positions']:
        x, y = pos['x'], pos['y']
        add(f'<rect x="{x-3}" y="{y-3}" width="6" height="6" fill="none" stroke="#a00" stroke-width="0.12"/>')
        add(f'<circle cx="{x}" cy="{y}" r="1.75" fill="none" stroke="#a00" stroke-width="0.08"/>')
        add(f'<path d="M{x-1.2} {y}H{x+1.2}M{x} {y-1.2}V{y+1.2}" stroke="#a00" stroke-width="0.08"/>')
        for sx in (-1, 1):
            for sy in (-1, 1):
                if pos['legs'] == 'top/bottom':
                    px, py = x+sx*pitch/2, y+sy*(span/2-0.9)
                    add(f'<rect x="{px-0.7:.2f}" y="{py-0.9:.2f}" width="1.4" height="1.8" '
                        f'fill="none" stroke="#a00" stroke-width="0.06"/>')
                else:
                    px, py = x+sx*(span/2-0.9), y+sy*pitch/2
                    add(f'<rect x="{px-0.9:.2f}" y="{py-0.7:.2f}" width="1.8" height="1.4" '
                        f'fill="none" stroke="#a00" stroke-width="0.06"/>')
        dy = -7.2 if pos['legs'] == 'top/bottom' else -4.4
        add(f'<text x="{x}" y="{y+dy}" font-size="1.4" text-anchor="middle">{pos["original"]} ({x}, {y})</text>')
    for led in SOURCE['indicators']:
        x, y = led['x'], led['y']
        add(f'<circle cx="{x}" cy="{y}" r="0.8" fill="none" stroke="#c60" stroke-width="0.1"/>')
        add(f'<text x="{x+1.4}" y="{y+0.5}" font-size="1.2">{led["original"]}</text>')
    jp3 = SOURCE['reference_only_mm']['JP3']
    add(f'<rect x="{jp3["x"][0]}" y="{jp3["y"][0]}" width="{jp3["x"][1]-jp3["x"][0]:.1f}" '
        f'height="{jp3["y"][1]-jp3["y"][0]:.1f}" fill="none" stroke="#888" stroke-width="0.1" '
        f'stroke-dasharray="0.8 0.6"/>')
    add(f'<text x="{sum(jp3["x"])/2}" y="{jp3["y"][1]+1.8}" font-size="1.3" text-anchor="middle" '
        f'fill="#666">JP3 (referencia, ±1 mm)</text>')
    base = max(ys)+6
    add(f'<path d="M0 {base}H100M0 {base-1}V{base+1}M100 {base-1}V{base+1}" stroke="#000" stroke-width="0.15"/>')
    add(f'<text x="50" y="{base+3}" font-size="1.8" text-anchor="middle">100 mm: comprobar escala al imprimir</text>')
    add(f'<text x="0" y="{base+6.5}" font-size="1.6">Frontal {SOURCE["board_reference"]["silkscreen"]} · '
        f'{SOURCE["status"]} · {SOURCE["source_date"]} · cotas ±{SOURCE["outline_mm"]["uncertainty"]} mm · '
        f'vista cara de componentes, origen arriba-izquierda</text>')
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}mm" height="{height:.1f}mm" '
           f'viewBox="{-MARGIN} {-MARGIN} {width:.1f} {height:.1f}" font-family="sans-serif">\n'
           f'<rect x="{-MARGIN}" y="{-MARGIN}" width="{width:.1f}" height="{height:.1f}" fill="#fff"/>\n'
           + '\n'.join(parts) + '\n</svg>\n')
    OUT.write_text(svg, encoding='utf-8')
    print(f'Wrote {OUT.relative_to(ROOT)} ({width:.1f} x {height:.1f} mm)')


if __name__ == '__main__':
    main()
