"""Place, autoroute and pour the front panel PCB (source of truth for the layout).

1. Places every footprint: switches, LED and connectors from mechanical-source.json,
   the key RC networks in two combs beside U1 (hardware/front-panel/layout.md).
2. Adds a short stub and via to GND next to every SMD GND pad.
3. Exports Specctra DSN without GND_UI, routes it with Freerouting and imports
   the session. GND is carried by pours on both layers plus stitching vias.
Re-running replaces tracks, vias and zones. Edit this script, not the board, or
port manual edits here first. Run with KiCad Python after sync_front_panel_pcb.py:

    <KiCad python> tools/layout_front_panel_pcb.py [--no-route | --silk-only]

Freerouting is found through FREEROUTING or the default Windows install.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'hardware/front-panel'
BOARD_PATH = BASE/'kicad/front-panel-reva.kicad_pcb'
WORK = BASE/'validation/autoroute'
MECH = json.loads((BASE/'mechanical-source.json').read_text(encoding='utf-8'))
MM = pcb.FromMM
GND, VCC = '/GND_UI', '/3V3_UI'
VIA, DRILL, STUB = 0.6, 0.3, 0.3
PASSES = 40

SWITCH_POS = {p['original']: (p['x'], p['y']) for p in MECH['switches']['positions']}
LED_POS = (MECH['indicators'][0]['x'], MECH['indicators'][0]['y'])

# ref: (x, y, rotation in degrees). Rotations put RAW pads (pin 1) towards U1.
PLACE = {
    'SW1': (*SWITCH_POS['PB1'], 180), 'SW2': (*SWITCH_POS['PB2'], 180),
    'SW3': (*SWITCH_POS['PB3'], 180), 'SW4': (*SWITCH_POS['PB8'], 270),
    'SW5': (*SWITCH_POS['PB4/PB6'], 0), 'SW6': (*SWITCH_POS['PB5'], 0),
    'SW7': (*SWITCH_POS['PB7'], 0),
    'D1': (*LED_POS, 180), 'R7': (LED_POS[0]-3.0, LED_POS[1], 0),
    'J2': (99.0, 6.6, 180),        # PH8 opening towards the top edge, pin 1 at x=99
    'J1': (139.7, 57.3, 90),       # IDC 2x8 in the JP3 tab, pin 1 bottom-left
    'C3': (131.5, 57.5, 90),
    'U1': (112.0, 30.0, 0),
    'C1': (116.2, 25.8, 0), 'C2': (116.2, 24.0, 0),
    'R1': (122.4, 42.6, 180), 'R2': (122.4, 44.2, 180), 'R3': (122.4, 41.0, 180),
    'R4': (91.0, 10.4, 90), 'R5': (87.0, 10.4, 90), 'R6': (85.0, 10.4, 270),
}
# Key channel rows: left comb (KEY_1..4, U1 P0-P3) and right comb (KEY_5..7, P4-P6).
# In each row: C1x (KEY over GND), R1x (3V3 over KEY) and R2x in line to the switch.
LEFT_ROWS = {1: 24.5, 2: 28.0, 3: 31.5, 4: 35.0}
RIGHT_ROWS = {7: 27.0, 6: 30.5, 5: 34.0}
for i, y in LEFT_ROWS.items():
    PLACE[f'C1{i}'] = (101.5, y+0.775, 270)
    PLACE[f'R1{i}'] = (99.5, y-0.825, 270)
    PLACE[f'R2{i}'] = (96.5, y, 180)
for i, y in RIGHT_ROWS.items():
    PLACE[f'C1{i}'] = (123.0, y+0.775, 270)
    PLACE[f'R1{i}'] = (125.0, y-0.825, 270)
    PLACE[f'R2{i}'] = (128.0, y, 0)

# (ref, pad position selector, via x, via y): stub from the pad to a GND via.
GND_VIAS = [('U1', (109.138, 28.375), 107.7, 28.375), ('U1', (109.138, 32.275), 107.7, 32.275),
            ('C1', (116.975, 25.8), 118.1, 25.8), ('C3', (131.5, 56.725), 130.1, 56.725),
            ('R6', (85.0, 11.225), 85.0, 12.6), ('J2', (97.0, 6.6), 97.0, 9.3),
            ('SW4', (87.057, 45.75), 85.2, 45.75), ('SW4', (96.343, 45.75), 98.2, 45.75)]
GND_VIAS += [(f'C1{i}', (101.5, y+1.55), 102.75, y+1.55) for i, y in LEFT_ROWS.items()]
GND_VIAS += [(f'C1{i}', (123.0, y+1.55), 121.75, y+1.55) for i, y in RIGHT_ROWS.items()]
for ref, dx in (('SW1', -1.95), ('SW2', -1.95), ('SW3', -1.95), ('SW5', 1.95), ('SW6', 1.95), ('SW7', 1.95)):
    x, y, _ = PLACE[ref]
    padx = x+(2.25 if dx > 0 else -2.25)
    GND_VIAS += [(ref, (padx, y+s*4.643), padx+dx, y+s*4.643) for s in (-1, 1)]
# Short joins inside the same GND net: U1 A0-A2 and the C1/C2 GND pads.
GND_JOINS = [((108.55, 27.725), (108.55, 29.025)), ((116.975, 24.0), (116.975, 25.8))]


def place(board):
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    assert set(fps) == set(PLACE), sorted(set(fps) ^ set(PLACE))
    for ref, (x, y, rot) in PLACE.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(0)
        fp.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        # Dense 0603 combs: designators live on the fabrication layer, not on silk.
        fp.Reference().SetLayer(pcb.F_Fab if ref[0] in 'RC' else pcb.F_SilkS)
    for ref, (x, y) in REF_POS.items():
        text = fps[ref].Reference()
        text.SetTextAngleDegrees(0)
        text.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
        text.SetTextSize(pcb.VECTOR2I(MM(1.0), MM(1.0)))
        text.SetTextThickness(MM(0.15))
    model = '${KICAD10_3DMODEL_DIR}/Button_Switch_SMD.3dshapes/SW_SPST_PTS645Sx43SMTR92.step'
    for ref, fp in fps.items():
        if ref.startswith('SW') and not any(m.m_Filename == model for m in fp.Models()):
            stand_in = pcb.FP_3DMODEL()
            stand_in.m_Filename = model
            stand_in.m_Rotation = pcb.VECTOR3D(0, 0, 90)
            fp.Models().push_back(stand_in)
    # THT GND pins of the connectors sit between bus tracks: solid, not thermal, joints.
    for ref in ('J1', 'J2'):
        for pad in fps[ref].Pads():
            if pad.GetNetname() == GND:
                pad.SetLocalZoneConnection(pcb.ZONE_CONNECTION_FULL)
    # U1 GND pins reach their vias through explicit tracks; no pour spokes at 0.65 mm pitch.
    for pad in fps['U1'].Pads():
        if pad.GetNetname() == GND:
            pad.SetLocalZoneConnection(pcb.ZONE_CONNECTION_NONE)
    return fps


def hole_keepouts(board, margin=0.6, sides=32):
    """Rule areas around the milled holes: Freerouting keeps tracks and vias away."""
    layers = pcb.LSET()
    layers.AddLayer(pcb.F_Cu)
    layers.AddLayer(pcb.B_Cu)
    for hole in MECH['holes']:
        z = pcb.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetLayerSet(layers)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetZoneName(f'keepout {hole["reference"]}')
        poly = z.Outline()
        poly.NewOutline()
        r = hole['diameter']/2+margin
        for k in range(sides):
            a = 2*math.pi*k/sides
            poly.Append(MM(hole['x']+r*math.cos(a)), MM(hole['y']+r*math.sin(a)))
        board.Add(z)


def clear_copper(board):
    for item in list(board.GetTracks()):
        board.Delete(item)
    for zone in list(board.Zones()):
        board.Delete(zone)


def net(board, name):
    item = board.FindNet(name)
    assert item, name
    return item


def track(board, netname, a, b, width, layer=pcb.F_Cu, locked=True):
    t = pcb.PCB_TRACK(board)
    t.SetStart(pcb.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcb.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width))
    t.SetLayer(layer)
    t.SetNet(net(board, netname))
    t.SetLocked(locked)
    board.Add(t)


def via(board, netname, x, y, locked=True):
    v = pcb.PCB_VIA(board)
    v.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(VIA))
    v.SetDrill(MM(DRILL))
    v.SetNet(net(board, netname))
    v.SetLocked(locked)
    board.Add(v)


def gnd_fanout(board):
    pads = {(round(pcb.ToMM(p.GetPosition().x), 2), round(pcb.ToMM(p.GetPosition().y), 2)): p
            for fp in board.GetFootprints() for p in fp.Pads()}
    for ref, (px, py), vx, vy in GND_VIAS:
        pad = pads[(round(px, 2), round(py, 2))]
        assert pad.GetParentFootprint().GetReference() == ref and pad.GetNetname() == GND, (ref, px, py)
        track(board, GND, (px, py), (vx, vy), STUB)
        via(board, GND, vx, vy)
    for a, b in GND_JOINS:
        track(board, GND, a, b, STUB)


def freerouting_exe():
    candidates = [os.environ.get('FREEROUTING'),
                  str(Path(os.environ.get('LOCALAPPDATA', ''))/'Freerouting/freerouting.exe')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit('Freerouting not found; set FREEROUTING to freerouting.exe or a jar launcher.')


def unroute_net(dsn_text, netname):
    """Empty a net's pin list so Freerouting leaves it to the pours; its fixed wires stay."""
    start = dsn_text.index(f'(net {netname}\n')
    pins = dsn_text.index('(pins', start)
    depth, i = 0, pins
    while True:
        depth += {'(': 1, ')': -1}.get(dsn_text[i], 0)
        i += 1
        if depth == 0:
            break
    return dsn_text[:pins]+dsn_text[i:]


