"""Apply the accepted front-panel mechanics to the working KiCad PCB.

Reads hardware/front-panel/mechanical-source.json and adds the outline as
Edge.Cuts segments and the four 8.4 mm holes as Edge.Cuts circles (milled NPTH,
no screw-head keep-out). Switch centres, DL1, SP1-SP3 and the original JP3 go
to Dwgs.User as placement references; SW1-SW8 still have no footprint. Staging
footprints covered by the new outline (J1, U1) move to the off-board area.

Edits the KiCad 10 S-expression text, so pcbnew is not required. UUIDs derive
from item names: re-running is a no-op, and any other Edge.Cuts geometry stops
the script to protect manual CAD edits. Run KiCad DRC afterwards.
"""
import json
import re
import uuid
from pathlib import Path

from check_front_panel import parse

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'hardware/front-panel'
BOARD_PATH = BASE/'kicad/front-panel-reva.kicad_pcb'
IMPORT_PATH = BASE/'validation/pcb-import.json'
SOURCE = json.loads((BASE/'mechanical-source.json').read_text(encoding='utf-8'))
NS = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/itorralbo/open-saeco-controller/front-panel-mechanics')
STAGING_MOVES = {'J1': ((20, 40), (130, 100)), 'U1': ((55, 55), (130, 88))}
OLD_NOTE = ('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\\n'
            'No outline; connector footprints and mechanical dimensions pending')
NEW_NOTE = ('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\\n'
            'Rev A outline + 8.4 mm holes accepted 2026-09-18 (photo-derived, +/-0.3 mm); '
            'switch references on Dwgs.User')


def uid(name):
    return str(uuid.uuid5(NS, name))


def num(value):
    return f'{value:.4f}'.rstrip('0').rstrip('.')


def stroke(width, kind='default'):
    return f'\t\t(stroke\n\t\t\t(width {num(width)})\n\t\t\t(type {kind})\n\t\t)\n'


