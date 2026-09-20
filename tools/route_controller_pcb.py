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

# Primary copper stays on 1 oz (cheapest JLCPCB option). Phase tracks carrying
# the load current (~10 A) are 3 mm on both layers, joined by stitching vias,
# about 6 mm of 1 oz in total; the PSU and MOV branches are light.
MAINS_PHASE_WIDTH = 3.0
MAINS_VIA = 1.60
MAINS_DRILL = 0.80
MAINS_LIGHT_WIDTH = 1.0
MAINS_N_WIDTH = 1.5
ACT_WIDTH = 1.0
ACT_LANE_WIDTH = 0.8

GND_PLANE_NAME = 'GND_UI SELV plane (provisional)'
# SELV side of the barrier drawn by layout_controller_pcb.py, up to the SELV
# edge of its keepout band. The mains_to_selv rules still hold the fill 8 mm
# from any primary copper.
GND_PLANE_OUTLINE = [(0.5, 0.5), (141.1, 0.5), (141.1, 56.0), (47.0, 56.0),
                     (47.0, 134.7), (0.5, 134.7)]


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
    """Protected pair from U203 around its left side to R221/R222 and the ESP32.

    The pair leaves U203 facing away from the module, so DM crosses DP once on
    B.Cu just before the ESP32 pins.
    """
    polyline(board, '/USB_DM_DEVICE', [(32.862, 15.05), (30.60, 15.05),
                                       (30.60, 22.10), (39.175, 22.10)])
    polyline(board, '/USB_DP_DEVICE', [(32.862, 16.95), (31.50, 16.95),
                                       (31.50, 20.20), (39.175, 20.20)])
    polyline(board, '/USB_DP_RAW', [(40.825, 20.20), (42.20, 20.20),
                                    (44.30, 22.30), (45.25, 22.30)])
    track(board, '/USB_DM_RAW', (40.825, 22.10), (41.80, 22.10))
    via(board, '/USB_DM_RAW', (41.80, 22.10))
    track(board, '/USB_DM_RAW', (41.80, 22.10), (44.00, 21.03), pcb.B_Cu)
    via(board, '/USB_DM_RAW', (44.00, 21.03))
    track(board, '/USB_DM_RAW', (44.00, 21.03), (45.25, 21.03))


def route_stm32_supply(board):
    """Join U101 VDD pins under the body and decouple each VDD/VSS pair.

    VSS pins drop to the B.Cu plane through their own via inside the pad ring.
    VDD pins meet on an F.Cu ring under the package; their outer ends feed the
    corner capacitors placed by layout_controller_pcb.py. Pins 2-11, 14-17,
    21-27, 42-44 and 49-61 keep their escape channels free for signal routing.
    """
    v33, gnd = '/3V3_CORE', '/GND_UI'
    # Coordinates below are for U101 at (55, 65); shift them to its placement.
    at = board.FindFootprintByReference('U101').GetPosition()
    dx, dy = pcb.ToMM(at.x)-55.0, pcb.ToMM(at.y)-65.0

    def sh(point):
        return (point[0]+dx, point[1]+dy)

    def pl(netname, points, **kw):
        polyline(board, netname, [sh(p) for p in points], **kw)

    def tr(netname, a, b, **kw):
        track(board, netname, sh(a), sh(b), **kw)

    def vi(netname, point):
        via(board, netname, sh(point))

    # 3V3 ring under the LQFP body, reached from pins 1/64, 13, 19/20, 32, 48.
    ring = [(52.75, 62.60), (57.60, 62.60), (57.60, 67.80), (52.75, 67.80),
            (52.75, 62.60)]
    pl(v33, ring, width=RING_WIDTH)
    pl(v33, [(51.25, 59.60), (51.25, 61.25), (52.75, 62.60)],
             width=RING_WIDTH)
    tr(v33, (49.60, 61.25), (51.25, 61.25), width=PIN_WIDTH)
    tr(v33, (49.60, 67.25), (52.75, 67.25), width=PIN_WIDTH)
    tr(v33, (52.75, 70.40), (52.75, 67.80), width=PIN_WIDTH)
    pl(v33, [(52.25, 70.40), (52.25, 69.40), (52.75, 68.90)],
             width=PIN_WIDTH)
    pl(v33, [(58.75, 70.40), (58.75, 68.60), (57.60, 67.80)],
             width=PIN_WIDTH)
    pl(v33, [(60.30, 61.25), (58.20, 61.25), (57.60, 61.85),
                          (57.60, 62.60)], width=PIN_WIDTH)

    # Inner VSS vias: pins 12, 18, 31, 47 and 63.
    for path in ([(49.60, 66.75), (50.60, 66.75), (51.30, 66.40)],
                 [(51.75, 70.40), (51.75, 68.80)],
                 [(58.25, 70.40), (58.25, 69.30), (57.50, 69.30)],
                 [(60.30, 61.75), (59.50, 61.75), (59.10, 62.35)],
                 [(51.75, 59.60), (51.75, 60.35), (52.40, 61.00)]):
        pl(gnd, path, width=PIN_WIDTH)
        vi(gnd, path[-1])

    # C105 at VDD64/VSS63 and C111 at VBAT1.
    tr(v33, (51.25, 59.00), (51.25, 57.50), width=PIN_WIDTH)
    tr(gnd, (50.90, 55.825), (50.90, 54.60), width=PIN_WIDTH)
    vi(gnd, (50.90, 54.60))
    tr(v33, (49.00, 61.25), (47.375, 61.25), width=PIN_WIDTH)
    tr(gnd, (45.825, 61.25), (44.60, 61.25), width=PIN_WIDTH)
    vi(gnd, (44.60, 61.25))

    # C102 at VDD13/VSS12, left of the pin 14-16 escape.
    pl(v33, [(49.00, 67.25), (46.10, 67.25), (46.10, 68.375),
                          (45.40, 68.375)], width=PIN_WIDTH)
    tr(gnd, (49.00, 66.75), (45.50, 66.75), width=PIN_WIDTH)
    tr(gnd, (45.30, 66.825), (43.90, 66.825), width=PIN_WIDTH)
    vi(gnd, (43.90, 66.825))

    # C104 at VDD48/VSS47 with the C106 bulk capacitor beside it.
    tr(v33, (61.00, 61.25), (62.60, 61.25), width=PIN_WIDTH)
    tr(v33, (62.80, 60.875), (64.40, 60.875), width=RING_WIDTH)
    tr(gnd, (62.80, 59.325), (64.40, 59.325), width=RING_WIDTH)
    tr(gnd, (63.60, 59.325), (63.60, 58.30), width=PIN_WIDTH)
    vi(gnd, (63.60, 58.30))

    # C103 at VDD32/VSS31 and C110 below it.
    pl(v33, [(58.75, 71.00), (58.75, 72.40), (59.275, 72.925),
                          (59.275, 74.80)], width=PIN_WIDTH)
    pl(gnd, [(58.25, 71.00), (58.25, 72.40), (57.725, 72.925),
                          (57.725, 76.10)], width=PIN_WIDTH)
    vi(gnd, (57.725, 76.10))

    # VDDA20/VREF19 column: C107 10 nF nearest, then C109 and C108.
    for x in (52.25, 52.75):
        pl(v33, [(x, 71.00), (x, 71.80), (52.50, 72.05)],
                 width=PIN_WIDTH)
    pl(v33, [(52.50, 72.05), (52.50, 72.60), (52.00, 73.10),
                          (52.00, 76.80)], width=RING_WIDTH)
    pl(gnd, [(51.75, 71.00), (51.75, 72.35), (49.80, 72.35),
                          (49.80, 78.00)], width=RING_WIDTH)
    vi(gnd, (49.80, 78.00))


