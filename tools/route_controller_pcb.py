#!/usr/bin/env python3
"""Route reviewed critical nets on the controller PCB.

The script owns the USB data path, the STM32 supply/decoupling block and the
provisional SELV ground plane. It clears tracks and its own zones before
rebuilding them, while preserving placement and rule areas. Extend this file as
each block is reviewed; do not treat the remaining ratsnest as fabrication-ready.
"""
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'hardware/controller'
BOARD_PATH = BASE / 'kicad/controller-core-reva.kicad_pcb'
REPORT = BASE / 'validation/routing.json'
MM = pcb.FromMM

USB_WIDTH = 0.20
USB_VIA = 0.60
USB_DRILL = 0.30

# STM32 supply stubs leave 0.5 mm-pitch LQFP pads, so they stay narrower than
# the Power class default; the ring and cap links carry only MCU current.
PIN_WIDTH = 0.25
RING_WIDTH = 0.30

GND_PLANE_NAME = 'GND_UI SELV plane (provisional)'
# SELV side of the board. The mains_to_selv rules keep the fill 8 mm from any
# primary copper; the outline stops short of the PS701 primary half and the
# bottom mains connector row until the barrier geometry is fixed.
GND_PLANE_OUTLINE = [(0.5, 0.5), (141.1, 0.5), (141.1, 66.5), (70.0, 66.5),
                     (70.0, 109.5), (50.0, 109.5), (50.0, 134.7), (0.5, 134.7)]


def net(board, name):
    result = board.FindNet(name)
    assert result, name
    return result


def track(board, netname, start, end, layer=pcb.F_Cu, width=USB_WIDTH):
    item = pcb.PCB_TRACK(board)
    item.SetStart(pcb.VECTOR2I(MM(start[0]), MM(start[1])))
    item.SetEnd(pcb.VECTOR2I(MM(end[0]), MM(end[1])))
    item.SetWidth(MM(width))
    item.SetLayer(layer)
    item.SetNet(net(board, netname))
    item.SetLocked(True)
    board.Add(item)


def polyline(board, netname, points, layer=pcb.F_Cu, width=USB_WIDTH):
    for start, end in zip(points, points[1:]):
        track(board, netname, start, end, layer, width)


def via(board, netname, point, diameter=USB_VIA, drill=USB_DRILL):
    item = pcb.PCB_VIA(board)
    item.SetPosition(pcb.VECTOR2I(MM(point[0]), MM(point[1])))
    item.SetWidth(MM(diameter))
    item.SetDrill(MM(drill))
    item.SetNet(net(board, netname))
    item.SetLocked(True)
    board.Add(item)


def route_usb_port(board):
    """Fan out the reversible Type-C pins on F.Cu, then combine each net inside."""
    # Ordered fanout avoids crossing the alternating B6/A7/A6/B7 contact row.
    dp_fanout = [((35.25, 8.495), (35.25, 10.20), (33.50, 12.00)),
                 ((36.25, 8.495), (36.25, 11.00), (37.00, 13.00))]
    for path in dp_fanout:
        polyline(board, '/USB_DP_PORT', path)
        via(board, '/USB_DP_PORT', path[-1])

    # DP combines on B.Cu. DM stays on F.Cu after the DP fanout drops away.
    dp_join = (36.20, 16.95)
    polyline(board, '/USB_DP_PORT', [(33.50, 12.00), (33.50, 15.00),
                                     (35.50, 17.00), dp_join], pcb.B_Cu)
    polyline(board, '/USB_DP_PORT', [(37.00, 13.00), (37.00, 15.50), dp_join], pcb.B_Cu)
    via(board, '/USB_DP_PORT', dp_join)
    track(board, '/USB_DP_PORT', dp_join, (35.138, 16.95))

    dm_join = (36.20, 15.05)
    polyline(board, '/USB_DM_PORT', [(35.75, 8.495), (35.75, 11.00),
                                     (35.00, 13.00), (34.50, 14.00), dm_join])
    polyline(board, '/USB_DM_PORT', [(36.75, 8.495), (36.75, 10.20),
                                     (38.50, 12.00), (38.50, 13.50),
                                     (37.50, 14.50), dm_join])
    track(board, '/USB_DM_PORT', dm_join, (35.138, 15.05))


