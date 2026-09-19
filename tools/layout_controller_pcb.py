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


# Centre line of the primary/SELV barrier, from the bottom edge between J106
# and J115, around the relay contacts and across PS701 to the right edge. A
# band MAINS_BARRIER_MM wide around it holds no copper, vias or pads; parts
# certified across it (K701, PS701 and future optocouplers) may span it.
MAINS_BARRIER = [(51.0, 135.2), (51.0, 100.5), (69.5, 100.5), (69.5, 76.0),
                 (141.6, 76.0)]
MAINS_BARRIER_MM = 8.0
BARRIER_ZONE_NAME = 'mains/SELV barrier'


def mains_barrier_keepout(board):
    for zone in list(board.Zones()):
        if zone.GetZoneName() == BARRIER_ZONE_NAME:
            board.Delete(zone)
    half = MAINS_BARRIER_MM/2
    (x0, y0), (x1, y1), (x2, _), (x3, y3), (x4, _) = MAINS_BARRIER
    # Axis-aligned polyline, so the band outline is its offset on each side.
    band = [(x0-half, y0), (x1-half, y1-half), (x2-half, y1-half),
            (x3-half, y3-half), (x4, y3-half), (x4, y3+half),
            (x3+half, y3+half), (x2+half, y1+half), (x1+half, y1+half),
            (x0+half, y0)]
    zone = pcb.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetLayerSet(pcb.LSET.AllCuMask())
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowPads(True)
    zone.SetDoNotAllowFootprints(False)
    zone.SetZoneName(BARRIER_ZONE_NAME)
    poly = zone.Outline()
    poly.NewOutline()
    for x, y in band:
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
    'J112': (108, 6, 0), 'J114': (84, 64.5, 90),

    # Mains domain: everything below/right of MAINS_BARRIER. PS701 stands on
    # the right edge with its AC pins beside J118 and its 24 V pins in SELV.
    # Fuses and MOV sit between J118 and the relay; the free area left of them
    # is reserved for the heater, pump and grinder stages.
    'PS701': (121.3, 82.4, 90), 'F701': (99, 109, 180), 'F702': (79, 102, 0),
    'RV701': (84, 114, 0), 'J121': (108.5, 45.2, 0),

    # 24 V to 12 V buck beside the J112 24 V entry, clear of the mains domain.
    'C310': (117.5, 5, 0), 'U303': (122.5, 5, 0), 'C313': (125.7, 4.5, 270),
    'L302': (132, 5, 0), 'C311': (139, 4, 90), 'C312': (139, 10.5, 90),
    'R302': (121, 10, 0), 'R303': (125, 10, 0), 'C314': (129, 10, 0),

    # Phase-cut relay straddles the barrier: coil pins in SELV, contacts in
    # the mains domain. Its drive and flyback diode stay beside the coil.
    'U603': (34, 80, 0), 'Q701': (47.5, 91, 0),
    'R801': (29, 81, 0), 'R802': (29, 86, 0), 'D701': (53, 91, 90),
    'K701': (72, 91, 180),

    # STM32 reset, analog supply and local decoupling. Each capacitor sits at
    # its VDD/VSS pair outside the signal escape channels planned in layout.md;
    # route_controller_pcb.py joins the VDD pins through a ring under the body.
    'R101': (66, 61, 90), 'C101': (66, 65, 90), 'R102': (66, 69, 90),
    'C102': (45.3, 67.6, 90), 'C103': (58.5, 73.2, 180),
    'C104': (62.8, 60.1, 90), 'C105': (50.9, 56.6, 90),
    'C106': (64.4, 60.1, 90), 'C107': (50.9, 73.6, 180),
    'C108': (50.9, 76.8, 180), 'C109': (50.9, 75.2, 180),
    'C110': (58.5, 74.8, 180), 'C111': (46.6, 61.25, 180),

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
    'U302': (98.5, 51, 0), 'R301': (96, 48, 0), 'C307': (99, 55, 0),
    'C308': (94.5, 53, 90), 'C309': (99.5, 46.5, 0),

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
    # Kept above PS701; the right-edge column holds fault, VREF and IPROPI parts.
    'C501': (124, 21, 0), 'C502': (116, 21, 0), 'U501': (128, 43, 0),
    'C503': (133, 37, 90), 'C504': (134, 42.3, 90),
    'R501': (114, 34, 0), 'R502': (119, 34, 0),
    'R503': (114, 40, 0), 'R504': (119, 40, 0),
    'R505': (112, 46, 0), 'R506': (118, 46, 0),
    'R507': (136, 21, 0), 'R508': (136, 25, 0),
    'R509': (136, 29, 0), 'C505': (139.5, 29, 0),
    'R510': (136, 33, 0), 'C506': (139.5, 33, 0),

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
    mains_barrier_keepout(board)

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
        'mains_barrier_centre_line_mm': MAINS_BARRIER,
        'mains_barrier_width_mm': MAINS_BARRIER_MM,
    }
    (BASE/'validation/placement.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Controller mechanical/functional placement applied to {len(PLACE)} footprints; '
          f'{len(HARNESS_CONNECTORS)} harness connectors and holes preserved.')


if __name__ == '__main__':
    main()