def route_mains_input(board):
    """J118 to F701, F702 and PS701; fused phase to RV701 and K701.

    L_IN and PSU_L run nested down the gap between the heatsink area and
    PS701, 2.5 mm apart. N reaches PS701 on F.Cu and continues to RV701 on
    B.Cu, where no SELV plane exists, crossing under both phase tracks.
    """
    l_in, l_fused, psu_l = '/MAINS_L_IN', '/MAINS_L_FUSED', '/PSU_L_FUSED'
    neutral, load_l = '/MAINS_N', '/LOAD_L_ENABLED'
    # The stub leaving J118.1 is narrower to clear the unused middle VH pin.
    # B.Cu doubles the phase up to y = 77: N crosses on B.Cu above that, so
    # the last 3 mm bend and the F701 clip link stay on F.Cu only.
    for layer in (pcb.F_Cu, pcb.B_Cu):
        track(board, l_in, (106.04, 121.30), (104.50, 118.00), layer, width=2.2)
    polyline(board, l_in, [(104.50, 118.00), (99.50, 118.00), (96.50, 115.00),
                           (96.50, 74.00), (87.00, 74.00)], width=MAINS_PHASE_WIDTH)
    polyline(board, l_in, [(104.50, 118.00), (99.50, 118.00), (96.50, 115.00),
                           (96.50, 77.00)], pcb.B_Cu, width=MAINS_PHASE_WIDTH)
    for point in [(102.00, 118.00), (96.50, 110.00), (96.50, 101.00),
                  (96.50, 92.00), (96.50, 83.00), (96.50, 77.00)]:
        via(board, l_in, point, MAINS_VIA, MAINS_DRILL)
    polyline(board, psu_l, [(87.00, 67.00), (101.20, 67.00), (101.20, 110.00),
                            (104.35, 113.15), (106.30, 113.15)],
             width=MAINS_LIGHT_WIDTH)

    # Fused phase: both fuse clips, the MOV and the doubled K701 COM pads.
    # Every end is a THT pad, so both layers meet there; one stitching via
    # mid-way along the K701 link.
    for layer in (pcb.F_Cu, pcb.B_Cu):
        for start, end in [((72.00, 67.00), (77.00, 67.00)),
                           ((72.00, 74.00), (77.00, 74.00)),
                           ((72.00, 67.00), (72.00, 80.00))]:
            track(board, l_fused, start, end, layer, width=MAINS_PHASE_WIDTH)
        polyline(board, l_fused, [(57.00, 73.25), (57.00, 67.50), (72.00, 67.50)],
                 layer, width=2.5)
        # Doubled K701 NO pads; the triac stages will extend this net.
        track(board, load_l, (62.00, 73.25), (62.00, 80.75), layer, width=2.0)
    via(board, l_fused, (64.50, 67.50), MAINS_VIA, MAINS_DRILL)
    track(board, l_fused, (57.00, 73.25), (57.00, 80.75), pcb.B_Cu, width=2.5)

    polyline(board, neutral, [(113.96, 121.30), (113.96, 116.50),
                              (111.80, 114.34), (111.80, 113.15)], width=2.5)
    polyline(board, neutral, [(111.80, 113.15), (111.80, 70.50), (82.00, 70.50),
                              (82.00, 79.70), (79.50, 82.20)], pcb.B_Cu,
             width=MAINS_N_WIDTH)


def route_24v_output(board):
    """PS701 24 V through J121 to every 24V_ACT_RAW load on the SELV side.

    A 0.8 mm lane at x = 107.85 mm between the 3.3 V buck and the DRV8876
    resistors reaches J112 and the 12 V buck. The trunk follows the SELV edge
    of the barrier band and drops at x = 46 mm, left of it, to the relay coil,
    D701 and the valve branch.
    """
    internal, act = '/24V_INTERNAL_RAW', '/24V_ACT_RAW'
    polyline(board, internal, [(115.30, 51.65), (115.30, 49.20), (111.00, 49.20),
                               (109.15, 47.35), (109.15, 45.20)], width=ACT_WIDTH)

    # The lane runs up the empty column at x = 112.5 mm, east of the 3.3 V
    # output capacitors. It used to climb at x = 107.85 mm, straight between
    # the inductor and those capacitors, where every 3.3 V link crossed it.
    polyline(board, act, [(107.85, 45.20), (107.85, 43.6), (109.0, 43.0),
                          (112.5, 43.0), (112.5, 9.50), (114.00, 9.50),
                          (116.025, 7.475), (116.025, 5.00)],
             width=ACT_LANE_WIDTH)
    polyline(board, act, [(112.5, 11.0), (109.8, 8.0), (108.3, 6.6)],
             width=ACT_LANE_WIDTH)
    polyline(board, act, [(116.025, 7.30), (120.20, 7.30), (121.362, 6.14)],
             width=ACT_LANE_WIDTH)
    track(board, act, (121.362, 6.14), (121.362, 5.00), width=0.5)

    polyline(board, act, [(107.85, 45.20), (107.85, 46.60), (103.40, 46.60),
                          (101.80, 48.20), (101.80, 55.10), (46.40, 55.10),
                          (46.40, 79.10), (44.75, 80.75), (42.00, 80.75)],
             width=ACT_WIDTH)
    polyline(board, act, [(46.40, 55.10), (46.40, 42.00), (44.80, 40.40),
                          (41.90, 40.40)], width=ACT_WIDTH)
    track(board, act, (46.40, 52.00), (47.725, 52.00), width=ACT_LANE_WIDTH)
    polyline(board, act, [(62.50, 55.10), (62.50, 42.80), (57.20, 42.80),
                          (55.62, 41.22), (55.62, 40.00)], width=ACT_LANE_WIDTH)
    # Below the relay coil the trunk continues down the SELV edge of the
    # barrier band to the flyback diode and the valve fuse.
    polyline(board, act, [(46.40, 79.10), (46.40, 92.00), (45.40, 93.00),
                          (10.60, 93.00), (10.60, 94.50)], width=ACT_WIDTH)
    track(board, act, (46.40, 90.00), (43.50, 90.00), width=ACT_LANE_WIDTH)