def autoroute(board):
    WORK.mkdir(parents=True, exist_ok=True)
    dsn, ses = WORK/'front-panel.dsn', WORK/'front-panel.ses'
    assert pcb.ExportSpecctraDSN(board, str(dsn)), 'DSN export failed'
    dsn.write_text(unroute_net(dsn.read_text(encoding='utf-8'), GND), encoding='utf-8')
    if ses.exists():
        ses.unlink()
    cmd = [freerouting_exe(), '-de', str(dsn), '-do', str(ses), '-mp', str(PASSES),
           '--gui.enabled=false']
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    (WORK/'freerouting.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    assert ses.exists(), f'Freerouting produced no session; see {WORK/"freerouting.log"}'
    assert pcb.ImportSpecctraSES(board, str(ses)), 'SES import failed'


def zones(board):
    outline = MECH['outline_mm']['vertices']
    for layer in (pcb.F_Cu, pcb.B_Cu):
        z = pcb.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(net(board, GND))
        poly = z.Outline()
        poly.NewOutline()
        for x, y in outline:
            poly.Append(MM(x), MM(y))
        z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName(f'GND {"top" if layer == pcb.F_Cu else "bottom"}')
        board.Add(z)


def inside_outline(x, y, margin):
    pts = MECH['outline_mm']['vertices']
    inside = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]+pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1+(y-y1)*(x2-x1)/(y2-y1):
            inside = not inside
    if not inside:
        return False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]+pts[:1]):
        if seg_dist((x, y), (x1, y1), (x2, y2)) < margin:
            return False
    return all(math.hypot(x-h['x'], y-h['y']) > h['diameter']/2+margin for h in MECH['holes'])


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx-ax, by-ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))


