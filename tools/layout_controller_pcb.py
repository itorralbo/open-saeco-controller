"""Apply the reviewed mechanical/functional placement to the Rev A PCB.

This step does not create copper. It keeps the accepted outline and mounting
holes and photo-derived harness locations, places every electrical footprint by
functional block, and refuses a partial placement map. Run after
sync_controller_pcb.py with KiCad's Python.
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


MECHANICAL = json.loads((BASE/'mechanical-source.json').read_text())
HARNESS_CONNECTORS = {
    item['new_reference']: (*item['footprint_origin_mm'], item['rotation_deg'])
    for item in MECHANICAL['connector_placements']
}


def pending_power_connector_keepouts(board):
    """Protect required power-connector locations until their footprints exist."""
    prefix = 'pending required power connector '
    legacy_prefix = 'reserved original connector '
    for zone in list(board.Zones()):
        if zone.GetZoneName().startswith((prefix, legacy_prefix)):
            board.Delete(zone)
    layers = pcb.LSET.AllCuMask()
    present = {fp.GetReference() for fp in board.GetFootprints()}
    for item in MECHANICAL['required_power_connector_placements']:
        if item['new_reference'] in present:
            continue
        cx, cy = item['center_mm']
        width, height = item['size_mm']
        x1, x2 = max(0, cx-width/2), min(MECHANICAL['outline_mm']['width'], cx+width/2)
        y1, y2 = max(0, cy-height/2), min(MECHANICAL['outline_mm']['height'], cy+height/2)
        zone = pcb.ZONE(board)
        zone.SetIsRuleArea(True)
        zone.SetLayerSet(layers)
        zone.SetDoNotAllowTracks(True)
        zone.SetDoNotAllowVias(True)
        zone.SetDoNotAllowZoneFills(True)
        zone.SetDoNotAllowPads(True)
        zone.SetDoNotAllowFootprints(True)
        zone.SetZoneName(prefix+item['original_reference'])
        poly = zone.Outline()
        poly.NewOutline()
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            poly.Append(MM(x), MM(y))
        board.Add(zone)


# Coordinates use the accepted component-side origin in mechanical-source.json.
# Original harness connectors use the photo-derived positions in
# mechanical-source.json. U201 orientation 0 puts its antenna/keepout at the top
# edge. New service/power connectors avoid the original connector envelopes.
PLACE = {
    'U101': (55, 65, 0), 'U201': (66, 31, 0),
    'J101': (96, 6, 0), 'J102': (31, 35, 0), 'J103': (30, 60, 0),
    **HARNESS_CONNECTORS,
    'J115': (59.04, 120.8, 0), 'J117': (91.02, 120.8, 0),
    'J118': (106.04, 121.3, 0),
    'J110': (36, 4.45, 180), 'J111': (21, 27, 0),
    'J112': (108, 6, 0), 'J114': (96, 60, 90),

    # Integrated mains supply. The IRM module is rotated so its mains pins face
    # the right-side high-voltage corridor and its 24 V pins face the logic.
    'F701': (137, 52, 90), 'RV701': (130, 61, 0), 'F702': (137, 27, 90),
    'PS701': (105, 89, 180), 'J121': (69, 113, 0),
    'U303': (51, 106, 0), 'L302': (61, 104, 0),
    'C310': (47, 112, 0), 'C311': (54, 113, 0), 'C312': (62, 113, 0),
    'C313': (67, 96, 0), 'R302': (68, 100, 0), 'R303': (68, 104, 0),
    'C314': (68, 108, 0),

    # Independent phase-cut relay and low-voltage drive.
    'U603': (34, 80, 0), 'Q701': (28, 93, 0),
    'R801': (29, 81, 0), 'R802': (29, 86, 0), 'D701': (29, 115, 0),
    'K701': (49, 93, 0),

    # STM32 reset, analog supply and local decoupling.
    'R101': (66, 61, 90), 'C101': (66, 65, 90), 'R102': (66, 69, 90),
    'C102': (49, 56, 0), 'C103': (53, 56, 0),
    'C104': (57, 56, 0), 'C105': (61, 56, 0),
    'C106': (47, 75, 0), 'C107': (51, 75, 0), 'C108': (55, 75, 0),
    'C109': (59, 75, 0), 'C110': (63, 75, 0), 'C111': (45, 65, 90),

    # ESP32 reset/boot, module supply, USB data and service-power path.
    'R201': (83, 29, 90), 'C201': (83, 33, 90), 'R202': (83, 37, 90),
    'C202': (78, 28, 90), 'C203': (81, 28, 90),
    'U203': (34, 16, 180), 'R221': (50, 40.65, 0), 'R222': (50, 42.55, 0),
    'R223': (44, 27, 0), 'R224': (48, 27, 0),
    'R225': (26, 13, 0), 'R226': (27, 18, 90), 'C204': (23, 19, 0),
    'C205': (23, 22, 0), 'F302': (18, 24, 0), 'D303': (28, 27, 0),
    **row(['R213','R214','R215','R216','R217','R218'], 47, 47, 3.3, 90),
    'R211': (61, 51, 0), 'R212': (64, 51, 0),

    # 12 V input, 3.3 V buck and UI load switch.
    'F301': (88, 27, 0), 'D301': (95, 27, 0), 'D302': (103, 27, 0),
    'C301': (110, 27, 0), 'C302': (113, 31, 90), 'U301': (97, 36, 0),
    'C303': (102, 33, 0), 'L301': (104, 39, 0),
    'C304': (110, 36, 0), 'C305': (110, 41, 0), 'C306': (105, 44, 0),
    'U302': (101, 51, 0), 'R301': (96, 48, 0), 'C307': (107, 54, 0),
    'C308': (96, 53, 90), 'C309': (107, 49, 90),

    # Passive sensor interfaces follow the original harness connector zones.
    'R401': (28, 105, 90), 'R402': (31, 105, 90), 'C401': (34, 105, 90),
    'R403': (38, 104, 90), 'R404': (41, 104, 90), 'C402': (44, 104, 90),
    'R405': (15, 71, 90), 'R406': (18, 71, 90), 'C403': (21, 71, 90),
    'R411': (19, 116, 90), 'C406': (22, 116, 90),
    'R407': (16, 52, 90), 'R408': (19, 52, 90), 'C404': (22, 52, 90),
    'R409': (16, 59, 90), 'R410': (19, 59, 90), 'C405': (22, 59, 90),

    # 24 V input and brew-unit bridge.
    'R704': (70, 59, 0), 'R705': (75, 59, 0),
    'R706': (80, 59, 0), 'C702': (85, 59, 0),
    'F303': (76, 52, 0), 'D304': (84, 52, 0),
    'C501': (124, 21, 0), 'C502': (116, 21, 0), 'U501': (128, 43, 0),
    'C503': (133, 37, 90), 'C504': (133, 49, 90),
    'R501': (114, 34, 0), 'R502': (119, 34, 0),
    'R503': (114, 40, 0), 'R504': (119, 40, 0),
    'R505': (112, 46, 0), 'R506': (118, 46, 0),
    'R507': (112, 51, 0), 'R508': (118, 51, 0),
    'R509': (112, 56, 0), 'C505': (118, 56, 0),
    'R510': (112, 61, 0), 'C506': (118, 61, 0),

    # Valve branch above original JP3, kept away from sensor conditioning.
    'F304': (7, 91, 0), 'D305': (15, 91, 0), 'D306': (22, 99, 0),
    'U502': (11, 101, 0), 'Q501': (22, 107, 0),
    'R511': (5, 99, 0), 'R512': (5, 104, 0),
    'R513': (16, 108, 0), 'R514': (21, 113, 0),
    'C507': (10, 95, 0), 'C508': (14, 95, 0),

    # Hardware watchdog/interlock beside the STM32 and actuator commands.
    'U601': (42, 80, 0), 'U602': (53, 80, 0),
    'R601': (39, 84, 0), 'R602': (43, 84, 0),
    'R603': (50, 84, 0), 'R604': (55, 84, 0),
    'C601': (44, 76, 0), 'C602': (60, 77, 0),

    # 12/24 V diagnostic dividers; high-side pairs remain near each input.
    'R701': (100, 19, 90), 'R702': (103, 19, 90),
    'R703': (106, 19, 90), 'C701': (109, 19, 90),
}


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    board.SetCopperLayerCount(2)
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    # Keep the library's all-copper antenna exclusion intact.
    for zone in footprints['U201'].Zones():
        zone.SetLayerSet(pcb.LSET.AllCuMask())
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
        if isinstance(item, pcb.PCB_TEXT) and (
                item.GetText().startswith('UNROUTED COMPONENT STAGING') or
                item.GetText().startswith('FUNCTIONAL PLACEMENT')):
            item.SetText('MECHANICAL CONNECTOR PLACEMENT / NOT FOR FABRICATION\n'
                         'Original harness positions estimated from IMG_1098/1101; copper pending')

    pending_power_connector_keepouts(board)

    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    after = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for ref, position in before_holes.items():
        assert after[ref].GetPosition() == position, f'Mounting hole moved: {ref}'
    for ref, (x, y, rotation) in HARNESS_CONNECTORS.items():
        actual = after[ref]
        assert actual.GetPosition() == pcb.VECTOR2I(MM(x), MM(y)), f'Connector moved: {ref}'
        assert actual.GetOrientationDegrees() == rotation, f'Connector rotated: {ref}'
    result = {
        'status': 'mechanical_connector_placement_unrouted_not_fabricable',
        'kicad_version': pcb.GetBuildVersion(),
        'copper_layers': check.GetCopperLayerCount(),
        'electrical_footprints_placed': len(PLACE),
        'mounting_holes_preserved': sorted(before_holes),
        'antenna_at_top_edge': {'reference': 'U201', 'position_mm': PLACE['U201'][:2]},
        'photo_aligned_harness_connectors': sorted(HARNESS_CONNECTORS),
        'required_power_connectors_pending_footprints': [
            item['original_reference']
            for item in MECHANICAL['required_power_connector_placements']
            if item['new_reference'] not in after
        ],
        'connector_position_uncertainty_mm': MECHANICAL['connector_position_uncertainty_mm'],
    }
    (BASE/'validation/placement.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Controller mechanical/functional placement applied to {len(PLACE)} footprints; '
          f'{len(HARNESS_CONNECTORS)} harness connectors and holes preserved.')


if __name__ == '__main__':
    main()