def line(name, a, b, layer, width):
    return (f'\t(gr_line\n\t\t(start {num(a[0])} {num(a[1])})\n\t\t(end {num(b[0])} {num(b[1])})\n'
            f'{stroke(width)}\t\t(layer "{layer}")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def circle(name, c, r, layer, width):
    return (f'\t(gr_circle\n\t\t(center {num(c[0])} {num(c[1])})\n\t\t(end {num(c[0]+r)} {num(c[1])})\n'
            f'{stroke(width)}\t\t(fill no)\n\t\t(layer "{layer}")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def rect(name, a, b, layer, width, kind='default'):
    return (f'\t(gr_rect\n\t\t(start {num(a[0])} {num(a[1])})\n\t\t(end {num(b[0])} {num(b[1])})\n'
            f'{stroke(width, kind)}\t\t(fill no)\n\t\t(layer "{layer}")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def text(name, value, at, size=0.8):
    return (f'\t(gr_text "{value}"\n\t\t(at {num(at[0])} {num(at[1])} 0)\n\t\t(layer "Dwgs.User")\n'
            f'\t\t(uuid "{uid(name)}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {num(size)} {num(size)})\n'
            f'\t\t\t\t(thickness {num(size*0.15)})\n\t\t\t)\n\t\t)\n\t)\n')


def edge_items():
    vertices = SOURCE['outline_mm']['vertices']
    items = [(uid(f'edge/{i}'), line(f'edge/{i}', a, vertices[(i+1) % len(vertices)], 'Edge.Cuts', 0.05))
             for i, a in enumerate(vertices)]
    for hole in SOURCE['holes']:
        name = f'hole/{hole["reference"]}'
        items.append((uid(name), circle(name, (hole['x'], hole['y']), hole['diameter']/2, 'Edge.Cuts', 0.05)))
    return items


def reference_items():
    items = []
    add = lambda name, block: items.append((uid(name), block))
    for hole in SOURCE['holes']:
        ref = hole['reference']
        add(f'label/{ref}', text(f'label/{ref}', f'{ref} Ø{num(hole["diameter"])} NPTH',
                                 (hole['x'], hole['y']+hole['diameter']/2+1.2)))
    sw = SOURCE['switches']
    pitch, span = sw['leg_pitch_mm'], sw['pad_outer_span_mm']
    for pos in sw['positions']:
        x, y, key = pos['x'], pos['y'], 'switch/'+pos['original']
        add(key+'/body', rect(key+'/body', (x-3, y-3), (x+3, y+3), 'Dwgs.User', 0.1))
        add(key+'/actuator', circle(key+'/actuator', (x, y), 1.75, 'Dwgs.User', 0.1))
        add(key+'/cross-x', line(key+'/cross-x', (x-1, y), (x+1, y), 'Dwgs.User', 0.1))
        add(key+'/cross-y', line(key+'/cross-y', (x, y-1), (x, y+1), 'Dwgs.User', 0.1))
        vertical = pos['legs'] == 'top/bottom'
        for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            if vertical:
                px, py, hw, hh = x+sx*pitch/2, y+sy*(span/2-0.9), 0.7, 0.9
            else:
                px, py, hw, hh = x+sx*(span/2-0.9), y+sy*pitch/2, 0.9, 0.7
            add(f'{key}/leg{i}', rect(f'{key}/leg{i}', (px-hw, py-hh), (px+hw, py+hh), 'Dwgs.User', 0.05))
        add(key+'/label', text(key+'/label', f'{pos["original"]} ({num(x)}, {num(y)})',
                               (x, y-6.6 if vertical else y-4)))
    for led in SOURCE['indicators']:
        key = 'indicator/'+led['original']
        add(key+'/mark', circle(key+'/mark', (led['x'], led['y']), 0.6, 'Dwgs.User', 0.1))
        add(key+'/label', text(key+'/label', f'{led["original"]} orig.', (led['x']+4, led['y'])))
    for pad in SOURCE['square_pads']:
        key, x, y, s = 'pad/'+pad['reference'], pad['x'], pad['y'], pad['size']
        add(key+'/outline', rect(key+'/outline', (x-s/2, y-s/2), (x+s/2, y+s/2), 'Dwgs.User', 0.1))
        add(key+'/label', text(key+'/label', f'{pad["reference"]} TBD', (x, y+s/2+1)))
    jp3 = SOURCE['reference_only_mm']['JP3']
    add('jp3/zone', rect('jp3/zone', (jp3['x'][0], jp3['y'][0]), (jp3['x'][1], jp3['y'][1]),
                         'Dwgs.User', 0.1, 'dash'))
    add('jp3/label', text('jp3/label', 'JP3 orig. (+/-1 mm)', (sum(jp3['x'])/2, 60.8)))
    return items


def top_level_graphics(board):
    return re.findall(r'\n\t\(gr_\w+\n.*?\n\t\)', board, flags=re.S)


def insert_missing(board, items, label):
    present = [u for u, _ in items if f'(uuid "{u}")' in board]
    if len(present) == len(items):
        print(f'{label}: already present')
        return board
    assert not present, f'{label}: partially present; preserve manual work'
    end = '\n\t(embedded_fonts no)\n)'
    assert board.endswith(end+'\n') or board.endswith(end), 'Unexpected board file ending'
    head, tail = board.rsplit(end, 1)
    print(f'{label}: added {len(items)} items')
    return head+'\n'+''.join(block for _, block in items).rstrip('\n')+end+tail


def move_staging(board):
    for ref, (old, new) in STAGING_MOVES.items():
        match = re.search(r'\n\t\(footprint "[^"]+"\n\t\t\(layer "[^"]+"\)\n\t\t\(uuid "[^"]+"\)\n'
                          r'\t\t\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)\n(?:(?!\n\t\(footprint ).)*?'
                          rf'\(property "Reference" "{ref}"', board, flags=re.S)
        assert match, f'Footprint {ref} not found'
        at = (float(match.group(1)), float(match.group(2)))
        if at == new:
            print(f'{ref}: already at staging {new}')
        elif at == old:
            start, end = match.span(1)[0], match.span(2)[1]
            board = board[:start]+f'{num(new[0])} {num(new[1])}'+board[end:]
            print(f'{ref}: moved {old} -> {new} (off-board staging)')
        else:
            print(f'{ref}: at {at}, left untouched')
    return board


def main():
    assert SOURCE['status'] == 'owner_accepted_rev_a_baseline'
    assert SOURCE['mechanical_layout_released'] is True
    assert SOURCE['manufacturing_release'] is False
    raw = BOARD_PATH.read_bytes()
    crlf = b'\r\n' in raw
    board = raw.decode('utf-8').replace('\r\n', '\n')

    edges = edge_items()
    ours = {u for u, _ in edges}
    found = {re.search(r'\(uuid "([^"]+)"\)', g).group(1)
             for g in top_level_graphics(board) if '(layer "Edge.Cuts")' in g}
    assert not found or found == ours, 'Unexpected Edge.Cuts; preserve manual work'
    board = insert_missing(board, edges, 'Edge.Cuts outline + holes')
    board = insert_missing(board, reference_items(), 'Dwgs.User references')
    board = move_staging(board)
    if OLD_NOTE in board:
        head, tail = board.split(OLD_NOTE, 1)
        tail = tail.replace('\n\t\t(at 75 30 0)', '\n\t\t(at 92 -6 0)', 1)
        board = head+NEW_NOTE+tail

    root = parse(board)
    assert root[0] == 'kicad_pcb'
    edge_uuids = {re.search(r'\(uuid "([^"]+)"\)', g).group(1)
                  for g in top_level_graphics(board) if '(layer "Edge.Cuts")' in g}
    assert edge_uuids == ours
    vertices = SOURCE['outline_mm']['vertices']
    max_y = max(v[1] for v in vertices)
    for ref, (_, new) in STAGING_MOVES.items():
        assert new[1] > max_y+5, f'{ref} staging position overlaps the board'
    BOARD_PATH.write_bytes(board.replace('\n', '\r\n' if crlf else '\n').encode('utf-8'))

    report = json.loads(IMPORT_PATH.read_text(encoding='utf-8'))
    report['outline'] = True
    report['edge_cuts_items'] = len(ours)
    report['outline_source'] = 'hardware/front-panel/mechanical-source.json'
    IMPORT_PATH.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'Front PCB: {len(vertices)} outline segments, {len(SOURCE["holes"])} milled holes; '
          'run KiCad DRC to validate.')


if __name__ == '__main__':
    main()
