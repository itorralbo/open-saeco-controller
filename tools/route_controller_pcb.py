#!/usr/bin/env python3
"""Route reviewed critical nets on the controller PCB.

The script currently owns the USB data path. It clears tracks before rebuilding
them, while preserving placement and rule areas. Extend this file as each block
is reviewed; do not treat the remaining ratsnest as fabrication-ready.
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


def via(board, netname, point):
    item = pcb.PCB_VIA(board)
    item.SetPosition(pcb.VECTOR2I(MM(point[0]), MM(point[1])))
    item.SetWidth(MM(USB_VIA))
    item.SetDrill(MM(USB_DRILL))
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


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    assert board.GetCopperLayerCount() == 2
    for item in list(board.GetTracks()):
        board.Delete(item)
    route_usb_port(board)
    route_usb_device(board)
    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    result = {
        'status': 'critical_routing_in_progress_not_fabricable',
        'routed_blocks': ['USB-C reversible fanout', 'USB ESD-to-series-pair', 'USB series-to-ESP32'],
        'track_segments': sum(isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA)
                              for item in check.GetTracks()),
        'vias': sum(isinstance(item, pcb.PCB_VIA) for item in check.GetTracks()),
        'remaining_blocks': ['mains input and isolated supply', 'heater, pump and grinder',
                             'decoupling', 'logic', 'sensors', '24 V actuators',
                             'domain-specific copper fills'],
    }
    REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
