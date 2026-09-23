#!/usr/bin/env python3
"""Front silkscreen of the controller: logo, title, connector names and marks.

Run with KiCad's Python after route_controller_pcb.py. Everything it draws
lives in one group, which it deletes and redraws on every run.

- The owner's logo (hardware/controller/silkscreen/bicho.png, traced into
  bicho-outline.json by trace_silkscreen_logo.py) and the title sit in the
  free SELV corner above PS701.
- Every harness and service connector gets a label with the original board's
  name (JPxx) and what it goes to. Labels are placed automatically: the first
  candidate position around the connector whose text box clears pads,
  footprint silkscreen, courtyards, the board edge and the other labels.
- Polarity marks on JP8 (+/-) and JP17 (L/N), the two PE tabs, and a
  mains warning in the copper-free barrier band.
"""
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / 'hardware/controller/kicad/controller-core-reva.kicad_pcb'
LOGO_PATH = ROOT / 'hardware/controller/silkscreen/bicho-outline.json'
REPORT = ROOT / 'hardware/controller/validation/silkscreen.json'
MM = pcb.FromMM
GROUP_NAME = 'silkscreen: logo, title and connector labels'

LOGO_ORIGIN = (117.0, 11.5)
TITLE = (('OPEN SAECO CONTROLLER', 1.1, 0.16), ('HD8911 · Rev A · 2026', 1.0, 0.15))
TITLE_TOP = 25.8

# Connector labels: original harness name first, then what it feeds.
LABELS = {
    'J118': 'JP17 RED 230 V',
    'J116': '< JP19 CALENTADOR',
    'J117': 'JP24 BOMBA',
    'J115': 'JP8 MOLINILLO',
    'J119': 'JP1 PE',
    'J120': 'JP9 PE',
    'J113': 'JP3 VALVULA',
    'J105': 'JP13 NTC',
    'J106': 'JP5 CAUDAL',
    'J109': 'JP22 AGUA',
    'J107': 'JP14 PUERTA',
    'J108': 'JP16 GRUPO',
    'J104': 'JP21 FRONTAL',
    'J110': 'USB SERVICIO',
    'J101': '12 V BANCO',
    'J112': '24 V BANCO',
    'J102': 'SWD STM32',
    'J103': 'UART ESP32',
    'J111': 'USB BANCO',
    'J121': '24 V INT',
    'J114': 'MEDIDA',
}
# Labels the automatic search puts somewhere ambiguous: (x, y, angle).
# JP8 stands upright in the gap between J115 and JP19; JP21 goes under the
# right half of the IDC header rather than beside the USB-C.
# JP17 sits under its L/N marks, and JP19, boxed in by JP8 and JP24, points
# back at its block from the free strip east of it.
LABEL_AT = {'J115': (71.1, 121.4, 90.0), 'J104': (23.5, 11.2, 0.0),
            'J118': (110.0, 131.3, 0.0), 'J116': (96.5, 128.9, 0.0)}
# Pin marks: (reference, pad, text), straight above or below their pin.
PIN_MARKS = (('J115', '1', '+'), ('J115', '3', '-'),
             ('J118', '1', 'L'), ('J118', '3', 'N'))
WARNING_AT = (58.5, 60.0)

TEXT_SIZES = ((1.0, 0.15), (0.8, 0.12))
GAPS = (0.4, 0.9, 1.5)
SHIFTS = (0.0, -2.0, 2.0, -4.0, 4.0, -6.0, 6.0)
PAD_CLEARANCE = 0.25
EDGE_CLEARANCE = 0.6


