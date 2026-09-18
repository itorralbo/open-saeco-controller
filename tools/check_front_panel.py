"""Check actual draft schematic connectivity; this is NOT KiCad ERC.

Deliberately supports only the unrotated, single-sheet subset used in this draft.
Unsupported constructs fail instead of silently claiming electrical validation.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'hardware/front-panel'


def parse(text):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack, roots = [], []
    for token in tokens:
        if token == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ')':
            assert stack, 'Unexpected closing parenthesis'
            stack.pop()
        else:
            assert stack, 'Atom outside root'
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and len(roots) == 1, 'Unbalanced schematic'
    return roots[0]


def children(node, key):
    return [x for x in node if isinstance(x, list) and x[0] == key]


def one(node, key):
    values = children(node, key)
    assert len(values) == 1, (key, len(values))
    return values[0]


def point(node):
    return tuple(round(float(v), 4) for v in node[1:3])


def main():
    root = parse((BASE/'kicad/front-panel-reva.kicad_sch').read_text())
    assert root[0] == 'kicad_sch'
    for unsupported in ('sheet', 'bus', 'bus_entry', 'global_label', 'hierarchical_label'):
        assert not children(root, unsupported), f'Unsupported: {unsupported}'
    parent = {}

    def find(p):
        parent.setdefault(p, p)
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

    def join(a, b):
        parent[find(a)] = find(b)

    for wire in children(root, 'wire'):
        pts = children(one(wire, 'pts'), 'xy')
        assert len(pts) == 2
        a, b = map(point, pts)
        assert a[0] == b[0] or a[1] == b[1], 'Non-orthogonal wire'
        join(a, b)
    labels = {}
    for label in children(root, 'label'):
        p = point(one(label, 'at'))
        assert p in parent, 'Label not attached to a wire endpoint'
        labels.setdefault(find(p), set()).add(label[1])
    assert all(len(v) == 1 for v in labels.values()), 'Conflicting net labels / short'
    nc = {point(one(n, 'at')) for n in children(root, 'no_connect')}
    libs = {s[1]: s for s in children(one(root, 'lib_symbols'), 'symbol')}
    actual, values, refs = {}, {}, set()
    for symbol in children(root, 'symbol'):
        properties = {p[1]: p[2] for p in children(symbol, 'property')}
        ref = properties['Reference']
        if ref.startswith('#'):
            continue  # Virtual power-source assertions, not physical BOM items.
        assert ref not in refs, f'Duplicate reference {ref}'
        refs.add(ref)
        at = one(symbol, 'at')
        assert float(at[3]) == 0 and not children(symbol, 'mirror'), 'Unsupported transform'
        x, y = point(at)
        lib = libs[one(symbol, 'lib_id')[1]]
        actual[ref] = {}
        values[ref] = properties['Value']
        for unit in children(lib, 'symbol'):
            for pin in children(unit, 'pin'):
                dx, dy = point(one(pin, 'at'))
                p = (round(x+dx, 4), round(y-dy, 4))
                n = one(pin, 'number')[1]
                assert n not in actual[ref], f'Duplicate pin {ref}.{n}'
                if p in nc:
                    assert p not in parent, f'NC also wired: {ref}.{n}'
                    actual[ref][n] = None
                else:
                    assert p in parent and find(p) in labels, f'Unconnected: {ref}.{n}'
                    actual[ref][n] = next(iter(labels[find(p)]))

    # Independent manufacturer pin map, TI SCPS197D section 5 (PW package).
    expected_ic = {'1': 'GND_UI', '2': 'GND_UI', '3': 'GND_UI',
                   '8': 'GND_UI', '13': 'KEY_INT_N', '14': 'KEY_SCL',
                   '15': 'KEY_SDA', '16': '3V3_UI'}
    expected_ic.update({str(pin): f'KEY_{i}_N' for i, pin in
                        enumerate([4, 5, 6, 7, 9, 10, 11], 1)})
    expected_ic['12'] = 'LED_STBY_N'  # P7 drives the standby LED, active low.
    assert actual['U1'] == expected_ic, 'TCA9534 package pinout mismatch'
    expected_link = ['3V3_UI', 'GND_UI', 'LCD_SCLK', 'GND_UI', 'LCD_MOSI',
                     'GND_UI', 'LCD_CS_N', 'LCD_DC', 'LCD_RST_N', 'LCD_BL_PWM',
                     'KEY_SCL', 'KEY_SDA', 'KEY_INT_N', 'GND_UI', 'GND_UI', None]
    assert actual['J1'] == dict(zip(map(str, range(1, 17)), expected_link))
    expected_display = ['3V3_UI', 'GND_UI', 'LCD_MOSI', 'LCD_SCLK',
                        'LCD_CS_N', 'LCD_DC', 'LCD_RST_N', 'LCD_BL_PWM']
    assert actual['J2'] == dict(zip(map(str, range(1, 9)), expected_display))

    def pair(ref, value, a, b):
        assert actual[ref] == {'1': a, '2': b}, f'Wrong circuit at {ref}'
        assert values[ref].split(' / ')[0] == value, f'Wrong value at {ref}'

    for i in range(1, 8):
        key, raw = f'KEY_{i}_N', f'SW_{i}_RAW'
        pair(f'R{10+i}', '10k', '3V3_UI', key)
        pair(f'R{20+i}', '1k', key, raw)
        pair(f'SW{i}', f'KEY {i}', raw, 'GND_UI')
        pair(f'C{10+i}', '100nF', key, 'GND_UI')
    for ref, val, a, b in [('R1', '4.7k', '3V3_UI', 'KEY_SCL'),
                          ('R2', '4.7k', '3V3_UI', 'KEY_SDA'),
                          ('R3', '10k', '3V3_UI', 'KEY_INT_N'),
                          ('R4', '10k', '3V3_UI', 'LCD_CS_N'),
                          ('R5', '10k', '3V3_UI', 'LCD_RST_N'),
                          ('R6', '100k', 'LCD_BL_PWM', 'GND_UI'),
                          ('C1', '100nF', '3V3_UI', 'GND_UI'),
                          ('C2', '1uF', '3V3_UI', 'GND_UI'),
                          ('C3', '10uF', '3V3_UI', 'GND_UI'),
                          ('R7', '470', '3V3_UI', 'LED_STBY_A'),
                          ('D1', 'KT-0603R', 'LED_STBY_N', 'LED_STBY_A')]:
        pair(ref, val, a, b)
    net_export = json.loads((BASE/'design-nets.json').read_text())
    assert actual == {c['reference']: c['pins'] for c in net_export['components']}
    with (BASE/'bom-draft.csv').open() as f:
        bom = list(csv.DictReader(f))
    assert len(bom) == len(refs) and {c['reference'] for c in bom} == refs
    print(f'Front panel: {len(refs)} components; draft pinout and RC networks match.')
    print('Not KiCad parsing/ERC, PCB/DRC, signal-integrity or hardware validation.')


if __name__ == '__main__':
    main()
