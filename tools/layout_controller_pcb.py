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


# STM32 block: U101 and its decoupling move together. route_controller_pcb.py
# reads U101's position and applies the same offset to its supply routing.
U101_AT = (76.0, 40.0)


def stm(dx, dy, rot):
    return (U101_AT[0]+dx, U101_AT[1]+dy, rot)


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


# Centre line of the primary/SELV barrier: up from the bottom edge between J106
# and J115, then across K701 and PS701 to the right edge. A
# band MAINS_BARRIER_MM wide around it holds no tracks, vias or fills; parts
# certified across it (K701, PS701 and the optocouplers) may span it. Pads are
# allowed in the band because the 300 mil optocouplers put theirs 0.8 mm into
# it; the 8 mm mains-to-SELV DRC rule still covers every pad.
MAINS_BARRIER = [(51.0, 135.2), (51.0, 60.0), (141.6, 60.0)]
MAINS_BARRIER_MM = 8.0
BARRIER_ZONE_NAME = 'mains/SELV barrier'


# Chosen heatsink: a standard 33 x 21 mm extruded profile, 35 mm tall, fins
# vertical, with the two TO-220 triacs bolted to its south face. The original
# was 40 mm wide, but 40 mm leaves no lane between the profile and the phase
# that climbs beside PS701, and the switched live has to get from K701 down to
# the triacs somehow. 33 mm leaves a 7 mm lane at x = 55-62 that carries both
# the optocoupler's primary pads and the switched live.
#
# The area now forbids copper as well as other footprints: the profile's base
# sits on the board, so nothing may run underneath it.
HEATSINK_AREA = (62.0, 84.5, 95.0, 105.5)
HEATSINK_ZONE_NAME = 'heatsink foot: 33 x 21 x 35 mm extruded profile'


def heatsink_reservation(board):
    stale = (HEATSINK_ZONE_NAME, 'reserved heatsink: heater and pump triacs')
    for zone in list(board.Zones()):
        if zone.GetZoneName() in stale:
            board.Delete(zone)
    x1, y1, x2, y2 = HEATSINK_AREA
    zone = pcb.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetLayerSet(pcb.LSET.AllCuMask())
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowPads(True)
    zone.SetDoNotAllowFootprints(True)
    zone.SetZoneName(HEATSINK_ZONE_NAME)
    poly = zone.Outline()
    poly.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        poly.Append(MM(x), MM(y))
    board.Add(zone)


# Two devices carry mains on pins of their own fixed pitch: the optocoupler's
# secondary row at 2.54 mm and the triac's three terminals at 2.54 mm. The
# 2.5 mm the rules ask between primary tracks cannot apply there, so each gets
# a named area where mains-to-mains drops to the pitch the package imposes.
# The areas cover only the mains side of the optocoupler: the gap between its
# two rows is the isolation barrier and keeps the full 8 mm.
DEVICE_PITCH_AREAS = ((53.9, 96.2, 57.4, 103.8), (55.3, 105.6, 78.0, 113.5),
                      (53.9, 112.2, 57.4, 119.8), (85.2, 108.2, 92.8, 110.8))
DEVICE_PITCH_ZONE_NAME = 'mains device pitch'


def mains_device_pitch_areas(board):
    for zone in list(board.Zones()):
        if zone.GetZoneName() == DEVICE_PITCH_ZONE_NAME:
            board.Delete(zone)
    for x1, y1, x2, y2 in DEVICE_PITCH_AREAS:
        zone = pcb.ZONE(board)
        zone.SetIsRuleArea(True)
        zone.SetLayerSet(pcb.LSET.AllCuMask())
        for setter in ('SetDoNotAllowTracks', 'SetDoNotAllowVias',
                       'SetDoNotAllowZoneFills', 'SetDoNotAllowPads',
                       'SetDoNotAllowFootprints'):
            getattr(zone, setter)(False)
        zone.SetZoneName(DEVICE_PITCH_ZONE_NAME)
        poly = zone.Outline()
        poly.NewOutline()
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            poly.Append(MM(x), MM(y))
        board.Add(zone)


# One area per barrier optocoupler, covering both pad rows and the short stubs
# that enter them. Inside it the rules accept the 6.02 mm air gap between the
# rows; the slot in the footprint keeps the surface path over 8 mm.
OPTO_SLOT_AREAS = ((45.7, 96.0, 56.6, 104.0), (45.7, 112.0, 56.6, 120.0))
OPTO_SLOT_ZONE_NAME = 'optocoupler barrier slot'


