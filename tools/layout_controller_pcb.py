"""Apply the reviewed functional placement to the Rev A controller PCB.

This step does not create copper. It keeps the accepted outline and mounting
holes, places every electrical footprint by functional block, and refuses a
partial placement map. Run after sync_controller_pcb.py with KiCad's Python.
"""
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'hardware/controller'
BOARD_PATH = BASE/'kicad/controller-core-reva.kicad_pcb'
MM = pcb.FromMM


def row(refs, x0, y, dx=3.2, rot=0):
    return {ref: (x0+i*dx, y, rot) for i, ref in enumerate(refs)}


# Coordinates use the accepted component-side origin in mechanical-source.json.
# Connectors stay on board edges; their final rotations still require an arnes
# mating check. U201 orientation 0 puts its antenna/keepout at the top edge.
PLACE = {
    'U101': (73, 65, 0), 'U201': (55, 31, 0),
    'J101': (92, 6, 0), 'J102': (49, 92, 0), 'J103': (7, 78, 0),
    'J104': (5.5, 7, 0), 'J105': (5, 124, 0), 'J106': (16, 124, 0),
    'J107': (30, 124, 0), 'J108': (107.5, 124, 0), 'J109': (42, 124, 0),
    'J110': (20, 4.45, 180), 'J111': (21, 27, 0),
    'J112': (135, 6, 0), 'J113': (63, 124, 0), 'J114': (96, 106, 0),

    # STM32 reset, analog supply and local decoupling.
    'R101': (84, 61, 90), 'C101': (84, 65, 90), 'R102': (84, 69, 90),
    'C102': (67, 56, 0), 'C103': (71, 56, 0),
    'C104': (75, 56, 0), 'C105': (79, 56, 0),
    'C106': (65, 75, 0), 'C107': (69, 75, 0), 'C108': (73, 75, 0),
    'C109': (77, 75, 0), 'C110': (81, 75, 0), 'C111': (63, 65, 90),

    # ESP32 reset/boot, module supply, USB data and service-power path.
    'R201': (76, 29, 90), 'C201': (76, 33, 90), 'R202': (76, 37, 90),
    'C202': (68, 28, 90), 'C203': (72, 28, 90),
    'U203': (20, 13.5, 0), 'R221': (40, 41, 90), 'R222': (40, 44, 90),
    'R223': (15, 37, 0), 'R224': (15, 40, 0),
    'R225': (25, 13, 0), 'R226': (28, 13, 0), 'C204': (28, 17, 90),
    'C205': (24, 17, 90), 'F302': (14, 24, 0), 'D303': (28, 27, 0),
    **row(['R213','R214','R215','R216','R217','R218'], 47, 47, 3.3, 90),
    'R211': (61, 51, 0), 'R212': (64, 51, 0),

    # 12 V input, 3.3 V buck and UI load switch.
    'F301': (82, 21, 0), 'D301': (89, 21, 0), 'D302': (97, 21, 0),
    'C301': (104, 21, 0), 'C302': (107, 25, 90), 'U301': (91, 32, 0),
    'C303': (96, 29, 0), 'L301': (98, 34, 0),
    'C304': (104, 32, 0), 'C305': (104, 36, 0), 'C306': (100, 39, 0),
    'U302': (95, 46, 0), 'R301': (90, 43, 0), 'C307': (101, 49, 0),
    'C308': (90, 48, 90), 'C309': (101, 44, 90),

    # Passive sensor interfaces, directly above their edge connectors.
    'R401': (5, 108, 90), 'R402': (8, 108, 90), 'C401': (11, 108, 90),
    'R403': (16, 108, 90), 'R404': (19, 108, 90), 'C402': (22, 108, 90),
    'R405': (29, 108, 90), 'R406': (32, 108, 90), 'C403': (35, 108, 90),
    'R411': (42, 108, 90), 'C406': (45, 108, 90),
    'R407': (103, 108, 90), 'R408': (106, 108, 90), 'C404': (109, 108, 90),
    'R409': (112, 108, 90), 'R410': (115, 108, 90), 'C405': (118, 108, 90),

    # 24 V input and brew-unit bridge.
    'R704': (112, 7, 0), 'R705': (118, 7, 0),
    'R706': (124, 7, 0), 'C702': (130, 7, 0),
    'F303': (108, 14, 0), 'D304': (116, 14, 0),
    'C501': (129, 21, 0), 'C502': (120, 21, 0), 'U501': (129, 43, 0),
    'C503': (136, 37, 90), 'C504': (136, 49, 90),
    'R501': (112, 36, 0), 'R502': (118, 36, 0),
    'R503': (112, 41, 0), 'R504': (118, 41, 0),
    'R505': (112, 46, 0), 'R506': (118, 46, 0),
    'R507': (112, 51, 0), 'R508': (118, 51, 0),
    'R509': (112, 56, 0), 'C505': (118, 56, 0),
    'R510': (112, 61, 0), 'C506': (118, 61, 0),

    # Valve branch next to JP3, kept away from sensor conditioning.
    'F304': (64, 88, 0), 'D305': (72, 88, 0), 'D306': (78, 96, 0),
    'U502': (68, 98, 0), 'Q501': (78, 104, 0),
    'R511': (62, 96, 0), 'R512': (62, 101, 0),
    'R513': (72, 105, 0), 'R514': (77, 110, 0),
    'C507': (67, 92, 0), 'C508': (71, 92, 0),

    # Hardware watchdog/interlock beside the STM32 and actuator commands.
    'U601': (88, 80, 0), 'U602': (98, 80, 0),
    'R601': (84, 83, 0), 'R602': (88, 86, 0),
    'R603': (94, 86, 0), 'R604': (100, 86, 0),
    'C601': (88, 75, 0), 'C602': (98, 75, 0),

    # 12/24 V diagnostic dividers; high-side pairs remain near each input.
    'R701': (100, 8, 90), 'R702': (103, 8, 90),
    'R703': (106, 8, 90), 'C701': (109, 8, 90),
}


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    electrical = set(footprints)-{'MH1','MH2','MH3'}
    assert electrical == set(PLACE), sorted(electrical ^ set(PLACE))
    before_holes = {ref: footprints[ref].GetPosition() for ref in ('MH1','MH2','MH3')}

    for ref, (x, y, rotation) in PLACE.items():
        fp = footprints[ref]
        fp.SetOrientationDegrees(0)
        fp.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rotation)
        fp.Reference().SetTextSize(pcb.VECTOR2I(MM(.8), MM(.8)))
        fp.Reference().SetTextThickness(MM(.12))
        fp.Reference().SetLayer(pcb.F_Fab)
        fp.Reference().SetPosition(fp.GetPosition())

    for item in board.GetDrawings():
        if isinstance(item, pcb.PCB_TEXT) and item.GetText().startswith('UNROUTED COMPONENT STAGING'):
            item.SetText('FUNCTIONAL PLACEMENT / NOT FOR FABRICATION\n'
                         'Rev A low-voltage blocks placed; copper routing pending')

    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    after = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for ref, position in before_holes.items():
        assert after[ref].GetPosition() == position, f'Mounting hole moved: {ref}'
    result = {
        'status': 'functional_placement_unrouted_not_fabricable',
        'kicad_version': pcb.GetBuildVersion(),
        'electrical_footprints_placed': len(PLACE),
        'mounting_holes_preserved': sorted(before_holes),
        'antenna_at_top_edge': {'reference': 'U201', 'position_mm': PLACE['U201'][:2]},
        'connectors_on_edges': [f'J{i}' for i in range(101,115)],
        'tracks': len(list(check.GetTracks())),
    }
    (BASE/'validation/placement.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Controller functional placement applied to {len(PLACE)} footprints; holes preserved.')


if __name__ == '__main__':
    main()