def box_mm(box, grow=0.0):
    return (pcb.ToMM(box.GetLeft()) - grow, pcb.ToMM(box.GetTop()) - grow,
            pcb.ToMM(box.GetRight()) + grow, pcb.ToMM(box.GetBottom()) + grow)


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class Placer:
    """Keeps the boxes that silkscreen text must stay clear of."""

    def __init__(self, board):
        self.edge = box_mm(board.GetBoardEdgesBoundingBox())
        self.hard = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                self.hard.append(box_mm(pad.GetBoundingBox(), PAD_CLEARANCE))
            for item in fp.GraphicalItems():
                if item.GetLayer() == pcb.F_SilkS:
                    self.hard.append(box_mm(item.GetBoundingBox(), 0.15))
            courtyard = fp.GetCourtyard(pcb.F_CrtYd)
            if courtyard.OutlineCount():
                self.hard.append(box_mm(courtyard.BBox(), 0.1))
        for item in board.GetDrawings():
            if item.GetLayer() == pcb.Edge_Cuts:
                self.hard.append(box_mm(item.GetBoundingBox(), EDGE_CLEARANCE))
        for zone in board.Zones():
            if zone.GetIsRuleArea() and zone.GetDoNotAllowFootprints():
                self.hard.append(box_mm(zone.GetBoundingBox()))

    def free(self, box):
        x0, y0, x1, y1 = self.edge
        if (box[0] < x0 + EDGE_CLEARANCE or box[1] < y0 + EDGE_CLEARANCE or
                box[2] > x1 - EDGE_CLEARANCE or box[3] > y1 - EDGE_CLEARANCE):
            return False
        return not any(overlaps(box, other) for other in self.hard)

    def take(self, box):
        self.hard.append((box[0] - 0.2, box[1] - 0.2, box[2] + 0.2, box[3] + 0.2))


def text(board, value, point, size, thickness, angle=0.0):
    item = pcb.PCB_TEXT(board)
    item.SetText(value)
    item.SetLayer(pcb.F_SilkS)
    item.SetTextSize(pcb.VECTOR2I(MM(size), MM(size)))
    item.SetTextThickness(MM(thickness))
    item.SetHorizJustify(pcb.GR_TEXT_H_ALIGN_CENTER)
    item.SetVertJustify(pcb.GR_TEXT_V_ALIGN_CENTER)
    item.SetTextAngleDegrees(angle)
    item.SetPosition(pcb.VECTOR2I(MM(point[0]), MM(point[1])))
    return item


def candidates(courtyard, vertical):
    """Centres around a connector: beside it for edge connectors, else above/below."""
    l, t, r, b = courtyard
    cx, cy = (l + r) / 2, (t + b) / 2
    for gap in GAPS:
        if vertical:
            for shift in SHIFTS:
                yield (r + gap, cy + shift), 90.0, 'right'
                yield (l - gap, cy + shift), 90.0, 'left'
        for shift in SHIFTS:
            yield (cx + shift, b + gap), 0.0, 'below'
            yield (cx + shift, t - gap), 0.0, 'above'
    # Connectors hemmed in above and below: beside them, level or upright.
    for gap in GAPS:
        for shift in SHIFTS + (8.0, 10.0):
            yield (r + gap, cy + shift), 0.0, 'right'
            yield (l - gap, cy + shift), 0.0, 'left'
        for shift in SHIFTS:
            yield (r + gap, cy + shift), 90.0, 'right'
            yield (l - gap, cy + shift), 90.0, 'left'


def mark_candidates(courtyard):
    l, t, r, b = courtyard
    for gap in GAPS + (2.0,):
        yield ((l + r) / 2, b + gap), 0.0, 'below'
        yield ((l + r) / 2, t - gap), 0.0, 'above'


def place(board, placer, value, courtyard, vertical=False, spots=None):
    for size, thickness in TEXT_SIZES:
        spots_here = spots(courtyard) if spots else candidates(courtyard, vertical)
        for (x, y), angle, side in spots_here:
            item = text(board, value, (x, y), size, thickness, angle)
            box = box_mm(item.GetBoundingBox())
            # Push the text off the courtyard by its own half size.
            dx = dy = 0.0
            if side == 'below':
                dy = (box[3] - box[1]) / 2
            elif side == 'above':
                dy = -(box[3] - box[1]) / 2
            elif side == 'right':
                dx = (box[2] - box[0]) / 2
            else:
                dx = -(box[2] - box[0]) / 2
            item.Move(pcb.VECTOR2I(MM(dx), MM(dy)))
            box = box_mm(item.GetBoundingBox())
            if placer.free(box):
                placer.take(box)
                return item, box
    raise RuntimeError(f'No room for the silkscreen label {value!r}')


