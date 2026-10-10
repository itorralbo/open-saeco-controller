"""Export the candidate JLCPCB fabrication and assembly package of the main board.

Writes hardware/controller/fabrication/: the four-layer Gerbers + Excellon drill
(zipped) with a drill map, BOM and CPL for the positions JLCPCB assembles, and
a list of the positions it does not: DNP parts, solder jumpers, parts with no
JLCPCB code, and parts JLCPCB had none of at the last stock refresh
(tools/refresh_jlc_stock.py); those are bought elsewhere and hand-soldered or
consigned. Parts still unchosen or only photo-matched are printed as open
items; the package is not a release.
Shared steps and formats in jlc_fab.py.
"""
import argparse

from jlc_fab import (export_gerbers, out_of_stock, positions, prepare_cpl, read_bom, ref_key,
                     write_bom, write_cpl, write_not_assembled)
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
    return out_of_stock(part)


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-unverified', action='store_true',
                        help='Write a review CPL with unresolved placements explicitly reported')
    args = parser.parse_args()
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

    cpl_path, cpl_rows, pending = prepare_cpl(
        BOARD, OUT, NAME, [p for p in placements if p['Ref'] not in skipped], args.allow_unverified)

    files = export_gerbers(BOARD, LAYERS, OUT/f'{NAME}-gerbers.zip')
    lines = write_bom(OUT/f'{NAME}-bom-jlcpcb.csv', assembled)
    write_cpl(cpl_path, cpl_rows)
    if pending:
        (OUT/f'{NAME}-cpl-jlcpcb.csv').unlink(missing_ok=True)
        print(f'  REVIEW ONLY: {cpl_path.name}; unresolved: {", ".join(pending)}')
    else:
        (OUT/f'{NAME}-cpl-jlcpcb-review.csv').unlink(missing_ok=True)
    write_not_assembled(OUT/f'{NAME}-not-assembled.csv', parts, skipped)

    print(f'{NAME}: {files} Gerber/drill files zipped; BOM {lines} lines / '
          f'{len(assembled)} positions; CPL {len(assembled)} placements; '
          f'{len(skipped)} positions not assembled by JLCPCB.')
    bottom = sorted(p['Ref'] for p in placements
                    if p['Side'] == 'bottom' and p['Ref'] not in skipped)
    if bottom:
        # One fitted part underneath means a two-sided assembly order, unless
        # it is soldered by hand.
        print(f'  assembled on the bottom side: {", ".join(bottom)}')
    buy = sorted((r for r, why in skipped.items() if why.startswith('Sin stock')), key=ref_key)
    if buy:
        print(f'  out of stock at JLCPCB, buy separately: {", ".join(buy)}')
    pending = [(p['reference'], open_item(p)) for p in parts if open_item(p)]
    for ref, why in sorted(pending, key=lambda r: ref_key(r[0])):
        print(f'  open before ordering: {ref}: {why}')


if __name__ == '__main__':
    main()