def stitching(board, pitch=7.0):
    """GND vias on a grid wherever they clear every other copper item by 0.35 mm."""
    obstacles = []   # (kind, geometry, radius)
    for t in board.GetTracks():
        if t.GetNetname() == GND:
            continue
        if isinstance(t, pcb.PCB_VIA):
            p = t.GetPosition()
            obstacles.append(('c', (pcb.ToMM(p.x), pcb.ToMM(p.y)), pcb.ToMM(t.GetWidth(pcb.F_Cu))/2))
        else:
            a, b = t.GetStart(), t.GetEnd()
            obstacles.append(('s', ((pcb.ToMM(a.x), pcb.ToMM(a.y)), (pcb.ToMM(b.x), pcb.ToMM(b.y))),
                              pcb.ToMM(t.GetWidth())/2))
    vias = [(pcb.ToMM(t.GetPosition().x), pcb.ToMM(t.GetPosition().y)) for t in board.GetTracks()
            if isinstance(t, pcb.PCB_VIA)]
    boxes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            boxes.append((pcb.ToMM(bb.GetLeft()), pcb.ToMM(bb.GetTop()), pcb.ToMM(bb.GetRight()), pcb.ToMM(bb.GetBottom())))
        cy = fp.GetCourtyard(pcb.F_Cu).BBox()
        if fp.GetReference().startswith(('U', 'J')):
            boxes.append((pcb.ToMM(cy.GetLeft()), pcb.ToMM(cy.GetTop()), pcb.ToMM(cy.GetRight()), pcb.ToMM(cy.GetBottom())))
    added = 0
    y = 2.0
    while y < 62.3:
        x = 2.0
        while x < 184:
            ok = inside_outline(x, y, VIA/2+0.6)
            ok = ok and all(math.hypot(x-vx, y-vy) > 2.0 for vx, vy in vias)
            ok = ok and all(not (l-0.65 < x < r+0.65 and t-0.65 < y < b+0.65) for l, t, r, b in boxes)
            for kind, geo, radius in obstacles if ok else []:
                d = math.hypot(x-geo[0], y-geo[1]) if kind == 'c' else seg_dist((x, y), *geo)
                if d < VIA/2+radius+0.35:
                    ok = False
                    break
            if ok:
                via(board, GND, x, y, locked=False)
                vias.append((x, y))
                added += 1
            x += pitch
        y += pitch
    return added