def route_h_bridge(board):
    """DRV8876 at (35, 37) rotated 270 deg beside JP16.

    OUT1 leaves the top-left pin and OUT2 the bottom row; both drop down the
    left of the driver and enter J108 between its filter rows. VM is fed from
    D304 along y = 46.4 through C501/C502/C503 to pin 11. The control pins fan
    north and east into six 1.6 mm rows of resistors; each pull-down/series
    pair is joined by a wrap over the pull-down's ground pad.
    """
    gnd, vm = '/GND_UI', '/24V_BREW'
    out1, out2 = '/BREW_OUT1', '/BREW_OUT2'
    # Exposed pad and ground pins.
    for point in [(34.4, 36.4), (35.6, 36.4), (34.4, 37.6), (35.6, 37.6)]:
        via(board, gnd, point)
    polyline(board, gnd, [(33.375, 33.35), (33.375, 32.9), (33.0, 32.5)])
    via(board, gnd, (33.0, 32.5))
    polyline(board, gnd, [(32.725, 40.65), (32.3, 40.9), (31.6, 40.9)])
    via(board, gnd, (31.6, 40.9))
    polyline(board, gnd, [(36.625, 40.65), (36.625, 41.2), (37.275, 41.2),
                          (37.275, 40.65)])
    track(board, gnd, (37.275, 41.2), (37.7, 41.6))
    via(board, gnd, (37.7, 41.7))

    # Motor outputs, 0.8 mm after a pad-width stub.
    track(board, out1, (32.6, 34.125), (31.9, 34.125), width=0.4)
    polyline(board, out1, [(31.9, 34.125), (28.0, 38.0), (28.0, 62.0), (3.0, 62.0)],
             width=ACT_LANE_WIDTH)
    polyline(board, out2, [(33.375, 40.65), (33.375, 41.1), (32.6, 41.9)], width=0.4)
    polyline(board, out2, [(32.6, 41.9), (29.2, 45.3), (29.2, 64.5), (3.0, 64.5)],
             width=ACT_LANE_WIDTH)

    # Charge pump and VM: pins 11-14 drop straight into C503 and C504.
    polyline(board, vm, [(34.025, 40.6), (34.1, 41.7), (33.4, 42.4), (32.975, 42.9),
                         (32.975, 43.3)], width=0.3)
    track(board, '/BREW_VCP', (34.675, 40.65), (34.675, 43.3))
    polyline(board, '/BREW_CPH', [(35.325, 40.65), (35.325, 44.4), (34.875, 44.85),
                                  (34.875, 45.2)])
    polyline(board, '/BREW_CPL', [(35.975, 40.65), (35.975, 44.4), (36.425, 44.85),
                                  (36.425, 45.2)])
    polyline(board, vm, [(43.0, 44.3), (43.0, 45.6), (42.2, 46.4), (32.975, 46.4),
                         (32.975, 43.775)], width=ACT_LANE_WIDTH)
    polyline(board, vm, [(32.975, 46.4), (31.6, 47.8), (31.6, 48.5)], width=ACT_LANE_WIDTH)
    track(board, vm, (35.525, 46.4), (35.525, 47.6), width=0.5)
    track(board, gnd, (37.075, 48.0), (38.0, 48.0), width=0.5)
    via(board, gnd, (38.2, 48.0))
    polyline(board, gnd, [(31.1, 56.95), (30.4, 57.7), (30.4, 58.5)], width=0.5)
    via(board, gnd, (30.4, 58.5))
    track(board, '/24V_BREW_FUSED', (39.1, 41.0), (39.1, 43.0), width=ACT_LANE_WIDTH)

    # Control fan: pins 1-2 leave to the right, 3-6 upwards, each to its row.
    rows = {'/BREW_CURRENT_ADC': 29.4, '/BREW_VREF': 31.0, '/BREW_FAULT_N': 32.6,
            '/BREW_SLEEP_DRV': 34.2, '/BREW_DIR_DRV': 35.8, '/BREW_EN_DRV': 37.4}
    polyline(board, '/BREW_EN_DRV', [(37.275, 34.125), (38.1, 34.125), (38.1, 37.4),
                                     (42.225, 37.4)])
    polyline(board, '/BREW_DIR_DRV', [(36.625, 33.35), (36.625, 33.0), (38.55, 33.0),
                                      (38.55, 35.8), (42.225, 35.8)])
    polyline(board, '/BREW_SLEEP_DRV', [(35.975, 33.35), (35.975, 32.4), (39.0, 32.4),
                                        (39.0, 34.2), (42.225, 34.2)])
    polyline(board, '/BREW_FAULT_N', [(35.325, 33.35), (35.325, 31.9), (39.45, 31.9),
                                      (39.45, 32.6), (49.825, 32.6)])
    polyline(board, '/BREW_VREF', [(34.675, 33.35), (34.675, 31.0), (42.225, 31.0)])
    polyline(board, '/BREW_CURRENT_ADC', [(34.025, 33.35), (34.025, 29.4), (42.225, 29.4)])

    def wrap(netname, y, x0=42.225, x1=46.025):
        """Hop over a ground pad and its via between two pads of one row."""
        polyline(board, netname, [(x0, y), (x0+0.575, y-0.8), (x1-0.575, y-0.8), (x1, y)])

    for netname in ('/BREW_EN_DRV', '/BREW_DIR_DRV', '/BREW_SLEEP_DRV',
                    '/BREW_VREF', '/BREW_CURRENT_ADC'):
        wrap(netname, rows[netname])
    wrap('/BREW_VREF', 31.0, 46.025, 49.825)
    polyline(board, '/BREW_CURRENT_ADC', [(46.025, 29.4), (46.6, 28.6), (49.4, 28.6),
                                          (50.2, 29.7), (56.0, 29.7)])
    polyline(board, '/BREW_FAULT_N', [(49.825, 32.6), (50.4, 33.4), (52.3, 33.4),
                                      (52.9, 32.6), (56.0, 32.6)])
    for y in (29.4, 31.0, 34.2, 35.8, 37.4):
        track(board, gnd, (43.775, y), (44.9, y))
        via(board, gnd, (44.9, y))
    for y in (29.4, 31.0):
        track(board, gnd, (47.575, y), (48.7, y))
        via(board, gnd, (48.7, y))
    track(board, '/3V3_CORE', (51.375, 31.475), (51.375, 32.125), width=0.3)