def route_usb_device(board):
    """Keep the protected device-side pair parallel around the RF keepout."""
    dm_a = [(32.862, 15.05), (30.00, 15.05), (30.00, 23.00),
            (38.00, 31.00), (38.00, 35.00)]
    dp_a = [(32.862, 16.95), (32.00, 18.00), (32.00, 23.00),
            (40.00, 31.00), (40.50, 37.50)]
    polyline(board, '/USB_DM_DEVICE', dm_a)
    polyline(board, '/USB_DP_DEVICE', dp_a)
    for name, start, end in [('/USB_DM_DEVICE', (38.00, 35.00), (44.00, 39.00)),
                             ('/USB_DP_DEVICE', (40.50, 37.50), (46.50, 41.50))]:
        via(board, name, start)
        track(board, name, start, end, pcb.B_Cu)
        via(board, name, end)
    polyline(board, '/USB_DM_DEVICE', [(44.00, 39.00), (47.00, 39.00),
                                       (49.175, 40.65)])
    polyline(board, '/USB_DP_DEVICE', [(46.50, 41.50), (49.175, 42.55)])

    polyline(board, '/USB_DM_RAW', [(50.825, 40.65), (53.00, 40.65),
                                    (55.00, 40.98), (57.25, 40.98)])
    polyline(board, '/USB_DP_RAW', [(50.825, 42.55), (53.00, 42.55),
                                    (55.00, 42.25), (57.25, 42.25)])


def route_stm32_supply(board):
    """Join U101 VDD pins under the body and decouple each VDD/VSS pair.

    VSS pins drop to the B.Cu plane through their own via inside the pad ring.
    VDD pins meet on an F.Cu ring under the package; their outer ends feed the
    corner capacitors placed by layout_controller_pcb.py. Pins 2-11, 14-17,
    21-27, 42-44 and 49-61 keep their escape channels free for signal routing.
    """
    v33, gnd = '/3V3_CORE', '/GND_UI'

    # 3V3 ring under the LQFP body, reached from pins 1/64, 13, 19/20, 32, 48.
    ring = [(52.75, 62.60), (57.60, 62.60), (57.60, 67.80), (52.75, 67.80),
            (52.75, 62.60)]
    polyline(board, v33, ring, width=RING_WIDTH)
    polyline(board, v33, [(51.25, 59.60), (51.25, 61.25), (52.75, 62.60)],
             width=RING_WIDTH)
    track(board, v33, (49.60, 61.25), (51.25, 61.25), width=PIN_WIDTH)
    track(board, v33, (49.60, 67.25), (52.75, 67.25), width=PIN_WIDTH)
    track(board, v33, (52.75, 70.40), (52.75, 67.80), width=PIN_WIDTH)
    polyline(board, v33, [(52.25, 70.40), (52.25, 69.40), (52.75, 68.90)],
             width=PIN_WIDTH)
    polyline(board, v33, [(58.75, 70.40), (58.75, 68.60), (57.60, 67.80)],
             width=PIN_WIDTH)
    polyline(board, v33, [(60.30, 61.25), (58.20, 61.25), (57.60, 61.85),
                          (57.60, 62.60)], width=PIN_WIDTH)

    # Inner VSS vias: pins 12, 18, 31, 47 and 63.
    for path in ([(49.60, 66.75), (50.60, 66.75), (51.30, 66.40)],
                 [(51.75, 70.40), (51.75, 68.80)],
                 [(58.25, 70.40), (58.25, 69.30), (57.50, 69.30)],
                 [(60.30, 61.75), (59.50, 61.75), (59.10, 62.35)],
                 [(51.75, 59.60), (51.75, 60.35), (52.40, 61.00)]):
        polyline(board, gnd, path, width=PIN_WIDTH)
        via(board, gnd, path[-1])

    # C105 at VDD64/VSS63 and C111 at VBAT1.
    track(board, v33, (51.25, 59.00), (51.25, 57.50), width=PIN_WIDTH)
    track(board, gnd, (50.90, 55.825), (50.90, 54.60), width=PIN_WIDTH)
    via(board, gnd, (50.90, 54.60))
    track(board, v33, (49.00, 61.25), (47.375, 61.25), width=PIN_WIDTH)
    track(board, gnd, (45.825, 61.25), (44.60, 61.25), width=PIN_WIDTH)
    via(board, gnd, (44.60, 61.25))

    # C102 at VDD13/VSS12, left of the pin 14-16 escape.
    polyline(board, v33, [(49.00, 67.25), (46.10, 67.25), (46.10, 68.375),
                          (45.40, 68.375)], width=PIN_WIDTH)
    track(board, gnd, (49.00, 66.75), (45.50, 66.75), width=PIN_WIDTH)
    track(board, gnd, (45.30, 66.825), (43.90, 66.825), width=PIN_WIDTH)
    via(board, gnd, (43.90, 66.825))

    # C104 at VDD48/VSS47 with the C106 bulk capacitor beside it.
    track(board, v33, (61.00, 61.25), (62.60, 61.25), width=PIN_WIDTH)
    track(board, v33, (62.80, 60.875), (64.40, 60.875), width=RING_WIDTH)
    track(board, gnd, (62.80, 59.325), (64.40, 59.325), width=RING_WIDTH)
    track(board, gnd, (63.60, 59.325), (63.60, 58.30), width=PIN_WIDTH)
    via(board, gnd, (63.60, 58.30))

    # C103 at VDD32/VSS31 and C110 below it.
    polyline(board, v33, [(58.75, 71.00), (58.75, 72.40), (59.275, 72.925),
                          (59.275, 74.80)], width=PIN_WIDTH)
    polyline(board, gnd, [(58.25, 71.00), (58.25, 72.40), (57.725, 72.925),
                          (57.725, 76.10)], width=PIN_WIDTH)
    via(board, gnd, (57.725, 76.10))

    # VDDA20/VREF19 column: C107 10 nF nearest, then C109 and C108.
    for x in (52.25, 52.75):
        polyline(board, v33, [(x, 71.00), (x, 71.80), (52.50, 72.05)],
                 width=PIN_WIDTH)
    polyline(board, v33, [(52.50, 72.05), (52.50, 72.60), (52.00, 73.10),
                          (52.00, 76.80)], width=RING_WIDTH)
    polyline(board, gnd, [(51.75, 71.00), (51.75, 72.35), (49.80, 72.35),
                          (49.80, 78.00)], width=RING_WIDTH)
    via(board, gnd, (49.80, 78.00))


