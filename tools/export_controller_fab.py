"""Export the candidate JLCPCB fabrication and assembly package of the main board.

Writes hardware/controller/fabrication/: the four-layer Gerbers + Excellon drill
(zipped) with a drill map, BOM and CPL for the positions JLCPCB assembles, and
a list of the positions it does not: DNP parts, solder jumpers, and parts with
no JLCPCB code (hand-soldered or consigned). Parts still unchosen or only
photo-matched are printed as open items; the package is not a release.
Shared steps and formats in jlc_fab.py.
"""
import csv

from jlc_fab import export_gerbers, positions, read_bom, ref_key, write_bom, write_cpl
from validate_kicad import ROOT

BASE = ROOT/'hardware/controller'
BOARD = BASE/'kicad/controller-core-reva.kicad_pcb'
OUT = BASE/'fabrication'
NAME = 'controller-core-reva'
LAYERS = ('F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,'
          'F.Mask,B.Mask,Edge.Cuts')


def not_assembled(part):
    """Why JLCPCB does not place `part`, or None if it does."""
    if part['status'].startswith('dnp'):
        return 'DNP: huella reservada, no se monta'
    if part['footprint'].startswith('Jumper:'):
        return 'Puente de soldadura: cobre, no es una pieza'
    if not part['mpn']:
        return 'Pieza sin elegir'
    if not part['lcsc']:
        return 'Sin código JLCPCB: soldar a mano o aportar'
    return None


def open_item(part):
    """A position that must be settled before ordering, or None."""
    if part['status'].startswith('dnp'):
        return None
    if not part['mpn'] and not part['footprint'].startswith('Jumper:'):
        return 'sin pieza elegida'
    if part['status'].startswith('photo_candidate'):
        return 'cabecera candidata por foto, sin confirmar'
    return None


def main():
    OUT.mkdir(exist_ok=True)
    parts = read_bom(BASE/'bom-draft.csv')
    placements = positions(BOARD)
    placed = {p['Ref'] for p in placements}
    # Solder jumpers are excluded from the position file by KiCad.
    jumpers = {p['reference'] for p in parts if p['footprint'].startswith('Jumper:')}
    assert placed | jumpers == {p['reference'] for p in parts}, \
        sorted((placed | jumpers) ^ {p['reference'] for p in parts})

    skipped = {p['reference']: not_assembled(p) for p in parts if not_assembled(p)}
    assembled = [p for p in parts if p['reference'] not in skipped]
    assert all(p['lcsc'] for p in assembled)

    files = export_gerbers(BOARD, LAYERS, OUT/f'{NAME}-gerbers.zip')
    lines = write_bom(OUT/f'{NAME}-bom-jlcpcb.csv', assembled)
    write_cpl(OUT/f'{NAME}-cpl-jlcpcb.csv', [p for p in placements if p['Ref'] not in skipped])
    with (OUT/f'{NAME}-not-assembled.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Designator', 'Value', 'Manufacturer', 'MPN', 'Reason'])
        for p in sorted((p for p in parts if p['reference'] in skipped),
                        key=lambda p: ref_key(p['reference'])):
            w.writerow([p['reference'], p['value'], p['manufacturer'], p['mpn'],
                        skipped[p['reference']]])

    print(f'{NAME}: {files} Gerber/drill files zipped; BOM {lines} lines / '
          f'{len(assembled)} positions; CPL {len(assembled)} placements; '
          f'{len(skipped)} positions not assembled by JLCPCB.')
    bottom = sorted(p['Ref'] for p in placements
                    if p['Side'] == 'bottom' and p['Ref'] not in skipped)
    if bottom:
        # One fitted part underneath means a two-sided assembly order, unless
        # it is soldered by hand.
        print(f'  assembled on the bottom side: {", ".join(bottom)}')
    pending = [(p['reference'], open_item(p)) for p in parts if open_item(p)]
    for ref, why in sorted(pending, key=lambda r: ref_key(r[0])):
        print(f'  open before ordering: {ref}: {why}')


if __name__ == '__main__':
    main()