def route_watchdog_interlock(board):
    """Supervisor, interlock gates and the K701 coil driver.

    U601 watches 3V3_CORE and drives STM_NRST; U602 gates the brew and valve
    arm lines with it; U603 gates the mains arm line and drives Q701, whose
    drain pulls the relay coil down to the D701 flyback diode. A 3V3 spine runs
    in the channel between the chips and the capacitor column. The 1.35 mm
    channel west of U601/U602, between them and C501, is left empty: STM_NRST
    and the raw STM32 arm lines claim it in the signal pass, so this block
    leaves those pins open rather than blocking their only approach.
    """
    gnd, v33 = '/GND_UI', '/3V3_CORE'

    # 3V3 spine: U601 VDD and MR, C601, U602 VCC and C602.
    polyline(board, v33, [(39.138, 53.05), (40.52, 53.05), (41.275, 53.05)],
             width=PIN_WIDTH)
    track(board, v33, (40.52, 53.05), (40.52, 61.025), width=RING_WIDTH)
    polyline(board, v33, [(39.85, 61.025), (40.52, 61.025), (41.275, 61.025)],
             width=PIN_WIDTH)
    polyline(board, v33, [(36.862, 54.95), (36.1, 55.7), (36.1, 59.75),
                          (40.52, 59.75)], width=PIN_WIDTH)

    # Watchdog input: U601 WDI to the R601 series resistor and the R602
    # pull-down that keeps the supervisor kicked if the GPIO floats.
    polyline(board, '/WATCHDOG_KICK', [(39.138, 54.95), (39.138, 55.9),
                                       (38.825, 56.3), (38.825, 56.8)],
             width=PIN_WIDTH)
    polyline(board, '/WATCHDOG_KICK', [(38.825, 56.8), (38.825, 57.6),
                                       (37.175, 58.4), (37.175, 58.8)],
             width=PIN_WIDTH)

    # Valve arm input and its pull-down, both east of U602.
    polyline(board, '/VALVE_EN_RAW', [(41.675, 64.5), (41.0, 63.8),
                                      (40.4, 62.975)], width=PIN_WIDTH)

    # Every ground pin drops into the B.Cu plane on its own via.
    for start, point in (((36.862, 54.0), (38.4, 54.0)),
                         ((43.275, 53.05), (44.4, 53.05)),
                         ((38.825, 58.8), (39.8, 57.9)),
                         ((43.275, 61.025), (44.4, 61.025)),
                         ((43.325, 64.5), (44.4, 64.5)),
                         ((32.175, 61.025), (31.1, 61.025)),
                         ((36.3, 62.975), (36.3, 64.6)),
                         ((33.7, 72.025), (35.6, 72.025)),
                         ((30.3, 72.025), (30.3, 70.6)),
                         ((26.825, 75.0), (28.0, 75.0)),
                         ((31.062, 79.45), (31.062, 80.8))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)
    # U603 2A/2B are strapped low so its spare gate cannot arm the relay.
    track(board, gnd, (30.3, 72.675), (30.3, 72.025), width=PIN_WIDTH)

    # C603 decouples the gate that arms mains, like C601 and C602 do for the
    # supervisor and the interlock gate.
    polyline(board, v33, [(30.3, 73.975), (30.3, 75.0), (30.725, 75.6)],
             width=PIN_WIDTH)
    track(board, gnd, (32.275, 75.6), (33.6, 75.6), width=PIN_WIDTH)
    via(board, gnd, (33.6, 75.6))

    # Relay chain: U603 1Y through the gate resistor, the off pull-down and
    # Q701 to the K701 coil and the D701 flyback diode.
    polyline(board, '/MAINS_RELAY_EN', [(30.3, 73.325), (29.0, 73.325),
                                        (27.25, 71.0)], width=PIN_WIDTH)
    polyline(board, '/MAINS_RELAY_GATE', [(25.175, 71.0), (25.175, 77.55),
                                          (31.062, 77.55)], width=PIN_WIDTH)
    polyline(board, '/MAINS_RELAY_RETURN', [(32.938, 78.5), (34.5, 78.5),
                                            (36.5, 76.5), (40.2, 76.5),
                                            (42.0, 74.7), (42.0, 73.25)],
             width=0.5)
    # West of the coil pins: the 24 V feed to K701.1 owns the east corridor.
    polyline(board, '/MAINS_RELAY_RETURN', [(42.0, 73.25), (39.5, 74.4),
                                            (39.5, 84.0), (43.5, 86.0)],
             width=0.5)