def selv_ground_plane(board):
    """Rebuild the provisional B.Cu GND_UI plane on the SELV side."""
    for zone in list(board.Zones()):
        if zone.GetZoneName() == GND_PLANE_NAME:
            board.Delete(zone)
    zone = pcb.ZONE(board)
    zone.SetLayer(pcb.B_Cu)
    zone.SetNet(net(board, '/GND_UI'))
    zone.SetZoneName(GND_PLANE_NAME)
    zone.SetLocalClearance(MM(0.30))
    zone.SetMinThickness(MM(0.25))
    zone.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(MM(0.30))
    zone.SetThermalReliefSpokeWidth(MM(0.40))
    zone.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
    poly = zone.Outline()
    poly.NewOutline()
    for x, y in GND_PLANE_OUTLINE:
        poly.Append(MM(x), MM(y))
    board.Add(zone)
    pcb.ZONE_FILLER(board).Fill(board.Zones())


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    assert board.GetCopperLayerCount() == 2
    for item in list(board.GetTracks()):
        board.Delete(item)
    route_usb_port(board)
    route_usb_device(board)
    route_stm32_supply(board)
    selv_ground_plane(board)
    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    result = {
        'status': 'critical_routing_in_progress_not_fabricable',
        'routed_blocks': ['USB-C reversible fanout', 'USB ESD-to-series-pair', 'USB series-to-ESP32',
                          'STM32 VDD ring, VSS vias and decoupling',
                          'provisional SELV GND_UI plane on B.Cu'],
        'track_segments': sum(isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA)
                              for item in check.GetTracks()),
        'vias': sum(isinstance(item, pcb.PCB_VIA) for item in check.GetTracks()),
        'remaining_blocks': ['mains/SELV floorplan fix required by the 8 mm barrier rule',
                             'mains input and isolated supply', 'heater, pump and grinder',
                             '3V3 trunk and remaining decoupling', 'logic', 'sensors',
                             '24 V actuators', 'final domain copper fills'],
    }
    REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
