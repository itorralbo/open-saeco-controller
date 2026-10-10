"""Compare each board footprint with the public LCSC/EasyEDA numbered pads.

Run with KiCad's Python: audit_jlc_placements.py CACHE_DIRECTORY.
Only reads boards. Third-party SVGs stay in the scratch cache. The report is
geometric evidence, not approval of the order-specific JLCPCB assembly preview.
"""
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BOARDS = {'controller': 'controller-core-reva', 'front-panel': 'front-panel-reva'}
# Explicit electrical aliases, never inferred merely from similar pad locations.
PIN_ALIASES = {
    'C2689964': {'EP': 'SH'},  # USB shell tabs.
    'C2149727': {str(i): str((i+1)//2) for i in range(1, 9)},  # Two tails/tab.
    'C5169636': {str(i): str((i+1)//2) for i in range(1, 7)},
    'C575074': {'2': '1'},  # One conductive FASTON tab, two tails.
    'C83916': {'1': '1', '2': '1', '3': '2', '4': '2'},  # Switch terminals.
    # EasyEDA symbol: 3=+V,4=-V; our ACDC4: 3=-V,4=+V.
    'C6280124': {'3': '4', '4': '3'},
}
NOTES = {
    'C397236': 'BLOCKED: K701 holes span 20 mm; Omron G5RL-1A-E-HR requires 25 mm (20+5). Fix footprint/routing, not CPL. Source: https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5rl.pdf page 5.',
    'C5169636': 'REVIEW: paired tails differ by 2.5 mm with contact order preserved. Check TE drawing, locating post and harness pin 1; do not rotate to conceal a contact reversal.',
    'C142716': 'BLOCKED: BOM orders a leadless 0215002.MXP fuse, but PCB footprint is a pair of Littelfuse 111 clips. Clips are not separate BOM items. Resolve assembly BOM/mechanics.',
    'C142789': 'REVIEW: model lead pitch 25.50 mm versus PCB 27.50 mm; axial leads need forming. Confirm the assembly operation with JLCPCB.',
    'C178840': 'REVIEW: model is horizontal at 28 mm pitch, PCB is vertical at 5.08 mm. Requires lead forming/manual assembly; rotating a horizontal model cannot validate it.',
    'C2687402': 'DATASHEET CHECKED: KiCad pads 2.95 x 3.5 mm at +/-2.725 mm give 8.4 mm outer span and 2.5 mm gap, exactly the Bourns recommended layout. The public model uses different pad extensions. Center is unchanged; +180 degrees matches numbered pads (electrically equivalent for this inductor). Source: https://www.bourns.com/data/global/pdfs/SRP7028A.pdf page 1.',
    'C2838912': 'NO MODEL: public API has no PCB footprint. Nonpolarized 1206 fuse; retained original CPL, pending vendor preview.',
    'C49326334': 'NO MODEL: public API has no PCB footprint. Nonpolarized 0603 capacitor; retained original CPL, pending vendor preview.',
    'C6280124': 'Aliases verified by EasyEDA symbol (+V=3,-V=4) and Mean Well IRM-30-SPEC drawing 2026-04-03 page 4; local symbol uses +V=4,-V=3. Pad-envelope center is 10.5 mm from body origin.',
    'C83916': 'Switch has four physical tails but two electrical contacts; EasyEDA 1/2 map to local 1, 3/4 to local 2.',
    'C575074': 'Both tails belong to the same conductive FASTON tab. 90 and 270 degrees are electrically/geometrically equivalent; using 90.',
    'C2149727': 'Two tails per RAST contact: model 1/2->1,3/4->2,5/6->3,7/8->4. NPTH locating post must not shift the electrical pad center.',
    'C2689964': 'USB shell pad name EP in the vendor model corresponds to SH in KiCad.',
}


def rotate(x, y, degrees):
    """Counterclockwise rotation in an X-right/Y-up coordinate system."""
    a = math.radians(degrees)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def model_pads(path):
    raw = path.read_bytes()
    response = json.loads(raw)
    models = [m for m in response.get('result', []) if m.get('docType') == 4]
    if len(models) != 1:
        raise ValueError(f'Expected one PCB model, found {len(models)}')
    model = models[0]
    root = ET.fromstring(model['svg'])
    pads = []
    for node in root.iter():
        a = node.attrib
        if a.get('c_partid') != 'part_pad':
            continue
        x, y = (float(v) * .254 for v in a['c_origin'].split(','))
        w, h = float(a['c_width']) * .254, float(a['c_height']) * .254
        angle = float(a.get('c_rotation', 0))
        pads.append({'pin': a.get('number', ''), 'x': x, 'y': -y,
                     'w': w, 'h': h, 'angle': angle})
    if not pads:
        raise ValueError('Model has no pads')
    # Like Bouni, use the pad envelope, not the library anchor or silk/text.
    boxes = []
    for p in pads:
        c, s = abs(math.cos(math.radians(p['angle']))), abs(math.sin(math.radians(p['angle'])))
        ex, ey = (p['w'] * c + p['h'] * s) / 2, (p['w'] * s + p['h'] * c) / 2
        boxes.append((p['x'] - ex, p['y'] - ey, p['x'] + ex, p['y'] + ey))
    center = ((min(b[0] for b in boxes) + max(b[2] for b in boxes))/2,
              (min(b[1] for b in boxes) + max(b[3] for b in boxes))/2)
    for p in pads:
        p['x'] -= center[0]
        p['y'] -= center[1]
    return pads, {'url': f'https://easyeda.com/api/products/{path.stem.split("-")[0]}/svgs',
                  'model_uuid': model['component_uuid'], 'model_updated': model.get('updateTime'),
                  'response_sha256': hashlib.sha256(raw).hexdigest()}


def pin_centers(pads):
    groups = defaultdict(list)
    for p in pads:
        if p['pin']:
            groups[p['pin']].append((p['x'], p['y']))
    return {pin: (sum(p[0] for p in ps)/len(ps), sum(p[1] for p in ps)/len(ps))
            for pin, ps in groups.items()}


def fit(native, model, split_pins=()):
    """Compare all common numbered pad centers under four rigid rotations."""
    k, e = pin_centers(native), pin_centers(model)
    common = sorted(k.keys() & e.keys())
    count_mismatch = [pin for pin in common if pin not in split_pins and
                      sum(p['pin'] == pin for p in native) != sum(p['pin'] == pin for p in model)]
    if not common or (len(common) < 2 and len(native) < 2):
        return {'status': 'unresolved_pin_mapping', 'native_pins': sorted(k), 'model_pins': sorted(e)}
    trials = []
    for angle in (0, 90, 180, 270):
        rotated = {pin: rotate(*e[pin], angle) for pin in common}
        # Midrange avoids shifting SOT-23 bodies toward the side with more pins
        # merely because the two libraries use different solder-pad extensions.
        rotated_pads = [{**p, 'x': rotate(p['x'], p['y'], angle)[0],
                         'y': rotate(p['x'], p['y'], angle)[1]} for p in model]
        dx, dy = [((min(p[axis] for p in native) + max(p[axis] for p in native)) -
                   (min(p[axis] for p in rotated_pads) + max(p[axis] for p in rotated_pads)))/2
                  for axis in ('x', 'y')]
        residuals = []
        for pin in common:
            kp = [(p['x'], p['y']) for p in native if p['pin'] == pin]
            ep = [(p['x']+dx, p['y']+dy) for p in rotated_pads if p['pin'] == pin]
            if len(kp) == len(ep):
                # Check duplicate tails individually, not just their centroid.
                residuals.extend(min(math.dist(p, q) for q in ep) for p in kp)
                residuals.extend(min(math.dist(p, q) for q in kp) for p in ep)
            else:
                # A split thermal pad and a single copper pad may share a number.
                residuals.append(math.hypot(k[pin][0]-rotated[pin][0]-dx,
                                            k[pin][1]-rotated[pin][1]-dy))
        trials.append({'rotation': angle, 'offset_x': round(dx, 5), 'offset_y': round(dy, 5),
                       'max_error_mm': round(max(residuals), 5),
                       'rms_error_mm': round(math.sqrt(sum(r*r for r in residuals)/len(residuals)), 5)})
    trials.sort(key=lambda r: r['rms_error_mm'])
    best = trials[0]
    complete = k.keys() == e.keys() and not count_mismatch
    best.update({'status': 'geometry_match' if complete and best['max_error_mm'] <= .3
                 else 'review_geometry', 'matched_pins': common,
                 'native_only_pins': sorted(k.keys() - e.keys()),
                 'model_only_pins': sorted(e.keys() - k.keys()),
                 'pad_count_mismatch': count_mismatch,
                 'equivalent_rotations': [t['rotation'] for t in trials
                                         if abs(t['rms_error_mm']-best['rms_error_mm']) < .001],
                 'runner_up_error_mm': trials[1]['rms_error_mm']})
    return best


def board_footprints(path):
    import pcbnew as pcb
    board = pcb.LoadBoard(str(path))
    records = {}
    for fp in board.GetFootprints():
        origin = fp.GetPosition()
        angle = fp.GetOrientationDegrees()
        bottom = fp.GetLayer() == pcb.B_Cu
        pads = list(fp.Pads())
        bbox = pads[0].GetBoundingBox() if pads else None
        for pad in pads[1:]:
            bbox.Merge(pad.GetBoundingBox())
        center = bbox.GetCenter() if bbox else origin
        # Board coordinates are Y-down; audit offsets are Y-up.
        record = {'x': pcb.ToMM(origin.x), 'y': -pcb.ToMM(origin.y),
                  'angle': angle, 'side': 'bottom' if bottom else 'top',
                  'pad_center_x': pcb.ToMM(center.x), 'pad_center_y': -pcb.ToMM(center.y),
                  'footprint': str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName())}
        # Work on an unsaved in-memory board to recover canonical top geometry.
        if bottom:
            fp.Flip(origin, False)
        fp.SetOrientationDegrees(0)
        record['pads'] = [{'pin': p.GetNumber(),
                           'x': pcb.ToMM(p.GetPosition().x - origin.x),
                           'y': -pcb.ToMM(p.GetPosition().y - origin.y),
                           'w': pcb.ToMM(p.GetSize().x), 'h': pcb.ToMM(p.GetSize().y),
                           'angle': p.GetOrientationDegrees()}
                          for p in fp.Pads() if p.GetNumber()]
        records[fp.GetReference()] = record
    return records


def main():
    cache = Path(sys.argv[1])
    out = ROOT/'hardware/assembly/placement-audit.json'
    rows, board_hashes = [], {}
    for board, name in BOARDS.items():
        base = ROOT/'hardware'/board
        board_path = base/'kicad'/f'{name}.kicad_pcb'
        footprints = board_footprints(board_path)
        from jlc_placement_corrections import board_digest
        board_hashes[board] = board_digest(board_path)
        from export_controller_fab import not_assembled
        from jlc_fab import out_of_stock
        for part in csv.DictReader((base/'bom-draft.csv').open()):
            ref = part['reference']
            fp = footprints[ref]
            assert fp['footprint'] == part['footprint'], ref
            row = {'board': board, 'reference': ref, 'lcsc': part['lcsc'],
                   'mpn': part['mpn'], 'footprint': part['footprint'],
                   'assembled': not (not_assembled(part) if board == 'controller' else out_of_stock(part)),
                   'native': fp}
            row['note'] = NOTES.get(part['lcsc'], '')
            path = cache/f'{part["lcsc"]}-svg.json'
            if part['lcsc'] and path.is_file():
                row['source'] = {'url': f'https://easyeda.com/api/products/{part["lcsc"]}/svgs',
                                 'response_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            try:
                model, source = model_pads(path)
                row['source'] = source
                aliases = PIN_ALIASES.get(part['lcsc'], {})
                if aliases:
                    row['pin_aliases'] = aliases
                    model = [{**p, 'pin': aliases.get(p['pin'], p['pin'])} for p in model]
                split_pins = ('41',) if part['lcsc'] == 'C2980300' else ()
                row['fit'] = fit(fp['pads'], model, split_pins)
                if part['lcsc'] == 'C2687402' and part['footprint'] == 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm':
                    # Reviewed against the manufacturer's dimensioned land pattern,
                    # not a relaxed threshold for all parts of this package.
                    pads = fp['pads']
                    if (len(pads) == 2 and row['fit'].get('rotation') == 180
                            and all(abs(abs(p['x'])-2.725) < .001 and abs(p['y']) < .001
                                    and abs(p['w']-2.95) < .001 and abs(p['h']-3.5) < .001 for p in pads)):
                        row['fit'].update(status='datasheet_checked', offset_x=0, offset_y=0)
                        row['datasheet'] = 'https://www.bourns.com/data/global/pdfs/SRP7028A.pdf'
            except (OSError, ValueError, KeyError, TypeError) as error:
                row['fit'] = {'status': 'no_model', 'reason': str(error)}
            rows.append(row)
    report = {'checked_on': date.today().isoformat(), 'board_sha256': board_hashes,
              'source': 'JLCEDA/EasyEDA public library linked from JLCPCB part pages',
              'scope': 'Numbered pad-center alignment; assembly preview still requires verification', 'rows': rows}
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    write_report(report)
    from collections import Counter
    print(Counter(r['fit']['status'] for r in rows if r['assembled']))
    seen = set()
    for r in rows:
        key = r['lcsc'], r['footprint']
        if key in seen or not r['assembled']:
            continue
        seen.add(key)
        print(r['board'], r['reference'], r['lcsc'], r['footprint'], r['fit'])


def write_report(report):
    from jlc_placement_corrections import RESOLVED, transform
    lines = ['# Auditoría de colocación JLCPCB', '',
             'Fecha: '+report['checked_on']+'. **Candidatos para revisión, no liberados para fabricar.**', '',
             'Se comprueba cada referencia de ambas BOM, incluidas las excluidas del montaje. '
             'Para cada código LCSC se contrasta la huella pública enlazada por JLCPCB '
             'con los pads numerados de la PCB. Los alias eléctricos están documentados; '
             'no se aplica una corrección por el mero nombre del encapsulado.', '',
             'Fuente: [JLCEDA/EasyEDA Official Library](https://easyeda.com), '
             '[JLCEDA](https://lceda.cn/), a través del visor de las fichas de JLCPCB. '
             'Los SVG originales quedan en caché local; el JSON registra URL, UUID y SHA-256. '
             'No se redistribuyen las bibliotecas originales.', '',
             'La comparación comprueba orientación y centro, no tolerancias de fabricación, '
             'soldabilidad ni aprobación de la previsualización de un pedido concreto. '
             'El umbral de 0,30 mm es un filtro para diferencias entre land patterns, '
             'no una tolerancia admisible de colocación de la máquina.', '',
             'Se usa el enfoque de [Bouni](https://github.com/Bouni/kicad-jlcpcb-tools/blob/b2ff3a08173e04d77ba35019bc1670a9c3f1317d/fabrication.py) '
             'para ángulos/cara inferior, con reglas exactas por pieza verificadas contra pads. '
             'La tabla genérica da resultados distintos para varios SOT/TSOT. '
             'El centro se obtiene alineando los extremos de los pads numerados: incluir '
             'un tetón NPTH como hace el bounding box genérico desplaza J116/J118.', '',
             '## Pendientes de las posiciones montadas', '']
    for r in report['rows']:
        if r['assembled'] and r['fit']['status'] not in RESOLVED:
            lines.append(f'- **{r["board"]} {r["reference"]} / {r["lcsc"]}:** {r["note"] or r["fit"]["status"]}')
    lines += ['', '## Resultado por componente', '',
              'ΔX/ΔY son desplazamientos en ejes del CPL (X derecha, Y arriba), después '
              'de considerar el giro y la cara de la placa. Δθ es la corrección local; '
              'la columna final incluye también la convención de cara inferior. '
              'Los pendientes conservan los valores originales en el archivo de revisión.', '',
              '| Placa | Ref | LCSC | Montaje | Estado | Δθ | ΔX mm | ΔY mm | Giro final | Error máximo pads mm |',
              '|---|---|---|---|---|---:|---:|---:|---:|---:|']
    for r in report['rows']:
        n, f = r['native'], r['fit']
        good = f['status'] in RESOLVED
        x, y, a = transform(n, f) if good else (n['x'], n['y'], n['angle'])
        code = f'[{r["lcsc"]}](https://jlcpcb.com/partdetail/{r["lcsc"]})' if r['lcsc'] else '—'
        lines.append(f'| {r["board"]} | {r["reference"]} | {code} | {"sí" if r["assembled"] else "excluido"} '
                     f'| {f["status"]} | {f["rotation"] if good else "—"} | {x-n["x"]:.4f} '
                     f'| {y-n["y"]:.4f} | {a:.1f} | {f.get("max_error_mm", "—")} |')
    lines += ['', '## Notas por código LCSC', '']
    for code, note in NOTES.items():
        lines.append(f'- **{code}:** {note}')
    (ROOT/'hardware/assembly/placement-audit.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
