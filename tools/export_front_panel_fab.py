"""Export the JLCPCB fabrication and assembly package of the front panel.

Writes hardware/front-panel/fabrication/: Gerbers + Excellon drill (zipped), a
drill map, BOM and CPL. Shared steps and formats in jlc_fab.py.
"""
from jlc_fab import export_gerbers, positions, read_bom, write_bom, write_cpl
from validate_kicad import ROOT

BASE = ROOT/'hardware/front-panel'
BOARD = BASE/'kicad/front-panel-reva.kicad_pcb'
OUT = BASE/'fabrication'
NAME = 'front-panel-reva'
LAYERS = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'


def main():
    OUT.mkdir(exist_ok=True)
    files = export_gerbers(BOARD, LAYERS, OUT/f'{NAME}-gerbers.zip')
    placements = positions(BOARD)
    parts = read_bom(BASE/'bom-draft.csv')
    assert all(p['lcsc'] for p in parts), 'Every position needs an LCSC code'
    placed = {p['Ref'] for p in placements}
    assert placed == {p['reference'] for p in parts}, sorted(placed ^ {p['reference'] for p in parts})
    # Seven identical switches end up on one line (grouped by MPN).
    lines = write_bom(OUT/f'{NAME}-bom-jlcpcb.csv', parts)
    write_cpl(OUT/f'{NAME}-cpl-jlcpcb.csv', placements)
    print(f'{NAME}: {files} Gerber/drill files zipped; BOM {lines} lines / '
          f'{len(parts)} positions; CPL {len(placements)} placements.')


if __name__ == '__main__':
    main()