def route_valve_stage(board):
    """Low-side valve driver: F304, D305, D306, U502, Q501 and J113.

    The 24 V branch and the switched return run as a pair down the left edge
    and along y = 121 mm, so the gate chain between U502, R513, Q501 and R514
    keeps a clear corridor and no signal has to cross the power pair. The
    interlocked enable arriving from U602 is left for the signal pass.
    """
    gnd = '/GND_UI'
    v24, ret = '/24V_VALVE', '/VALVE_RETURN'

    # Fused branch: the 24 V trunk already lands on F304.1.
    track(board, '/24V_VALVE_FUSED', (13.4, 95.0), (16.0, 95.0), width=ACT_LANE_WIDTH)
    # D305 anode, D306 cathode and the long run to JP3 pin 1 on the left edge,
    # clear of the mains-free bottom band and of the sensor conditioning.
    track(board, v24, (20.0, 95.0), (20.0, 99.0), width=ACT_LANE_WIDTH)
    # The 24 V trunk to F304 runs along y = 93 mm, so the branch dips to B.Cu
    # for 2.6 mm to pass under it rather than carve a detour around the whole
    # sensor block; the plane loses only that slot.
    track(board, v24, (20.0, 95.0), (22.5, 95.0), width=ACT_LANE_WIDTH)
    via(board, v24, (22.5, 94.3), 1.0, 0.5)
    track(board, v24, (22.5, 94.3), (22.5, 91.7), pcb.B_Cu, width=ACT_LANE_WIDTH)
    via(board, v24, (22.5, 91.7), 1.0, 0.5)
    polyline(board, v24, [(22.5, 91.7), (2.2, 91.7), (2.2, 122.0),
                          (3.5, 124.0), (3.5, 125.3)], width=ACT_LANE_WIDTH)
    # Switched return: flyback cathode, Q501 drain and JP3 pin 2.
    polyline(board, ret, [(25.25, 99.0), (26.5, 100.3), (26.5, 121.0),
                          (6.0, 121.0), (6.0, 125.3)], width=ACT_LANE_WIDTH)
    track(board, ret, (23.678, 107.0), (26.5, 107.0), width=ACT_LANE_WIDTH)

    # 12 V driver supply: U502 VDD north to its two local capacitors.
    polyline(board, '/12V_PROTECTED', [(12.137, 100.05), (13.6, 98.6),
                                       (13.6, 96.5), (10.725, 96.5),
                                       (10.725, 97.1)], width=0.5)
    track(board, '/12V_PROTECTED', (10.725, 97.5), (8.775, 97.5), width=0.5)

    # Enable chain: R511 series and R512 pull-down into the driver input.
    polyline(board, '/VALVE_EN_DRV', [(5.825, 99.0), (7.8, 99.0), (8.8, 100.05),
                                      (9.4, 100.05)], width=PIN_WIDTH)
    polyline(board, '/VALVE_EN_DRV', [(4.175, 104.0), (4.175, 102.5),
                                      (6.9, 100.3), (6.9, 99.0), (6.25, 99.0)],
             width=PIN_WIDTH)

    # Gate chain: driver output, series resistor, MOSFET gate and pull-down.
    polyline(board, '/VALVE_GATE_RAW', [(12.137, 101.95), (13.3, 103.2),
                                        (13.3, 106.5), (14.75, 108.0)],
             width=PIN_WIDTH)
    polyline(board, '/VALVE_GATE', [(16.825, 108.0), (18.3, 106.8),
                                    (19.6, 106.05), (20.5, 106.05)],
             width=PIN_WIDTH)
    polyline(board, '/VALVE_GATE', [(18.3, 106.8), (18.3, 111.5),
                                    (19.9, 113.0)], width=PIN_WIDTH)

    for start, point in (((7.225, 97.5), (6.0, 97.5)),
                         ((12.275, 97.5), (12.275, 98.8)),
                         ((5.825, 104.0), (7.2, 104.0)),
                         ((21.825, 113.0), (23.2, 113.0))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)
    polyline(board, gnd, [(9.4, 101.0), (8.5, 101.5), (9.4, 101.95)],
             width=PIN_WIDTH)
    via(board, gnd, (8.5, 101.5))
    track(board, gnd, (21.062, 107.95), (21.062, 109.6), width=PIN_WIDTH)
    via(board, gnd, (21.062, 109.6))


def route_sensors(board):
    """Harness side of the NTC, flow, water, door and brew-unit contacts.

    Each input keeps its pull-up, series resistor and filter capacitor as a
    row, with the raw harness net brought up from the connector and the
    filtered net stopping at the capacitor. The 3V3 pull-up ends and the
    conditioned nets to the STM32 wait for the supply and signal passes.
    """
    gnd = '/GND_UI'

    # JP16 pins 3 and 4 are strapped: the brew-unit contact common.
    track(board, '/BU_BRIDGE', (3.0, 59.5), (3.0, 57.0), width=PIN_WIDTH)

    # Brew-unit present and working contacts (JP16 pins 6 and 8).
    polyline(board, '/BU_PRESENT_RAW', [(3.0, 52.0), (12.0, 52.0),
                                        (14.5, 51.175), (19.0, 51.175)],
             width=PIN_WIDTH)
    track(board, '/BU_PRESENT_N', (19.0, 52.825), (22.0, 52.775), width=PIN_WIDTH)
    # The working contact climbs east of MH1 and C501 so it never crosses the
    # present-contact row on its way to the second divider.
    polyline(board, '/BU_WORK_RAW', [(3.0, 47.0), (18.0, 47.0), (26.5, 50.5),
                                     (26.5, 56.5), (14.5, 56.5), (15.5, 58.175),
                                     (19.0, 58.175)], width=PIN_WIDTH)
    track(board, '/BU_WORK_N', (19.0, 59.825), (22.0, 59.775), width=PIN_WIDTH)

    # Door contact (JP14).
    polyline(board, '/DOOR_RAW', [(3.0, 73.5), (6.0, 73.5), (13.0, 71.825),
                                  (15.0, 71.825)], width=PIN_WIDTH)
    polyline(board, '/DOOR_RAW', [(15.475, 71.825), (16.5, 71.0),
                                  (17.6, 70.175)], width=PIN_WIDTH)
    track(board, '/DOOR_CLOSED_N', (18.0, 71.825), (21.0, 71.775), width=PIN_WIDTH)

    # NTC (JP13): raw net up the gap between the pull-up and the series part.
    polyline(board, '/NTC_RAW', [(29.0, 125.3), (29.5, 124.0), (29.5, 106.5),
                                 (30.4, 105.9), (31.0, 105.825)], width=PIN_WIDTH)
    polyline(board, '/NTC_RAW', [(29.5, 106.5), (29.5, 103.5), (28.0, 103.5),
                                 (28.0, 103.9)], width=PIN_WIDTH)
    polyline(board, '/NTC_ADC', [(31.0, 104.175), (32.5, 104.8), (33.6, 105.5)],
             width=PIN_WIDTH)

    # Flow meter (JP5): the raw net clears MH2 on the east side.
    polyline(board, '/FLOW_RAW', [(38.5, 125.3), (38.5, 122.0), (46.0, 118.0),
                                  (46.0, 101.5), (38.0, 101.5), (38.0, 102.9)],
             width=PIN_WIDTH)
    polyline(board, '/FLOW_RAW', [(46.0, 106.3), (41.8, 106.0), (41.0, 105.0)],
             width=PIN_WIDTH)
    polyline(board, '/FLOW_TIM', [(41.0, 103.175), (42.5, 103.9), (43.5, 104.775),
                                  (44.0, 104.775)], width=PIN_WIDTH)

    # Water level (JP22): east of the valve return pair, then west to R411.
    # West of the valve pair: the return already owns y = 121 mm eastwards.
    polyline(board, '/WATER_RAW', [(21.0, 128.2), (21.0, 126.8), (4.75, 126.8),
                                   (4.75, 120.0), (19.0, 120.0), (19.0, 117.0)],
             width=PIN_WIDTH)
    polyline(board, '/WATER_LEVEL', [(19.0, 115.175), (20.5, 115.9),
                                     (22.0, 116.775)], width=PIN_WIDTH)

    for start, point in (((31.5, 125.3), (33.2, 125.3)),
                         ((34.0, 104.225), (35.4, 104.225)),
                         ((41.0, 125.3), (40.2, 122.5)),
                         ((44.0, 103.225), (45.2, 102.6)),
                         ((23.0, 128.2), (24.6, 127.0)),
                         ((22.0, 115.225), (23.4, 115.225)),
                         ((21.0, 70.225), (22.4, 70.225)),
                         ((3.0, 71.0), (4.8, 71.0)),
                         ((22.0, 51.225), (23.4, 51.225)),
                         ((22.0, 58.225), (23.4, 58.225)),
                         ((3.0, 54.5), (4.8, 54.5)),
                         ((3.0, 49.5), (4.8, 49.5))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)