def optocoupler_slot_areas(board):
    for zone in list(board.Zones()):
        if zone.GetZoneName() == OPTO_SLOT_ZONE_NAME:
            board.Delete(zone)
    for x1, y1, x2, y2 in OPTO_SLOT_AREAS:
        zone = pcb.ZONE(board)
        zone.SetIsRuleArea(True)
        zone.SetLayerSet(pcb.LSET.AllCuMask())
        for setter in ('SetDoNotAllowTracks', 'SetDoNotAllowVias',
                       'SetDoNotAllowZoneFills', 'SetDoNotAllowPads',
                       'SetDoNotAllowFootprints'):
            getattr(zone, setter)(False)
        zone.SetZoneName(OPTO_SLOT_ZONE_NAME)
        poly = zone.Outline()
        poly.NewOutline()
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            poly.Append(MM(x), MM(y))
        board.Add(zone)


def mains_barrier_keepout(board):
    for zone in list(board.Zones()):
        if zone.GetZoneName() == BARRIER_ZONE_NAME:
            board.Delete(zone)
    half = MAINS_BARRIER_MM/2
    (x0, y0), (x1, y1), (x2, _) = MAINS_BARRIER
    # Axis-aligned L, so the band outline is its offset on each side.
    band = [(x0-half, y0), (x1-half, y1-half), (x2, y1-half),
            (x2, y1+half), (x1+half, y1+half), (x0+half, y0)]
    zone = pcb.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetLayerSet(pcb.LSET.AllCuMask())
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowPads(False)
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
    'U101': stm(0, 0, 0), 'U201': (54, 14.2, 0),
    'J101': (96, 6, 0), 'J102': (74.5, 31, 90), 'J103': (75, 10, 90),
    **HARNESS_CONNECTORS,
    'J115': (59.04, 120.8, 0), 'J117': (91.02, 120.8, 0),
    'J118': (106.04, 121.3, 0),
    # Heater block and the two protective-earth tabs, in the envelopes that
    # mechanical-source.json had been reserving for them.
    'J116': (80.5, 124.05, 0), 'J119': (121.5, 124.0, 0), 'J120': (128.0, 124.0, 0),

    # Heater switching stage. U701 straddles the barrier centred on x = 51:
    # a 300 mil DIP whose footprint mills a 2 mm slot between the rows. Q703
    # stands against the south face of the heatsink, and R710 lives in the lane
    # beside it because it carries mains and cannot cross to the SELV side.
    'U701': (47.19, 97.46, 0), 'Q703': (68.46, 109.5, 0),
    'R710': (58, 108.5, 180),
    'R707': (31, 99, 0), 'R708': (31, 96, 180), 'Q705': (38, 99.5, 0),
    'R709': (36, 96, 0), 'R711': (28, 66, 180),

    # Pump stage, the heater's twin. U702 crosses the barrier one step south
    # of U701, low enough that its courtyard clears R710 and high enough to
    # clear J115. Q704 takes the east half of the heatsink's south
    # face, and R712 sits in the lane under R710, both fed from the same
    # switched phase. The LED driver fills the strip between U702 and MH2;
    # U604, the pump's reset gate, goes in the column west of MH2 with its
    # decoupling and pull-down.
    'U702': (47.19, 113.46, 0), 'Q704': (86.46, 109.5, 0),
    'R712': (58.3, 113.0, 180),
    'R716': (45.3, 110.6, 270), 'Q706': (43.8, 116.0, 0),
    'R714': (43.3, 108.2, 0), 'R715': (43.3, 106.6, 180),
    'U604': (31.9, 111.5, 90), 'C604': (31.9, 115.6, 0), 'R713': (31.9, 117.8, 0),
    'J110': (36, 4.45, 180), 'J111': (21, 27, 0),
    'J112': (108, 6, 0), 'J114': (48, 40, 90),

    # Mains domain: below/right of MAINS_BARRIER. PS701 stands on the right
    # edge with its AC pins beside J118 and its 24 V pins in SELV. Fuses and
    # MOV sit above the reserved heatsink; the gap between the heatsink and
    # PS701 carries L and PSU_L between J118, the fuses and PS701.
    # F702 (PSU branch) sits above F701 so that L_IN and PSU_L run nested down
    # the gap without crossing. J121 is turned so 24V_ACT_RAW leaves on the left.
    'PS701': (121.3, 82.4, 90), 'F701': (92, 74, 180), 'F702': (72, 67, 0),
    'RV701': (72, 80, 0), 'J121': (108.5, 45.2, 180),

    # 24 V to 12 V buck beside the J112 24 V entry, clear of the mains domain.
    'C310': (117.5, 5, 0), 'U303': (122.5, 5, 0), 'C313': (125.7, 4.5, 270),
    'L302': (132, 5, 0), 'C311': (139, 4, 90), 'C312': (139, 10.5, 90),
    # Feedback divider on the top edge, north-west of the switcher. It used to
    # sit below it at y = 10 mm, where the 24 V lane that wraps round C310 to
    # reach the input pins left no path back to FB. Here the whole divider
    # shares one quiet line at y = 3.4 mm that reaches pin 1 without crossing
    # anything, and R303 faces its ground pad west into open copper.
    'R302': (113, 2.2, 0), 'R303': (108, 2.2, 180), 'C314': (117, 2.2, 0),

    # Phase-cut relay straddles the vertical barrier: coil pins in SELV,
    # contacts in the mains domain. Drive and flyback diode sit by the coil.
    'U603': (32, 73, 180), 'C603': (31.5, 75.6, 0), 'Q701': (32, 78.5, 0),
    'R801': (26, 71, 180), 'R802': (26, 75, 0), 'D701': (43.5, 88, 90),
    'K701': (52, 77, 180),

    # STM32 reset, analog supply and local decoupling. Each capacitor sits at
    # its VDD/VSS pair outside the signal escape channels planned in layout.md;
    # route_controller_pcb.py joins the VDD pins through a ring under the body.
    # The reset pull-up and filter moved from east of the MCU, where its NRST
    # pin does not face, to the reset net's own corridor beside the supervisor
    # that drives it. R102 stays: BOOT0 is an east-side pin.
    'R101': (41.0, 48.6, 0), 'C101': (44.2, 48.6, 0), 'R102': stm(11, 4, 90),
    'C102': stm(-9.7, 2.6, 90), 'C103': stm(3.5, 8.2, 180),
    'C104': stm(7.8, -4.9, 90), 'C105': stm(-4.1, -8.4, 90),
    'C106': stm(9.4, -4.9, 90), 'C107': stm(-4.1, 8.6, 180),
    'C108': stm(-4.1, 11.8, 180), 'C109': stm(-4.1, 10.2, 180),
    'C110': stm(3.5, 9.8, 180), 'C111': stm(-8.4, -3.75, 180),

    # ESP32-S3-WROOM-1U beside the USB port; its U.FL lead leaves from the top.
    # EN/BOOT, module supply, USB data and service-power path around it.
    'R201': (42.5, 13.0, 90), 'C201': (42.5, 16.4, 90), 'R202': (66, 22, 270),
    'C202': (42.5, 6.2, 90), 'C203': (42.5, 9.6, 90),
    'U203': (34, 16, 180), 'R221': (40, 22.1, 0), 'R222': (40, 20.2, 0),
    'R223': (44, 27, 0), 'R224': (48, 27, 0),
    'R225': (26, 13, 0), 'R226': (27, 18, 90), 'C204': (23, 19, 0),
    'C205': (23, 22, 0), 'F302': (18, 24, 0), 'D303': (30, 29, 0),
    **row(['R213','R214','R215','R216','R217','R218'], 51, 28, 3.3, 90),
    'R211': (67, 9.6, 0), 'R212': (67, 11.5, 0),

    # 12 V input, 3.3 V buck and UI load switch.
    # F301 moved west to open the gap between it and D301: the 3.3 V spine
    # climbs there, and the fused link needs room for its own via.
    'F301': (85, 27, 0), 'D301': (95, 27, 0), 'D302': (103, 27, 0),
    'C301': (110, 27, 0), 'U301': (97, 36, 0),
    # C302 is the switcher's input HF capacitor, so it sits under the package
    # bridging the input pins to the ground pin instead of 8 mm away by C301.
    'C302': (97, 39, 0),
    'C303': (102, 33, 0), 'L301': (104, 39, 0),
    'C304': (110, 36, 0), 'C305': (110, 41, 0), 'C306': (105, 44, 0),
    # UI load switch. PS701's footprint walls this pocket off at x = 101.25 mm,
    # so everything that used to sit east of U302 moves west or north of it.
    # C307 sets the rise time and now sits at pin 4 instead of 8 mm away, C308
    # decouples the input right at pin 1, and C309 holds the switched output.
    'U302': (98.5, 51, 0), 'R301': (94.5, 53.6, 0), 'C307': (98.5, 53.7, 0),
    'C308': (94.5, 50.05, 180), 'C309': (97.5, 45.5, 0),

    # Passive sensor interfaces follow the original harness connector zones.
    'R401': (28, 105, 90), 'R402': (31, 105, 90), 'C401': (34, 105, 90),
    # R404 turned so the raw flow net lands on the same row as R403's, which
    # removes the crossing the filter link used to make.
    'R403': (38, 104, 90), 'R404': (41, 104, 270), 'C402': (44, 104, 90),
    # R405 turned so its 3.3 V pad faces north: the door harness net owns the
    # y = 71.8 mm lane west of it, so the pull-up cannot be fed from below.
    'R405': (15, 71, 270), 'R406': (18, 71, 270), 'C403': (21, 71, 90),
    'R411': (19, 116, 90), 'C406': (22, 116, 90),
    'R407': (16, 52, 90), 'R408': (19, 52, 270), 'C404': (22, 52, 90),
    'R409': (16, 59, 90), 'R410': (19, 59, 270), 'C405': (22, 59, 90),

    # 24 V divider, brew-branch fuse and diode on the SELV side of the barrier.
    'R704': (48.5, 52, 0), 'R705': (52.5, 52, 0),
    'R706': (56.5, 52, 0), 'C702': (60.5, 52, 0),
    'F303': (40.5, 40.4, 180), 'D304': (40.75, 43.6, 180),
    # DRV8876 beside JP16 (J108), above MH1, in the space J102 left. Rotated
    # 270 deg: control pins 1-6 face north, the charge pump and OUT2 face
    # south, OUT1 leaves the top-left corner. OUT1/OUT2 drop down the left at
    # x = 28/29.2 mm and enter J108 at y = 62/64.5 mm between its filter rows.
    'U501': (35, 37, 270),
    'C503': (33.75, 43.3, 180), 'C504': (35.65, 45.2, 0),
    'C501': (31.1, 52.5, 270), 'C502': (36.3, 48.0, 0),
    # Control rows east of U501, 1.6 mm pitch, pull-downs first, then the
    # series resistors; the STM32 signals continue east above J114.
    'R510': (43.0, 29.4, 0), 'C506': (46.8, 29.4, 0),
    'R509': (43.0, 31.0, 0), 'C505': (46.8, 31.0, 0), 'R508': (50.6, 31.0, 180),
    'R507': (50.6, 32.6, 180),
    'R506': (43.0, 34.2, 0), 'R505': (46.8, 34.2, 180),
    'R504': (43.0, 35.8, 0), 'R503': (46.8, 35.8, 180),
    'R502': (43.0, 37.4, 0), 'R501': (46.8, 37.4, 180),

    # Valve branch above original JP3, kept away from sensor conditioning.
    'F304': (12, 95, 0), 'D305': (18, 95, 180), 'D306': (22, 99, 0),
    'U502': (11, 101, 0), 'Q501': (22, 107, 0),
    'R511': (5, 99, 0), 'R512': (5, 104, 0),
    'R513': (16, 108, 0), 'R514': (21, 113, 0),
    'C507': (8, 97.5, 180), 'C508': (11.5, 97.5, 0),

    # Hardware watchdog/interlock on the SELV side, left of the barrier.
    'U601': (38, 54, 0), 'U602': (38, 62, 0),
    # R601/R602 tuck under U601 so the channel between the chips and the
    # capacitor column stays free for the 3V3 spine. The 1.35 mm channel west
    # of U601/U602 is reserved for STM_NRST and is not used by this block.
    'R601': (38, 56.8, 0), 'R602': (38, 58.8, 0),
    'R603': (33, 61.025, 180), 'R604': (42.5, 64.5, 0),
    'C601': (42.5, 53.05, 0), 'C602': (42.5, 61.025, 0),

    # 12/24 V diagnostic dividers; high-side pairs remain near each input.
    # R702 turned so the divider's mid node faces R701 and the filtered node
    # continues east in one straight line to R703 and C701.
    'R701': (100, 19, 90), 'R702': (103, 19, 270),
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
    mains_device_pitch_areas(board)
    optocoupler_slot_areas(board)
    heatsink_reservation(board)

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
        'reserved_heatsink_area_mm': HEATSINK_AREA,
    }
    (BASE/'validation/placement.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Controller mechanical/functional placement applied to {len(PLACE)} footprints; '
          f'{len(HARNESS_CONNECTORS)} harness connectors and holes preserved.')


if __name__ == '__main__':
    main()
