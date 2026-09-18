"""Export the JLCPCB fabrication and assembly package of the front panel.

Writes hardware/front-panel/fabrication/: Gerbers + Excellon drill (zipped), a
drill map, BOM (Comment, Designator, Footprint, LCSC Part #) and CPL (Designator,
Mid X, Mid Y, Layer, Rotation) following the JLCPCB help pages for KiCad.
Plain Python; needs kicad-cli (KICAD_CLI or PATH, as validate_kicad.py).
Rotations are KiCad's: check orientation and polarity in the JLCPCB preview.
"""
import csv
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from validate_kicad import ROOT, cli_path

BASE = ROOT/'hardware/front-panel'
BOARD = BASE/'kicad/front-panel-reva.kicad_pcb'
OUT = BASE/'fabrication'
NAME = 'front-panel-reva'
LAYERS = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'


def run(*args):
    subprocess.run([cli_path(), *args], check=True, capture_output=True, text=True)


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        gerbers = Path(tmp)/'gerbers'
        gerbers.mkdir()
        run('pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask', '--no-x2',
            '--check-zones', '-o', str(gerbers), str(BOARD))
        run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm',
            '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'alternate',
            '--generate-map', '--map-format', 'gerberx2', '-o', str(gerbers)+'/', str(BOARD))
        files = sorted(p for p in gerbers.iterdir() if p.is_file())
        with zipfile.ZipFile(OUT/f'{NAME}-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for path in files:
                z.write(path, path.name)
        pos = Path(tmp)/'pos.csv'
        run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both',
            '-o', str(pos), str(BOARD))
        with pos.open(newline='', encoding='utf-8') as f:
            placements = list(csv.DictReader(f))

    with (BASE/'bom-draft.csv').open(newline='', encoding='utf-8') as f:
        parts = list(csv.DictReader(f))
    assert all(p['lcsc'] for p in parts), 'Every position needs an LCSC code'
    placed = {p['Ref'] for p in placements}
    assert placed == {p['reference'] for p in parts}, sorted(placed ^ {p['reference'] for p in parts})

    groups = {}
    for p in parts:
        # Passives by value, everything else by MPN (seven identical switches, one line).
        comment = p['value'].split(' / ')[0] if p['reference'][0] in 'RC' else p['mpn']
        key = (comment, p['footprint'].split(':')[1], p['lcsc'])
        groups.setdefault(key, []).append(p['reference'])
    with (OUT/f'{NAME}-bom-jlcpcb.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (comment, footprint, lcsc), refs in sorted(groups.items(), key=lambda g: g[1][0]):
            w.writerow([comment, ','.join(sorted(refs, key=lambda r: (r.rstrip('0123456789'), int(r.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))))),
                        footprint, lcsc])
    with (OUT/f'{NAME}-cpl-jlcpcb.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for p in sorted(placements, key=lambda p: p['Ref']):
            w.writerow([p['Ref'], f"{float(p['PosX']):.4f}mm", f"{float(p['PosY']):.4f}mm",
                        'Top' if p['Side'] == 'top' else 'Bottom', f"{float(p['Rot']) % 360:.1f}"])
    print(f'{NAME}: {len(files)} Gerber/drill files zipped; BOM {len(groups)} lines / '
          f'{len(parts)} positions; CPL {len(placements)} placements.')


if __name__ == '__main__':
    main()