def route_12v_buck(board):
    """AP63200 24 V to 12 V stage in the top-right corner.

    The switch node is kept short between U303, the bootstrap capacitor and
    L302; the output capacitors sit past the inductor and the feedback divider
    runs back under them. The rail leaving this cluster towards J101 and F301
    waits for the supply pass, where it has to cross the 24 V lane.
    """
    gnd, sw = '/GND_UI', '/BUCK12_SW'
    out, fb = '/12V_ISO_RAW', '/BUCK12_FB'

    polyline(board, sw, [(123.638, 5.0), (125.7, 5.275), (129.275, 5.0)],
             width=0.6)
    polyline(board, '/BUCK12_BST', [(123.638, 4.05), (124.6, 3.725),
                                    (125.7, 3.725)], width=PIN_WIDTH)

    # Output bank: the two 1210 capacitors share the x = 139 mm column with a
    # ground pad between them, so the rail hops round their east side.
    polyline(board, out, [(134.725, 5.0), (137.0, 5.2), (139.0, 5.475)],
             width=0.5)
    polyline(board, out, [(139.0, 5.475), (136.0, 7.5), (136.0, 10.5),
                          (139.0, 11.975)], width=0.5)

    # Feedback. The divider now sits north-west of the switcher, so one line at
    # y = 3.4 mm collects R303, R302 and C314 and reaches pin 1 without meeting
    # the 24 V lane, which stays at y >= 5 mm all the way round C310.
    polyline(board, fb, [(120.702, 4.05), (120.2, 3.4), (108.825, 3.4)],
             width=PIN_WIDTH)
    for x in (108.825, 113.825, 117.825):
        track(board, fb, (x, 3.4), (x, 2.675), width=PIN_WIDTH)
    # Divider top end: a no-current sense line along the top edge back to the
    # inductor pad, clear of the switcher and bootstrap pads below it.
    polyline(board, out, [(112.175, 2.2), (112.175, 1.2), (134.725, 1.2),
                          (134.725, 3.3)], width=PIN_WIDTH)
    track(board, out, (116.175, 1.2), (116.175, 2.2), width=PIN_WIDTH)

    for start, point in (((118.975, 5.0), (118.975, 6.35)),
                         ((123.638, 5.95), (123.638, 8.0)),
                         ((139.0, 2.525), (136.8, 2.525)),
                         ((139.0, 9.025), (136.8, 9.025)),
                         ((107.175, 2.2), (105.8, 2.2))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)


def route_3v3_buck(board):
    """AP63203 12 V to 3.3 V stage, its 12 V input side and the rail telemetry.

    12V_FUSED crosses over D301 on the north side and 12V_PROTECTED leaves on
    the south, so the diode pair never has a track running across its own pads.
    The 3.3 V sense line back to pin 1 runs north of the switcher at
    y = 31.5 mm, clear of the bootstrap and switch nodes below it. The UI load
    switch around U302 is left for the next pass.
    """
    gnd, v33 = '/GND_UI', '/3V3_CORE'
    v12 = '/12V_PROTECTED'

    # The fused link passes under D301's own body on B.Cu rather than round it:
    # the gap north of the diode carries the 3.3 V spine.
    track(board, '/12V_FUSED', (86.4, 27.0), (88.0, 27.0), width=0.5)
    via(board, '/12V_FUSED', (88.0, 27.0), 0.8, 0.4)
    track(board, '/12V_FUSED', (88.0, 27.0), (95.0, 27.0), pcb.B_Cu, width=0.5)
    via(board, '/12V_FUSED', (95.0, 27.0), 0.8, 0.4)
    track(board, '/12V_FUSED', (95.0, 27.0), (97.0, 27.0), width=0.5)

    # Protected rail: one line south of the diodes, with stubs up into each
    # pad, and a branch down the west side into the switcher input pins.
    polyline(board, v12, [(93.0, 27.0), (92.8, 28.6), (92.8, 37.3),
                          (95.4, 36.95)], width=0.5)
    track(board, v12, (95.5, 36.95), (95.5, 36.0), width=0.5)
    track(board, v12, (92.8, 29.0), (109.05, 29.0), width=0.5)
    track(board, v12, (101.0, 29.0), (101.0, 27.9), width=0.5)
    track(board, v12, (109.05, 29.0), (109.05, 27.7), width=0.5)
    polyline(board, v12, [(99.0, 29.0), (99.0, 21.5), (100.0, 20.6),
                          (100.0, 20.2)], width=PIN_WIDTH)
    # Input HF capacitor: straight down from the second input pin.
    polyline(board, v12, [(95.4, 36.95), (95.7, 38.0), (96.3, 38.7)], width=0.5)

    # Switch and bootstrap nodes stay short and away from the sense line.
    polyline(board, '/SW_NODE', [(98.798, 36.0), (99.8, 36.2), (101.0, 37.0)],
             width=0.6)
    polyline(board, '/SW_NODE', [(102.775, 33.0), (102.775, 35.0), (102.0, 36.4)],
             width=0.6)
    polyline(board, '/BST_NODE', [(98.798, 35.05), (99.8, 34.2), (100.9, 33.0)],
             width=PIN_WIDTH)

    # 3.3 V: inductor down to the output bank, the HF capacitor, and the sense
    # line round the north of U301 back to pin 1. All of it west of the lane.
    polyline(board, v33, [(107.15, 37.0), (108.6, 36.2)], width=0.5)
    polyline(board, v33, [(107.15, 40.5), (108.6, 41.0)], width=0.5)
    polyline(board, v33, [(106.0, 41.8), (104.5, 42.6), (104.2, 43.6)], width=0.5)
    polyline(board, v33, [(105.5, 37.0), (105.0, 35.5), (105.0, 31.5),
                          (94.3, 31.5), (94.3, 35.05), (95.3, 35.05)],
             width=PIN_WIDTH)

    # 12 V rail telemetry beside the input, filtered node in one straight line.
    polyline(board, '/RAIL_12V_DIV', [(100.0, 18.175), (100.0, 17.3),
                                      (103.0, 17.3), (103.0, 18.175)],
             width=PIN_WIDTH)
    track(board, '/RAIL_12V_ADC', (103.0, 19.825), (109.0, 19.8), width=PIN_WIDTH)

    # The switcher's ground pin reaches the plane through the input capacitor's
    # own pad, so the input loop closes in copper before it reaches a via.
    track(board, gnd, (98.138, 36.95), (98.138, 38.7), width=0.5)
    polyline(board, gnd, [(98.0, 39.0), (99.2, 39.6)], width=0.5)
    via(board, gnd, (99.2, 39.6))

    for start, point in (((110.95, 36.0), (110.95, 33.8)),
                         ((110.95, 41.0), (110.95, 38.5)),
                         ((105.775, 44.0), (106.5, 45.2)),
                         ((110.95, 27.0), (110.95, 24.5)),
                         ((105.0, 27.0), (107.3, 27.0)),
                         ((106.0, 18.175), (106.0, 16.8)),
                         ((109.0, 18.225), (109.0, 16.8))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)