def logo(board):
    data = json.loads(LOGO_PATH.read_text())
    x0, y0 = LOGO_ORIGIN
    poly = pcb.SHAPE_POLY_SET()
    poly.NewOutline()
    for x, y in data['outer']:
        poly.Append(MM(x0 + x), MM(y0 + y))
    for hole in data['holes']:
        poly.NewHole()
        for x, y in hole:
            poly.Append(MM(x0 + x), MM(y0 + y), -1, 0)
    poly.Fracture()
    shape = pcb.PCB_SHAPE(board, pcb.SHAPE_T_POLY)
    shape.SetPolyShape(poly)
    shape.SetFilled(True)
    shape.SetWidth(0)
    shape.SetLayer(pcb.F_SilkS)
    box = (x0, y0, x0 + data['width_mm'], y0 + data['height_mm'])
    return shape, box


def warning(board, point):
    """Triangle with an exclamation mark and the mains legend beside it."""
    x, y = point
    side = 4.0
    top = (x, y - side * 0.5)
    left = (x - side / 2, y + side * 0.37)
    right = (x + side / 2, y + side * 0.37)
    items = []
    for start, end in ((top, left), (left, right), (right, top)):
        line = pcb.PCB_SHAPE(board, pcb.SHAPE_T_SEGMENT)
        line.SetStart(pcb.VECTOR2I(MM(start[0]), MM(start[1])))
        line.SetEnd(pcb.VECTOR2I(MM(end[0]), MM(end[1])))
        line.SetWidth(MM(0.25))
        line.SetLayer(pcb.F_SilkS)
        items.append(line)
    items.append(text(board, '!', (x, y + 0.25), 1.6, 0.25))
    items.append(text(board, 'PELIGRO 230 V~', (x + 9.5, y - 0.6), 1.0, 0.15))
    items.append(text(board, 'ZONA DE RED', (x + 9.5, y + 1.0), 1.0, 0.15))
    return items


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    for group in list(board.Groups()):
        if group.GetName() == GROUP_NAME:
            for item in list(group.GetItems()):
                board.Delete(item)
            board.Delete(group)
    placer = Placer(board)
    group = pcb.PCB_GROUP(board)
    group.SetName(GROUP_NAME)
    board.Add(group)

    def add(item):
        board.Add(item)
        group.AddItem(item)

    shape, box = logo(board)
    assert placer.free(box), 'logo area is not free'
    placer.take(box)
    add(shape)
    y = TITLE_TOP
    cx = (box[0] + box[2]) / 2
    for value, size, thickness in TITLE:
        item = text(board, value, (cx, y + size / 2), size, thickness)
        tbox = box_mm(item.GetBoundingBox())
        assert placer.free(tbox), f'title line {value!r} is not free'
        placer.take(tbox)
        add(item)
        y += size + 1.1

    for item in warning(board, WARNING_AT):
        add(item)

    placed = {}
    for ref, number, value in PIN_MARKS:
        fp = board.FindFootprintByReference(ref)
        pad = next(p for p in fp.Pads() if p.GetNumber() == number)
        px = pcb.ToMM(pad.GetPosition().x)
        courtyard = box_mm(fp.GetCourtyard(pcb.F_CrtYd).BBox())
        item, tbox = place(board, placer, value, (px - 0.5, courtyard[1], px + 0.5, courtyard[3]),
                           spots=mark_candidates)
        add(item)
        placed[f'{ref}.{number}'] = {'text': value, 'box_mm': [round(v, 2) for v in tbox]}

    for ref, value in LABELS.items():
        fp = board.FindFootprintByReference(ref)
        courtyard = box_mm(fp.GetCourtyard(pcb.F_CrtYd).BBox())
        if ref in LABEL_AT:
            x, y, angle = LABEL_AT[ref]
            item = text(board, value, (x, y), *TEXT_SIZES[0], angle)
            tbox = box_mm(item.GetBoundingBox())
            assert placer.free(tbox), f'fixed label {value!r} is not free'
            placer.take(tbox)
        else:
            vertical = courtyard[0] < 8.0 and (courtyard[3] - courtyard[1]) > (courtyard[2] - courtyard[0])
            item, tbox = place(board, placer, value, courtyard, vertical)
        add(item)
        placed[ref] = {'text': value, 'box_mm': [round(v, 2) for v in tbox]}

    pcb.SaveBoard(str(BOARD_PATH), board)
    report = {'logo_box_mm': [round(v, 2) for v in box], 'labels': placed}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'Silkscreen: logo, {len(TITLE)} title lines, {len(placed)} labels and marks.')


if __name__ == '__main__':
    main()
