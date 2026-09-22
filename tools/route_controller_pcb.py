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
# Logic signals between the MCU and its peripherals; 0.2 mm is the Default
# class width and lets a track pass between two 2.54 mm-pitch THT pads.
SIGNAL_WIDTH = 0.20

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
    """Join the two contact rows of the top-entry Type-C and fan them out.

    The north row (A) faces the south row (B) mirrored, so each data net has
    one pad in each row and the pair swaps order between them. The receptacle
    is SMD, so B.Cu under its body is free: A6 and A7 drop through vias just
    north of the row and run south underneath. DP joins its south pad on B.Cu
    at the via below B6; DM crosses back to F.Cu below B7 and continues there.
    """
    dp, dm = '/USB_DP_PORT', '/USB_DM_PORT'
    track(board, dp, (35.75, 4.15), (35.75, 2.95))
    via(board, dp, (35.75, 2.95))
    polyline(board, dp, [(35.75, 2.95), (35.75, 7.10), (36.10, 7.45)], pcb.B_Cu)
    track(board, dp, (36.25, 5.85), (36.10, 7.45))
    via(board, dp, (36.10, 7.45))

    polyline(board, dm, [(36.25, 4.15), (36.25, 3.30), (36.60, 2.95),
                         (36.60, 2.60)])
    via(board, dm, (36.60, 2.60))
    polyline(board, dm, [(36.60, 2.60), (36.80, 2.80), (36.80, 7.90),
                         (36.20, 8.50), (35.30, 8.50)], pcb.B_Cu)
    via(board, dm, (35.30, 8.50))
    polyline(board, dm, [(35.75, 5.85), (35.75, 6.60), (35.30, 7.05),
                         (35.30, 14.90), (35.138, 15.05)])

    # DP runs south on F.Cu and hops under U203's ground stub on B.Cu.
    polyline(board, dp, [(36.10, 7.45), (36.30, 7.65), (36.30, 11.60),
                         (36.70, 12.00)])
    via(board, dp, (36.70, 12.00))
    polyline(board, dp, [(36.70, 12.00), (36.70, 16.45), (36.20, 16.95)], pcb.B_Cu)
    via(board, dp, (36.20, 16.95))
    track(board, dp, (36.20, 16.95), (35.138, 16.95))

    # CC1 leaves north over the shell leg to R223; CC2 leaves the south row
    # east of the pair to R224.
    polyline(board, '/USB_CC1', [(35.25, 4.15), (35.25, 3.45), (35.10, 3.30),
                                 (35.10, 1.80),
                                 (34.70, 1.40), (31.20, 1.40), (30.45, 2.15),
                                 (30.45, 3.375)], width=PIN_WIDTH)
    polyline(board, '/USB_CC2', [(36.75, 5.85), (36.75, 6.70), (37.35, 7.30),
                                 (37.35, 11.80), (38.05, 12.50), (38.675, 12.50)],
             width=PIN_WIDTH)

    # Each ground pin goes to the shell leg beside it, which is on the plane.
    gnd = '/GND_UI'
    for pin, leg in (((33.25, 4.15), (33.60, 2.85)), ((33.25, 5.85), (33.60, 7.15)),
                     ((38.75, 4.15), (38.40, 2.85)), ((38.75, 5.85), (38.40, 7.15))):
        track(board, gnd, pin, leg, width=PIN_WIDTH)


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
        track(board, l_in, (106.04, 122.10), (104.50, 118.00), layer, width=2.2)
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

    polyline(board, neutral, [(113.96, 122.10), (113.96, 116.50),
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
                         ((26.825, 75.0), (28.0, 75.0)),
                         ((31.062, 79.45), (31.062, 80.8))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)
    # U603 2A/2B are strapped low so its spare gate cannot arm the relay.

    # C603 decouples the gate that arms mains, like C601 and C602 do for the
    # supervisor and the interlock gate.
    polyline(board, v33, [(30.3, 73.975), (30.3, 75.0), (30.725, 75.6)],
             width=PIN_WIDTH)
    track(board, gnd, (32.275, 75.6), (33.6, 75.6), width=PIN_WIDTH)
    via(board, gnd, (33.6, 75.6))

    # Relay chain: U603 1Y through the gate resistor, the off pull-down and
    # Q701 to the K701 coil and the D701 flyback diode.
    # Straight west before turning north, so that the pocket beside pin 6
    # stays free for its reset via.
    polyline(board, '/MAINS_RELAY_EN', [(30.3, 73.325), (27.6, 73.325),
                                        (27.6, 71.6), (27.1, 71.0)],
             width=PIN_WIDTH)
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
    # The lane at x = 43.5 mm keeps clear of MH2 to the west and of the heater
    # optocoupler's primary pads to the east.
    # The lane sits between MH2 and the heater optocoupler's primary pads, and
    # both flow pull-up and series resistor now present their raw pad on the
    # same row, so the filtered net leaves straight east underneath.
    polyline(board, '/FLOW_RAW', [(38.5, 125.3), (38.5, 122.0), (35.3, 118.0),
                                  (35.3, 102.0), (36.5, 103.175),
                                  (41.0, 103.175)], width=PIN_WIDTH)
    track(board, '/FLOW_TIM', (41.0, 104.825), (44.0, 104.775), width=PIN_WIDTH)

    # Water level (JP22): east of the valve return pair, then west to R411.
    # West of the valve pair: the return already owns y = 121 mm eastwards.
    polyline(board, '/WATER_RAW', [(21.0, 128.2), (21.0, 126.8), (4.75, 126.8),
                                   (4.75, 120.0), (19.0, 120.0), (19.0, 117.0)],
             width=PIN_WIDTH)
    polyline(board, '/WATER_LEVEL', [(19.0, 115.175), (20.5, 115.9),
                                     (22.0, 116.775)], width=PIN_WIDTH)

    for start, point in (((31.5, 125.3), (33.2, 125.3)),
                         ((34.0, 104.225), (34.0, 102.3)),
                         ((41.0, 125.3), (40.2, 122.5)),
                         ((44.0, 103.225), (44.0, 101.3)),
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
    polyline(board, v33, [(64.5, 2.5), (64.5, 20.7), (65.6, 21.175)],
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
    for start, point in (((23.775, 19.0), (24.9, 17.8)),
                         ((23.775, 22.0), (24.9, 22.0)),
                         ((27.0, 17.175), (27.0, 15.9)),
                         ((35.798, 16.0), (37.8, 16.5)),
                         ((42.5, 15.625), (41.4, 15.0)),
                         ((42.5, 5.425), (41.4, 4.8)),
                         ((42.5, 8.825), (41.4, 9.4)),
                         ((45.25, 5.79), (46.6, 4.8)),
                         ((62.75, 5.79), (61.4, 4.8)),
                         ((30.45, 5.025), (30.45, 6.0)),
                         ((40.325, 12.5), (41.3, 12.5))):
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
    # U603 pin 2 is reached from the east. The loop keeps 0.7 mm clear of
    # pin 3 so that the heater interlock can drop to B.Cu inside it.
    polyline(board, nrst, [(34.9, 68.2), (34.9, 71.0), (37.2, 71.0),
                           (37.2, 73.325), (34.4, 73.325)], width=PIN_WIDTH)
    # U603 pin 6, the heater gate's reset input: out west into the pocket
    # between pins 5 and 7, then under the package on B.Cu to the same via.
    track(board, nrst, (29.5, 72.675), (28.85, 72.6), width=PIN_WIDTH)
    via(board, nrst, (28.85, 72.6))
    track(board, nrst, (28.85, 72.6), (34.9, 68.2), pcb.B_Cu, width=PIN_WIDTH)
    # Two reset points stay open: U602 pin 6, whose only approach is the
    # 0.87 mm gap east of the package that the valve arm net already uses, and
    # the SWD header's reset pin, which would have to cross the decoupling
    # link north of the MCU.


def route_usb_power(board):
    """Service-USB rail: VBUS from the connector to the ESD part, the sense
    divider, the resettable fuse and the bench-power jumper.

    U203 carries VBUS on the middle pin of its west side, with the protected
    data pair leaving on either side of it, so that pin is reached on B.Cu
    from the connector rather than through its own fanout.
    """
    vbus = '/USB_VBUS'
    # Each VBUS column joins its two rows across the gap between them. The
    # east column climbs to a via and crosses to the west on B.Cu, north of
    # the connector and down its west side, clear of the data pair.
    for x in (34.75, 37.25):
        track(board, vbus, (x, 4.15), (x, 5.85), width=0.3)
    track(board, vbus, (37.25, 4.15), (37.25, 1.70), width=0.3)
    via(board, vbus, (37.25, 1.70))
    polyline(board, vbus, [(37.25, 1.70), (31.40, 1.70), (31.40, 10.60),
                           (31.0, 11.0)], pcb.B_Cu, width=0.5)
    track(board, vbus, (34.75, 5.85), (34.75, 6.60), width=0.3)
    polyline(board, vbus, [(34.75, 6.60), (34.75, 7.80), (33.55, 9.0),
                           (31.0, 11.0)], width=0.4)
    polyline(board, vbus, [(31.0, 11.0), (27.0, 11.6), (25.175, 12.4),
                           (25.175, 12.6)], width=0.5)
    via(board, vbus, (31.0, 11.0))
    track(board, vbus, (31.0, 11.0), (31.6, 16.0), pcb.B_Cu, width=0.5)
    via(board, vbus, (31.6, 16.0))
    track(board, vbus, (31.6, 16.0), (32.4, 16.0), width=0.5)
    polyline(board, vbus, [(24.9, 13.3), (21.0, 16.0), (21.0, 21.6),
                           (21.9, 22.0)], width=0.5)
    polyline(board, vbus, [(21.9, 22.0), (20.0, 22.5), (17.0, 22.5),
                           (16.6, 23.4)], width=0.5)

    polyline(board, '/USB_VBUS_FUSED', [(19.4, 24.0), (19.4, 26.0),
                                        (20.35, 26.8)], width=0.5)
    # The bench jumper's far side reaches D303 round the south of the diode.
    polyline(board, '/USB_BENCH_ENABLE', [(21.65, 27.25), (22.5, 28.5),
                                          (23.0, 31.3), (32.0, 31.3),
                                          (32.0, 29.8)], width=PIN_WIDTH)

    sense = '/USB_VBUS_SENSE'
    polyline(board, sense, [(26.825, 13.0), (28.2, 14.0), (28.2, 19.5),
                            (27.3, 18.825)], width=PIN_WIDTH)
    polyline(board, sense, [(26.7, 18.825), (25.6, 19.8), (25.0, 20.8),
                            (22.225, 20.8), (22.225, 19.4)], width=PIN_WIDTH)
    polyline(board, sense, [(28.2, 19.5), (29.0, 20.5), (29.0, 25.5),
                            (56.0, 25.5), (57.175, 24.0)], width=PIN_WIDTH)

    polyline(board, '/ESP_BOOT0', [(65.525, 22.825), (64.0, 22.6),
                                   (63.3, 22.3)], width=PIN_WIDTH)


def route_earth_and_heater_return(board):
    """Protective-earth bond and the heater's neutral return.

    JP1 comes from the boiler body and JP9 from the mains inlet, so the board
    is the junction between them: the bond is doubled on both layers like a
    load phase, because it has to carry fault current until the upstream
    protective device opens.

    The boiler element measures 27.5 ohm, so it draws 8.4 A at 230 V. Its
    return goes straight to neutral on tab 3, the tab nearest the board edge;
    the switched live waits on tab 1 for the triac at the heatsink.
    """
    pe, neutral = '/PROTECTIVE_EARTH', '/MAINS_N'
    for layer in (pcb.F_Cu, pcb.B_Cu):
        track(board, pe, (121.5, 124.0), (128.0, 124.0), layer,
              width=MAINS_PHASE_WIDTH)
    via(board, pe, (124.75, 124.0), MAINS_VIA, MAINS_DRILL)

    # Neutral leaves JP17 south of the connector row and runs west under it.
    # The stub out of the pad is narrowed, like the phase, to hold 1.2 mm to
    # the unused middle pin of the VH connector.
    # Every tab of the TE 1971845-4 solders through two tails, 5 mm apart.
    # Tab 3 has them at 79.25 and 84.25 mm, y = 126.55. The run climbs over
    # the polarizing-post hole at (86.9, 129.05) and drops onto the east tail.
    for layer in (pcb.F_Cu, pcb.B_Cu):
        track(board, neutral, (113.96, 122.1), (113.96, 124.0), layer, width=2.2)
        polyline(board, neutral, [(113.96, 124.0), (113.96, 127.5),
                                  (92.0, 127.5), (89.5, 125.0), (86.5, 125.0),
                                  (84.25, 126.55), (79.25, 126.55)], layer,
                 width=MAINS_PHASE_WIDTH)
    for point in ((113.96, 126.0), (105.0, 127.5), (96.0, 127.5),
                  (88.0, 125.0)):
        via(board, neutral, point, MAINS_VIA, MAINS_DRILL)

    # Tabs 2 and 4 are not wired, but each one is a single piece of metal on
    # two tails, so their pads are joined to keep the floating tab whole.
    for tab, y in (('2', 121.55), ('4', 131.55)):
        track(board, f'unconnected-(J116-Pad{tab})', (76.75, y), (81.75, y),
              width=MAINS_LIGHT_WIDTH)


def route_heater_enable(board):
    """HEATER_EN_RAW into U603's second gate and its output down to R707.

    Pin 5 climbs to a B.Cu hop under the 3.3 V branch and reaches the R711
    pull-down from the east. Pin 3 is fenced in by the ground stub of pin 4
    and the reset loop of pin 2, so it drops to B.Cu inside the loop and runs
    south under the relay-return and 12 V branches to the LED driver's gate
    resistor. The MCU side of HEATER_EN_RAW (PB10) waits with the other STM32
    signals.
    """
    raw, gated = '/HEATER_EN_RAW', '/HEATER_EN_INTERLOCK'
    polyline(board, raw, [(29.5, 72.025), (29.7, 71.8), (29.7, 69.0)],
             width=PIN_WIDTH)
    via(board, raw, (29.7, 69.0))
    track(board, raw, (29.7, 69.0), (30.0, 66.0), pcb.B_Cu, width=PIN_WIDTH)
    via(board, raw, (30.0, 66.0))
    track(board, raw, (30.0, 66.0), (28.825, 66.0), width=PIN_WIDTH)

    track(board, gated, (33.7, 72.675), (36.5, 72.675), width=PIN_WIDTH)
    via(board, gated, (36.5, 72.675))
    polyline(board, gated, [(36.5, 72.675), (36.5, 90.0), (29.4, 97.1),
                            (29.4, 100.0)], pcb.B_Cu, width=PIN_WIDTH)
    via(board, gated, (29.4, 100.0))
    track(board, gated, (29.4, 100.0), (30.175, 99.0), width=PIN_WIDTH)


# A barrier optocoupler sits on x = 51 with its rows at 47.19 and 54.81 mm.
# Tracks reach its pads through short stubs that stay wholly inside the
# 'optocoupler barrier slot' area, the only place where the rules accept less
# than 8 mm between the rows; everything beyond the stub ends is 8 mm clear.
OPTO_SELV_STUB = (45.85, 46.6)
OPTO_MAINS_STUB = (55.3, 56.3)
OPTO_SELV_STUB_END, OPTO_MAINS_STUB_END = OPTO_SELV_STUB[0], OPTO_MAINS_STUB[1]


def opto_stubs(board, ref, pins, layer=pcb.F_Cu):
    """Stub each listed optocoupler pin to the edge of its slot area."""
    pads = {int(pad.GetNumber()): pad for pad in board.FindFootprintByReference(ref).Pads()}
    for number, netname in pins.items():
        y = pcb.ToMM(pads[number].GetPosition().y)
        x0, x1 = OPTO_SELV_STUB if number <= 3 else OPTO_MAINS_STUB
        track(board, netname, (x0, y), (x1, y), layer, width=PIN_WIDTH)


def route_heater_stage(board):
    """Zero-cross optocoupler and triac for the 1900 W boiler element.

    The optocoupler is a 300 mil DIP straddling the barrier over the slot its
    footprint mills between the rows. Its secondary pins are through-hole, so
    the gate and the feed leave on B.Cu, where the mains domain has no plane
    and there is room to keep 2.5 mm between them. That frees the 5 mm lane
    west of the heatsink for the switched phase, which is the only heavy net
    that has to get past.
    """
    gnd = '/GND_UI'

    # LED loop. The 12 V rail is picked up from the valve driver's own feed.
    # The rail hops under the valve return, which climbs at x = 26.5 mm.
    polyline(board, '/12V_PROTECTED', [(13.6, 98.6), (14.8, 100.5),
                                       (14.8, 101.6), (25.3, 101.6)], width=0.5)
    via(board, '/12V_PROTECTED', (25.3, 101.6))
    track(board, '/12V_PROTECTED', (25.3, 101.6), (27.7, 101.6), pcb.B_Cu, width=0.5)
    via(board, '/12V_PROTECTED', (27.7, 101.6))
    polyline(board, '/12V_PROTECTED', [(27.7, 101.6), (28.0, 101.3),
                                       (28.0, 94.2), (34.5, 94.2),
                                       (35.175, 95.5)], width=0.5)
    polyline(board, '/HEATER_LED_ANODE', [(36.825, 96.0), (39.5, 96.3),
                                          (44.5, 97.46),
                                          (OPTO_SELV_STUB_END, 97.46)],
             width=PIN_WIDTH)
    polyline(board, '/HEATER_LED_RETURN', [(38.938, 99.5), (41.0, 99.8),
                                           (OPTO_SELV_STUB_END, 100.0)],
             width=PIN_WIDTH)
    opto_stubs(board, 'U701', {1: '/HEATER_LED_ANODE', 2: '/HEATER_LED_RETURN'})
    track(board, '/HEATER_LED_GATE', (31.825, 99.0), (31.825, 96.0), width=PIN_WIDTH)
    polyline(board, '/HEATER_LED_GATE', [(31.825, 99.0), (34.0, 98.8),
                                         (36.5, 98.55)], width=PIN_WIDTH)
    for start, point in (((30.175, 96.0), (28.9, 96.0)),
                         ((37.062, 100.45), (37.062, 101.9))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)

    # Switched phase: K701 down the lane, then into the middle terminal from
    # the 3 mm strip between the heatsink foot and the device row.
    polyline(board, '/LOAD_L_ENABLED', [(62.0, 80.75), (62.0, 82.2),
                                        (59.6, 84.6), (59.6, 106.5)], width=3.0)
    track(board, '/LOAD_L_ENABLED', (59.6, 106.5), (59.6, 108.8), width=2.0)
    polyline(board, '/LOAD_L_ENABLED', [(59.6, 106.5), (71.0, 106.5),
                                        (71.0, 108.8)], width=0.9)

    # Gate feed and gate, both on the back layer past the optocoupler.
    opto_stubs(board, 'U701', {4: '/HEATER_GATE_FEED', 6: '/HEATER_TRIAC_GATE'},
               pcb.B_Cu)
    polyline(board, '/HEATER_GATE_FEED', [(OPTO_MAINS_STUB_END, 102.54),
                                          (56.6, 104.0), (56.6, 106.2)],
             pcb.B_Cu, width=PIN_WIDTH)
    via(board, '/HEATER_GATE_FEED', (56.6, 106.2))
    track(board, '/HEATER_GATE_FEED', (56.6, 106.2), (56.6, 108.0), width=PIN_WIDTH)
    polyline(board, '/HEATER_TRIAC_GATE', [(OPTO_MAINS_STUB_END, 97.46), (60.8, 98.8),
                                           (60.8, 112.0), (73.54, 112.0),
                                           (73.54, 110.2)], pcb.B_Cu,
             width=PIN_WIDTH)

    # Element side: out of the first terminal and down to JP19 tab 1.
    track(board, '/HEATER_AC_SWITCHED', (68.46, 110.2), (68.46, 112.0), width=1.5)
    # Into both tails of JP19 tab 1, at 79.25 and 84.25 mm.
    polyline(board, '/HEATER_AC_SWITCHED', [(68.46, 112.0), (70.5, 114.5),
                                            (77.0, 116.55), (84.25, 116.55)],
             width=2.5)
    track(board, '/HEATER_AC_SWITCHED', (79.25, 116.55), (84.25, 116.55),
          pcb.B_Cu, width=2.5)


def route_pump_stage(board):
    """Zero-cross optocoupler and triac for the ULKA pump, the heater's twin.

    U702 crosses the barrier one step south of U701 and Q704 stands on the
    east half of the heatsink. The switched phase reaches Q704 along the
    strip under the heatsink foot that already feeds Q703, and R712 takes it
    from R710's pad in the lane. The gate is the only net that runs the
    35 mm to the triac: on B.Cu, south of the heater gate and north of JP19's
    tab 1, holding 2.5 mm to both. The pump current is 0.4 A, so its own
    tracks stay at 1.2 mm, narrow enough to keep 2.5 mm between the two JP24
    pads.
    """
    gnd = '/GND_UI'

    # LED loop on the SELV side. 12 V comes from JP5 pin 3 on B.Cu along the
    # plane edge; the gate network sits north of Q706, clear of MH2.
    polyline(board, '/12V_PROTECTED', [(43.5, 125.3), (45.3, 123.5),
                                       (45.3, 108.4)], pcb.B_Cu, width=0.5)
    via(board, '/12V_PROTECTED', (45.3, 108.4))
    track(board, '/12V_PROTECTED', (45.3, 108.4), (45.3, 109.775), width=0.5)
    polyline(board, '/PUMP_LED_ANODE', [(45.3, 111.425), (45.85, 111.975),
                                        (OPTO_SELV_STUB_END, 113.46)],
             width=PIN_WIDTH)
    track(board, '/PUMP_LED_RETURN', (44.737, 116.0), (OPTO_SELV_STUB_END, 116.0),
          width=PIN_WIDTH)
    opto_stubs(board, 'U702', {1: '/PUMP_LED_ANODE', 2: '/PUMP_LED_RETURN'})
    track(board, '/PUMP_LED_GATE', (44.125, 106.6), (44.125, 108.2), width=PIN_WIDTH)
    polyline(board, '/PUMP_LED_GATE', [(44.125, 108.2), (43.5, 108.9),
                                       (43.5, 114.3), (42.862, 115.05)],
             width=PIN_WIDTH)
    for start, point in (((42.475, 106.6), (41.6, 106.6)),
                         ((42.862, 116.95), (42.862, 118.2))):
        track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point)

    # Mains side: the feed from R710's phase pad down to R712 and into pin 6.
    track(board, '/LOAD_L_ENABLED', (59.6, 108.8), (59.763, 113.0), width=0.6)
    opto_stubs(board, 'U702', {6: '/PUMP_GATE_FEED'})
    track(board, '/PUMP_GATE_FEED', (OPTO_MAINS_STUB_END, 113.46), (56.837, 113.0),
          width=PIN_WIDTH)

    # Gate from pin 4 to Q704 on the back layer.
    opto_stubs(board, 'U702', {4: '/PUMP_TRIAC_GATE'}, pcb.B_Cu)
    polyline(board, '/PUMP_TRIAC_GATE', [(OPTO_MAINS_STUB_END, 118.54),
                                         (58.84, 116.0), (74.0, 116.0),
                                         (77.4, 112.6), (91.54, 112.6),
                                         (91.54, 110.3)], pcb.B_Cu,
             width=PIN_WIDTH)

    # Switched phase along the strip under the heatsink into the middle
    # terminal, then the pump side down to JP24 pin 1 and neutral to pin 2.
    # The pump side stops at the top of its pad to keep 2.5 mm from the
    # neutral run to JP19.
    polyline(board, '/LOAD_L_ENABLED', [(71.0, 106.5), (89.0, 106.5),
                                        (89.0, 108.8)], width=0.9)
    polyline(board, '/PUMP_AC_SWITCHED', [(86.46, 110.3), (86.46, 112.0),
                                          (91.02, 116.5), (91.02, 119.8)],
             width=1.2)
    track(board, '/MAINS_N', (94.98, 120.8), (94.98, 127.5), width=1.2)


def route_pump_enable(board):
    """PB11 into U604's first gate, and its output down to R714.

    U604 sits under Q701, the heater gate's twin, where reset and 3.3 V are
    close. Its pins leave by hand: the raw order west to the R713 pull-down,
    reset north between the pad rows, 3.3 V east to C604, the gated output
    east and south, and the grounds to their own vias. The long legs were
    searched on a 0.25 mm grid that favours F.Cu, then fixed here.

    PB11 is the first pin of U101's east side. It leaves south past the
    bottom-right decoupling and crosses to B.Cu under the 24 V bend, running
    west along the southern edge of the ground plane, so the cut barely
    touches it, before climbing past U602 to Q701. The output hops under the
    24 V branch at y = 93 mm on B.Cu, as the heater's does, and meets R714
    from the north. The corridor to U603 stays open for PB10.
    """
    raw, nrst, v33 = '/PUMP_EN_RAW', '/STM_NRST', '/3V3_CORE'
    gated, gnd = '/PUMP_EN_INTERLOCK', '/GND_UI'

    # Pin escapes.
    polyline(board, raw, [(30.8, 85.025), (29.75, 85.025), (29.25, 84.5),
                          (28.25, 84.5), (28.25, 85.075)], width=PIN_WIDTH)
    polyline(board, nrst, [(30.8, 85.675), (32.0, 85.675), (32.0, 84.25)],
             width=PIN_WIDTH)
    polyline(board, v33, [(34.2, 85.025), (35.25, 85.025), (36.9, 85.425),
                          (37.0, 84.5)], width=PIN_WIDTH)
    polyline(board, gated, [(34.2, 85.675), (35.4, 85.675), (36.0, 86.275),
                            (36.0, 88.5)], width=PIN_WIDTH)
    # Pins 5 and 6 share a via; pin 4, R713 and C604 get one each.
    polyline(board, gnd, [(34.2, 86.325), (34.6, 86.325), (34.6, 87.9)],
             width=PIN_WIDTH)
    track(board, gnd, (34.2, 86.975), (34.6, 86.975), width=PIN_WIDTH)
    for start, point in (((34.6, 87.9), None), ((30.8, 86.975), (29.5, 87.5)),
                         ((28.25, 86.725), (28.25, 87.75)),
                         # East of the heater gate's B.Cu run at x = 36.5.
                         ((36.9, 86.975), (37.9, 87.2))):
        if point:
            track(board, gnd, start, point, width=PIN_WIDTH)
        via(board, gnd, point or start)

    # PB11 from U101 pin 33.
    polyline(board, raw, [(29.25, 84.5), (34.5, 79.25), (34.75, 79.25),
                          (36.5, 77.5), (37.25, 77.5)], width=PIN_WIDTH)
    via(board, raw, (37.25, 77.5))
    polyline(board, raw, [(37.25, 77.5), (37.25, 67.75), (43.75, 61.25),
                          (43.75, 60.75), (46.0, 58.5), (46.0, 55.75),
                          (46.25, 55.5), (51.5, 55.5), (51.75, 55.25),
                          (67.25, 55.25), (67.75, 54.75), (68.0, 54.75),
                          (69.0, 53.75), (71.0, 53.75), (71.5, 53.25),
                          (71.75, 53.25)], pcb.B_Cu, width=PIN_WIDTH)
    via(board, raw, (71.75, 53.25))
    polyline(board, raw, [(71.75, 53.25), (72.25, 52.75), (73.25, 52.75),
                          (74.25, 51.75), (79.0, 51.75), (80.0, 50.75),
                          (80.75, 50.75), (81.25, 50.25), (81.25, 44.75),
                          (81.75, 44.25), (81.75, 43.75)], width=PIN_WIDTH)

    # 3.3 V from C603, reset from the via beside U603, both hopping under
    # Q701's area on B.Cu.
    polyline(board, v33, [(37.0, 84.5), (36.25, 83.75), (36.25, 83.0),
                          (34.75, 81.5), (34.75, 80.0)], width=PIN_WIDTH)
    via(board, v33, (34.75, 80.0))
    polyline(board, v33, [(34.75, 80.0), (32.75, 78.0), (32.75, 77.5)],
             pcb.B_Cu, width=PIN_WIDTH)
    via(board, v33, (32.75, 77.5))
    track(board, v33, (32.75, 77.5), (30.75, 75.5), width=PIN_WIDTH)
    track(board, nrst, (32.0, 84.25), (32.0, 82.75), width=PIN_WIDTH)
    via(board, nrst, (32.0, 82.75))
    polyline(board, nrst, [(32.0, 82.75), (30.25, 81.0), (30.25, 79.25),
                           (29.0, 78.0), (29.0, 72.5)], pcb.B_Cu,
             width=PIN_WIDTH)

    # Gated output down to R714.
    track(board, gated, (36.0, 88.5), (39.25, 91.75), width=PIN_WIDTH)
    via(board, gated, (39.25, 91.75))
    track(board, gated, (39.25, 91.75), (39.25, 104.0), pcb.B_Cu, width=PIN_WIDTH)
    via(board, gated, (39.25, 104.0))
    polyline(board, gated, [(39.25, 104.0), (40.0, 104.75), (40.0, 105.25),
                            (40.75, 106.0), (40.75, 106.75), (42.25, 108.25),
                            (42.475, 108.2)], width=PIN_WIDTH)


def route_debug_header(board):
    """SWDIO, SWCLK and SWO from the north pad row to J102.

    PA13 and PA14 are the two east-most pins of the row but reach J102 in
    crossed order, so SWCLK keeps F.Cu along y = 32.3 mm, under J102.3, and
    SWDIO drops to B.Cu just east of its pad and runs back west under it. SWO
    climbs between J102.1 and J102.2 and runs above the header to pin 6.
    """
    polyline(board, '/STM_SWCLK', [(79.25, 34.33), (79.25, 32.6), (79.55, 32.3),
                                   (81.4, 32.3), (82.12, 31.58), (82.12, 31.0)],
             width=SIGNAL_WIDTH)
    polyline(board, '/STM_SWDIO', [(79.75, 34.33), (79.75, 33.6), (80.4, 33.0)],
             width=SIGNAL_WIDTH)
    via(board, '/STM_SWDIO', (80.4, 33.0))
    polyline(board, '/STM_SWDIO', [(80.4, 33.0), (78.6, 33.0), (77.04, 31.44),
                                   (77.04, 31.0)], pcb.B_Cu, width=SIGNAL_WIDTH)
    polyline(board, '/STM_SWO', [(76.25, 34.33), (76.25, 33.1), (75.8, 32.65),
                                 (75.8, 30.5), (76.5, 29.8), (86.0, 29.8),
                                 (87.2, 31.0)], width=SIGNAL_WIDTH)


def route_supervisor_orders(board):
    """PB4, PB5, PB6 and PB7 from the north pad row to the supervisor side.

    The north-west corner is closed on F.Cu by the pin 64 supply, so the four
    pins leave on B.Cu. PB6 (fault) goes north and west under J102.1; PB7,
    PB5 and PB4 drop into the band inside the pad ring and run west under the
    north row in lanes 0.62 mm apart, south to north in the same order as
    their destinations, so they never cross again. Each lane surfaces west of
    the package on a staggered via. The long legs were searched on a 0.05 mm
    grid that favours F.Cu and fixed here; they pass between the J114 pins and
    under the 24 V branches on short B.Cu hops.
    """
    w = SIGNAL_WIDTH
    arm, sleep = '/MAINS_ARM_RAW', '/BREW_SLEEP_RAW'
    kick, fault = '/WATCHDOG_KICK_RAW', '/BREW_FAULT_N'

    # Escapes.
    polyline(board, arm, [(74.25, 34.33), (74.25, 35.85)], width=w)
    via(board, arm, (74.25, 35.85))
    polyline(board, arm, [(74.25, 35.85), (73.75, 35.35), (71.55, 35.35)],
             pcb.B_Cu, width=w)
    via(board, arm, (71.55, 35.35))
    polyline(board, sleep, [(75.25, 34.33), (75.25, 35.85)], width=w)
    via(board, sleep, (75.25, 35.85))
    polyline(board, sleep, [(75.25, 35.85), (74.13, 34.73), (70.85, 34.73)],
             pcb.B_Cu, width=w)
    via(board, sleep, (70.85, 34.73))
    polyline(board, kick, [(75.75, 34.33), (75.75, 35.5), (76.05, 35.8),
                           (76.05, 36.7)], width=w)
    via(board, kick, (76.05, 36.7))
    polyline(board, kick, [(76.05, 36.7), (76.05, 34.7), (75.46, 34.11),
                           (70.15, 34.11)], pcb.B_Cu, width=w)
    via(board, kick, (70.15, 34.11))
    polyline(board, fault, [(74.75, 34.33), (74.75, 32.8)], width=w)
    via(board, fault, (74.75, 32.8))
    track(board, fault, (74.75, 32.8), (70.8, 32.8), pcb.B_Cu, width=w)
    via(board, fault, (70.8, 32.8))

    # PB6 joins the fault row left by the H-bridge block.
    polyline(board, fault, [(70.8, 32.8), (56.2, 32.8), (56.0, 32.6)], width=w)

    # PB7 to U603 pin 1, the mains arm gate.
    polyline(board, arm, [(71.55, 35.35), (71.5, 35.4), (55.95, 35.4),
                          (51.85, 39.5), (51.85, 49.2), (52.45, 49.8)], width=w)
    via(board, arm, (52.45, 49.8))
    track(board, arm, (52.45, 49.8), (52.45, 51.2), pcb.B_Cu, width=w)
    via(board, arm, (52.45, 51.2))
    polyline(board, arm, [(52.45, 51.2), (52.4, 51.15), (51.2, 51.15),
                          (50.15, 52.2), (50.15, 52.5), (49.4, 53.25),
                          (48.5, 53.25)], width=w)
    via(board, arm, (48.5, 53.25))
    polyline(board, arm, [(48.5, 53.25), (48.5, 54.25), (47.9, 54.85),
                          (45.25, 54.85)], pcb.B_Cu, width=w)
    via(board, arm, (45.25, 54.85))
    polyline(board, arm, [(45.25, 54.85), (45.25, 64.6), (43.05, 66.8),
                          (43.05, 67.15), (37.75, 72.45), (37.75, 73.5),
                          (37.3, 73.95), (33.7, 73.975)], width=w)

    # PB5 to R603 and, under the reset corridor, to U602 pin 1.
    polyline(board, sleep, [(70.85, 34.73), (54.05, 34.75), (49.25, 39.55),
                            (49.25, 42.85), (47.55, 44.55)], width=w)
    via(board, sleep, (47.55, 44.55))
    track(board, sleep, (47.55, 44.55), (45.25, 44.55), pcb.B_Cu, width=w)
    via(board, sleep, (45.25, 44.55))
    polyline(board, sleep, [(45.25, 44.55), (42.05, 47.75), (39.7, 47.75),
                            (38.0, 49.45), (36.35, 49.45), (34.15, 51.65),
                            (34.15, 60.05)], width=w)
    polyline(board, sleep, [(34.15, 60.05), (33.825, 60.4), (33.825, 61.025)],
             width=w)
    via(board, sleep, (34.15, 60.05))
    polyline(board, sleep, [(34.15, 60.05), (34.4, 60.3), (35.65, 60.3)],
             pcb.B_Cu, width=w)
    via(board, sleep, (35.65, 60.3))
    polyline(board, sleep, [(35.65, 60.3), (36.3, 60.95), (36.3, 61.025)],
             width=w)

    # PB4 to R601, the watchdog input.
    polyline(board, kick, [(70.15, 34.11), (54.0, 34.1), (49.3, 38.8),
                           (41.55, 38.8), (40.45, 39.9), (40.45, 45.05),
                           (40.1, 45.4)], width=w)
    via(board, kick, (40.1, 45.4))
    polyline(board, kick, [(40.1, 45.4), (40.1, 53.4), (38.0, 55.5)],
             pcb.B_Cu, width=w)
    via(board, kick, (38.0, 55.5))
    polyline(board, kick, [(38.0, 55.5), (37.15, 56.35), (37.175, 56.8)],
             width=w)


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
    route_usb_power(board)
    route_earth_and_heater_return(board)
    route_heater_enable(board)
    route_heater_stage(board)
    route_pump_stage(board)
    route_pump_enable(board)
    route_debug_header(board)
    route_supervisor_orders(board)
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
                          'reset tree: MCU, pull-up, filter, SWD header and the gates',
                          'service-USB rail, sense divider and bench jumper',
                          'protective-earth bond and the heater neutral return',
                          'heater stage: optocoupler, triac, gate and switched phase',
                          'heater enable: U603 second gate, R711 pull-down and R707',
                          'pump stage: optocoupler, triac, gate, LED loop and JP24',
                          'pump enable: PB11, U604 first gate, R713 pull-down and R714',
                          'SWD header: SWDIO, SWCLK and SWO to J102',
                          'supervisor orders: PB4 kick, PB5 sleep, PB6 fault and PB7 arm'],
        'track_segments': sum(isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA)
                              for item in check.GetTracks()),
        'vias': sum(isinstance(item, pcb.PCB_VIA) for item in check.GetTracks()),
        'remaining_blocks': ['grinder stage',
                             '3V3 trunk and remaining decoupling', 'logic', 'sensors',
                             '24 V actuators', 'final domain copper fills'],
    }
    REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