def anchor_islands(board, rounds=6, step=0.4):
    """Join every GND fill island to the main pour with vias.

    Islands (both layers) are linked by GND vias and THT pads; any group not linked
    to the largest islands gets a via where one of its islands overlaps the main
    island of the other layer. The fill keeps clearance to other nets, holes and
    edges, so a via fully covered by fill on both layers is clear by construction.
    """
    added = 0
    for _ in range(rounds):
        pcb.ZONE_FILLER(board).Fill(board.Zones())
        pours = {z.GetLayer(): z.GetFilledPolysList(z.GetLayer()) for z in board.Zones()
                 if not z.GetIsRuleArea()}
        # (layer, fill, index): Contains(point, index) honours the island's holes.
        islands = [(layer, polys, i) for layer, polys in pours.items() for i in range(polys.OutlineCount())]
        bridges = [t.GetPosition() for t in board.GetTracks()
                   if isinstance(t, pcb.PCB_VIA) and t.GetNetname() == GND]
        bridges += [pad.GetPosition() for fp in board.GetFootprints() for pad in fp.Pads()
                    if pad.GetNetname() == GND and pad.GetAttribute() == pcb.PAD_ATTRIB_PTH]
        parent = list(range(len(islands)))

        def find(i):
            while parent[i] != i:
                i = parent[i]
            return i
        for point in bridges:
            hit = [k for k, (_, polys, i) in enumerate(islands) if polys.Contains(point, i)]
            for k in hit[1:]:
                parent[find(k)] = find(hit[0])
        main = {layer: max((k for k, (l, _, _) in enumerate(islands) if l == layer),
                           key=lambda k: islands[k][1].Outline(islands[k][2]).Area()) for layer in pours}
        root = find(main[pcb.F_Cu])
        parent[find(main[pcb.B_Cu])] = root
        root = find(root)
        keep = [pad for fp in board.GetFootprints() for pad in fp.Pads()]
        new = 0
        done = set()
        for k, (layer, polys, i) in enumerate(islands):
            group = find(k)
            if group == root or group in done or polys.Outline(i).Area() < MM(1)**2:
                continue
            other = islands[main[pcb.B_Cu if layer == pcb.F_Cu else pcb.F_Cu]]
            spot = free_spot((polys, i), other[1:], keep, bridges, step)
            if spot:
                via(board, GND, *spot, locked=False)
                done.add(group)
                new += 1
            else:
                bb = polys.Outline(i).BBox()
                print(f'WARNING: no via spot for GND island near ({pcb.ToMM(bb.Centre().x):.1f}, '
                      f'{pcb.ToMM(bb.Centre().y):.1f}) on {board.GetLayerName(layer)}')
        added += new
        if not new:
            break
    return added


