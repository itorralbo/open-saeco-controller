"""Apply photo-derived outline and mounting holes to the controller PCB.

The values remain provisional and are loaded from mechanical-source.json.
Existing copper and footprints are preserved. Re-running is allowed only when
the existing outline and MH references exactly match the recorded source; any
other mechanical geometry stops the script to protect manual CAD edits.
Run with KiCad's bundled Python/pcbnew.
"""
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'hardware/controller'
BOARD_PATH = BASE/'kicad/controller-core-reva.kicad_pcb'
SOURCE = json.loads((BASE/'mechanical-source.json').read_text())
FP_ROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')


def segment(board, start, end):
    item = pcb.PCB_SHAPE(board)
    item.SetShape(pcb.SHAPE_T_SEGMENT)
    item.SetLayer(pcb.Edge_Cuts)
    item.SetWidth(pcb.FromMM(0.05))
    item.SetStart(pcb.VECTOR2I(pcb.FromMM(start[0]), pcb.FromMM(start[1])))
    item.SetEnd(pcb.VECTOR2I(pcb.FromMM(end[0]), pcb.FromMM(end[1])))
    board.Add(item)


def main():
    assert SOURCE['status'] == 'owner_accepted_rev_a_baseline'
    assert SOURCE['mechanical_layout_released'] is True
    assert SOURCE['manufacturing_release'] is False
    board = pcb.LoadBoard(str(BOARD_PATH))
    edge_items = [item for item in board.GetDrawings() if item.GetLayer() == pcb.Edge_Cuts]
    refs = {fp.GetReference() for fp in board.GetFootprints()}

    width = SOURCE['outline_mm']['width']
    height = SOURCE['outline_mm']['height']
    if edge_items:
        assert len(edge_items) == 4, 'Unexpected Edge.Cuts; preserve manual work'
    else:
        for a, b in [((0, 0), (width, 0)), ((width, 0), (width, height)),
                     ((width, height), (0, height)), ((0, height), (0, 0))]:
            segment(board, a, b)

    for hole in SOURCE['mounting_holes']:
        if hole['reference'] in refs:
            continue
        fp = pcb.FootprintLoad(str(FP_ROOT/'MountingHole.pretty'), 'MountingHole_3.5mm')
        assert fp is not None
        fp.SetReference(hole['reference'])
        fp.SetValue('PHOTO-DERIVED 3.5mm NPTH')
        fp.SetFPIDAsString('MountingHole:MountingHole_3.5mm')
        fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(hole['x']), pcb.FromMM(hole['y'])))
        fp.Reference().SetVisible(True)
        fp.Value().SetVisible(False)
        board.Add(fp)

    for item in board.GetDrawings():
        if isinstance(item, pcb.PCB_TEXT) and item.GetText().startswith('UNROUTED COMPONENT STAGING'):
            item.SetText('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\n'
                         'Rev A mechanical baseline accepted; connector footprints and placement pending')
    if not any(isinstance(item, pcb.PCB_TEXT) and
               (item.GetText().startswith('OUTLINE + MH') or item.GetText().startswith('REV A OUTLINE'))
               for item in board.GetDrawings()):
        note = pcb.PCB_TEXT(board)
        note.SetLayer(pcb.Dwgs_User)
        note.SetPosition(pcb.VECTOR2I(pcb.FromMM(70.8), pcb.FromMM(4)))
        note.SetText('REV A OUTLINE + MOUNTING HOLES / OWNER-ACCEPTED BASELINE')
        note.SetTextSize(pcb.VECTOR2I(pcb.FromMM(1), pcb.FromMM(1)))
        note.SetTextThickness(pcb.FromMM(0.15))
        board.Add(note)

    for item in board.GetDrawings():
        if isinstance(item, pcb.PCB_TEXT) and item.GetText().startswith('OUTLINE + MH'):
            item.SetText('REV A OUTLINE + MOUNTING HOLES / OWNER-ACCEPTED BASELINE')

    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    assert len([d for d in check.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]) == 4
    by_ref = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for hole in SOURCE['mounting_holes']:
        fp = by_ref[hole['reference']]
        pos = fp.GetPosition()
        assert abs(pcb.ToMM(pos.x)-hole['x']) < 0.001
        assert abs(pcb.ToMM(pos.y)-hole['y']) < 0.001
    print(f'Verified {width:.1f} x {height:.1f} mm Rev A outline and 3 mounting holes.')


if __name__ == '__main__':
    main()
