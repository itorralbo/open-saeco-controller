"""Apply the versioned, per-part placement audit without network access.

Angles/bottom handling follow Bouni/kicad-jlcpcb-tools. Offsets are measured
from the KiCad anchor in canonical top-view X-right/Y-up axes. They align the
numbered pads with the public vendor model, rather than including NPTH locating
posts in a generic bounding box. No generic package-name rule is applied.
"""
import hashlib
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT/'hardware/assembly/placement-audit.json'
RESOLVED = {'geometry_match', 'datasheet_checked'}


def board_digest(board):
    """Ignore checkout CRLF/LF conversion, but no other board changes."""
    return hashlib.sha256(board.read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def transform(native, correction):
    if native['side'] not in ('top', 'bottom'):
        raise ValueError('Unknown board side')
    if not all(math.isfinite(v) for v in (native['x'], native['y'], native['angle'],
                                        correction['offset_x'], correction['offset_y'], correction['rotation'])):
        raise ValueError('Non-finite placement')
    angle = native['angle'] if native['side'] == 'top' else (180-native['angle']) % 360
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    dx, dy = correction['offset_x'], correction['offset_y']
    x, y = dx*c-dy*s, dx*s+dy*c
    if native['side'] == 'bottom':
        x = -x
    return (native['x']+x, native['y']+y, (angle+correction['rotation']) % 360)


def load_audit(board):
    report = json.loads(AUDIT.read_text(encoding='utf-8'))
    key = board.parent.parent.name
    if board_digest(board) != report['board_sha256'][key]:
        raise ValueError(f'{key}: PCB changed since placement audit; rerun audit_jlc_placements.py')
    records = {r['reference']: r for r in report['rows'] if r['board'] == key}
    if len(records) != sum(r['board'] == key for r in report['rows']):
        raise ValueError(f'{key}: duplicate audit reference')
    with (board.parent.parent/'bom-draft.csv').open(newline='', encoding='utf-8') as f:
        parts = list(csv.DictReader(f))
    if {p['reference'] for p in parts} != set(records):
        raise ValueError(f'{key}: BOM references changed since audit')
    for part in parts:
        if any(part[field] != records[part['reference']][field] for field in ('lcsc', 'mpn', 'footprint')):
            raise ValueError(f'{key}:{part["reference"]}: part changed since audit')
    return records


def corrected_placements(board, placements, *, allow_unverified=False):
    records = load_audit(board)
    pending = [p['Ref'] for p in placements if records[p['Ref']]['fit']['status'] not in RESOLVED]
    if pending and not allow_unverified:
        raise ValueError('Unresolved JLCPCB placements: '+', '.join(pending)+
                         '. See hardware/assembly/placement-audit.md. '
                         'Use --allow-unverified only to generate a separate review CPL.')
    result = []
    for p in placements:
        row = records[p['Ref']]
        n = row['native']
        if (abs(float(p['PosX'])-n['x']) > .0001 or abs(float(p['PosY'])-n['y']) > .0001
                or abs((float(p['Rot'])-n['angle']+180) % 360-180) > .001
                or p['Side'] != n['side']):
            raise ValueError(f'{p["Ref"]}: CLI placement does not match audited PCB')
        if row['fit']['status'] in RESOLVED:
            x, y, angle = transform(n, row['fit'])
            result.append({**p, 'PosX': x, 'PosY': y, 'Rot': angle})
        else:
            # Do not silently use a best-fit rotation for an incompatible part.
            result.append(dict(p))
    return result