def free_spot(island, other, pads, vias, step, r=VIA/2+0.1):
    (polys, index), (other_polys, other_index) = island, other
    bb = polys.Outline(index).BBox()
    x0, y0, x1, y1 = (pcb.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    cx, cy = (x0+x1)/2, (y0+y1)/2
    points = [(x0+i*step, y0+j*step) for i in range(int((x1-x0)/step)+1) for j in range(int((y1-y0)/step)+1)]
    boxes = []
    for pad in pads:
        bb = pad.GetBoundingBox()
        boxes.append((pcb.ToMM(bb.GetLeft())-0.6, pcb.ToMM(bb.GetTop())-0.6,
                      pcb.ToMM(bb.GetRight())+0.6, pcb.ToMM(bb.GetBottom())+0.6))
    others = [(pcb.ToMM(v.x), pcb.ToMM(v.y)) for v in vias]
    for x, y in sorted(points, key=lambda q: (q[0]-cx)**2+(q[1]-cy)**2):
        if any(l < x < r_ and t < y < b for l, t, r_, b in boxes):
            continue
        if any(math.hypot(x-vx, y-vy) < 1.0 for vx, vy in others):
            continue
        ring = [(x, y)]+[(x+r*math.cos(a*math.pi/4), y+r*math.sin(a*math.pi/4)) for a in range(8)]
        if all(polys.Contains(pcb.VECTOR2I(MM(px), MM(py)), index) and
               other_polys.Contains(pcb.VECTOR2I(MM(px), MM(py)), other_index) for px, py in ring):
            return round(x, 2), round(y, 2)
    return None


# Silkscreen designators that the footprint default would put far from the part.
REF_POS = {'U1': (112.0, 34.3), 'J2': (80.6, 6.6), 'J1': (148.6, 50.4), 'D1': (91.8, 50.3)}
# (layer, text, x, y, size): board identity and JLCPCB order-number placeholder.
LABELS = [(pcb.F_SilkS, 'OPEN SAECO - FRONTAL Rev A.0', 62.0, 50.8, 1.2),
          (pcb.B_SilkS, 'JLCJLCJLCJLC', 62.0, 21.5, 1.0)]


def labels(board):
    for item in list(board.GetDrawings()):
        if isinstance(item, pcb.PCB_TEXT) and item.GetText() in {t for _, t, *_ in LABELS}:
            board.Delete(item)
    for layer, text, x, y, size in LABELS:
        t = pcb.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(layer)
        t.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
        t.SetTextSize(pcb.VECTOR2I(MM(size), MM(size)))
        t.SetTextThickness(MM(size*0.15))
        t.SetMirrored(layer == pcb.B_SilkS)
        board.Add(t)


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    if '--silk-only' in sys.argv:
        place(board)   # same coordinates: copper stays valid; refreshes text and models
        labels(board)
        pcb.SaveBoard(str(BOARD_PATH), board)
        print('Silkscreen, designators and 3D models refreshed; routing untouched.')
        return
    clear_copper(board)
    fps = place(board)
    labels(board)
    hole_keepouts(board)
    gnd_fanout(board)
    if '--no-route' not in sys.argv:
        autoroute(board)
    stitched = stitching(board)
    zones(board)
    anchored = anchor_islands(board)
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    tracks = [t for t in check.GetTracks() if not isinstance(t, pcb.PCB_VIA)]
    print(f'Placed {len(fps)} footprints; {len(tracks)} track segments, '
          f'{len(list(check.GetTracks()))-len(tracks)} vias ({stitched} stitching, {anchored} island anchors), '
          f'{len(list(check.Zones()))} zones (GND pours and hole keep-outs).')


if __name__ == '__main__':
    main()
