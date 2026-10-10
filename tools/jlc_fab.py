"""Shared steps of the JLCPCB fabrication and assembly exports.

Gerbers + Excellon drill (zipped) with a drill map, BOM (Comment, Designator,
Footprint, LCSC Part #) and CPL (Designator, Mid X, Mid Y, Layer, Rotation)
following the JLCPCB help pages for KiCad. Plain Python; needs kicad-cli
(KICAD_CLI or PATH, as validate_kicad.py). CPL corrections require the versioned
per-part audit; unresolved parts can only be exported to a review CPL.
"""
import csv
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from validate_kicad import ROOT, cli_path
from jlc_placement_corrections import RESOLVED, corrected_placements, load_audit, transform

STOCK = {p['lcsc']: p for p in json.loads(
    (ROOT/'hardware/assembly/parts-catalog.json').read_text())['parts'].values()
    if p.get('lcsc')}


def out_of_stock(part):
    """Why JLCPCB cannot place `part` for lack of stock, or None.

    Reads the stock seen at the last tools/refresh_jlc_stock.py run.
    """
    seen = STOCK.get(part['lcsc'])
    if seen and not seen['stock_observed']:
        return (f"Sin stock en JLCPCB el {seen['stock_checked_on']}: "
                'comprar aparte y soldar a mano o aportar')
    return None


def run(*args):
    subprocess.run([cli_path(), *args], check=True, capture_output=True, text=True)


def export_gerbers(board, layers, zip_path):
    """Zip the Gerbers and drill files of `board`; return how many files.

    Plated and non-plated holes go to separate Excellon files: in a merged
    file only comments say which holes are plated.
    """
    with tempfile.TemporaryDirectory() as tmp:
        gerbers = Path(tmp)
        run('pcb', 'export', 'gerbers', '--layers', layers, '--subtract-soldermask', '--no-x2',
            '--check-zones', '-o', str(gerbers), str(board))
        run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm',
            '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'alternate',
            '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2',
            '-o', str(gerbers)+'/', str(board))
        files = sorted(p for p in gerbers.iterdir() if p.is_file())
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in files:
                z.write(path, path.name)
    return len(files)


def positions(board):
    """Footprint placements of `board` as kicad-cli writes them (Ref, PosX, PosY, Rot, Side)."""
    with tempfile.TemporaryDirectory() as tmp:
        pos = Path(tmp)/'pos.csv'
        run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both',
            '-o', str(pos), str(board))
        with pos.open(newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))


def read_bom(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def ref_key(ref):
    return ref.rstrip('0123456789'), int(ref.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))


def write_bom(path, parts):
    """One line per part: passives by value, everything else by MPN. Returns the line count."""
    groups = {}
    for p in parts:
        comment = p['value'].split(' / ')[0] if p['reference'][0] in 'RC' else p['mpn']
        key = (comment, p['footprint'].split(':')[1], p['lcsc'])
        groups.setdefault(key, []).append(p['reference'])
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (comment, footprint, lcsc), refs in sorted(groups.items(), key=lambda g: g[1][0]):
            w.writerow([comment, ','.join(sorted(refs, key=ref_key)), footprint, lcsc])
    return len(groups)


def write_not_assembled(path, parts, reasons):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Designator', 'Value', 'Manufacturer', 'MPN', 'Reason'])
        for p in sorted((p for p in parts if p['reference'] in reasons),
                        key=lambda p: ref_key(p['reference'])):
            w.writerow([p['reference'], p['value'], p['manufacturer'], p['mpn'],
                        reasons[p['reference']]])


def write_cpl(path, placements):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for p in sorted(placements, key=lambda p: p['Ref']):
            w.writerow([p['Ref'], f"{float(p['PosX']):.4f}mm", f"{float(p['PosY']):.4f}mm",
                        'Top' if p['Side'] == 'top' else 'Bottom', f"{float(p['Rot']) % 360:.1f}"])


def prepare_cpl(board, out, name, placements, allow_unverified=False):
    """Validate before exporting any files; choose a clearly marked review name."""
    rows = corrected_placements(board, placements, allow_unverified=allow_unverified)
    records = load_audit(board)
    pending = [p['Ref'] for p in placements if records[p['Ref']]['fit']['status'] not in RESOLVED]
    suffix = '-cpl-jlcpcb-review.csv' if pending else '-cpl-jlcpcb.csv'
    return out/f'{name}{suffix}', rows, pending


def check_package(out, name, refs):
    """Fail if the committed BOM or CPL in `out` does not place exactly `refs`.

    Catches a package left behind after a BOM change; it does not re-export.
    """
    with (out/f'{name}-bom-jlcpcb.csv').open(newline='', encoding='utf-8') as f:
        bom = [r for row in csv.DictReader(f) for r in row['Designator'].split(',')]
    board = out.parent/'kicad'/f'{name}.kicad_pcb'
    records = load_audit(board)
    pending = any(records[ref]['fit']['status'] not in RESOLVED for ref in refs)
    suffix = '-cpl-jlcpcb-review.csv' if pending else '-cpl-jlcpcb.csv'
    with (out/f'{name}{suffix}').open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        cpl = [row['Designator'] for row in rows]
    for label, found in (('BOM', bom), ('CPL', cpl)):
        assert len(found) == len(set(found)) and set(found) == set(refs), (
            f'{name} {label} is stale; re-run the fabrication export: '
            f'{sorted(set(found) ^ set(refs))}')
    for row in rows:
        record = records[row['Designator']]
        native, fit = record['native'], record['fit']
        expected = transform(native, fit) if fit['status'] in RESOLVED else (
            native['x'], native['y'], native['angle'] % 360)
        actual = (float(row['Mid X'].removesuffix('mm')), float(row['Mid Y'].removesuffix('mm')),
                  float(row['Rotation']))
        assert all(abs(a-b) <= .0001 for a, b in zip(actual, expected)), (
            f'{name}:{row["Designator"]}: CPL differs from audited placement')
        assert row['Layer'].lower() == native['side']
    if pending:
        assert not (out/f'{name}-cpl-jlcpcb.csv').exists(), 'Remove obsolete, unaudited CPL'