def route_ui_load_switch(board):
    """TPS22918 that gates 3.3 V to the front panel, plus its 3.3 V feed.

    PS701's footprint closes this pocket off at x = 101.25 mm, so the parts sit
    west and north of the switch and the 3.3 V rail comes in along y = 43 mm
    and down the free column at x = 91.6 mm, west of the capacitor stack.
    """
    gnd, v33 = '/GND_UI', '/3V3_CORE'

    polyline(board, v33, [(104.225, 44.0), (103.0, 43.0), (92.5, 43.0),
                          (91.6, 44.0), (91.6, 53.6), (93.275, 53.6)],
             width=0.5)
    polyline(board, v33, [(91.6, 51.5), (95.275, 51.5), (95.275, 50.4)],
             width=0.5)
    track(board, v33, (95.725, 50.05), (96.9, 50.05), width=0.5)

    polyline(board, '/UI_PWR_EN', [(95.275, 53.6), (96.2, 52.8), (96.9, 52.2)],
             width=PIN_WIDTH)
    polyline(board, '/UI_RISE', [(99.638, 52.25), (98.4, 52.4), (97.725, 53.4)],
             width=PIN_WIDTH)
    track(board, '/3V3_UI', (99.638, 51.0), (99.638, 50.05), width=0.5)
    polyline(board, '/3V3_UI', [(99.638, 49.9), (99.0, 48.5), (97.5, 46.8),
                                (96.9, 45.9)], width=0.5)

    for start, point in (((93.725, 50.05), (92.6, 50.05)),
                         ((96.9, 51.0), (96.3, 51.2)),
                         ((99.275, 53.7), (100.4, 53.7)),
                         ((98.275, 45.5), (99.4, 45.5))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)


def route_3v3_distribution(board):
    """Spine from the 3.3 V buck to the logic, debug headers and pull-ups.

    One line leaves the buck along y = 43 mm. A northern branch climbs the
    1.1 mm gap between F301 and D301 at x = 90.9 mm, runs over the top of the
    ESP32 at y = 2.5 mm and drops into its supply pins, and a western branch
    runs under the 24 V trunk at y = 54.2 mm to the supervisor spine and on to
    the sensor pull-ups. The bottom-row pull-ups and J109 still wait: the 24 V
    valve branch crosses the board at y = 93 mm and needs a hop to reach them.
    """
    v33 = '/3V3_CORE'

    # Northern branch: ESP32 supply pins, its straps and the UART header.
    polyline(board, v33, [(95.5, 43.0), (90.9, 43.0), (90.9, 3.5), (89.0, 2.5),
                          (44.6, 2.5), (43.9, 4.0), (43.9, 13.825)], width=0.5)
    for y in (6.975, 10.375, 13.825):
        track(board, v33, (43.9, y), (42.9, y), width=PIN_WIDTH)
    track(board, v33, (43.9, 7.06), (44.8, 7.06), width=PIN_WIDTH)
    polyline(board, v33, [(64.5, 2.5), (64.5, 22.35), (65.6, 22.825)],
             width=PIN_WIDTH)
    polyline(board, v33, [(75.0, 2.5), (75.0, 9.3)], width=PIN_WIDTH)

    # STM32 side: the reset pull-up is fed from the bulk capacitor at the
    # corner of the supply ring, which leaves the column east of R101 free for
    # the reset net itself. The SWD header hangs off the pin 1/64 feed.
    polyline(board, v33, [(71.9, 32.375), (72.5, 31.5), (73.9, 31.0)],
             width=PIN_WIDTH)

    # Western branch: it slips between the 24 V trunk at y = 55.1 mm and the
    # capacitor column, joins the supervisor spine and carries on west.
    # Western spine. Two 24 V branches climb across its path, at x = 46.4 mm to
    # the brew fuse and at x = 62.5 mm to the measurement header, so it passes
    # under each on B.Cu. It runs in the 1.1 mm gap between the supervisor
    # capacitors and the 24 V trunk below them.
    polyline(board, v33, [(91.6, 53.6), (91.6, 54.0), (63.9, 54.0)], width=0.4)
    for east, west in (((63.9, 54.0), (61.1, 54.0)),
                       ((47.8, 54.0), (45.0, 54.0))):
        via(board, v33, east)
        track(board, v33, east, west, pcb.B_Cu, width=0.4)
        via(board, v33, west)
    track(board, v33, (61.1, 54.0), (47.8, 54.0), width=0.4)
    track(board, v33, (45.0, 54.0), (40.52, 54.0), width=0.4)

    # Reset pull-up, under the reset corridor that shares this lane.
    polyline(board, v33, [(40.52, 54.0), (40.0, 52.2), (39.4, 51.6)],
             width=PIN_WIDTH)
    via(board, v33, (39.4, 51.6))
    track(board, v33, (39.4, 51.6), (39.4, 49.6), pcb.B_Cu, width=PIN_WIDTH)
    via(board, v33, (39.4, 49.6))
    polyline(board, v33, [(39.4, 49.6), (39.9, 48.6)], width=PIN_WIDTH)

    # Measurement header, from the spine between the two hops.
    track(board, v33, (50.25, 54.0), (50.25, 53.5), width=PIN_WIDTH)
    via(board, v33, (50.25, 53.5))
    track(board, v33, (50.25, 53.5), (50.25, 49.3), pcb.B_Cu, width=PIN_WIDTH)
    via(board, v33, (50.25, 49.3))
    polyline(board, v33, [(50.25, 49.3), (50.5, 41.5), (50.54, 40.85)],
             width=PIN_WIDTH)

    # Far west: out of the supervisor block south of R604, then to the arm
    # gate and the sensor pull-ups.
    polyline(board, v33, [(41.725, 61.025), (41.725, 62.0), (42.5, 62.8),
                          (42.5, 67.0), (32.0, 67.0), (32.0, 73.975),
                          (31.2, 73.975)], width=PIN_WIDTH)
    polyline(board, v33, [(32.0, 67.0), (16.0, 68.0), (15.0, 69.0),
                          (15.0, 69.7)], width=PIN_WIDTH)
    # The motor outputs run west to J108 at y = 62 and 64.5 mm, so the feed to
    # the contact pull-ups passes under both on B.Cu in one hop.
    polyline(board, v33, [(16.0, 68.0), (13.5, 67.0)], width=PIN_WIDTH)
    via(board, v33, (13.5, 67.0))
    track(board, v33, (13.5, 67.0), (13.5, 60.0), pcb.B_Cu, width=PIN_WIDTH)
    via(board, v33, (13.5, 60.0))
    polyline(board, v33, [(13.5, 60.0), (13.5, 52.825), (15.6, 52.825)],
             width=PIN_WIDTH)
    track(board, v33, (13.5, 59.825), (15.6, 59.825), width=PIN_WIDTH)


