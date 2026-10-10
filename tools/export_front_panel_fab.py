"""Export the JLCPCB fabrication and assembly package of the front panel.

Writes hardware/front-panel/fabrication/: Gerbers + Excellon drill (zipped), a
drill map, BOM and CPL, and the parts JLCPCB had none of at the last stock
refresh, to buy elsewhere. Shared steps and formats in jlc_fab.py.
"""
import argparse

from jlc_fab import (export_gerbers, out_of_stock, positions, prepare_cpl, read_bom, write_bom,
                     write_cpl, write_not_assembled)
from validate_kicad import ROOT

BASE = ROOT/'hardware/front-panel'
BOARD = BASE/'kicad/front-panel-reva.kicad_pcb'
OUT = BASE/'fabrication'
NAME = 'front-panel-reva'
LAYERS = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-unverified', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    placements = positions(BOARD)
    parts = read_bom(BASE/'bom-draft.csv')
    assert all(p['lcsc'] for p in parts), 'Every position needs an LCSC code'
    placed = {p['Ref'] for p in placements}
    assert placed == {p['reference'] for p in parts}, sorted(placed ^ {p['reference'] for p in parts})
    skipped = {p['reference']: out_of_stock(p) for p in parts if out_of_stock(p)}
    assembled = [p for p in parts if p['reference'] not in skipped]
    cpl_path, cpl_rows, pending = prepare_cpl(
        BOARD, OUT, NAME, [p for p in placements if p['Ref'] not in skipped], args.allow_unverified)
    files = export_gerbers(BOARD, LAYERS, OUT/f'{NAME}-gerbers.zip')
    # Seven identical switches end up on one line (grouped by MPN).
    lines = write_bom(OUT/f'{NAME}-bom-jlcpcb.csv', assembled)
    write_cpl(cpl_path, cpl_rows)
    if pending:
        (OUT/f'{NAME}-cpl-jlcpcb.csv').unlink(missing_ok=True)
        print(f'  REVIEW ONLY: unresolved: {", ".join(pending)}')
    else:
        (OUT/f'{NAME}-cpl-jlcpcb-review.csv').unlink(missing_ok=True)
    write_not_assembled(OUT/f'{NAME}-not-assembled.csv', parts, skipped)
    print(f'{NAME}: {files} Gerber/drill files zipped; BOM {lines} lines / '
          f'{len(assembled)} positions; {len(skipped)} not assembled by JLCPCB.')


if __name__ == '__main__':
    main()
