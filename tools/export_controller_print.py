#!/usr/bin/env python3
"""Export a 1:1 paper print of the controller's top side.

Writes hardware/controller/preview/controller-top-1to1.pdf: edge, front
silkscreen, fab outlines, courtyards and mask openings, drills at their real
size, on A4 landscape. The board sits at the page origin in KiCad, where a
printer's margin would crop it, so a scratch copy is shifted 30 mm in and
gets a 100 mm scale bar to check the print was not scaled. Print at 100 %
("actual size"), then lay the real connectors, the relay and the PSU on it.
"""
import subprocess
import tempfile
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / 'hardware/controller/kicad/controller-core-reva.kicad_pcb'
TARGET = ROOT / 'hardware/controller/preview/controller-top-1to1.pdf'
KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
MM = pcb.FromMM
OFFSET = (30.0, 30.0)
LAYERS = 'Edge.Cuts,F.SilkS,F.Fab,F.CrtYd,F.Mask,User.Comments'


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    shift = pcb.VECTOR2I(MM(OFFSET[0]), MM(OFFSET[1]))
    for items in (board.GetFootprints(), board.GetDrawings(), board.GetTracks(), board.Zones()):
        for item in items:
            item.Move(shift)
    x0, y0 = OFFSET
    bottom = y0 + pcb.ToMM(board.GetBoardEdgesBoundingBox().GetHeight()) + 8.0
    for start, end in (((x0, bottom), (x0 + 100.0, bottom)),
                       ((x0, bottom - 2), (x0, bottom + 2)),
                       ((x0 + 100.0, bottom - 2), (x0 + 100.0, bottom + 2))):
        line = pcb.PCB_SHAPE(board, pcb.SHAPE_T_SEGMENT)
        line.SetStart(pcb.VECTOR2I(MM(start[0]), MM(start[1])))
        line.SetEnd(pcb.VECTOR2I(MM(end[0]), MM(end[1])))
        line.SetWidth(MM(0.2))
        line.SetLayer(pcb.Cmts_User)
        board.Add(line)
    label = pcb.PCB_TEXT(board)
    label.SetText('100 mm - si no mide 100 mm, la impresion esta escalada')
    label.SetLayer(pcb.Cmts_User)
    label.SetTextSize(pcb.VECTOR2I(MM(2.0), MM(2.0)))
    label.SetTextThickness(MM(0.25))
    label.SetHorizJustify(pcb.GR_TEXT_H_ALIGN_LEFT)
    label.SetPosition(pcb.VECTOR2I(MM(x0 + 104.0), MM(bottom)))
    board.Add(label)
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / BOARD_PATH.name
        pcb.SaveBoard(str(copy), board)
        subprocess.run([KICAD_CLI, 'pcb', 'export', 'pdf', '--layers', LAYERS,
                        '--mode-single', '--black-and-white', '--scale', '1',
                        '--drill-shape-opt', '2', '-o', str(TARGET), str(copy)],
                       check=True, capture_output=True)
    print(f'{TARGET.relative_to(ROOT)}: 1:1, shifted {OFFSET} mm, with a 100 mm scale bar')


if __name__ == '__main__':
    main()