def route_logic_grounds(board):
    """Drop the USB and ESP32 ground pins into the B.Cu plane."""
    gnd = '/GND_UI'
    for start, point in (((23.775, 19.0), (24.9, 19.0)),
                         ((23.775, 22.0), (24.9, 22.0)),
                         ((27.0, 17.175), (27.0, 15.9)),
                         ((35.798, 16.0), (37.8, 16.5)),
                         ((42.5, 15.625), (41.4, 15.0)),
                         ((42.5, 5.425), (41.4, 4.8)),
                         ((42.5, 8.825), (41.4, 9.4)),
                         ((45.25, 5.79), (46.6, 4.8)),
                         ((62.75, 5.79), (61.4, 4.8)),
                         ((44.825, 27.0), (45.9, 27.6)),
                         ((48.825, 27.0), (49.9, 27.6)),
                         ((32.75, 8.495), (31.4, 9.6)),
                         ((39.25, 8.495), (40.6, 9.6))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)


def route_reset_tree(board):
    """STM_NRST from the MCU to its pull-up, filter, SWD header and the gates.

    The MCU pin escapes west, drops south of the package and runs east at
    y = 47 mm to the column at x = 88.8 mm, which serves R101, C101 and the
    SWD header. A second leg goes west at y = 45 mm and down to y = 50.5 mm,
    where it passes under the 24 V branch at x = 46.4 mm and enters the 1.35 mm
    channel west of the supervisor that was left empty for it.
    """
    nrst = '/STM_NRST'

    # The pin escapes west on its own row, because the west pads sit on a
    # 0.5 mm pitch, then drops to y = 50.5 mm and runs west under two 24 V
    # branches into the 1.35 mm channel left empty for it beside C501.
    polyline(board, nrst, [(70.325, 39.25), (66.0, 39.25), (63.8, 40.8),
                           (63.8, 50.5)], width=PIN_WIDTH)
    via(board, nrst, (63.8, 50.5))
    track(board, nrst, (63.8, 50.5), (61.2, 50.5), pcb.B_Cu, width=PIN_WIDTH)
    via(board, nrst, (61.2, 50.5))
    polyline(board, nrst, [(61.2, 50.5), (47.6, 50.5)], width=PIN_WIDTH)
    via(board, nrst, (47.6, 50.5))
    track(board, nrst, (47.6, 50.5), (45.2, 50.5), pcb.B_Cu, width=PIN_WIDTH)
    via(board, nrst, (45.2, 50.5))
    polyline(board, nrst, [(45.2, 50.5), (36.0, 50.5), (34.9, 51.8),
                           (34.9, 65.9)], width=PIN_WIDTH)
    track(board, nrst, (34.9, 61.675), (35.7, 61.675), width=PIN_WIDTH)
    track(board, nrst, (34.9, 53.05), (36.3, 53.05), width=PIN_WIDTH)
    # Pull-up and filter, both on this corridor.
    track(board, nrst, (41.825, 50.5), (41.825, 49.1), width=PIN_WIDTH)
    track(board, nrst, (43.375, 50.5), (43.375, 49.1), width=PIN_WIDTH)
    # Under the 3.3 V branch that crosses west at y = 67 mm.
    via(board, nrst, (34.9, 65.9))
    track(board, nrst, (34.9, 65.9), (34.9, 68.2), pcb.B_Cu, width=PIN_WIDTH)
    via(board, nrst, (34.9, 68.2))
    polyline(board, nrst, [(34.9, 68.2), (34.9, 71.0), (36.5, 71.0),
                           (36.5, 73.325), (34.4, 73.325)], width=PIN_WIDTH)
    # Two reset points stay open: U602 pin 6, whose only approach is the
    # 0.87 mm gap east of the package that the valve arm net already uses, and
    # the SWD header's reset pin, which would have to cross the decoupling
    # link north of the MCU.


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
    route_mains_input(board)
    route_24v_output(board)
    route_h_bridge(board)
    route_watchdog_interlock(board)
    route_valve_stage(board)
    route_sensors(board)
    route_12v_buck(board)
    route_3v3_buck(board)
    route_ui_load_switch(board)
    route_3v3_distribution(board)
    route_logic_grounds(board)
    route_reset_tree(board)
    selv_ground_plane(board)
    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    result = {
        'status': 'critical_routing_in_progress_not_fabricable',
        'routed_blocks': ['USB-C reversible fanout', 'USB ESD-to-series-pair', 'USB series-to-ESP32',
                          'STM32 VDD ring, VSS vias and decoupling',
                          'provisional SELV GND_UI plane on B.Cu',
                          'mains input: J118, F701, F702, RV701, K701 and PS701',
                          '24 V: PS701, J121 and all 24V_ACT_RAW loads',
                          'DRV8876 H-bridge: outputs to J108, VM, charge pump and control rows',
                          'watchdog supply, interlock gates and the K701 coil driver',
                          'valve branch: F304, D305, D306, U502, Q501 and J113',
                          'sensor harness side: NTC, flow, water, door and contacts',
                          '24 V to 12 V buck: switch node, output bank and feedback',
                          '12 V to 3.3 V buck, its input side and the 12 V telemetry',
                          'UI load switch and the 3.3 V feed into its pocket',
                          '3.3 V spine to the logic, headers and pull-ups',
                          'USB and ESP32 ground pins into the plane',
                          'reset tree: MCU, pull-up, filter, SWD header and the gates'],
        'track_segments': sum(isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA)
                              for item in check.GetTracks()),
        'vias': sum(isinstance(item, pcb.PCB_VIA) for item in check.GetTracks()),
        'remaining_blocks': ['heater, pump and grinder stages',
                             '3V3 trunk and remaining decoupling', 'logic', 'sensors',
                             '24 V actuators', 'final domain copper fills'],
    }
    REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
